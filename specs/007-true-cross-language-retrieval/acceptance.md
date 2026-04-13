# Acceptance Criteria — True Cross-Language Retrieval

## Dense Alignment Fidelity
- [ ] Submitting a question in Italian successfully returns English-origin textual source nodes within the `top_k` set whenever semantic density natively aligns.
- [ ] Submitting a question in English reliably surfaces identical context as long as English-origin source chunks contain facts.

## Invariant Generation Language
- [ ] The generated output strictly replies completely in the primary inferred language of the user's string in query requests. If the question string is an Italian sentence, it responds in Italian without intermixing English (except where acceptable terms of art or proper names override).
- [ ] An answer should still gracefully reference technical noun entities naturally if contextually warranted.

## Metadata Rendering & Tracking
- [ ] Valid REST API outputs generated through Open WebUI interactions reliably serialize `language` nodes within `citations` structures if present.
- [ ] The Streamlit QA chat client visually renders the source chunk's `language` metadata effectively directly within the expander context widgets for full transparency. 
- [ ] Running a `.get()` Qdrant endpoint sanity check verifies all newly ingested texts reflect language schemas inside `payload`.
