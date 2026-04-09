# Acceptance Criteria — 001 Q&A-only PoC

## AC1 — Mirror ingestion works
Given a configured local static mirror, the ingest command discovers HTML pages, extracts content, creates chunks, and indexes them without fatal errors.

## AC2 — Wget-mirror compatibility is explicit
The implementation and documentation clearly assume a local static mirror compatible with `wget --mirror --convert-links --page-requisites --no-parent ...` and do not require MediaWiki API access.

## AC3 — Retrieved answers are grounded
Given an answerable question, the system answers using retrieved evidence and displays source citations.

## AC4 — Unsupported questions fail safely
Given an unsupported question, the system returns the explicit insufficient-evidence fallback.

## AC5 — English works
A supported English question receives an English answer.

## AC6 — Italian works
A supported Italian question receives an Italian answer.

## AC7 — Retrieval is inspectable
The UI exposes retrieved chunks and metadata in a debug panel.
