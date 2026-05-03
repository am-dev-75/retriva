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

from retriva.ingestion.html_parser import extract_main_content, extract_title

def test_extract_main_content():
    html = """
    <html>
        <head><title>Test Title</title></head>
        <body>
            <nav>Should be removed</nav>
            <div id='content'>
                <p>Paragraph 1</p>
                <script>ignore</script>
                <p>Paragraph 2</p>
            </div>
            <footer>Remove</footer>
        </body>
    </html>
    """
    
    content = extract_main_content(html)
    assert "Should be removed" not in content
    assert "ignore" not in content
    assert "Remove" not in content
    assert "Paragraph 1" in content
    assert "Paragraph 2" in content
    
def test_extract_title():
    html = "<html><head><title>Test Title </title></head><body></body></html>"
    assert extract_title(html) == "Test Title"
