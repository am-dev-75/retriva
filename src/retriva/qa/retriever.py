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
from typing import List, Dict

logger = get_logger(__name__)

def retrieve_top_chunks(query: str, top_k: int = 5) -> List[Dict]:
    logger.debug(f"Retrieving top_{top_k} chunks for query...")
    embeddings = get_embeddings([query])
    query_vector = embeddings[0]
    
    client = get_client()
    results = search_chunks(client, query_vector, top_k=top_k)
    return results
