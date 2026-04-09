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

import urllib.parse
from pathlib import Path
from retriva.config import settings
from retriva.logger import get_logger

logger = get_logger(__name__)

def source_to_canonical(source_path: str) -> str:
    """
    Converts a local mirror file path back to its canonical URL.
    Takes into account wget's domain translation and index.html standardizations.
    """
    base = Path(settings.mirror_base_path).resolve()
    target = Path(source_path).resolve()
    
    try:
        rel = target.relative_to(base)
    except ValueError:
        logger.warning(f"File {source_path} is outside of mirror base path {base}.")
        return ""
        
    rel_str = str(rel)
    
    # Typically wget puts files under mirror_base_path/domain.com/
    canonical_domain = urllib.parse.urlparse(settings.canonical_base_url).netloc
    parts = rel.parts
    
    if parts and parts[0] == canonical_domain:
        rel_str = "/".join(parts[1:])
        
    # Strip known extensions
    if rel_str.endswith("index.html"):
        rel_str = rel_str[:-10]
    elif rel_str.endswith(".html"):
        rel_str = rel_str[:-5]
    elif rel_str.endswith(".htm"):
        rel_str = rel_str[:-4]
        
    rel_str = rel_str.strip("/")
    
    canonical = settings.canonical_base_url.rstrip("/")
    if rel_str:
        canonical = f"{canonical}/{rel_str}"
        
    return canonical
