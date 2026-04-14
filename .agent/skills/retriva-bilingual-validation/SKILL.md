---
name: retriva-bilingual-validation
description: Guidance for validating English/Italian retrieval and answering behavior in Retriva.
---

# Retriva Bilingual Validation

## Objective
Validate that Retriva behaves correctly across all bilingual pathways:
- EN→EN
- IT→IT
- EN→IT
- IT→EN

## What to validate
- retrieval returns relevant evidence
- cross-language evidence is reachable
- answer language matches the user query language
- citations remain grounded and inspectable
- fallback behavior still works when evidence is weak or absent
