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

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

VERSION = "0.10.0"

class Settings(BaseSettings):
    mirror_base_path: str = str((Path(__file__).resolve().parent / "mirror").resolve())
    canonical_base_url: str = "https://wiki.dave.eu"
    
    qdrant_url: str = "http://192.168.1.64:6333"
    local_openai_api_key: str = "sk-mock-key"
    openrouter_openai_api_key: str = ""
    
    # Embedding model
    embedding_base_url: str = "https://openrouter.ai/api/v1"
    embedding_model: str = "baai/bge-m3"
    embedding_dimension: int = 1024
    embedding_openai_api_key: Optional[str] = None

    # Visual model
    visual_base_url: str = "https://openrouter.ai/api/v1"
    visual_model: str = "qwen/qwen3-vl-32b-instruct"
    visual_openai_api_key: Optional[str] = None
    visual_max_tokens: int = 2048
    visual_temperature: float = 0.0
    
    # Chat model
    chat_base_url: str = "https://openrouter.ai/api/v1"
    chat_model: str = "qwen/qwen3.5-27b"
    chat_openai_api_key: Optional[str] = None
    chat_temperature: float = 0.0
    chat_top_p: float = 0.9

    # Chunking
    max_chunk_chars: int = 12000
    chunk_overlap: int = 500
    indexing_batch_size: int = 50

    # Retrieving stuff
    retriever_top_k: int = 200

    # OpenAI-compatible API (for Open WebUI)
    openai_api_port: int = 8001

    # Modular Injection API
    ingestion_api_port: int = 8000
    
    model_config = SettingsConfigDict(
        env_file=str((Path(__file__).resolve().parents[2] / ".env").resolve()), 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    def model_post_init(self, __context) -> None:
        """Fall back per-service API keys to the shared openrouter key."""
        if not self.embedding_openai_api_key:
            self.embedding_openai_api_key = self.openrouter_openai_api_key
        if not self.visual_openai_api_key:
            self.visual_openai_api_key = self.openrouter_openai_api_key
        if not self.chat_openai_api_key:
            self.chat_openai_api_key = self.openrouter_openai_api_key

settings = Settings()
