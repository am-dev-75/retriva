import sys
import os
from pathlib import Path

# Mock get_logger to avoid dependency issues
class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")
    def debug(self, msg): pass

def get_logger(name): return MockLogger()

# Mock settings
class MockSettings:
    mirror_base_path = "."
    canonical_base_url = "http://example.com"

settings = MockSettings()

# Inject mocks into sys.modules before importing discover
sys.modules["retriva.logger"] = type("module", (), {"get_logger": get_logger})
sys.modules["retriva.config"] = type("module", (), {"settings": settings})

sys.path.append(os.path.join(os.getcwd(), "src"))
from retriva.ingestion.discover import discover_files

# Create test structure
base = Path("test_discovery")
base.mkdir(exist_ok=True)
(base / "sub1").mkdir(exist_ok=True)
(base / "doc1.md").write_text("content")
(base / "sub1" / "doc2.markdown").write_text("content")
(base / "other.txt").write_text("content")

try:
    print("Testing recursive discovery...")
    found = discover_files(base)
    print(f"Found files: {found}")
    
    md_files = found.get("markdown", [])
    assert len(md_files) == 2
    assert any("doc1.md" in f for f in md_files)
    assert any("doc2.markdown" in f for f in md_files)
    print("SUCCESS: Recursive discovery works for Markdown.")
finally:
    # Cleanup
    import shutil
    if base.exists():
        shutil.rmtree(base)
