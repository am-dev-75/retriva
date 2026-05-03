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

import httpx
import sys

BASE_URL = "http://localhost:8000"

def test_delete_non_existent():
    doc_id = "non-existent-doc-123"
    url = f"{BASE_URL}/api/v1/documents/{doc_id}"
    print(f"Testing DELETE {url}")
    try:
        response = httpx.delete(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 204:
            print("SUCCESS: Received 204 No Content for non-existent document.")
        else:
            print(f"FAILURE: Received {response.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_delete_non_existent()
