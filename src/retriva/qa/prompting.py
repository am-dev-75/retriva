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
    Builds the grounded system prompt and user query safely formatted.
    """
    context_str = ""
    for idx, chunk in enumerate(retrieved_chunks):
        title = chunk.get("page_title", "Unknown Page")
        url = chunk.get("canonical_doc_id", "Unknown URL")
        text = chunk.get("text", "")
        # Add a clear citation block
        context_str += f"\n--- Document {idx+1} | Source: {title} ({url}) ---\n{text}\n"
        
    system_prompt = f"""You are Retriva, a grounded QA chatbot. Answer the user's question based ONLY on the provided context.
If the context does not contain sufficient evidence to answer the question, you must explicitly refuse by stating:
"I do not have sufficient evidence in my knowledge base to answer this question."

Support your factual claims with citations in the format [Document X].
Identify the language of the user's question. Formulate your complete answer strictly in the exact language used by the user, even if the provided chunks are documented entirely in a different language.

CONTEXT:
{context_str}
"""
    return system_prompt
