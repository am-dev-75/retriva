from retriva.qa.prompting import build_prompt

def test_build_prompt_includes_fallback_and_context():
    chunks = [
        {
            "page_title": "Dave's Page",
            "canonical_doc_id": "https://wiki.dave.eu/page",
            "text": "The sky is blue today."
        }
    ]
    
    prompt = build_prompt("What color is the sky?", chunks)
    
    # Must include fallback behavior instruction
    assert "I do not have sufficient evidence" in prompt
    
    # Must include contextual evidence and metadata
    assert "The sky is blue today." in prompt
    assert "Dave's Page" in prompt
    assert "https://wiki.dave.eu/page" in prompt
