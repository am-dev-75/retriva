# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

import uvicorn
import argparse
from retriva.logger import setup_logging

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Retriva API Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Binding host")
    parser.add_argument("--port", type=int, default=8000, help="Binding port")
    args = parser.parse_args()
    
    print(f"Starting API server on {args.host}:{args.port}...")
    uvicorn.run("retriva.ingestion_api.main:app", host=args.host, port=args.port, reload=False)

if __name__ == "__main__":
    main()
