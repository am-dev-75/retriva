# Tasks — Document Deletion (v1)

- [x] Define API endpoint `DELETE /api/v1/documents/{doc_id}`
- [x] Implement filter-based deletion in `QdrantStore`
- [x] Implement idempotent response handling (204 for missing docs)
- [x] Register `documents` router in `main.py`
- [x] Update Retriva Adapter to suppress 404 alerts during sync
- [x] Verify deletion consistency with test scripts
