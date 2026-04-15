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
MediaWiki XML export parser.

Streams ``<page>`` elements from a MediaWiki native export file using
``xml.etree.ElementTree.iterparse`` for constant-memory usage.
Converts raw wikitext to plain text suitable for embedding/chunking.
"""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional

from retriva.logger import get_logger

logger = get_logger(__name__)

# MediaWiki export XML namespace (version-agnostic pattern)
_MW_NS_PATTERN = re.compile(r"\{http://www\.mediawiki\.org/xml/export[^}]*\}")

# Default namespaces to index (0 = Main articles, 6 = File description pages)
DEFAULT_NAMESPACES = {0, 6}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class WikiPage:
    """A single page extracted from a MediaWiki XML export."""
    title: str
    namespace: int
    page_id: int
    text: str                               # raw wikitext
    timestamp: str = ""
    file_references: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# XML sniffing
# ---------------------------------------------------------------------------

def is_mediawiki_export(xml_path: Path) -> bool:
    """
    Check whether *xml_path* looks like a MediaWiki XML export by reading
    the first 1 KB and searching for the ``<mediawiki`` root element.
    """
    try:
        with open(xml_path, "r", encoding="utf-8", errors="ignore") as f:
            head = f.read(1024)
        return "<mediawiki" in head.lower()
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Streaming XML parser
# ---------------------------------------------------------------------------

def _strip_ns(tag: str) -> str:
    """Remove the XML namespace prefix from a tag, e.g. ``{…}page`` → ``page``."""
    return _MW_NS_PATTERN.sub("", tag)


def parse_export(
    xml_path: Path,
    namespaces: set[int] | None = None,
) -> Iterator[WikiPage]:
    """
    Yield :class:`WikiPage` objects from a MediaWiki XML export file.

    Uses ``iterparse`` with ``end`` events so each ``<page>`` subtree is
    fully built before processing, then immediately freed.

    Only pages whose ``<ns>`` value is in *namespaces* are yielded.
    Defaults to :data:`DEFAULT_NAMESPACES` ``{0, 6}``.
    """
    if namespaces is None:
        namespaces = DEFAULT_NAMESPACES

    context = ET.iterparse(str(xml_path), events=("end",))

    for event, elem in context:
        tag = _strip_ns(elem.tag)
        if tag != "page":
            continue

        # --- Extract page-level fields ---
        ns_elem = elem.find(".//{http://www.mediawiki.org/xml/export-0.11/}ns")
        # Fall back to a namespace-agnostic search
        if ns_elem is None:
            for child in elem.iter():
                if _strip_ns(child.tag) == "ns":
                    ns_elem = child
                    break

        page_ns = int(ns_elem.text) if ns_elem is not None and ns_elem.text else 0

        if page_ns not in namespaces:
            elem.clear()
            continue

        title_elem = _find_direct_child(elem, "title")
        id_elem = _find_direct_child(elem, "id")

        # --- Find latest revision (last <revision> in document order) ---
        revisions = [
            child for child in elem
            if _strip_ns(child.tag) == "revision"
        ]
        latest_rev = revisions[-1] if revisions else None

        text = ""
        timestamp = ""
        if latest_rev is not None:
            text_elem = _find_child(latest_rev, "text")
            ts_elem = _find_child(latest_rev, "timestamp")
            text = text_elem.text if text_elem is not None and text_elem.text else ""
            timestamp = ts_elem.text if ts_elem is not None and ts_elem.text else ""

        file_refs = extract_file_references(text) if text else []

        yield WikiPage(
            title=title_elem.text if title_elem is not None and title_elem.text else "",
            namespace=page_ns,
            page_id=int(id_elem.text) if id_elem is not None and id_elem.text else 0,
            text=text,
            timestamp=timestamp,
            file_references=file_refs,
        )

        # Free memory
        elem.clear()


def _find_child(parent: ET.Element, local_name: str) -> Optional[ET.Element]:
    """Find a nested child by local tag name, ignoring XML namespaces."""
    for child in parent.iter():
        if _strip_ns(child.tag) == local_name:
            return child
    return None


def _find_direct_child(parent: ET.Element, local_name: str) -> Optional[ET.Element]:
    """Find a **direct** child by local tag name, ignoring XML namespaces."""
    for child in parent:
        if _strip_ns(child.tag) == local_name:
            return child
    return None


# ---------------------------------------------------------------------------
# Wikitext → plain text conversion
# ---------------------------------------------------------------------------

# Pre-compiled patterns for wikitext stripping
_RE_COMMENT    = re.compile(r"<!--.*?-->", re.DOTALL)
_RE_NOWIKI     = re.compile(r"<nowiki>.*?</nowiki>", re.DOTALL | re.IGNORECASE)
_RE_REF        = re.compile(r"<ref[^>]*/?>(?:.*?</ref>)?", re.DOTALL | re.IGNORECASE)
_RE_HTML_TAG   = re.compile(r"<[^>]+>")
_RE_TEMPLATE   = re.compile(r"\{\{[^{}]*\}\}")  # applied iteratively for nesting
_RE_TABLE      = re.compile(r"^\{\|.*?^\|\}", re.DOTALL | re.MULTILINE)
_RE_TABLE_ROW  = re.compile(r"^\|-.*$", re.MULTILINE)
_RE_TABLE_HEAD = re.compile(r"^!\s*", re.MULTILINE)
_RE_TABLE_CELL = re.compile(r"^\|\s*", re.MULTILINE)
_RE_TABLE_PIPE = re.compile(r"\|\|")
_RE_TABLE_BANG = re.compile(r"!!")
_RE_HEADING    = re.compile(r"^(={1,6})\s*(.+?)\s*\1\s*$", re.MULTILINE)
_RE_BOLD_ITAL  = re.compile(r"'{2,5}")
_RE_FILE_IMG   = re.compile(
    r"\[\[(?:File|Image):([^|\]]+)(?:\|[^\]]*)?\]\]", re.IGNORECASE
)
_RE_CATEGORY   = re.compile(r"\[\[Category:[^\]]*\]\]", re.IGNORECASE)
_RE_WIKILINK   = re.compile(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]")
_RE_EXTLINK    = re.compile(r"\[https?://[^\s\]]+ ([^\]]+)\]")
_RE_EXTLINK_B  = re.compile(r"\[https?://[^\]]+\]")
_RE_MAGIC      = re.compile(r"__[A-Z]+__")
_RE_MULTI_NL   = re.compile(r"\n{3,}")
_RE_MULTI_SP   = re.compile(r"[ \t]{2,}")


def wikitext_to_plaintext(wikitext: str) -> str:
    """
    Convert raw MediaWiki wikitext to clean plain text for embedding.

    Handles headings, bold/italic, wikilinks, categories, file/image
    links, templates, references, HTML tags, tables, and external links.
    """
    text = wikitext

    # 1. HTML comments
    text = _RE_COMMENT.sub("", text)

    # 2. <nowiki> blocks (remove markup preservation)
    text = _RE_NOWIKI.sub("", text)

    # 3. <ref> citations
    text = _RE_REF.sub("", text)

    # 4. Templates — iteratively strip because of nesting: {{a|{{b}}}}
    for _ in range(10):
        new_text = _RE_TEMPLATE.sub("", text)
        if new_text == text:
            break
        text = new_text

    # 5. Tables — extract cell content
    text = _strip_wiki_tables(text)

    # 6. Remaining HTML tags
    text = _RE_HTML_TAG.sub("", text)

    # 7. Headings → plain text
    text = _RE_HEADING.sub(r"\2", text)

    # 8. Bold / italic markers
    text = _RE_BOLD_ITAL.sub("", text)

    # 9. File/Image links → remove (already extracted separately)
    text = _RE_FILE_IMG.sub("", text)

    # 10. Categories → remove
    text = _RE_CATEGORY.sub("", text)

    # 11. Wikilinks [[Target|Label]] → Label
    text = _RE_WIKILINK.sub(r"\1", text)

    # 12. External links [url text] → text
    text = _RE_EXTLINK.sub(r"\1", text)
    text = _RE_EXTLINK_B.sub("", text)

    # 13. Magic words (__TOC__, __NOTOC__, etc.)
    text = _RE_MAGIC.sub("", text)

    # 14. Cleanup whitespace
    text = _RE_MULTI_NL.sub("\n\n", text)
    text = _RE_MULTI_SP.sub(" ", text)

    return text.strip()


def _strip_wiki_tables(text: str) -> str:
    """
    Extract cell text from wiki tables ``{| … |}``, discarding
    table markup. Returns text with the table blocks replaced by
    their cell contents on separate lines.
    """
    def _table_to_text(match: re.Match) -> str:
        block = match.group(0)
        lines = block.split("\n")
        cells = []
        for line in lines:
            line = line.strip()
            if line.startswith("{|") or line.startswith("|}") or line.startswith("|-"):
                continue
            if line.startswith("!"):
                # Header cell
                cell_text = re.sub(r"^!\s*", "", line)
                # Handle !! separators
                for part in cell_text.split("!!"):
                    part = part.strip()
                    # Strip formatting after pipe (e.g., ! scope="col" | Text)
                    if "|" in part:
                        part = part.split("|", 1)[-1].strip()
                    if part:
                        cells.append(part)
            elif line.startswith("|"):
                cell_text = re.sub(r"^\|\s*", "", line)
                for part in cell_text.split("||"):
                    part = part.strip()
                    if "|" in part:
                        part = part.split("|", 1)[-1].strip()
                    if part:
                        cells.append(part)
        return "\n".join(cells)

    return _RE_TABLE.sub(_table_to_text, text)


# ---------------------------------------------------------------------------
# File / image reference extraction
# ---------------------------------------------------------------------------

def extract_file_references(wikitext: str) -> list[str]:
    """
    Return a deduplicated list of filenames referenced via
    ``[[File:name.ext|…]]`` or ``[[Image:name.ext|…]]`` in *wikitext*.
    """
    matches = _RE_FILE_IMG.findall(wikitext)
    # Deduplicate while preserving order
    seen: set[str] = set()
    result: list[str] = []
    for name in matches:
        name = name.strip()
        if name and name not in seen:
            seen.add(name)
            result.append(name)
    return result
