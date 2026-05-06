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

from pathlib import Path
from typing import Dict, Optional
from retriva.rendering import register_renderer
from retriva.logger import get_logger

logger = get_logger(__name__)

def clean_text_for_pdf(text: str) -> str:
    """Replace common Unicode characters with Latin-1 equivalents for fpdf2."""
    replacements = {
        "\u2013": "-",  # en-dash
        "\u2014": "--", # em-dash
        "\u2018": "'",  # left single quote
        "\u2019": "'",  # right single quote
        "\u201c": '"',  # left double quote
        "\u201d": '"',  # right double quote
        "\u2022": "*",  # bullet
        "\u2026": "...", # ellipsis
        "\u2122": "(TM)",
        "\u00a9": "(C)",
        "\u00ae": "(R)",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Fallback: replace any remaining non-latin-1 characters with '?'
    return text.encode("latin-1", "replace").decode("latin-1")

class PDFRenderer:
    """Renderer for PDF artifacts using fpdf2."""

    def render(
        self,
        artifact_type: str,
        parameters: Dict[str, str],
        output_path: Path,
        cancel_check: Optional[callable] = None,
    ) -> bool:
        logger.info(f"Rendering PDF artifact: {artifact_type}")
        
        try:
            from fpdf import FPDF
        except ImportError:
            logger.error("fpdf2 not installed. Cannot render PDF.")
            return False

        from retriva.rendering.services import fetch_artifact_data
        data = fetch_artifact_data(artifact_type, parameters)
        
        title = clean_text_for_pdf(data.get("title", "Retriva Artifact"))
        content = clean_text_for_pdf(data.get("content", "No content available."))
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(10)
        
        pdf.set_font("helvetica", "", 12)
        pdf.multi_cell(0, 10, content)
        
        if cancel_check and cancel_check():
            return False
            
        pdf.output(str(output_path))
        return True

# Register the renderer
register_renderer("pdf", PDFRenderer)
