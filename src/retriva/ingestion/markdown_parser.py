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

import re
from pathlib import Path
from typing import Dict, List, Optional

from retriva.logger import get_logger

logger = get_logger(__name__)

# Regex to match Markdown headings (H1 to H6)
# Matches lines starting with 1-6 '#' followed by a space
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def split_by_headings(text: str) -> List[Dict[str, str]]:
    """
    Split Markdown text into sections based on headings.
    Returns a list of {"heading": str, "content": str}.
    The first section might have an empty heading if there's text before the first heading.
    """
    sections = []
    matches = list(_HEADING_RE.finditer(text))
    
    if not matches:
        return [{"heading": "", "content": text.strip()}]

    # Handle text before the first heading
    first_start = matches[0].start()
    if first_start > 0:
        content = text[:first_start].strip()
        if content:
            sections.append({"heading": "", "content": content})

    for i, match in enumerate(matches):
        heading_text = match.group(2).strip()
        
        # Start of current section is after the heading line
        start = match.end()
        # End of current section is the start of the next heading or the end of text
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        
        content = text[start:end].strip()
        sections.append({"heading": heading_text, "content": content})

    return sections


def derive_title(text: str, path: Path) -> str:
    """
    Derive document title:
    1. First H1 heading if found.
    2. Filename stem as fallback.
    """
    h1_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if h1_match:
        return h1_match.group(1).strip()
    
    return path.stem.replace("_", " ").replace("-", " ").title()


def parse_markdown(path: Path) -> Optional[Dict]:
    """
    Parse a Markdown file into a dictionary compatible with the ingestion payload.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        logger.error(f"Error reading Markdown file {path}: {e}")
        return None

    title = derive_title(text, path)
    sections = split_by_headings(text)

    # Filter out empty sections
    sections = [s for s in sections if s["content"].strip()]

    return {
        "title": title,
        "source_path": str(path.resolve()),
        "sections": sections,
    }
