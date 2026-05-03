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
import threading
from unittest.mock import patch, MagicMock

import retriva.config as config
from retriva.domain.models import ParsedDocument
from retriva.ingestion.chunker import create_chunks
from retriva.ingestion_api.job_manager import JobManager, JobStatus
from retriva.ingestion_api.schemas import TextIngestRequest
from retriva.ingestion_api.routers.ingest_text import process_text_in_background

def run_test():
    print("Setting up cooperative cancellation test...")
    JobManager._reset()
    mgr = JobManager()
    
    # 1. Prepare a payload that produces multiple chunks
    payload = TextIngestRequest(
        source_path="test://cancel-behavior",
        page_title="Cancel Test",
        content_text="word " * 50000  # Will produce many chunks
    )
    
    job = mgr.create_job(source=payload.source_path, job_type="text")
    
    # 2. Mock 'get_embeddings' to return zeros instantly
    # 3. Mock 'client.upsert' to sleep for 0.5s per batch
    upsert_call_count = [0]
    
    def mocked_upsert(*args, **kwargs):
        upsert_call_count[0] += 1
        print(f"  [Qdrant_Mock] Simulated upsert of batch {upsert_call_count[0]}...")
        time.sleep(0.5)
        
    original_batch = config.settings.indexing_batch_size
    config.settings.indexing_batch_size = 2  # Small batches to trigger checkpoints

    with patch('retriva.ingestion_api.routers.ingest_text.get_client') as mock_get_client, \
         patch('retriva.indexing.qdrant_store.get_embeddings') as mock_get_embeds:
        
        mock_client = MagicMock()
        mock_client.upsert.side_effect = mocked_upsert
        mock_get_client.return_value = mock_client
        mock_get_embeds.return_value = [[0.0]*384] * config.settings.indexing_batch_size
        
        # 4. Start processing in background thread
        print(f"Starting ingestion job {job.id}...")
        worker = threading.Thread(target=process_text_in_background, args=(payload, job.id))
        worker.start()
        
        # 5. Let it run for ~1.2 seconds (should process 2-3 batches)
        time.sleep(1.2)
        
        # 6. Request cancellation
        print(f"Requesting cancellation for job {job.id}...")
        mgr.request_cancel(job.id)
        
        # 7. Wait for worker to exit
        worker.join()
        
        # 8. Verify results
        final_job = mgr.get_job(job.id)
        print("\n--- Results ---")
        print(f"Final Job Status: {final_job.status.value}")
        print(f"Batches Upserted: {upsert_call_count[0]}")
        
        assert final_job.status == JobStatus.CANCELLED, "Job didn't transition to CANCELLED"
        assert upsert_call_count[0] > 0, "Job didn't process any batches"
        assert upsert_call_count[0] < 10, "Job didn't stop early"
        print("✅ Validation successful: Background ingestion stopped mid-flight and transitioned to CANCELLED.")

try:
    run_test()
finally:
    config.settings.indexing_batch_size = 100 # restore default
