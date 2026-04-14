---
name: retriva-extension-architecture
description: Guidance on designing and integrating extensible architectures for Retriva.
---

# Retriva Extension Architecture

## Core principle

The OSS core owns:
- interfaces
- contracts
- invariants
- default implementations

Extensions may:
- replace implementations
- add new capabilities
- register themselves at startup

They must not:
- change public API behavior
- violate grounding or citation invariants
