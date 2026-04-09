# Mirror Contract — Retriva v0.1.1

## Primary input format
The primary tested corpus artifact is a local static mirror created with a command equivalent to:

```bash
wget --mirror --convert-links --page-requisites --no-parent https://wiki.dave.eu
```

The implementation must target the **filesystem artifact**, not the `wget` binary itself.

## Expected characteristics
- HTML pages
- downloaded images referenced by those pages
- CSS / JS / auxiliary assets
- locally rewritten relative links

## Include rules
Prefer:
- `.html`
- `.htm`
- `index.html` inside mirrored folders

## Exclude rules
Exclude obvious non-content assets such as:
- CSS
- JS
- fonts
- generic media assets that are not HTML pages

## Content extraction rules
Try site-specific selectors first:
- `#content`
- `#mw-content-text`
- `main`
- `.mw-parser-output`

Remove boilerplate such as nav, footer, script, and style.

## Canonicalization
Store both:
- `source_path`
- `canonical_doc_id`

## Metadata minimum
- `doc_id`
- `source_path`
- `page_title`
- `section_path`
- `chunk_id`
- `chunk_index`
- `chunk_type`
- `language`
