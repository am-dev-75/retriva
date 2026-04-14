# Agent Instructions — Retriva Core + Proprietary Extensions (Model 3)

## Mission
Introduce a **Core + Extensions architecture** enabling Retriva to support an
open-source core and proprietary/enterprise extensions without forks or feature flags.

## Order of authority
1. `specs/009-core-plus-extensions/spec.md`
2. `specs/009-core-plus-extensions/architecture.md`
3. `.agent/rules/retriva-constitution.md`
4. `specs/009-core-plus-extensions/tasks.md`

## Non-negotiable rules
- Do not modify the repository root README.md
- The OSS core must not depend on proprietary code
- Proprietary code may depend on the OSS core
- All extension points must be explicit and documented
- No build-time or runtime forks of the OSS core
