import pytest
import os
from pathlib import Path

@pytest.fixture
def mock_mirror_dir(tmp_path):
    mirror = tmp_path / "mirror"
    mirror.mkdir()
    
    domain_dir = mirror / "wiki.dave.eu"
    domain_dir.mkdir()
    
    (domain_dir / "index.html").write_text("<html><head><title>Home</title></head><body><main>Home Page</main></body></html>")
    (domain_dir / "about.html").write_text("<html><head><title>About</title></head><body><div id='content'>About Page</div></body></html>")
    
    return mirror
