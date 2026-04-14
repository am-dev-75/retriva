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

from bs4 import BeautifulSoup
from typing import Optional
from retriva.ingestion.normalize import normalize_text
from retriva.logger import get_logger

logger = get_logger(__name__)

def extract_main_content(html: str) -> Optional[str]:
    """
    Extracts the main content using mirror-contract selectors
    and removes boilerplate elements.
    """
    soup = BeautifulSoup(html, "html.parser")
    
    for element in soup(["nav", "footer", "script", "style", "aside", "header"]):
        element.decompose()
        
    selectors = ["#content", "#mw-content-text", "main", ".mw-parser-output"]
    target_node = None
    
    for selector in selectors:
        nodes = soup.select(selector)
        if nodes:
            target_node = nodes[0]
            logger.debug(f"Content extracted using selector: {selector}")
            break
            
    if target_node is None:
        target_node = soup.body
        if target_node is None:
            logger.warning("Could not find any content or body in HTML.")
            return None
        logger.debug("Content extracted using fallback: <body>")
            
    raw_text = target_node.get_text(separator="\n")
    return normalize_text(raw_text)

def extract_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return ""

def extract_language(html: str) -> str:
    """Extract language from html tag lang attribute. Defaults to 'en'."""
    soup = BeautifulSoup(html, "html.parser")
    if soup.html and soup.html.get("lang"):
        return soup.html.get("lang").strip().split("-")[0].lower() # e.g. "en-us" -> "en"
    if soup.html and soup.html.get("xml:lang"):
        return soup.html.get("xml:lang").strip().split("-")[0].lower()
    return "en"


class DefaultHTMLParser:
    """OSS default HTML parser — BeautifulSoup-based content and language extraction."""

    def extract_content(self, html: str) -> str | None:
        return extract_main_content(html)

    def extract_language(self, html: str) -> str:
        return extract_language(html)


# Register as default implementation
from retriva.registry import CapabilityRegistry
CapabilityRegistry().register("html_parser", DefaultHTMLParser, priority=100)
