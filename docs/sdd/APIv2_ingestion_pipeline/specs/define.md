# Define: Retriva Core API v2
**Goal**: Implement an independent `/api/v2` routing-based ingestion API that coexists safely with `/api/v1`.
**Key Requirements**:
1. Implement generic `POST /api/v2/documents`.
2. Propagate `metadata.user_metadata` into all chunk metadata.
3. Introduce a stage-aware job model (Detection -> Preprocessing -> Parsing -> Normalization).
4. Do not alter or break any existing `/api/v1` routes.
