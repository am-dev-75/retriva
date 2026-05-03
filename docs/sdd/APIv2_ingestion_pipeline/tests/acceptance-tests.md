# Acceptance Criteria
1. **Coexistence**: Requests to `/api/v1/ingest/text` still succeed and return identical v1 responses.
2. **Metadata**: Ingesting via v2 with `{"user_metadata": {"tenant": "A"}}` results in chunks containing `"tenant": "A"`.
3. **Jobs**: Fetching a v2 job returns stage data (e.g., `current_stage: "PARSING"`).
