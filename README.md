![](docs/assets/Retriva_logo_slogan_white_background.jpg)

# Retriva

- [Retriva](#retriva)
  - [Introduction](#introduction)
  - [Architecture](#architecture)
    - [Logical architecture](#logical-architecture)
    - [Software architecture](#software-architecture)
  - [Implementation](#implementation)
  - [Quick Start](#quick-start)
  - [Licensing](#licensing)

## Introduction

Retriva is a conversational AI agent. It is built to provide users with accurate and relevant information by leveraging the power of Retrieval Augmented Generation (RAG). It is built to provide users with accurate and relevant information by leveraging the power of Retrieval Augmented Generation (RAG). It is designed for enterprise use cases where data privacy and security are of utmost importance.

For more details, please refer to [Retriva Documentation](https://github.com/am-dev-75/retriva-docs).

## Architecture

Retriva is built around a RAG (Retrieval-Augmented Generation) paradigm, currently tailored for technical documentation about embedded systems and electronics boards. Current architecture is modular and decoupled, consisting of the following key components:

- **Ingestion API (`ingestion_api/`)**: A standalone HTTP service that handles the data processing pipeline. It locally discovers filesystem-based static HTML mirrors, extracts main content, and performs section-aware text chunking.
- **Embeddings & Vector Store (`indexing/`)**: Extracted metadata and text chunks are converted into multilingual embeddings via an OpenAI-compatible endpoint. These embeddings are batched and stored in a Qdrant vector database for fast and scalable dense retrieval.
- **QA Pipeline (`qa/`)**: Drives the retrieval and generation phases. It queries Qdrant for semantic similarity, retrieves contextual chunks, and generates grounded answers based strictly on the retrieved data.
- **User Interface (`ui/`)**: A Streamlit-based frontend offering a conversational chat experience. It supports grounded answers, citations, and features an integrated debug panel to visualize the retrieval process.

### Logical architecture

The final architecture should look like ![this:](docs/assets/Retriva_target_logic_architecture.drawio.png)

### Software architecture

![](docs/assets/Retriva_software_architecture.drawio.png)

## Implementation

See [this page](docs/implementation.md) for the implementation details.

## Quick Start

* If not already available, [deploy a Qdrant instance](https://qdrant.tech/documentation/quickstart/).
  * This is the typical log when you start the containerized version:
```
           _                 _    
  __ _  __| |_ __ __ _ _ __ | |_  
 / _` |/ _` | '__/ _` | '_ \| __| 
| (_| | (_| | | | (_| | | | | |_  
 \__, |\__,_|_|  \__,_|_| |_|\__| 
    |_|                           

Version: 1.17.1, build: eabee371
Access web UI at http://localhost:6333/dashboard

2026-04-03T21:17:56.070752Z  INFO storage::content_manager::consensus::persistent: Loading raft state from ./storage/raft_state.json
2026-04-03T21:17:56.081084Z  INFO storage::content_manager::toc: Loading collection: retriva_chunks
2026-04-03T21:17:56.101527Z  INFO collection::shards::local_shard: Recovering shard ./storage/collections/retriva_chunks/0: 0/1 (0%)
2026-04-03T21:17:56.103581Z  INFO collection::shards::local_shard: Recovered collection retriva_chunks: 1/1 (100%)
2026-04-03T21:17:56.108149Z  INFO qdrant: Distributed mode disabled
2026-04-03T21:17:56.108463Z  INFO qdrant: Telemetry reporting enabled, id: c012b687-e64f-419e-abf8-8ada1e63a2b8
2026-04-03T21:17:56.147714Z  INFO qdrant::tonic: Qdrant gRPC listening on 6334
2026-04-03T21:17:56.147723Z  INFO qdrant::tonic: TLS disabled for gRPC API
2026-04-03T21:17:56.148679Z  INFO qdrant::actix: REST transport settings: keep_alive=5s, client_request_timeout=5s, client_disconnect_timeout=5s
2026-04-03T21:17:56.148694Z  INFO qdrant::actix: TLS disabled for REST API
2026-04-03T21:17:56.148977Z  INFO qdrant::actix: Qdrant HTTP listening on 6333
2026-04-03T21:17:56.149118Z  INFO actix_server::builder: starting 31 workers
2026-04-03T21:17:56.149514Z  INFO actix_server::server: Actix runtime found; starting in Actix runtime
2026-04-03T21:17:56.149519Z  INFO actix_server::server: starting service: "actix-web-service-0.0.0.0:6333", workers: 31, listening on: 0.0.0.0:6333
```

* After cloning this repository
  * install dependencies (the use of a virtual environment is recommended):
```pip install -r requirements.txt```
  * Copy `.env` from `.env.example` and fill in the values so that Retriva can connect to the Qdrant instance and the LLM's runner(s) you intend to use.

* Build the knowledge base from *your* documents with the CLI. For instance:
```bash
PYTHONPATH=src python -m retriva.cli reindex --path ~/my_documents
```

* Start the Retriva backend providing OpenAI API:
```bash
PYTHONPATH=src python -m retriva.openai_api
```
 * This is the typical log when it starts:
```
(retriva-v0.1) llandre@vm-ubnt-24-04-4:/mnt/shared/implementation/retriva$ PYTHONPATH=src python -m retriva.openai_api 2>&1 | tee ../logs/20260414-openai_api-languages.txt 
##### Retriva OpenAI-compatible API (0.11.2) #####

Starting OpenAI-compatible API on 0.0.0.0:8001...
[20260414 16:17:54] [DEBUG] [asyncio] Using selector: EpollSelector
INFO:     Started server process [184900]
INFO:     Waiting for application startup.
[20260414 16:17:55] [INFO] [retriva.openai_api.main] Initializing Retriva OpenAI-compatible API...
[20260414 16:17:55] [DEBUG] [httpcore.connection] connect_tcp.started host='192.168.1.64' port=6333 local_address=None timeout=5.0 socket_options=None
[20260414 16:17:55] [DEBUG] [httpcore.connection] connect_tcp.complete return_value=<httpcore._backends.sync.SyncStream object at 0x718e8a26c5c0>
[20260414 16:17:55] [DEBUG] [httpcore.http11] send_request_headers.started request=<Request [b'GET']>
[20260414 16:17:55] [DEBUG] [httpcore.http11] send_request_headers.complete
[20260414 16:17:55] [DEBUG] [httpcore.http11] send_request_body.started request=<Request [b'GET']>
[20260414 16:17:55] [DEBUG] [httpcore.http11] send_request_body.complete
[20260414 16:17:55] [DEBUG] [httpcore.http11] receive_response_headers.started request=<Request [b'GET']>
[20260414 16:17:55] [DEBUG] [httpcore.http11] receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'transfer-encoding', b'chunked'), (b'content-type', b'application/json'), (b'vary', b'accept-encoding, Origin, Access-Control-Request-Method, Access-Control-Request-Headers'), (b'content-encoding', b'gzip'), (b'date', b'Tue, 14 Apr 2026 14:17:55 GMT')])
[20260414 16:17:55] [INFO] [httpx] HTTP Request: GET http://192.168.1.64:6333/collections/retriva_chunks/exists "HTTP/1.1 200 OK"
[20260414 16:17:55] [DEBUG] [httpcore.http11] receive_response_body.started request=<Request [b'GET']>
[20260414 16:17:55] [DEBUG] [httpcore.http11] receive_response_body.complete
[20260414 16:17:55] [DEBUG] [httpcore.http11] response_closed.started
[20260414 16:17:55] [DEBUG] [httpcore.http11] response_closed.complete
[20260414 16:17:55] [DEBUG] [retriva.indexing.qdrant_store] Collection 'retriva_chunks' already exists.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
[20260414 16:17:55] [DEBUG] [httpcore.connection] connect_tcp.started host='192.168.1.64' port=6333 local_address=None timeout=5 socket_options=None
[20260414 16:17:55] [DEBUG] [httpcore.connection] connect_tcp.complete return_value=<httpcore._backends.sync.SyncStream object at 0x718e8a26e630>
[20260414 16:17:55] [DEBUG] [httpcore.http11] send_request_headers.started request=<Request [b'GET']>
[20260414 16:17:55] [DEBUG] [httpcore.http11] send_request_headers.complete
[20260414 16:17:55] [DEBUG] [httpcore.http11] send_request_body.started request=<Request [b'GET']>
[20260414 16:17:55] [DEBUG] [httpcore.http11] send_request_body.complete
[20260414 16:17:55] [DEBUG] [httpcore.http11] receive_response_headers.started request=<Request [b'GET']>
[20260414 16:17:55] [DEBUG] [httpcore.http11] receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'transfer-encoding', b'chunked'), (b'vary', b'accept-encoding, Origin, Access-Control-Request-Method, Access-Control-Request-Headers'), (b'content-type', b'application/json'), (b'content-encoding', b'gzip'), (b'date', b'Tue, 14 Apr 2026 14:17:55 GMT')])
[20260414 16:17:55] [INFO] [httpx] HTTP Request: GET http://192.168.1.64:6333 "HTTP/1.1 200 OK"
[20260414 16:17:55] [DEBUG] [httpcore.http11] receive_response_body.started request=<Request [b'GET']>
[20260414 16:17:55] [DEBUG] [httpcore.http11] receive_response_body.complete
[20260414 16:17:55] [DEBUG] [httpcore.http11] response_closed.started
[20260414 16:17:55] [DEBUG] [httpcore.http11] response_closed.complete
[20260414 16:17:55] [DEBUG] [httpcore.connection] close.started
[20260414 16:17:55] [DEBUG] [httpcore.connection] close.complete
```

* Start an instance of [Open WebUI for Retriva](https://github.com/am-dev-75/open-webui_retriva).

* Point your browser to the URL of the Open WebUI for Retriva instance and start having fun.

## Licensing

This project, including all source code, agentic specifications, and documentation, is licensed under the Apache License 2.0. See the LICENSE file for details.
