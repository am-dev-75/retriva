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

import time
from openai import OpenAI
from retriva.config import settings
from retriva.logger import get_logger
from typing import List

logger = get_logger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0  # seconds

def _embed_batch(client: OpenAI, texts: List[str]) -> List[List[float]]:
    """Embed a batch of texts with retry logic."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.embeddings.create(
                input=texts,
                model=settings.embedding_model
            )
            if not response.data:
                raise ValueError("No embedding data received")
            return [data.embedding for data in response.data]
        except (ValueError, Exception) as e:
            delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
            if attempt < MAX_RETRIES:
                logger.warning(
                    f"Embedding attempt {attempt}/{MAX_RETRIES} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                raise RuntimeError(
                    f"Embedding failed after {MAX_RETRIES} attempts: {e}"
                ) from e

def get_embeddings(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
        
    logger.debug(f"Creating embeddings for {len(texts)} texts in batches of {settings.indexing_batch_size}...")
    client = OpenAI(
        api_key=settings.embedding_openai_api_key,
        base_url=settings.embedding_base_url
    )
    
    all_embeddings = []
    for i in range(0, len(texts), settings.indexing_batch_size):
        batch = texts[i : i + settings.indexing_batch_size]
        batch_num = i // settings.indexing_batch_size + 1
        try:
            embeddings = _embed_batch(client, batch)
            all_embeddings.extend(embeddings)
        except RuntimeError:
            # Batch failed after retries — fall back to one-by-one
            logger.warning(
                f"Batch {batch_num} failed after retries. "
                f"Falling back to individual embedding for {len(batch)} texts..."
            )
            for j, text in enumerate(batch):
                try:
                    embeddings = _embed_batch(client, [text])
                    all_embeddings.extend(embeddings)
                except RuntimeError as e:
                    logger.error(
                        f"Skipping text {i + j} (len={len(text)}): {e}"
                    )
                    # Append a zero vector so indices stay aligned
                    all_embeddings.append([0.0] * settings.embedding_dimension)
    
    return all_embeddings
