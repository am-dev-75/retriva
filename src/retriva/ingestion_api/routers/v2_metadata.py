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
v2 metadata catalog endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query
from retriva.ingestion_api.schemas_v2 import MetadataSchemaResponse, MetadataValuesResponse, MetadataFieldSchema
from retriva.indexing.qdrant_store import get_client, get_detailed_metadata_schema, get_metadata_values
from retriva.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v2/metadata", tags=["v2-metadata"])


@router.get("/schema", response_model=MetadataSchemaResponse)
async def get_metadata_schema_v2():
    """
    Get detailed metadata schema including field types and supported operators.
    Used by the UI to build dynamic filter components.
    """
    try:
        client = get_client()
        fields = get_detailed_metadata_schema(client)
        return MetadataSchemaResponse(
            fields=[MetadataFieldSchema(**f) for f in fields]
        )
    except Exception as e:
        logger.error(f"Error getting metadata schema: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/values/{key:path}", response_model=MetadataValuesResponse)
@router.get("/values", response_model=MetadataValuesResponse)
async def get_metadata_values_v2(key: Optional[str] = None, field: Optional[str] = Query(None)):
    """
    Get all unique values and document counts for a specific metadata key.
    Supports both path parameter and '?field=' query parameter.
    """
    metadata_key = field or key
    if not metadata_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Metadata key must be provided as path parameter or 'field' query parameter."
        )
        
    try:
        client = get_client()
        # Returns list of dicts with {"value": ..., "count": ...}
        values_with_counts = get_metadata_values(client, metadata_key)
        return MetadataValuesResponse(key=metadata_key, values=values_with_counts)
    except Exception as e:
        logger.error(f"Error getting metadata values for {metadata_key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
