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

from openai import OpenAI
from retriva.config import settings
from retriva.qa.grounding import validate_grounding
from retriva.registry import CapabilityRegistry
from retriva.logger import get_logger

# Import modules to trigger default registrations
import retriva.qa.retriever  # noqa: F401 — registers DefaultRetriever
import retriva.qa.prompting  # noqa: F401 — registers DefaultPromptBuilder

logger = get_logger(__name__)

def ask_question(question: str, retriever_top_k: int = 5) -> dict:
    """
    Full QA pipeline: Retrieve, Prompt, Generate Chat
    """
    logger.info(f"Processing question: {question}")
    registry = CapabilityRegistry()
    retriever = registry.get_instance("retriever")
    chunks = retriever.retrieve(question, top_k=retriever_top_k)
    logger.info(f"Retrieved {len(chunks)} chunks for context.")

    prompt_builder = registry.get_instance("prompt_builder")
    system_prompt = prompt_builder.build_prompt(question, chunks)
    
    logger.debug(f"Connecting to chat model ({settings.chat_base_url})...")
    client = OpenAI(
        api_key=settings.chat_openai_api_key,
        base_url=settings.chat_base_url
    )
    
    response = client.chat.completions.create(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        temperature=settings.chat_temperature,
        top_p=settings.chat_top_p
    )
    
    answer_text = response.choices[0].message.content
    grounding = validate_grounding(answer_text, chunks)

    return {
        "answer": answer_text,
        "retrieved_chunks": chunks,
        "grounding": grounding
    }


def ask_question_streaming(question: str, retriever_top_k: int = 5):
    """
    Streaming variant of ask_question().

    Returns (chunks, content_generator) where:
    - chunks: list of retrieved context chunks (for citation building)
    - content_generator: iterator yielding content strings from the LLM stream

    Note: grounding validation is skipped in streaming mode because it
    requires the full answer text.
    """
    logger.info(f"Processing question (streaming): {question}")
    registry = CapabilityRegistry()
    retriever = registry.get_instance("retriever")
    chunks = retriever.retrieve(question, top_k=retriever_top_k)
    logger.info(f"Retrieved {len(chunks)} chunks for context.")

    prompt_builder = registry.get_instance("prompt_builder")
    system_prompt = prompt_builder.build_prompt(question, chunks)

    logger.debug(f"Connecting to chat model (streaming) ({settings.chat_base_url})...")
    client = OpenAI(
        api_key=settings.chat_openai_api_key,
        base_url=settings.chat_base_url,
    )

    stream = client.chat.completions.create(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        temperature=settings.chat_temperature,
        top_p=settings.chat_top_p,
        stream=True,
    )

    def content_generator():
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    return chunks, content_generator()
