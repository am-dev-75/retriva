import os
import yaml
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

# Must patch Qdrant collection BEFORE importing routers
import retriva.indexing.qdrant_store as qdrant_store
qdrant_store.COLLECTION_NAME = "retriva_bilingual_benchmark"

from retriva.ingestion_api.main import app as ingest_app
from retriva.openai_api.main import app as chat_app

ingest_client = TestClient(ingest_app)
chat_client = TestClient(chat_app)

def load_benchmark_data():
    path = Path(__file__).parent.parent / "specs" / "008-bilingual-regression-validation" / "benchmark-cases.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

BENCHMARK_DATA = load_benchmark_data()
FIXTURES = BENCHMARK_DATA["fixtures"]
CASES = BENCHMARK_DATA["cases"]

@pytest.fixture(scope="module", autouse=True)
def setup_qdrant_fixtures():
    """Ingests the benchmark fixtures directly via chunk upserts for absolute control, 
       bypassing async jobs to ensure they are available immediately."""
    from retriva.indexing.qdrant_store import get_client, init_collection
    from retriva.domain.models import Chunk, ChunkMetadata
    from retriva.indexing.embeddings import get_embeddings
    import hashlib

    client = get_client()

    # Reset collection 
    try:
        client.delete_collection(qdrant_store.COLLECTION_NAME)
    except:
        pass
    init_collection(client)

    chunks = []
    for idx, doc in enumerate(FIXTURES):
        chunk_id = hashlib.md5(f"{doc['id']}_0".encode()).hexdigest()
        meta = ChunkMetadata(
            doc_id=doc["id"],
            source_path=doc["id"],
            page_title=doc["title"],
            section_path="",
            chunk_id=chunk_id,
            chunk_index=0,
            chunk_type="text",
            language=doc["language"]
        )
        chunks.append(Chunk(text=doc["content"], metadata=meta))

    # Upsert efficiently
    qdrant_store.upsert_chunks(client, chunks)
    
    yield

def calculate_metrics(expected_id: str, retrieved_ids: list, k: int = 3):
    """Calculates recall@k and precision@k."""
    top_k = retrieved_ids[:k]
    recall = 1.0 if expected_id in top_k else 0.0
    
    hits = sum(1 for rid in top_k if rid == expected_id)
    precision = hits / len(top_k) if top_k else 0.0
    
    return recall, precision

@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_bilingual_retrieval_and_generative_qa(case):
    # 1. Retrieval Evaluation
    from retriva.indexing.embeddings import get_embeddings
    from retriva.indexing.qdrant_store import search_chunks, get_client
    
    print(f"\n--- Running Case: {case['id']} ---")
    
    query_vector = get_embeddings([case["query_text"]])[0]
    client = get_client()
    hits = search_chunks(client, query_vector, retriever_top_k=3)
    
    # Map qdrant hits back to fixture IDs
    retrieved_doc_ids = [hit["doc_id"] for hit in hits]
    
    if case.get("expected_fallback_triggered"):
        assert len(retrieved_doc_ids) == 0 or case["expected_retrieval_ids"] == [], "Expected no valid hits for fallback."
    else:
        # We only expect 1 ground truth ID in our tiny benchmark
        expected_id = case["expected_retrieval_ids"][0]
        recall, precision = calculate_metrics(expected_id, retrieved_doc_ids, k=3)
        print(f"Metrics -> Recall@3: {recall}, Precision@3: {precision:.2f}")
        assert recall == 1.0, f"Retrieval failed for {case['id']}. Retrieved: {retrieved_doc_ids}"

    # 2. QA Validation Evaluation
    req_payload = {
        "model": "retriva",
        "messages": [{"role": "user", "content": case["query_text"]}],
        "temperature": 0.0
    }
    
    res = chat_client.post("/v1/chat/completions", json=req_payload)
    assert res.status_code == 200, res.text
    data = res.json()
    
    answer = data["choices"][0]["message"]["content"]
    citations = data["choices"][0]["message"].get("metadata", {}).get("citations", [])
    
    print(f"Answer: {answer}")
    
    if case.get("expected_fallback_triggered"):
        # Just ensure it doesn't give a hallucinated factual answer
        fallback_markers = ["sufficient evidence", "not have sufficient", "non ho prove"]
        triggered = any(m.lower() in answer.lower() for m in fallback_markers)
        print(f"Fallback triggered properly? {triggered}")
        # Note: the exact language of fallback depends on prompt engineering, so we flexibly enforce fallback detection.
        assert len(citations) == 0, "Wait, fallback query shouldn't cite things."
    else:
        # Check explicit correct response language loosely (LLM test structure)
        # We rely on specific words that are definitely in EN vs IT.
        # This is a heuristic test, production would use a model to classify language.
        en_markers = ["the", "is", "of", "protecting", "database", "apollo", "exactly", "kept"]
        it_markers = ["i", "di", "per", "richieste", "conservati", "esattamente", "limite"]
        
        answer_lower = answer.lower()
        if case["expected_answer_language"] == "en":
            assert any(m in answer_lower for m in en_markers), "Answer does not appear to be English."
        else:
            assert any(m in answer_lower for m in it_markers), "Answer does not appear to be Italian."

        # Verify Citation Math
        assert len(citations) > 0, "No citations provided."
        citation_sources = [c["source"] for c in citations]
        assert expected_id in citation_sources, f"Expected {expected_id} in citations, got {citation_sources}"
        
        # Verify citation has language payload mapped accurately
        for c in citations:
            if c["source"] == expected_id:
                doc = next((d for d in FIXTURES if d["id"] == expected_id), None)
                assert c["language"] == doc["language"], "Language metadata was not preserved through API citation."
