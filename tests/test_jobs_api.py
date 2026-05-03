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

"""API tests for the /api/v1/jobs endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from retriva.ingestion_api.job_manager import JobManager


@pytest.fixture(autouse=True)
def reset_job_manager():
    """Reset JobManager singleton between tests."""
    JobManager._reset()
    yield
    JobManager._reset()


@pytest.fixture(autouse=True)
def mock_qdrant():
    with patch("retriva.ingestion_api.main.get_client"), \
         patch("retriva.ingestion_api.main.init_collection"):
        yield


from retriva.ingestion_api.main import app


# ---------------------------------------------------------------------------
# GET /api/v1/jobs
# ---------------------------------------------------------------------------

def test_list_jobs_empty():
    with TestClient(app) as client:
        response = client.get("/api/v1/jobs")
    assert response.status_code == 200
    assert response.json() == []


def test_list_jobs_after_submit():
    """Submitting an ingestion request should create a job visible in the list."""
    with TestClient(app) as client:
        with patch("retriva.ingestion_api.routers.ingest_text.process_text_in_background"):
            client.post("/api/v1/ingest/text", json={
                "source_path": "/wiki/test",
                "page_title": "Test",
                "content_text": "Hello world",
            })
        response = client.get("/api/v1/jobs")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["source"] == "/wiki/test"
    assert jobs[0]["job_type"] == "text"
    assert jobs[0]["status"] == "pending"


# ---------------------------------------------------------------------------
# GET /api/v1/jobs/{job_id}
# ---------------------------------------------------------------------------

def test_get_job_detail():
    mgr = JobManager()
    job = mgr.create_job(source="/wiki/detail", job_type="html")

    with TestClient(app) as client:
        response = client.get(f"/api/v1/jobs/{job.id}")
    assert response.status_code == 200
    assert response.json()["job_id"] == job.id
    assert response.json()["source"] == "/wiki/detail"


def test_get_job_not_found():
    with TestClient(app) as client:
        response = client.get("/api/v1/jobs/nonexistent")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/v1/jobs/{job_id}/cancel
# ---------------------------------------------------------------------------

def test_cancel_running_job():
    mgr = JobManager()
    job = mgr.create_job(source="/test", job_type="html")
    mgr.start_job(job.id)

    with TestClient(app) as client:
        response = client.post(f"/api/v1/jobs/{job.id}/cancel")
    assert response.status_code == 202
    assert response.json()["status"] == "cancelling"


def test_cancel_completed_job_returns_409():
    mgr = JobManager()
    job = mgr.create_job(source="/test", job_type="text")
    mgr.start_job(job.id)
    mgr.complete_job(job.id)

    with TestClient(app) as client:
        response = client.post(f"/api/v1/jobs/{job.id}/cancel")
    assert response.status_code == 409


def test_cancel_unknown_job_returns_404():
    with TestClient(app) as client:
        response = client.post("/api/v1/jobs/nonexistent/cancel")
    assert response.status_code == 404


def test_cancel_already_cancelling_is_idempotent():
    mgr = JobManager()
    job = mgr.create_job(source="/test", job_type="html")
    mgr.start_job(job.id)
    mgr.request_cancel(job.id)

    with TestClient(app) as client:
        response = client.post(f"/api/v1/jobs/{job.id}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelling"


# ---------------------------------------------------------------------------
# IngestResponse includes job_id
# ---------------------------------------------------------------------------

def test_ingest_response_contains_job_id():
    """All ingest endpoints should return a job_id."""
    with TestClient(app) as client:
        with patch("retriva.ingestion_api.routers.ingest_text.process_text_in_background"):
            response = client.post("/api/v1/ingest/text", json={
                "source_path": "/wiki/test",
                "page_title": "Test",
                "content_text": "Hello",
            })
    assert response.status_code == 202
    assert "job_id" in response.json()
    assert response.json()["job_id"] is not None
