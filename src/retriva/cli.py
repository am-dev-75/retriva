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

import argparse
from pathlib import Path
from typing import Callable, Dict, List, Set

import requests

from retriva import config
from retriva.ingestion.discover import classify_file, discover_files, FILE_TYPE_REGISTRY
from retriva.ingestion.mirror import source_to_canonical
from retriva.ingestion.html_parser import extract_title
from retriva.logger import setup_logging, get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Per-type ingestion handlers
# ---------------------------------------------------------------------------
# To support a new format, add a handler here and a matching entry
# in discover.py's FILE_TYPE_REGISTRY.
# ---------------------------------------------------------------------------

def ingest_html_file(path: str, api_url: str) -> None:
    """Read an HTML file, extract title, and POST it to the ingestion API."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
    except Exception as e:
        logger.error(f"Error reading {path}: {e}")
        return

    canonical = source_to_canonical(path)
    title = extract_title(html)

    payload = {
        "source_path": canonical,
        "page_title": title,
        "html_content": html,
        "origin_file_path": path,
    }

    try:
        r = requests.post(f"{api_url}/api/v1/ingest/html", json=payload)
        r.raise_for_status()
    except Exception as e:
        logger.error(f"Error uploading HTML {path}: {e}")


def ingest_image_file(path: str, api_url: str) -> None:
    """POST a standalone image file to the ingestion API for VLM processing."""
    payload = {
        "source_path": path,
        "page_title": Path(path).stem,
        "file_path": path,
    }

    try:
        r = requests.post(f"{api_url}/api/v1/ingest/image", json=payload)
        r.raise_for_status()
    except Exception as e:
        logger.error(f"Error uploading image {path}: {e}")


# Maps file type keys (from FILE_TYPE_REGISTRY) to handler functions.
INGEST_HANDLERS: Dict[str, Callable[[str, str], None]] = {
    "html": ingest_html_file,
    "image": ingest_image_file,
}


# ---------------------------------------------------------------------------
# Core ingestion logic
# ---------------------------------------------------------------------------

def run_ingest(
    target: Path,
    api_url: str,
    limit: int = 0,
    exclude: Set[str] | None = None,
) -> None:
    """
    Discover and ingest all supported files under *target*.
    *target* may be a single file or a directory.

    Args:
        exclude: File-type keys to skip (e.g. {"image"}).
    """
    logger.info(f"Discovering files in '{target}'...")
    discovered = discover_files(target)

    # Remove excluded types before processing
    if exclude:
        for type_key in exclude:
            removed = discovered.pop(type_key, [])
            if removed:
                logger.info(f"Excluding {len(removed)} {type_key} file(s).")

    if not any(discovered.values()):
        logger.warning("No supported files found.")
        return

    total = 0
    for file_type, files in discovered.items():
        handler = INGEST_HANDLERS.get(file_type)
        if handler is None:
            logger.warning(f"No handler for type '{file_type}' — skipping {len(files)} file(s).")
            continue

        for path in files:
            if 0 < limit <= total:
                logger.info(f"Reached limit ({limit}). Stopping.")
                return
            logger.info(f"[{file_type}] Uploading {path}...")
            handler(path, api_url)
            total += 1

    logger.info(f"Ingestion complete — {total} file(s) processed.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    setup_logging()

    print(f"##### Retriva CLI ({config.VERSION}) #####\n")

    parser = argparse.ArgumentParser(description="Retriva CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ---- ingest: file or directory ----
    ingest_parser = subparsers.add_parser(
        "ingest", help="Ingest a file or directory into the index"
    )
    ingest_parser.add_argument(
        "--path", type=str, required=True,
        help="Path to a file or directory to ingest"
    )
    ingest_parser.add_argument(
        "--api-url", type=str, default="http://127.0.0.1:8000", help="API URL"
    )
    ingest_parser.add_argument(
        "--limit", type=int, default=0, help="Limit number of files"
    )
    ingest_parser.add_argument(
        "--exclude", type=str, action="append", default=[],
        metavar="FORMAT",
        help=(
            f"File type to exclude (repeatable). "
            f"Supported: {', '.join(sorted(FILE_TYPE_REGISTRY))}"
        ),
    )

    # ---- reindex: directory only ----
    reindex_parser = subparsers.add_parser(
        "reindex", help="Clear the collection and re-ingest a directory"
    )
    reindex_parser.add_argument(
        "--path", type=str, required=True,
        help="Path to the directory to scan and re-ingest"
    )
    reindex_parser.add_argument(
        "--api-url", type=str, default="http://127.0.0.1:8000", help="API URL"
    )
    reindex_parser.add_argument(
        "--limit", type=int, default=0, help="Limit number of files"
    )
    reindex_parser.add_argument(
        "--exclude", type=str, action="append", default=[],
        metavar="FORMAT",
        help=(
            f"File type to exclude (repeatable). "
            f"Supported: {', '.join(sorted(FILE_TYPE_REGISTRY))}"
        ),
    )

    args = parser.parse_args()
    target = Path(args.path)

    # Validate --exclude values early
    exclude: set[str] = set()
    for fmt in args.exclude:
        if fmt not in FILE_TYPE_REGISTRY:
            parser.error(
                f"Unknown format '{fmt}'. "
                f"Supported: {', '.join(sorted(FILE_TYPE_REGISTRY))}"
            )
        exclude.add(fmt)

    if args.command == "ingest":
        if not target.exists():
            logger.error(f"Path '{target}' does not exist.")
            return
        run_ingest(target, args.api_url, args.limit, exclude or None)

    elif args.command == "reindex":
        if not target.is_dir():
            logger.error(f"reindex requires a directory, got '{target}'")
            return
        logger.info("Reindexing (clearing and ingesting)...")
        try:
            r = requests.delete(f"{args.api_url}/api/v1/ingest/collection")
            r.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return
        run_ingest(target, args.api_url, args.limit, exclude or None)


if __name__ == "__main__":
    main()
