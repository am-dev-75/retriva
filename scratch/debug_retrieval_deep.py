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

from retriva.qa.retriever import DefaultRetriever
from retriva.config import settings

question = "What is the maximum power consumption of AURA SOM?"
retriever = DefaultRetriever()

print(f"--- Deep Inspection of Vector Search (Top 200) ---")
chunks = retriever.retrieve(question, top_k=200)

found_pdf = []
found_power_vals = []

for i, c in enumerate(chunks, 1):
    title = c.get("page_title", "")
    text = c.get("text", "")
    
    if "pdf" in title.lower():
        found_pdf.append((i, title))
    
    # Look for the specific numbers from the golden answer
    if "2.8" in text or "2.75" in text or "3.8" in text:
        found_power_vals.append((i, title, text[:50]))

print(f"\nPDF Sources found in Top 200:")
for rank, title in found_pdf:
    print(f"  Rank {rank}: {title}")

print(f"\nPotential 'Power Value' matches (2.8, 2.75, 3.8) in Top 200:")
for rank, title, snippet in found_power_vals:
    print(f"  Rank {rank}: [{title}] {snippet}...")

if not found_pdf and not found_power_vals:
    print("\n[!] CRITICAL: No PDF sources or power values found in top 200.")
    print("This suggests the evidence might not be in the vector store or the embedding model (BGE-M3) is not ranking it highly for this query.")
