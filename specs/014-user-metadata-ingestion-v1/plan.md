# Implementation Plan — User-Provided Metadata (v1)

1. Extend ingestion request models with optional `user_metadata`
2. Add validation (string keys and values)
3. Persist metadata on document creation
4. Propagate metadata to chunk creation
5. Ensure metadata is written to vector index payloads
6. Add regression tests
