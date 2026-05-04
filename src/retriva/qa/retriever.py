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

from retriva.indexing.embeddings import get_embeddings
from retriva.indexing.qdrant_store import get_client, search_chunks
from retriva.logger import get_logger
from typing import List, Dict, Optional

logger = get_logger(__name__)


def retrieve_top_chunks(query: str, retriever_top_k: int = 5, metadata_filter: Optional[Dict[str, str]] = None) -> List[Dict]:
    logger.debug(f"Retrieving top_{retriever_top_k} chunks for query...")
    embeddings = get_embeddings([query])
    query_vector = embeddings[0]
    
    client = get_client()
    results = search_chunks(client, query_vector, retriever_top_k=retriever_top_k, metadata_filter=metadata_filter)
    for i, res in enumerate(results):
        logger.info(f"  Chunk {i+1}: {res.get('page_title')} (path: {res.get('source_path')})")
    return results


class DefaultRetriever:
    """OSS default retriever — semantic search via embeddings + Qdrant."""

    def retrieve(self, query: str, top_k: int, metadata_filter: Optional[Dict[str, str]] = None) -> List[Dict]:
        return retrieve_top_chunks(query, retriever_top_k=top_k, metadata_filter=metadata_filter)


# Register as default implementation
from retriva.registry import CapabilityRegistry
CapabilityRegistry().register("retriever", DefaultRetriever, priority=100)
