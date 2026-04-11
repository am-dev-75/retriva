# Implementation Plan — Image Injection

## Phase 1: Schema Updates
- Update `ChunkMetadata` in `src/retriva/domain/models.py` with `image_path` explicitly.

## Phase 2: Sub-pipeline Implementation
- Build `image_parser.py` logic combining BeautifulSoup navigation to extract `<img>`/`<figure>` text attributes.
- Construct `create_image_chunks` within `chunker.py` to organize parsing outputs into indexable text formats.

## Phase 3: Integration
- Hook Image Parsing into `/api/v1/ingest/html` processing directly. 
- Avoid deleting or stripping raw tags until images are fully processed and mapped.

## Phase 4: Compatibility and Testing
- Validate existing standard HTML chunking workflows.
- Write tests confirming image chunk metadata structure and textual embedding context.
