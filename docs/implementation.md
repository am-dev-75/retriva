# Notes about the implementation

- [Notes about the implementation](#notes-about-the-implementation)
  - [Open WebUI Interfacing](#open-webui-interfacing)

## Open WebUI Interfacing

The implementation was made to allow Open WebUI to interface with Retriva. This was done by creating a new API endpoint that can be called by Open WebUI. The new API endpoint is located at `/api/v1/chat/completions` and is a drop-in replacement for the OpenAI API endpoint. Antigravity + Claude Opus 4.6 was used by following a SDD approach.

Key design decision: the OpenAI-compatible API lives in a separate package (openai_api/) running on port 8001, keeping it cleanly decoupled from the ingestion API on port 8000. It's a pure adapter over the existing ask_question() pipeline — no QA code is modified..

