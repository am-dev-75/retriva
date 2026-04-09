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

import os
from pathlib import Path
from typing import List
from retriva.config import settings
from retriva.logger import get_logger

logger = get_logger(__name__)

def is_html_content(file_path: Path) -> bool:
    """
    Checks if a file without an extension looks like HTML.
    """
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024).lower()
            return b"<html" in chunk or b"<!doctype" in chunk
    except Exception:
        return False

def discover_html_files() -> List[str]:
    """
    Discovers all HTML files in the local wget mirror folder.
    Excludes images/ and resources/ directories.
    Handles extensionless wiki pages by sniffing content.
    """
    logger.debug(f"Mirror base path: {settings.mirror_base_path}")    
    base = Path(settings.mirror_base_path).resolve()
    logger.debug(f"Base path: {base}")
    if not base.exists() or not base.is_dir():
        logger.warning(f"Mirror base path '{base}' does not exist or is not a directory.")
        return []
        
    logger.debug(f"Discovering HTML files in '{base}' (recursive)...")
    
    # Directories to exclude
    excluded_dirs = {"images", "resources"}
    # Binary/asset extensions to skip
    binary_exts = {
        ".png", ".jpg", ".jpeg", ".gif", ".pdf", 
        ".css", ".js", ".svg", ".ico", ".woff", ".woff2"
    }
    
    discovered_files = []
    
    # We use rglob("*") to find all files recursively
    for path in base.rglob("*"):
        if not path.is_file():
            continue
            
        # Check if any parent directory is in the excluded list
        if any(part in excluded_dirs for part in path.relative_to(base).parts):
            continue
            
        ext = path.suffix.lower()
        
        # 1. Standard HTML extensions
        if ext in {".html", ".htm"}:
            discovered_files.append(str(path))
            continue
            
        # 2. Skip known binary/asset extensions
        if ext in binary_exts:
            continue
            
        # 3. Handle extensionless files (very common in MediaWiki mirrors)
        if ext == "":
            if is_html_content(path):
                logger.debug(f"Discovered extensionless HTML file: {path.name}")
                discovered_files.append(str(path))
                
    logger.info(f"Found {len(discovered_files)} HTML files in '{base}'.")
    return discovered_files
