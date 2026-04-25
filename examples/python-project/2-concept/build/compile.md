```env
TARGET=3-specs
```

# Transform Concept into Technical Specifications (50-line version)

**Role**: Principal Software Architect. Convert project concept into 6 comprehensive specification markdown files.

## Required Files

**1. ARCHITECTURE.md**: System overview (2-3 para) | Design principles | Logic flow (Mermaid graph TD) | Component table (Name|Responsibility|Dependencies|Tech) | Integration points (sync/async/REST) | Error handling (retries, circuit breakers) | Scalability & caching | Security (auth, encryption, audit)

**2. REQUIREMENTS.md**: Functional requirements (FR-1.x per module; acceptance criteria; edge cases) | Non-functional requirements (performance, scalability, availability, security) | Constraints & assumptions | Out of scope

**3. API_SPEC.md**: Pydantic data models (fields, types, validation, examples) | Mermaid classDiagram | Function signatures (full type hints, exceptions) | Event/message schemas (topics, producer/consumer) | Config schema (env vars, secrets) | Error codes/exceptions (code, HTTP status, recovery)

**4. FILESYSTEM.md**: ASCII directory tree (trailing `/` for dirs) | Directory purpose table (Path|Purpose|Contains|Owner) | File naming conventions | Key artifacts (pyproject.toml, src/, test mirroring) | Entry points

**5. DEPLOYMENT.md**: Dev/staging/production architecture | Infrastructure (compute, storage, networking) | CI/CD pipeline (build, test, deploy) | Monitoring & logging | Database migrations | Runbook (restart, rollback, scaling)

**6. README.md**: Index linking all specs with relative links

## Standards

**Architecture**: SOLID | Layered | DI | Async-first | 100% type hints (Python 3.11+)

**Diagrams**: Mermaid only (graph TD, classDiagram, sequenceDiagram, stateDiagram-v2)

**Code**: Valid Python 3.11+ | Pydantic v2 | asyncio | TypedDict | Protocol | match/case

**Quality Gates**:
- No placeholder text
- Valid Mermaid syntax
- ≥3 concrete example payloads in API_SPEC
- No circular dependencies
- Supports 2x growth without major refactoring

**Format**: Self-contained + cross-referenced | Structured tables | Version-control friendly | Implementer-ready