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
