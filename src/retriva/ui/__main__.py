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

import sys
import argparse
from pathlib import Path

# Ensures 'src' is importable if run dynamically
src_path = str(Path(__file__).resolve().parent.parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from streamlit.web import cli as stcli

from retriva import config
from retriva.logger import setup_logging

def main():
    setup_logging()
    print(f"##### Retriva Streamlit UI ({config.VERSION}) #####\n")
    
    parser = argparse.ArgumentParser(description="Retriva Streamlit UI")
    parser.add_argument("--port", type=int, default=config.settings.ui_port, help="Binding port (default: %(default)s)")
    args = parser.parse_args()
    
    # Path to streamlit_app.py
    app_path = Path(__file__).resolve().parent / "streamlit_app.py"
    
    print(f"Starting Streamlit app on port {args.port}...")
    
    # Construct args for streamlit
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(args.port)
    ]
    
    # Hand off to Streamlit CLI
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
