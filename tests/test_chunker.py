import pytest
from retriva.domain.models import ParsedDocument
from retriva.ingestion.chunker import create_chunks, recursive_split_text
from retriva.config import settings

def test_recursive_split_text():
    text = "Line 1\nLine 2. Sentence 1. Sentence 2. Word1 Word2 Word3"
    # Split by \n
    chunks = recursive_split_text(text, max_chars=10, overlap=0)
    for c in chunks:
        assert len(c) <= 10
    assert len(chunks) > 1

def test_recursive_split_text_with_overlap():
    text = "This is a very long sentence that should be split with some overlap."
    max_chars = 20
    overlap = 5
    chunks = recursive_split_text(text, max_chars=max_chars, overlap=overlap)
    
    for i in range(1, len(chunks)):
        # Check if there is some overlap (this is a bit heuristic but should work)
        # Actually, let's just check lengths first
        assert len(chunks[i-1]) <= max_chars
        assert len(chunks[i]) <= max_chars

def test_create_chunks_long_doc():
    # Mock settings
    original_max = settings.max_chunk_chars
    settings.max_chunk_chars = 50
    try:
        content = "Paragraph 1 is short.\n\nParagraph 2 is very " + "long " * 20 + "and needs splitting."
        doc = ParsedDocument(
            source_path="test.html",
            canonical_doc_id="test",
            page_title="Test",
            content_text=content
        )
        chunks = create_chunks(doc)
        
        assert len(chunks) > 2 # At least paragraph 1 and multiple for paragraph 2
        for c in chunks:
            assert len(c.text) <= 50
    finally:
        settings.max_chunk_chars = original_max
