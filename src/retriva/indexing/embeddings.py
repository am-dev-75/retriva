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

import httpx
from openai import APIConnectionError, APITimeoutError, RateLimitError

logger = get_logger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0  # seconds


# ---------------------------------------------------------------------------
# Network-error detection
# ---------------------------------------------------------------------------

class NetworkUnreachableError(RuntimeError):
    """Raised when the host is unreachable at the OS/network level."""


def _is_network_unreachable(exc: BaseException) -> bool:
    """Walk the exception chain looking for errno 101 (ENETUNREACH)."""
    current: BaseException | None = exc
    while current is not None:
        if isinstance(current, OSError) and current.errno == 101:
            return True
        current = current.__cause__
    return False


# ---------------------------------------------------------------------------
# Core embedding with smart retry
# ---------------------------------------------------------------------------

def _embed_batch(client: OpenAI, texts: List[str]) -> List[List[float]]:
    """
    Embed a batch of texts with retry logic.

    Retries on transient errors (rate-limits, timeouts, brief connection
    hiccups) but fails fast on non-transient network errors such as
    'Network is unreachable' (errno 101).
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.embeddings.create(
                input=texts,
                model=settings.embedding_model,
            )
            if not response.data:
                raise ValueError("No embedding data received")
            return [data.embedding for data in response.data]

        except (APIConnectionError, httpx.ConnectError) as e:
            # Distinguish non-transient network failures from flaky ones
            if _is_network_unreachable(e):
                raise NetworkUnreachableError(
                    "Network is unreachable — cannot contact embedding service"
                ) from e

            # Other connection errors (DNS blip, TLS handshake) may be transient
            delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
            if attempt < MAX_RETRIES:
                logger.warning(
                    f"Embedding attempt {attempt}/{MAX_RETRIES} failed "
                    f"(connection error). Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                raise RuntimeError(
                    f"Embedding failed after {MAX_RETRIES} attempts: {e}"
                ) from e

        except (APITimeoutError, RateLimitError) as e:
            # Always worth retrying
            delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
            if attempt < MAX_RETRIES:
                logger.warning(
                    f"Embedding attempt {attempt}/{MAX_RETRIES} failed "
                    f"({type(e).__name__}). Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                raise RuntimeError(
                    f"Embedding failed after {MAX_RETRIES} attempts: {e}"
                ) from e

        except Exception as e:
            # Unexpected / non-retryable (bad request, auth, etc.)
            raise RuntimeError(f"Embedding failed: {e}") from e


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_embeddings(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []

    logger.debug(
        f"Creating embeddings for {len(texts)} text(s) "
        f"in batches of {settings.indexing_batch_size}..."
    )
    # Disable the SDK's own retry to avoid double-retry storms;
    # we handle retries ourselves in _embed_batch.
    client = OpenAI(
        api_key=settings.embedding_openai_api_key,
        base_url=settings.embedding_base_url,
        max_retries=0,
    )

    all_embeddings: List[List[float]] = []
    for i in range(0, len(texts), settings.indexing_batch_size):
        batch = texts[i : i + settings.indexing_batch_size]
        batch_num = i // settings.indexing_batch_size + 1
        try:
            embeddings = _embed_batch(client, batch)
            all_embeddings.extend(embeddings)

        except NetworkUnreachableError:
            # No point retrying individual texts or further batches —
            # the network is down.
            logger.error(
                "Network is unreachable. Aborting embedding — "
                f"skipping batch {batch_num} and all remaining batches."
            )
            remaining = len(texts) - i
            all_embeddings.extend(
                [[0.0] * settings.embedding_dimension] * remaining
            )
            break

        except RuntimeError:
            # Batch failed after retries — fall back to one-by-one
            logger.warning(
                f"Batch {batch_num} failed after retries. "
                f"Falling back to individual embedding for {len(batch)} text(s)..."
            )
            for j, text in enumerate(batch):
                try:
                    embeddings = _embed_batch(client, [text])
                    all_embeddings.extend(embeddings)
                except NetworkUnreachableError:
                    logger.error(
                        "Network is unreachable during individual fallback. "
                        "Aborting remaining embeddings."
                    )
                    remaining = len(batch) - j + (len(texts) - i - len(batch))
                    all_embeddings.extend(
                        [[0.0] * settings.embedding_dimension] * remaining
                    )
                    return all_embeddings
                except RuntimeError as e:
                    logger.error(
                        f"Skipping text {i + j} (len={len(text)}): {e}"
                    )
                    # Append a zero vector so indices stay aligned
                    all_embeddings.append([0.0] * settings.embedding_dimension)

    return all_embeddings
