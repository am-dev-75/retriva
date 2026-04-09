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
from retriva.ingestion.discover import discover_html_files
from retriva.ingestion.mirror import source_to_canonical
from retriva.ingestion.html_parser import extract_main_content, extract_title
from retriva.ingestion.chunker import create_chunks
from retriva.domain.models import ParsedDocument
from retriva.indexing.qdrant_store import get_client, init_collection, upsert_chunks, COLLECTION_NAME
from retriva.logger import setup_logging, get_logger

logger = get_logger(__name__)
def run_ingest(files_limit: int = 0):
    logger.info("Discovering files...")
    files = discover_html_files()
    if files_limit > 0:
        files = files[:files_limit]
        
    client = get_client()
    init_collection(client)
    
    for path in files:
        logger.info(f"Processing {path}...")
        try:
            with open(path, "r", encoding="utf-8") as f:
                html = f.read()
        except Exception as e:
            logger.error(f"Error reading {path}: {e}")
            continue
            
        canonical = source_to_canonical(path)
        title = extract_title(html)
        content = extract_main_content(html)
        
        if not content:
            continue
            
        doc = ParsedDocument(
            source_path=path,
            canonical_doc_id=canonical,
            page_title=title,
            content_text=content
        )
        
        chunks = create_chunks(doc)
        upsert_chunks(client, chunks)
        
    logger.info("Ingestion complete!")

def main():
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Retriva CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    ingest_parser = subparsers.add_parser("ingest", help="Ingest mirror to index")
    ingest_parser.add_argument("--limit", type=int, default=0, help="Limit number of files")
    
    reindex_parser = subparsers.add_parser("reindex", help="Reindex the repository")
    reindex_parser.add_argument("--limit", type=int, default=0, help="Limit number of files")
    
    args = parser.parse_args()
    
    if args.command == "ingest":
        run_ingest(args.limit)
    elif args.command == "reindex":
        logger.info("Reindexing (clearing and ingesting)...")
        client = get_client()
        if client.collection_exists(COLLECTION_NAME):
            client.delete_collection(COLLECTION_NAME)
        run_ingest(args.limit)

if __name__ == "__main__":
    main()
