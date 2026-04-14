---
description: Constitution for Core + Proprietary Extensions architecture
alwaysApply: true
---

# Retriva Constitution — Core + Extensions

## Product law
- Retriva OSS is a complete, functional RAG system
- Enterprise value is added through extensions, not forks
- OSS users must never require proprietary code for correctness

## Architecture law
- Core defines contracts and default implementations
- Extensions provide alternative implementations
- Selection happens through registration and composition

## Scope law
Out of scope:
- Licensing enforcement
- Auth / RBAC
- Build pipeline or packaging details
