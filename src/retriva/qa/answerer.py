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
from retriva.qa.retriever import retrieve_top_chunks
from retriva.qa.prompting import build_prompt
from retriva.qa.grounding import validate_grounding
from retriva.logger import get_logger

logger = get_logger(__name__)

def ask_question(question: str, top_k: int = 5) -> dict:
    """
    Full QA pipeline: Retrieve, Prompt, Generate Chat
    """
    logger.info(f"Processing question: {question}")
    chunks = retrieve_top_chunks(question, top_k=top_k)
    logger.info(f"Retrieved {len(chunks)} chunks for context.")
    
    system_prompt = build_prompt(question, chunks)
    
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
        temperature=0.0,
        top_p=0.9
    )
    
    answer_text = response.choices[0].message.content
    grounding = validate_grounding(answer_text, chunks)

    return {
        "answer": answer_text,
        "retrieved_chunks": chunks,
        "grounding": grounding
    }
