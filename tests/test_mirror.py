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
