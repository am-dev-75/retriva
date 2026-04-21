import sys
import os
sys.path.append(os.path.join(os.getcwd(), "src"))

from pathlib import Path
from retriva.ingestion.markdown_parser import parse_markdown

test_file = Path("test_doc.md")
test_file.write_text("# Test Title\n\n## Section 1\nContent of section 1\n\n## Section 2\nContent of section 2")

try:
    result = parse_markdown(test_file)
    print(f"Title: {result['title']}")
    for s in result['sections']:
        print(f"Heading: '{s['heading']}' | Content: '{s['content']}'")
finally:
    if test_file.exists():
        test_file.unlink()
