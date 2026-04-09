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

from pydantic import BaseModel, Field
from typing import List

class ChunkMetadata(BaseModel):
    doc_id: str
    source_path: str
    page_title: str
    section_path: str
    chunk_id: str
    chunk_index: int
    chunk_type: str = "text"
    language: str = "en"

class Chunk(BaseModel):
    text: str
    metadata: ChunkMetadata

class ParsedDocument(BaseModel):
    source_path: str
    canonical_doc_id: str
    page_title: str
    content_text: str
    chunks: List[Chunk] = Field(default_factory=list)
