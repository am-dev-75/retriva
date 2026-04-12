# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

import uvicorn
import argparse
from retriva.logger import setup_logging
from retriva import config


def main():
    setup_logging()
    print(f"##### Retriva OpenAI-compatible API ({config.VERSION}) #####\n")
    parser = argparse.ArgumentParser(
        description="Retriva OpenAI-compatible API for Open WebUI"
    )
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Binding host"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=config.settings.openai_api_port,
        help="Binding port (default: %(default)s)",
    )
    args = parser.parse_args()

    print(f"Starting OpenAI-compatible API on {args.host}:{args.port}...")
    uvicorn.run(
        "retriva.openai_api.main:app",
        host=args.host,
        port=args.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
