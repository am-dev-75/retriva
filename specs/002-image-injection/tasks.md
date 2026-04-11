# Tasks — Image Injection

- [ ] Analyze current HTML ingestion flow and Pydantic schemas.
- [ ] Add `image_path: Optional[str] = None` to `ChunkMetadata` in `src/retriva/domain/models.py`.
- [ ] Implement `src/retriva/ingestion/image_parser.py` with `extract_images(html: str)` logic.
- [ ] Update `src/retriva/ingestion/chunker.py` to add a `create_image_chunks` mapping function.
- [ ] Modify `src/retriva/ingestion_api/routers/ingest.py` to call `extract_images()` during HTML processing.
- [ ] Ensure image chunks are properly embedded linearly alongside text chunks.
- [ ] Add Pytest regression tests validating HTML processing integrity and Image chunk generation.
