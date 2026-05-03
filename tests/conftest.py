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
