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
MediaWiki export asset resolver.

Builds an index of the local ``assets/`` subtree and resolves
``[[File:…]]`` references from parsed wiki pages against it.
"""

from pathlib import Path
from typing import Optional

from retriva.logger import get_logger

logger = get_logger(__name__)

# Image extensions that are valid assets for VLM enrichment
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".tiff"}


def build_asset_index(assets_dir: Path) -> dict[str, Path]:
    """
    Recursively scan *assets_dir* and return a mapping from
    **lowercase filename** to its absolute :class:`Path`.

    If two files share the same lowercase name, the first one
    found (by walk order) wins and a warning is logged.
    """
    index: dict[str, Path] = {}

    if not assets_dir.is_dir():
        logger.warning(f"Assets directory does not exist: {assets_dir}")
        return index

    for path in assets_dir.rglob("*"):
        if not path.is_file():
            continue
        key = path.name.lower()
        if key in index:
            logger.debug(
                f"Duplicate asset name '{path.name}' — keeping {index[key]}, "
                f"ignoring {path}"
            )
            continue
        index[key] = path.resolve()

    logger.info(f"Asset index built: {len(index)} file(s) from {assets_dir}")
    return index


def resolve_file_reference(
    name: str, index: dict[str, Path]
) -> Optional[Path]:
    """
    Case-insensitive lookup of a file reference against the asset index.

    MediaWiki file names often have underscores instead of spaces, and
    may differ in casing from the actual filesystem. This function
    normalises the name before lookup.

    Returns the resolved :class:`Path` or ``None`` if not found.
    """
    # MediaWiki uses underscores for spaces in filenames
    normalised = name.strip().replace(" ", "_").lower()
    return index.get(normalised)


def find_assets_dirs(root: Path) -> list[Path]:
    """
    Find all directories named ``assets`` at or below *root*.

    Returns a list of :class:`Path` objects, sorted for determinism.
    """
    result = []
    if root.is_dir():
        for path in root.rglob("assets"):
            if path.is_dir():
                result.append(path)
    return sorted(result)


def is_image_asset(path: Path) -> bool:
    """Return ``True`` if *path* has an image file extension."""
    return path.suffix.lower() in IMAGE_EXTENSIONS
