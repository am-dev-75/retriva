# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

import uvicorn
import argparse
from retriva.logger import setup_logging
from retriva import config

def main():
    setup_logging()
    print(f"##### Retriva RAG backend ({config.VERSION}) #####\n")
    parser = argparse.ArgumentParser(description="Retriva RAG backend")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Binding host")
    parser.add_argument("--port", type=int, default=config.settings.ingestion_api_port, help="Binding port (default: %(default)s)")
    args = parser.parse_args()
    
    s = config.settings
    print("Active settings:")
    print(f"  Qdrant URL:           {s.qdrant_url}")
    print(f"  Embedding model:      {s.embedding_model}")
    print(f"  Embedding dimension:  {s.embedding_dimension}")
    print(f"  Embedding base URL:   {s.embedding_base_url}")
    print(f"  Max chunk chars:      {s.max_chunk_chars}")
    print(f"  Chunk overlap:        {s.chunk_overlap}")
    print(f"  Indexing batch size:  {s.indexing_batch_size}")
    print()
    print(f"Starting API server on {args.host}:{args.port}...")
    uvicorn.run("retriva.ingestion_api.main:app", host=args.host, port=args.port, reload=False)

if __name__ == "__main__":
    main()
