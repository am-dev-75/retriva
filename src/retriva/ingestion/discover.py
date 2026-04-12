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

from pathlib import Path
from typing import Callable, Dict, List, Optional, Set
from retriva.config import settings
from retriva.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Content sniffers — used for extensionless files
# ---------------------------------------------------------------------------

def is_html_content(file_path: Path) -> bool:
    """Checks if a file without an extension looks like HTML."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024).lower()
            return b"<html" in chunk or b"<!doctype" in chunk
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Extensible file-type registry
# ---------------------------------------------------------------------------
# To add a new format (e.g. PDF), append an entry here and create a
# matching handler in cli.py's INGEST_HANDLERS dict.
# ---------------------------------------------------------------------------

FILE_TYPE_REGISTRY: Dict[str, Dict] = {
    "html": {
        "extensions": {".html", ".htm"},
        "sniffer": is_html_content,
    },
    "image": {
        "extensions": {".png", ".jpg", ".jpeg", ".gif", ".webp"},
        "sniffer": None,
    },
    "text": {
        "extensions": {".txt"},
        "sniffer": None,
    },
    # Future formats:
    # "pdf": {"extensions": {".pdf"}, "sniffer": None},
}

# Directories that should never be traversed
EXCLUDED_DIRS: Set[str] = {
    ".git", "__pycache__", "resources", "node_modules",
}

# Filename prefixes that indicate wiki namespace pages, not real content.
# In a wget-mirrored MediaWiki site, ``index.php/File:image.png`` is an
# HTML file-description page, not the actual image binary.
EXCLUDED_FILE_PREFIXES = (
    "File:",
    "Special:",
    "Category:",
    "Talk:",
    "Template:",
)


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify_file(file_path: Path) -> Optional[str]:
    """
    Returns the registry key for a file (e.g. "html", "image") or None
    if the file is not a supported type.

    Handles wget-mirrored filenames that embed URL query strings
    (e.g. ``index.php?title=...File:img.png``).  The real extension
    is determined from the portion *before* any ``?`` character.
    """
    # Strip URL query-string artifacts baked into mirrored filenames
    name = file_path.name
    if "?" in name:
        name = name.split("?")[0]
    ext = Path(name).suffix.lower()

    for type_key, rules in FILE_TYPE_REGISTRY.items():
        if ext in rules["extensions"]:
            return type_key

    # Extensionless files — try each sniffer
    if ext == "":
        for type_key, rules in FILE_TYPE_REGISTRY.items():
            sniffer = rules.get("sniffer")
            if sniffer and sniffer(file_path):
                return type_key

    return None


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def discover_files(path: Path) -> Dict[str, List[str]]:
    """
    Recursively scans *path* and returns discovered files grouped by type.

    Returns:
        {"html": ["/abs/path/a.html", ...], "image": ["/abs/path/b.png", ...]}
    """
    base = path.resolve()

    if not base.exists():
        logger.warning(f"Path '{base}' does not exist.")
        return {}

    if base.is_file():
        file_type = classify_file(base)
        if file_type:
            return {file_type: [str(base)]}
        logger.warning(f"File '{base}' is not a supported type.")
        return {}

    if not base.is_dir():
        logger.warning(f"Path '{base}' is not a file or directory.")
        return {}

    logger.info(f"Discovering supported files in '{base}' (recursive)...")

    result: Dict[str, List[str]] = {key: [] for key in FILE_TYPE_REGISTRY}

    for child in base.rglob("*"):
        if not child.is_file():
            continue

        # Skip excluded directories
        try:
            rel_parts = child.relative_to(base).parts
        except ValueError:
            continue
        if any(part in EXCLUDED_DIRS for part in rel_parts):
            continue

        # Skip MediaWiki namespace pages (e.g. File:image.png)
        if child.name.startswith(EXCLUDED_FILE_PREFIXES):
            continue

        file_type = classify_file(child)
        if file_type:
            logger.debug(f"Discovered supported file for injection: [{file_type}] {child}")
            result[file_type].append(str(child))

    for type_key, files in result.items():
        if files:
            logger.info(f"  {type_key}: {len(files)} file(s)")

    return result


# ---------------------------------------------------------------------------
# Backward-compatible wrapper
# ---------------------------------------------------------------------------

def discover_html_files() -> List[str]:
    """Legacy wrapper — discovers HTML files under settings.mirror_base_path."""
    found = discover_files(Path(settings.mirror_base_path))
    return found.get("html", [])
