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
import retriva.qa.retriever  # noqa: F401 — registers DefaultRetriever
import retriva.qa.prompting  # noqa: F401 — registers DefaultPromptBuilder

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

def ask_question(question: str, retriever_top_k: int = 5) -> dict:
    logger.info(f"Processing question: {question}")
    registry = CapabilityRegistry()
    retriever = registry.get_instance("retriever")
    sanitized_question = question.replace('"', '').replace("'", "").strip()
    chunks = retriever.retrieve(sanitized_question, top_k=retriever_top_k)
    
    profiler = Profiler.get_current()
    if profiler:
        profiler.mark_phase("retrieval_vector_search_complete")
        profiler.mark_phase("retrieval_ranking_complete")

    chunks = _limit_chunks_by_citations(chunks, settings.max_citations)
    logger.info(f"Final context: {len(chunks)} chunks from up to {settings.max_citations} sources.")

    prompt_builder = registry.get_instance("prompt_builder")
    system_prompt = prompt_builder.build_prompt(question, chunks)
    
    client = OpenAI(api_key=settings.chat_openai_api_key, base_url=settings.chat_base_url)
    response = client.chat.completions.create(
        model=settings.chat_model,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": question}],
        temperature=settings.chat_temperature,
        top_p=settings.chat_top_p
    )
    
    answer_text = response.choices[0].message.content
    grounding = validate_grounding(answer_text, chunks)
    return {"answer": answer_text, "retrieved_chunks": chunks, "grounding": grounding}


def ask_question_streaming(question: str, retriever_top_k: int = 5):
    logger.info(f"Processing question (streaming): {question}")
    registry = CapabilityRegistry()
    retriever = registry.get_instance("retriever")
    sanitized_question = question.replace('"', '').replace("'", "").strip()
    chunks = retriever.retrieve(sanitized_question, top_k=retriever_top_k)
    
    profiler = Profiler.get_current()
    if profiler:
        profiler.mark_phase("retrieval_vector_search_complete")
        profiler.mark_phase("retrieval_ranking_complete")

    chunks = _limit_chunks_by_citations(chunks, settings.max_citations)

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
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    return chunks, content_generator()


def ask_question_without_retrieval(question: str) -> str:
    client = OpenAI(api_key=settings.chat_openai_api_key, base_url=settings.chat_base_url)
    response = client.chat.completions.create(
        model=settings.chat_model,
        messages=[{"role": "user", "content": question}],
        temperature=settings.chat_temperature,
    )
    return response.choices[0].message.content


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
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    return [], content_generator()

async def ask_question_streaming_async(question: str, retriever_top_k: int = 5):
    logger.info(f"Processing question (async streaming): {question}")
    registry = CapabilityRegistry()
    retriever = registry.get_instance("retriever")
    sanitized_question = question.replace('"', '').replace("'", "").strip()
    
    from starlette.concurrency import run_in_threadpool
    chunks = await run_in_threadpool(retriever.retrieve, sanitized_question, top_k=retriever_top_k)
    
    profiler = Profiler.get_current()
    if profiler:
        profiler.mark_phase("retrieval_vector_search_complete")
        profiler.mark_phase("retrieval_ranking_complete")

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
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
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
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    return [], content_generator()
