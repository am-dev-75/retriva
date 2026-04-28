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

import time
import uuid
import contextvars
from collections import deque
from typing import Dict, List, Optional
from retriva.config import settings
from retriva.logger import get_logger

logger = get_logger(__name__)

# In-memory storage for recent profiler logs
_profiler_logs = deque(maxlen=100)

# ContextVar to hold the profiler instance for the current request
_current_profiler = contextvars.ContextVar("current_profiler", default=None)

class Profiler:
    def __init__(self, request_id: str):
        self.request_id = request_id
        self.start_time = time.perf_counter()
        self.phases: Dict[str, float] = {}
        self.model: Optional[str] = None
        self.provider: Optional[str] = None
        self.is_streaming: bool = False

    def mark_phase(self, phase_name: str):
        """Record the timestamp for a specific phase."""
        if not settings.enable_internal_profiler:
            return
        
        elapsed_ms = (time.perf_counter() - self.start_time) * 1000
        self.phases[phase_name] = round(elapsed_ms, 2)
        logger.debug(f"[Profiler][{self.request_id}] Phase '{phase_name}' reached at {elapsed_ms:.2f}ms")

    def finalize(self):
        """Emit structured log and store in recent logs."""
        if not settings.enable_internal_profiler:
            return

        from datetime import datetime, timezone
        log_entry = {
            "request_id": self.request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": self.model or settings.chat_model,
            "provider": self.provider or settings.chat_base_url,
            "is_streaming": self.is_streaming,
            "phases": self.phases,
            "total_duration_ms": round((time.perf_counter() - self.start_time) * 1000, 2)
        }
        _profiler_logs.appendleft(log_entry)
        logger.info(f"PROFILER_LOG: {log_entry}")

    @classmethod
    def start_request(cls) -> "Profiler":
        """Initialize a new profiler for the current request context."""
        request_id = str(uuid.uuid4())
        profiler = cls(request_id)
        _current_profiler.set(profiler)
        profiler.mark_phase("request_received")
        return profiler

    @classmethod
    def get_current(cls) -> Optional["Profiler"]:
        """Retrieve the profiler instance for the current request."""
        return _current_profiler.get()

def get_recent_logs() -> List[Dict]:
    """Return a list of recent profiler log entries."""
    return list(_profiler_logs)
