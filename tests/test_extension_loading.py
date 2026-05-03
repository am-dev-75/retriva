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

"""Integration test: verify extension loading via RETRIVA_EXTENSIONS."""

import sys
import os
import pytest
from pathlib import Path
from retriva.registry import CapabilityRegistry


@pytest.fixture(autouse=True)
def reset_registry():
    CapabilityRegistry._reset()
    yield
    CapabilityRegistry._reset()
    # Re-trigger default registrations so other test files find a populated registry
    import importlib
    import retriva.qa.retriever
    import retriva.qa.prompting
    import retriva.ingestion.chunker
    import retriva.ingestion.html_parser
    import retriva.ingestion.vlm_describer
    importlib.reload(retriva.qa.retriever)
    importlib.reload(retriva.qa.prompting)
    importlib.reload(retriva.ingestion.chunker)
    importlib.reload(retriva.ingestion.html_parser)
    importlib.reload(retriva.ingestion.vlm_describer)


def test_mock_extension_overrides_default():
    """Load a mock extension and verify it replaces the default retriever."""
    reg = CapabilityRegistry()

    # Register the OSS default first (simulating normal import)
    from retriva.qa.retriever import DefaultRetriever
    reg.register("retriever", DefaultRetriever, priority=100)

    # Verify default is active
    assert reg.get("retriever") is DefaultRetriever

    # Now load the mock extension via the discovery mechanism
    # Ensure the fixtures directory is importable
    fixtures_dir = str(Path(__file__).parent / "fixtures")
    if fixtures_dir not in sys.path:
        sys.path.insert(0, fixtures_dir)

    reg.load_extensions("mock_extension")

    # The mock should now win (priority 200 > 100)
    from mock_extension import MockRetriever
    assert reg.get("retriever") is MockRetriever

    # Verify the instance works
    instance = reg.get_instance("retriever")
    result = instance.retrieve("test query", top_k=3)
    assert result[0]["doc_id"] == "mock_doc"


def test_no_extensions_uses_defaults():
    """With RETRIVA_EXTENSIONS empty, defaults are used."""
    reg = CapabilityRegistry()

    from retriva.qa.retriever import DefaultRetriever
    reg.register("retriever", DefaultRetriever, priority=100)

    # Simulate empty extensions
    reg.load_extensions("")

    assert reg.get("retriever") is DefaultRetriever
