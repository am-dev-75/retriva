import os
import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from retriva.config import settings
from retriva.profiler import _profiler_logs, Profiler

class TestProfiler(unittest.TestCase):
    def setUp(self):
        _profiler_logs.clear()
        settings.enable_internal_profiler = True

    def test_profiler_records_phases_manual(self):
        # Start a request
        profiler = Profiler.start_request()
        self.assertEqual(len(profiler.phases), 1)
        self.assertIn("request_received", profiler.phases)
        
        # Mark some phases
        profiler.mark_phase("retrieval_vector_search_complete")
        profiler.mark_phase("inference_complete")
        
        # Finalize
        profiler.finalize()
        
        # Check logs
        self.assertEqual(len(_profiler_logs), 1)
        entry = _profiler_logs[0]
        self.assertIn("retrieval_vector_search_complete", entry["phases"])
        self.assertIn("inference_complete", entry["phases"])
        self.assertEqual(entry["total_duration_ms"], entry["phases"]["inference_complete"])

    def test_profiler_disabled_no_logs(self):
        settings.enable_internal_profiler = False
        profiler = Profiler.start_request()
        profiler.mark_phase("test_phase")
        profiler.finalize()
        
        # finalized log entry is NOT added if disabled
        # Wait, my Profiler.finalize check:
        # if not settings.enable_internal_profiler: return
        self.assertEqual(len(_profiler_logs), 0)

if __name__ == "__main__":
    unittest.main()
