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
import requests
from retriva.ingestion.discover import discover_html_files
from retriva.ingestion.mirror import source_to_canonical
from retriva.ingestion.html_parser import extract_title
from retriva.logger import setup_logging, get_logger

logger = get_logger(__name__)

def run_ingest(api_url: str, files_limit: int = 0):
    logger.info("Discovering files...")
    files = discover_html_files()
    if files_limit > 0:
        files = files[:files_limit]
        
    for path in files:
        logger.info(f"Uploading {path}...")
        try:
            with open(path, "r", encoding="utf-8") as f:
                html = f.read()
        except Exception as e:
            logger.error(f"Error reading {path}: {e}")
            continue
            
        canonical = source_to_canonical(path)
        title = extract_title(html)
        
        payload = {
            "source_path": canonical,
            "page_title": title,
            "html_content": html
        }
        
        try:
            r = requests.post(f"{api_url}/api/v1/ingest/html", json=payload)
            r.raise_for_status()
        except Exception as e:
            logger.error(f"Error uploading {path}: {e}")
            
    logger.info("Ingestion complete!")

def main():
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Retriva CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    ingest_parser = subparsers.add_parser("ingest", help="Ingest mirror to index")
    ingest_parser.add_argument("--api-url", type=str, default="http://127.0.0.1:8000", help="API URL")
    ingest_parser.add_argument("--limit", type=int, default=0, help="Limit number of files")
    
    reindex_parser = subparsers.add_parser("reindex", help="Reindex the repository")
    reindex_parser.add_argument("--api-url", type=str, default="http://127.0.0.1:8000", help="API URL")
    reindex_parser.add_argument("--limit", type=int, default=0, help="Limit number of files")
    
    args = parser.parse_args()
    
    if args.command == "ingest":
        run_ingest(args.api_url, args.limit)
    elif args.command == "reindex":
        logger.info("Reindexing (clearing and ingesting)...")
        try:
            r = requests.delete(f"{args.api_url}/api/v1/ingest/collection")
            r.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return
        run_ingest(args.api_url, args.limit)

if __name__ == "__main__":
    main()
