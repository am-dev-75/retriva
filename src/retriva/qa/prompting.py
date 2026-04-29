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

from typing import List, Dict

def build_prompt(question: str, retrieved_chunks: List[Dict]) -> str:
    """
    Builds the grounded system prompt with Open WebUI-compatible citations.

    Open WebUI parses bracketed references (e.g. ``[Page Title]``) from the
    LLM response text and turns them into clickable citation chips.  To make
    this work the context blocks must carry identifiable source labels and
    the LLM must be instructed to reference those labels.
    """
    # Group chunks by title to avoid duplicate source IDs in the prompt
    grouped = {}
    for chunk in retrieved_chunks:
        title = chunk.get("page_title", "Unknown Page")
        if title not in grouped:
            grouped[title] = {
                "url": chunk.get("canonical_doc_id", chunk.get("source_path", "")),
                "texts": [chunk.get("text", "")]
            }
        else:
            # Only add if text is not exactly the same
            new_text = chunk.get("text", "")
            if new_text not in grouped[title]["texts"]:
                grouped[title]["texts"].append(new_text)

    context_str = ""
    source_list = ""
    for title, data in grouped.items():
        url = data["url"]
        combined_text = "\n\n---\n\n".join(data["texts"])
        source_id = f"[{title}]"
        
        # Build context block with unique source tag
        context_str += (
            f"\n<source id=\"{title}\">\n"
            f"Source: {title}\n"
            f"URL: {url}\n"
            f"{combined_text}\n"
            f"</source>\n"
        )
        source_list += f"  - {source_id}\n"

    system_prompt = f"""You are Retriva, a grounded QA chatbot. Answer the user's question based ONLY on the provided context.
If the context does not contain sufficient evidence to answer the question, you must explicitly refuse by stating:
"I do not have sufficient evidence in my knowledge base to answer this question."

CITATION RULES:
- Support your factual claims with citations using the exact source names provided.
- Use the format [Source Title] for each citation.
- You may cite multiple sources in one sentence.
- Available sources:
{source_list}
Identify the language of the user's question. Formulate your complete answer strictly in the exact language used by the user, even if the provided chunks are documented entirely in a different language.

CONTEXT:
{context_str}
"""
    return system_prompt


class DefaultPromptBuilder:
    """OSS default prompt builder — grounded QA with citation format."""

    def build_prompt(self, question: str, chunks: List[Dict]) -> str:
        return build_prompt(question, chunks)


# Register as default implementation
from retriva.registry import CapabilityRegistry
CapabilityRegistry().register("prompt_builder", DefaultPromptBuilder, priority=100)
