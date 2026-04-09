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

import re
from typing import List, Dict
from retriva.logger import get_logger

logger = get_logger(__name__)


def validate_grounding(answer: str, retrieved_chunks: List[Dict]) -> Dict:
    """
    Post-generation grounding validation.

    Checks:
    1. Citation presence  — does the answer contain [Document X] references?
    2. Citation validity  — do cited numbers fall within retrieved range?
    3. Textual overlap    — do key terms from the answer appear in context?
    4. Refusal detection  — did the model correctly refuse when unsure?

    Returns a dict with validation results and warnings.
    """
    warnings = []
    num_chunks = len(retrieved_chunks)

    # --- 1. Extract citations ---
    citation_pattern = re.compile(r"\[Document\s+(\d+)\]", re.IGNORECASE)
    cited_numbers = [int(m) for m in citation_pattern.findall(answer)]
    unique_citations = sorted(set(cited_numbers))

    # --- 2. Validate citation references ---
    invalid_citations = [n for n in unique_citations if n < 1 or n > num_chunks]
    citations_valid = len(invalid_citations) == 0

    if not unique_citations:
        warnings.append("No citations found in the answer.")
    if invalid_citations:
        warnings.append(
            f"Invalid citation(s) referencing non-existent documents: {invalid_citations}. "
            f"Valid range is [1..{num_chunks}]."
        )

    # --- 3. Refusal detection ---
    refusal_phrases = [
        "do not have sufficient evidence",
        "insufficient evidence",
        "cannot answer",
        "no relevant information",
    ]
    is_refusal = any(phrase in answer.lower() for phrase in refusal_phrases)

    # A refusal with no citations is expected and valid
    if is_refusal and not unique_citations:
        warnings = [w for w in warnings if "No citations" not in w]

    # --- 4. Textual overlap (lightweight keyword check) ---
    # Build a set of significant words from all retrieved context
    context_text = " ".join(
        chunk.get("text", "") for chunk in retrieved_chunks
    ).lower()
    context_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", context_text))

    # Extract significant words from the answer (skip common stop words)
    stop_words = {
        "this", "that", "with", "from", "have", "been", "were", "they",
        "their", "which", "would", "could", "should", "about", "these",
        "those", "will", "your", "more", "also", "does", "than", "into",
        "some", "such", "only", "other", "very", "just", "each", "based",
        "answer", "question", "document", "according", "states", "mentioned",
    }
    answer_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", answer.lower()))
    answer_words -= stop_words

    if answer_words:
        overlap = answer_words & context_words
        overlap_score = len(overlap) / len(answer_words)
    else:
        overlap_score = 0.0

    if overlap_score < 0.4 and not is_refusal:
        warnings.append(
            f"Low textual overlap ({overlap_score:.0%}) between answer and context. "
            f"The answer may contain information not grounded in the knowledge base."
        )

    # --- 5. Determine overall grounding status ---
    grounded = (
        (len(unique_citations) > 0 or is_refusal)
        and citations_valid
        and (overlap_score >= 0.4 or is_refusal)
    )

    result = {
        "grounded": grounded,
        "citations_found": unique_citations,
        "citations_valid": citations_valid,
        "overlap_score": round(overlap_score, 3),
        "is_refusal": is_refusal,
        "warnings": warnings,
    }

    if warnings:
        for w in warnings:
            logger.warning(f"Grounding: {w}")
    else:
        logger.debug(
            f"Grounding OK — {len(unique_citations)} citation(s), "
            f"overlap={overlap_score:.0%}"
        )

    return result
