# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from openai import OpenAI, AsyncOpenAI
from retriva.config import settings
from retriva.qa.grounding import validate_grounding
from retriva.registry import CapabilityRegistry
from retriva.logger import get_logger
from retriva.profiler import Profiler

# Import modules to trigger default registrations
import retriva.qa.retriever        # noqa: F401 — registers DefaultRetriever
import retriva.qa.prompting        # noqa: F401 — registers DefaultPromptBuilder
import retriva.qa.reranker         # noqa: F401 — registers DefaultReranker
import retriva.qa.hybrid_selector  # noqa: F401 — registers DefaultHybridSelector

logger = get_logger(__name__)

def _limit_chunks_by_citations(chunks: list[dict], max_citations: int) -> list[dict]:
    """
    Limits the number of unique sources (titles) in the context.
    Also applies a per-source character limit to prevent context explosion
    from highly descriptive vision model chunks.
    """
    if max_citations <= 0:
        return chunks
        
    seen_titles = {} # title -> char_count
    limited_chunks = []
    
    # 1. Title-based filtering
    for chunk in chunks:
        title = chunk.get("page_title", "Unknown Page")
        if title not in seen_titles:
            if len(seen_titles) >= max_citations:
                continue
            seen_titles[title] = 0
            
        # 2. Per-source size budgeting (approx 6000 chars per source max)
        text = chunk.get("text", "")
        if seen_titles[title] + len(text) > 6000:
            if seen_titles[title] < 2000: # Ensure at least some text per source
                 truncated = text[:2000] + " [TRUNCATED]"
                 limited_chunks.append({**chunk, "text": truncated})
                 seen_titles[title] += len(truncated)
            continue
            
        limited_chunks.append(chunk)
        seen_titles[title] += len(text)
        
    return limited_chunks


def _rerank_if_enabled(query: str, chunks: list[dict]) -> list[dict]:
    """
    Apply two-stage re-ranking if enabled in settings.

    1. Slice candidates to ``retrieval_rerank_candidates``.
    2. Call the registered reranker with ``retrieval_rerank_top_n``.

    If disabled, return chunks unchanged.
    """
    if not settings.enable_retrieval_reranking:
        logger.debug("Re-ranking disabled, using vector-search order.")
        return chunks

    # Candidate selection: limit what enters the reranker
    candidates = settings.retrieval_rerank_candidates
    if 0 < candidates < len(chunks):
        logger.debug(
            f"Candidate selection: {len(chunks)} → {candidates} "
            f"(RETRIEVAL_RERANK_CANDIDATES={candidates})"
        )
        chunks = chunks[:candidates]

    registry = CapabilityRegistry()
    reranker = registry.get_instance("reranker")
    return reranker.rerank(query, chunks, settings.retrieval_rerank_top_n)


def _hybrid_select_if_enabled(
    reranked: list[dict],
    vector_top: list[dict],
) -> list[dict]:
    """
    Apply hybrid retrieval selection if both reranking and hybrid selection
    are enabled.  Merges top-M reranked results with top-L vector-search
    results to recover implicit evidence.

    If either feature is disabled, return *reranked* unchanged.
    """
    if not settings.enable_retrieval_reranking:
        return reranked
    if not settings.enable_hybrid_retrieval_selection:
        logger.debug("Hybrid selection disabled, using reranked set only.")
        return reranked

    registry = CapabilityRegistry()
    selector = registry.get_instance("hybrid_selector")
    return selector.select(
        reranked,
        vector_top,
        keep_m=settings.hybrid_rerank_keep_top_m,
        keep_l=settings.hybrid_vector_keep_top_l,
    )


def _retrieve_and_select(query: str, retriever_top_k: int, profiler) -> list[dict]:
    """
    Run the full retrieval pipeline: vector search → rerank → hybrid select.

    Returns the final chunk list ready for context budgeting.
    """
    registry = CapabilityRegistry()
    retriever = registry.get_instance("retriever")
    chunks = retriever.retrieve(query, top_k=retriever_top_k)

    if profiler:
        profiler.mark_phase("retrieval_vector_search_complete")

    # Preserve original vector order for hybrid selection
    vector_top = chunks[:]

    chunks = _rerank_if_enabled(query, chunks)

    if profiler:
        profiler.mark_phase("retrieval_reranking_complete")

    chunks = _hybrid_select_if_enabled(chunks, vector_top)

    if profiler:
        profiler.mark_phase("retrieval_hybrid_selection_complete")

    return chunks


def ask_question(question: str, retriever_top_k: int = 5) -> dict:
    logger.info(f"Processing question: {question}")
    sanitized_question = question.replace('"', '').replace("'", "").strip()

    profiler = Profiler.get_current()
    chunks = _retrieve_and_select(sanitized_question, retriever_top_k, profiler)

    chunks = _limit_chunks_by_citations(chunks, settings.max_citations)
    logger.info(f"Final context: {len(chunks)} chunks from up to {settings.max_citations} sources.")

    registry = CapabilityRegistry()
    prompt_builder = registry.get_instance("prompt_builder")
    system_prompt = prompt_builder.build_prompt(question, chunks)
    
    client = OpenAI(api_key=settings.chat_openai_api_key, base_url=settings.chat_base_url)
    response = client.chat.completions.create(
        model=settings.chat_model,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": question}],
        temperature=settings.chat_temperature,
        top_p=settings.chat_top_p
    )
    
    if not response.choices:
        logger.error("LLM returned an empty response (no choices).")
        return {"answer": "Error: LLM returned an empty response.", "retrieved_chunks": chunks, "grounding": []}
        
    answer_text = response.choices[0].message.content
    if answer_text is None:
        answer_text = ""
        
    grounding = validate_grounding(answer_text, chunks)
    return {"answer": answer_text, "retrieved_chunks": chunks, "grounding": grounding}


def ask_question_streaming(question: str, retriever_top_k: int = 5):
    logger.info(f"Processing question (streaming): {question}")
    sanitized_question = question.replace('"', '').replace("'", "").strip()

    profiler = Profiler.get_current()
    chunks = _retrieve_and_select(sanitized_question, retriever_top_k, profiler)

    chunks = _limit_chunks_by_citations(chunks, settings.max_citations)

    registry = CapabilityRegistry()
    prompt_builder = registry.get_instance("prompt_builder")
    system_prompt = prompt_builder.build_prompt(question, chunks)

    client = OpenAI(api_key=settings.chat_openai_api_key, base_url=settings.chat_base_url)
    stream = client.chat.completions.create(
        model=settings.chat_model,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": question}],
        temperature=settings.chat_temperature,
        top_p=settings.chat_top_p,
        stream=True,
    )

    def content_generator():
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
    return chunks, content_generator()


def ask_question_without_retrieval(question: str) -> str:
    client = OpenAI(api_key=settings.chat_openai_api_key, base_url=settings.chat_base_url)
    response = client.chat.completions.create(
        model=settings.chat_model,
        messages=[{"role": "user", "content": question}],
        temperature=settings.chat_temperature,
    )
    if not response.choices:
        return "Error: LLM returned an empty response."
    return response.choices[0].message.content or ""


def ask_question_streaming_without_retrieval(question: str):
    client = OpenAI(api_key=settings.chat_openai_api_key, base_url=settings.chat_base_url)
    stream = client.chat.completions.create(
        model=settings.chat_model,
        messages=[{"role": "user", "content": question}],
        temperature=settings.chat_temperature,
        stream=True,
    )

    def content_generator():
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
    return [], content_generator()

async def ask_question_streaming_async(question: str, retriever_top_k: int = 5):
    logger.info(f"Processing question (async streaming): {question}")
    sanitized_question = question.replace('"', '').replace("'", "").strip()
    
    from starlette.concurrency import run_in_threadpool

    profiler = Profiler.get_current()

    registry = CapabilityRegistry()
    retriever = registry.get_instance("retriever")
    chunks = await run_in_threadpool(retriever.retrieve, sanitized_question, top_k=retriever_top_k)

    if profiler:
        profiler.mark_phase("retrieval_vector_search_complete")

    # Preserve original vector order for hybrid selection
    vector_top = chunks[:]

    chunks = await run_in_threadpool(_rerank_if_enabled, sanitized_question, chunks)

    if profiler:
        profiler.mark_phase("retrieval_reranking_complete")

    chunks = _hybrid_select_if_enabled(chunks, vector_top)

    if profiler:
        profiler.mark_phase("retrieval_hybrid_selection_complete")

    chunks = _limit_chunks_by_citations(chunks, settings.max_citations)

    prompt_builder = registry.get_instance("prompt_builder")
    system_prompt = prompt_builder.build_prompt(question, chunks)

    client = AsyncOpenAI(api_key=settings.chat_openai_api_key, base_url=settings.chat_base_url)
    stream = await client.chat.completions.create(
        model=settings.chat_model,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": question}],
        temperature=settings.chat_temperature,
        top_p=settings.chat_top_p,
        stream=True,
    )

    async def content_generator():
        async for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
    return chunks, content_generator()


async def ask_question_streaming_without_retrieval_async(question: str):
    client = AsyncOpenAI(api_key=settings.chat_openai_api_key, base_url=settings.chat_base_url)
    stream = await client.chat.completions.create(
        model=settings.chat_model,
        messages=[{"role": "user", "content": question}],
        temperature=settings.chat_temperature,
        stream=True,
    )
    async def content_generator():
        async for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
    return [], content_generator()
