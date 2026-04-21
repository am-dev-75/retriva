import sys
import os
from pathlib import Path

# Mock logger
class MockLogger:
    def info(self, msg): pass
    def error(self, msg): print(f"ERROR: {msg}")
    def debug(self, msg): pass

sys.modules["retriva.logger"] = type("module", (), {"get_logger": lambda n: MockLogger()})

sys.path.append(os.path.join(os.getcwd(), "src"))
from retriva.ingestion.markdown_parser import parse_markdown

# Create a sample markdown file
doc_path = Path("sample.md")
content = """# Main Title

Intro prose.

## Section 1
Content of section 1.

### Subsection 1.1
Content of subsection 1.1.

## Section 2
Content of section 2.
"""
doc_path.write_text(content)

try:
    print("Testing Markdown parsing...")
    result = parse_markdown(doc_path)
    
    assert result["title"] == "Main Title"
    sections = result["sections"]
    
    # We expect 4 sections:
    # 1. Heading="", Content="Intro prose."
    # 2. Heading="Section 1", Content="Content of section 1."
    # 3. Heading="Subsection 1.1", Content="Content of subsection 1.1."
    # 4. Heading="Section 2", Content="Content of section 2."
    
    print(f"Derived Title: {result['title']}")
    for i, s in enumerate(sections):
        print(f"Section {i}: Heading='{s['heading']}' | Content='{s['content']}'")
    
    assert len(sections) == 4
    assert sections[1]["heading"] == "Section 1"
    assert "Content of section 1" in sections[1]["content"]
    
    print("SUCCESS: Markdown parsing and section extraction work.")
finally:
    if doc_path.exists():
        doc_path.unlink()
