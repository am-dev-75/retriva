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

"""
Default hybrid selector for Retriva OSS.

After re-ranking selects the most precisely relevant chunks, hybrid
selection merges the top M re-ranked results with the top L vector-search
results (deduplicated), recovering implicit evidence without introducing
additional inference calls.

Pipeline position::

    Vector Search → Re-Rank → **Hybrid Selection** → Context Budget → LLM

Override path for Retriva Pro:
    Register a custom ``hybrid_selector`` capability at priority > 100
    via the CapabilityRegistry (e.g. Reciprocal Rank Fusion, MMR).
"""

from typing import Dict, List

from retriva.logger import get_logger

logger = get_logger(__name__)


class DefaultHybridSelector:
    """
    Two-knob hybrid merge: precision (M) + recall (L).

    Algorithm:
        1. Take the top *keep_m* from the re-ranked set (precision).
        2. Build a set of chunk identities from the precision set.
        3. Scan the top *keep_l* from vector-search results; append any
           chunk whose identity is not already present (recall).
        4. Return the merged list: precision first, then recall.

    Identity is determined by text content hash — the simplest stable
    key that works across all injector types.
    """

    def select(
        self,
        reranked: List[Dict],
        vector_top: List[Dict],
        keep_m: int,
        keep_l: int,
    ) -> List[Dict]:
        """
        Build hybrid context from re-ranked precision and vector recall.

        Returns ``reranked[:keep_m]`` followed by deduplicated
        ``vector_top[:keep_l]``.  Final size ≤ ``keep_m + keep_l``.
        """
        # 1. Precision set: top M from re-ranked
        precision = reranked[:keep_m] if keep_m > 0 else []

        if keep_l <= 0:
            return precision

        # 2. Build identity set from precision chunks
        seen = set()
        for chunk in precision:
            seen.add(self._identity(chunk))

        # 3. Recall set: top L from vector-search, deduplicated
        merged = list(precision)
        added = 0

        for chunk in vector_top[:keep_l]:
            ident = self._identity(chunk)
            if ident not in seen:
                seen.add(ident)
                merged.append(chunk)
                added += 1

        if added > 0:
            logger.info(
                f"Hybrid selection: {len(precision)} reranked (M) + "
                f"{added} vector (L) = {len(merged)} total"
            )
        else:
            logger.debug(
                f"Hybrid selection: all top-{keep_l} vector chunks "
                f"already present in reranked set — no additions."
            )

        return merged

    @staticmethod
    def _identity(chunk: Dict) -> int:
        """Return a hash-based identity for deduplication."""
        return hash(chunk.get("text", ""))


# Register as default implementation
from retriva.registry import CapabilityRegistry
CapabilityRegistry().register("hybrid_selector", DefaultHybridSelector, priority=100)
