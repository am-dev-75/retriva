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

"""Unit tests for the JobManager state machine and thread safety."""

import pytest
import threading
from retriva.ingestion_api.job_manager import (
    JobManager, JobStatus, Job, CancellationError, TERMINAL_STATES,
)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the JobManager singleton between tests."""
    JobManager._reset()
    yield
    JobManager._reset()


# ---------------------------------------------------------------------------
# State transitions
# ---------------------------------------------------------------------------

def test_create_job():
    mgr = JobManager()
    job = mgr.create_job(source="/wiki/test", job_type="html")
    assert job.status == JobStatus.PENDING
    assert job.source == "/wiki/test"
    assert job.job_type == "html"
    assert job.cancel_requested is False


def test_lifecycle_happy_path():
    mgr = JobManager()
    job = mgr.create_job(source="/test", job_type="text")
    mgr.start_job(job.id)
    assert mgr.get_job(job.id).status == JobStatus.RUNNING
    mgr.complete_job(job.id)
    assert mgr.get_job(job.id).status == JobStatus.COMPLETED


def test_lifecycle_failure():
    mgr = JobManager()
    job = mgr.create_job(source="/test", job_type="text")
    mgr.start_job(job.id)
    mgr.fail_job(job.id, "Qdrant down")
    j = mgr.get_job(job.id)
    assert j.status == JobStatus.FAILED
    assert j.error == "Qdrant down"


def test_cancel_running_job():
    mgr = JobManager()
    job = mgr.create_job(source="/test", job_type="html")
    mgr.start_job(job.id)
    assert mgr.request_cancel(job.id) is True
    assert mgr.get_job(job.id).status == JobStatus.CANCELLING
    assert mgr.is_cancel_requested(job.id) is True
    mgr.mark_cancelled(job.id)
    assert mgr.get_job(job.id).status == JobStatus.CANCELLED


def test_cancel_pending_job():
    mgr = JobManager()
    job = mgr.create_job(source="/test", job_type="text")
    assert mgr.request_cancel(job.id) is True
    assert mgr.get_job(job.id).status == JobStatus.CANCELLING


def test_cannot_cancel_completed_job():
    mgr = JobManager()
    job = mgr.create_job(source="/test", job_type="text")
    mgr.start_job(job.id)
    mgr.complete_job(job.id)
    assert mgr.request_cancel(job.id) is False
    assert mgr.get_job(job.id).status == JobStatus.COMPLETED


def test_cancel_idempotent():
    mgr = JobManager()
    job = mgr.create_job(source="/test", job_type="html")
    mgr.start_job(job.id)
    assert mgr.request_cancel(job.id) is True
    assert mgr.request_cancel(job.id) is True  # idempotent
    assert mgr.get_job(job.id).status == JobStatus.CANCELLING


def test_unknown_job_returns_none():
    mgr = JobManager()
    assert mgr.get_job("nonexistent") is None
    assert mgr.is_cancel_requested("nonexistent") is False


def test_list_jobs():
    mgr = JobManager()
    mgr.create_job(source="/a", job_type="html")
    mgr.create_job(source="/b", job_type="text")
    jobs = mgr.list_jobs()
    assert len(jobs) == 2


def test_job_to_dict():
    mgr = JobManager()
    job = mgr.create_job(source="/test", job_type="image")
    d = job.to_dict()
    assert d["job_id"] == job.id
    assert d["status"] == "pending"
    assert d["source"] == "/test"
    assert d["job_type"] == "image"
    assert "created_at" in d
    assert "updated_at" in d


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

def test_concurrent_creates():
    """100 concurrent job creates should not lose any."""
    mgr = JobManager()
    results = []

    def create():
        job = mgr.create_job(source="/concurrent", job_type="text")
        results.append(job.id)

    threads = [threading.Thread(target=create) for _ in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 100
    assert len(set(results)) == 100  # all unique IDs
    assert len(mgr.list_jobs()) == 100
