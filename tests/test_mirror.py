import pytest
from pathlib import Path
from retriva.ingestion.mirror import source_to_canonical
from retriva.config import settings

def test_source_to_canonical(mock_mirror_dir):
    settings.mirror_base_path = str(mock_mirror_dir)
    settings.canonical_base_url = "https://wiki.dave.eu"
    
    path1 = str(mock_mirror_dir / "wiki.dave.eu" / "index.html")
    assert source_to_canonical(path1) == "https://wiki.dave.eu"
    
    path2 = str(mock_mirror_dir / "wiki.dave.eu" / "about.html")
    assert source_to_canonical(path2) == "https://wiki.dave.eu/about"
    
    path3 = str(mock_mirror_dir / "wiki.dave.eu" / "other" / "page.htm")
    assert source_to_canonical(path3) == "https://wiki.dave.eu/other/page"
