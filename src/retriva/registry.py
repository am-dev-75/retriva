# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Thread-safe capability registry for Retriva's pluggable architecture.

The registry maps capability names (e.g. ``"retriever"``) to implementation
classes ranked by priority.  Default OSS implementations register at
priority 100; extensions use higher values to override them.
"""

import importlib
import threading
from typing import Any, Dict, List, Optional, Tuple

from retriva.logger import get_logger

logger = get_logger(__name__)


class CapabilityRegistry:
    """Thread-safe singleton registry for pipeline implementations."""

    _instance: Optional["CapabilityRegistry"] = None
    _init_lock = threading.Lock()

    def __new__(cls) -> "CapabilityRegistry":
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._capabilities: Dict[str, List[Tuple[int, type]]] = {}
                    instance._instances: Dict[str, Any] = {}
                    instance._lock = threading.Lock()
                    cls._instance = instance
        return cls._instance

    # -- Registration ------------------------------------------------------

    def register(self, name: str, impl_class: type, priority: int = 100) -> None:
        """Register an implementation class for a named capability.

        Args:
            name: Capability name (e.g. ``"retriever"``).
            impl_class: The class implementing the corresponding protocol.
            priority: Higher values take precedence. OSS defaults use 100.
        """
        with self._lock:
            if name not in self._capabilities:
                self._capabilities[name] = []
            self._capabilities[name].append((priority, impl_class))
            # Sort descending by priority so index-0 is always the winner
            self._capabilities[name].sort(key=lambda t: t[0], reverse=True)
            # Invalidate any cached instance when registrations change
            self._instances.pop(name, None)
        logger.debug(
            f"Registered '{name}' ← {impl_class.__name__} (priority={priority})"
        )

    # -- Resolution --------------------------------------------------------

    def get(self, name: str) -> type:
        """Return the highest-priority implementation class for *name*.

        Raises ``KeyError`` if no implementation has been registered.
        """
        with self._lock:
            entries = self._capabilities.get(name)
            if not entries:
                raise KeyError(
                    f"No implementation registered for capability '{name}'"
                )
            return entries[0][1]

    def get_instance(self, name: str) -> Any:
        """Return a cached singleton instance of the highest-priority class.

        The instance is created on first call and reused thereafter (until
        a new registration invalidates the cache).
        """
        with self._lock:
            if name in self._instances:
                return self._instances[name]
            entries = self._capabilities.get(name)
            if not entries:
                raise KeyError(
                    f"No implementation registered for capability '{name}'"
                )
            cls = entries[0][1]

        # Instantiate outside the lock to avoid holding it during __init__
        instance = cls()

        with self._lock:
            # Double-check: another thread may have beaten us
            if name not in self._instances:
                self._instances[name] = instance
            return self._instances[name]

    # -- Extension discovery -----------------------------------------------

    def load_extensions(self, extensions_csv: str = "") -> None:
        """Import extension modules and call their ``register(registry)`` hook.

        Args:
            extensions_csv: Comma-separated dotted module paths.
                If empty, reads from ``retriva.config.settings.retriva_extensions``.
        """
        if not extensions_csv:
            from retriva.config import settings
            extensions_csv = settings.retriva_extensions

        if not extensions_csv.strip():
            logger.debug("No extensions configured (RETRIVA_EXTENSIONS is empty).")
            return

        for module_path in extensions_csv.split(","):
            module_path = module_path.strip()
            if not module_path:
                continue
            try:
                mod = importlib.import_module(module_path)
                if hasattr(mod, "register"):
                    mod.register(self)
                    logger.info(f"Loaded extension: {module_path}")
                else:
                    logger.warning(
                        f"Extension module '{module_path}' has no register() function — skipped."
                    )
            except Exception as e:
                logger.error(f"Failed to load extension '{module_path}': {e}")

    # -- Introspection -----------------------------------------------------

    def list_capabilities(self) -> Dict[str, List[Tuple[int, str]]]:
        """Return all registered capabilities with priorities and class names."""
        with self._lock:
            return {
                name: [(p, cls.__name__) for p, cls in entries]
                for name, entries in self._capabilities.items()
            }

    # -- Testing support ---------------------------------------------------

    @classmethod
    def _reset(cls) -> None:
        """Reset the singleton — for testing only."""
        with cls._init_lock:
            if cls._instance is not None:
                cls._instance._capabilities.clear()
                cls._instance._instances.clear()
                cls._instance = None
