---
description: Constitution for bilingual regression validation and retrieval benchmarking
alwaysApply: true
---

# Retriva Constitution — Bilingual Regression Validation

## Product law
- This pack exists to verify and measure bilingual behavior, not to redesign retrieval.
- The system under test must support English and Italian.
- The benchmark must include same-language and cross-language cases.
- Grounded answers and citations remain required.

## Engineering law
- Keep fixtures deterministic and minimal.
- Prefer explicit expected evidence sets over vague qualitative checks.
- Preserve backward compatibility.
- Make benchmark outputs easy to compare across future releases.
