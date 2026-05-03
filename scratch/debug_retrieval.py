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

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from retriva.qa.answerer import _retrieve_and_select
from retriva.config import settings
from retriva.logger import get_logger

# Use the same question as the benchmark
question = "What is the maximum power consumption of AURA SOM?"

print(f"--- Debugging Retrieval for: '{question}' ---")
print(f"Config: CANDIDATES={settings.retrieval_rerank_candidates}, M={settings.hybrid_rerank_keep_top_m}, L={settings.hybrid_vector_keep_top_l}")

# We'll run the internal pipeline directly to see the chunks
chunks = _retrieve_and_select(question, retriever_top_k=settings.retriever_top_k, profiler=None)

print(f"\nFinal chunks sent to LLM ({len(chunks)}):")
for i, c in enumerate(chunks, 1):
    title = c.get("page_title", "Unknown")
    text_snippet = c.get("text", "")[:100].replace("\n", " ")
    print(f"{i}. [{title}] {text_snippet}...")

# Check if the PDF source is present
has_pdf = any("pdf" in c.get("page_title", "").lower() for c in chunks)
print(f"\nCritical evidence (PDF source) present: {'YES' if has_pdf else 'NO'}")
