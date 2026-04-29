# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

"""Unit tests for CapabilityRegistry."""

import threading
import pytest
from retriva.registry import CapabilityRegistry


@pytest.fixture(autouse=True)
def reset_registry():
    """Ensure a clean registry for every test."""
    CapabilityRegistry._reset()
    yield
    CapabilityRegistry._reset()
    # Re-trigger default registrations so other test files find a populated registry
    import importlib
    import retriva.qa.retriever
    import retriva.qa.prompting
    import retriva.qa.reranker
    import retriva.qa.hybrid_selector
    import retriva.ingestion.chunker
    import retriva.ingestion.html_parser
    import retriva.ingestion.vlm_describer
    import retriva.ingestion.pdf_parser
    importlib.reload(retriva.qa.retriever)
    importlib.reload(retriva.qa.prompting)
    importlib.reload(retriva.qa.reranker)
    importlib.reload(retriva.qa.hybrid_selector)
    importlib.reload(retriva.ingestion.chunker)
    importlib.reload(retriva.ingestion.html_parser)
    importlib.reload(retriva.ingestion.vlm_describer)
    importlib.reload(retriva.ingestion.pdf_parser)


# -- Basic registration & resolution --------------------------------------

class ImplA:
    pass

class ImplB:
    pass


def test_register_and_get():
    reg = CapabilityRegistry()
    reg.register("foo", ImplA, priority=100)
    assert reg.get("foo") is ImplA


def test_higher_priority_wins():
    reg = CapabilityRegistry()
    reg.register("foo", ImplA, priority=100)
    reg.register("foo", ImplB, priority=200)
    assert reg.get("foo") is ImplB


def test_lower_priority_does_not_override():
    reg = CapabilityRegistry()
    reg.register("foo", ImplA, priority=200)
    reg.register("foo", ImplB, priority=50)
    assert reg.get("foo") is ImplA


def test_missing_capability_raises_key_error():
    reg = CapabilityRegistry()
    with pytest.raises(KeyError, match="no_such_thing"):
        reg.get("no_such_thing")


# -- Instance caching ------------------------------------------------------

def test_get_instance_returns_same_object():
    reg = CapabilityRegistry()
    reg.register("bar", ImplA, priority=100)
    inst1 = reg.get_instance("bar")
    inst2 = reg.get_instance("bar")
    assert inst1 is inst2


def test_get_instance_invalidated_on_new_registration():
    reg = CapabilityRegistry()
    reg.register("bar", ImplA, priority=100)
    inst_a = reg.get_instance("bar")
    assert isinstance(inst_a, ImplA)

    reg.register("bar", ImplB, priority=200)
    inst_b = reg.get_instance("bar")
    assert isinstance(inst_b, ImplB)
    assert inst_b is not inst_a


# -- Singleton pattern -----------------------------------------------------

def test_singleton():
    a = CapabilityRegistry()
    b = CapabilityRegistry()
    assert a is b


# -- Thread safety ---------------------------------------------------------

def test_concurrent_registrations():
    reg = CapabilityRegistry()
    errors = []

    def register_many(prefix: str):
        try:
            for i in range(50):
                type_name = f"{prefix}_{i}"
                cls = type(type_name, (), {})
                reg.register(f"cap_{prefix}", cls, priority=i)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=register_many, args=(f"t{t}",)) for t in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Unexpected errors: {errors}"
    # Each of the 4 threads registered 50 items under its own capability
    caps = reg.list_capabilities()
    for t in range(4):
        assert f"cap_t{t}" in caps


# -- list_capabilities -----------------------------------------------------

def test_list_capabilities():
    reg = CapabilityRegistry()
    reg.register("x", ImplA, priority=100)
    reg.register("x", ImplB, priority=200)
    listing = reg.list_capabilities()
    assert "x" in listing
    assert listing["x"][0] == (200, "ImplB")
    assert listing["x"][1] == (100, "ImplA")
