```env
TARGET=5-docs
```
# Documentation Transformation Prompt (50-line version)

**Role**: Principal Technical Writer. Transform production codebase into comprehensive, maintainable documentation.

## 10 Required Documents

**1. README.md**: Title & tagline | Status badges | What it does (2-3 para) | Quick start (install, run, verify) | Mermaid architecture diagram | Key features | Doc map table | Contributing & license

**2. ARCHITECTURE.md**: System overview & patterns | Component map (Mermaid graph TD) | Per-module breakdown (responsibility, classes, async/sync, examples) | Data flow (Mermaid sequenceDiagram) | Concurrency model | Database schema & ORM | External integrations (APIs, rate limits, retries) | Config management | Error handling & resilience | Deployment architecture | Performance (p50/p95/p99) | Security (auth, encryption, audit)

**3. API_SPEC.md**: API overview (REST/gRPC/CLI) | Auth & authorization | Pydantic data models (Mermaid classDiagram) | REST endpoints (method/path/request/response with ≥3 examples/endpoint) | gRPC services | CLI commands | Internal APIs (signatures, docstrings) | Event schemas (topics, producer/consumer) | Config schema (env vars, defaults) | Error codes table (Code|Status|Message|Recovery) | Deprecated APIs | Version history

**4. DEPLOYMENT.md**: Platforms & resource requirements | Installation & setup | Environment config (dev/staging/prod) | Database management (migrations, backup, restore) | Start/stop & health checks | Monitoring & metrics | Scaling & performance tuning | Disaster recovery (RTO/RPO) | Upgrades & rollbacks | Troubleshooting (debug steps, log locations) | Operational runbooks (restart, failover, incident response)

**5. TESTING.md**: Test pyramid (unit/integration/E2E) | Coverage targets | Unit tests (framework, mocking, running tests) | Integration tests (fixtures, isolation) | E2E tests (critical workflows) | Performance benchmarks | Security tests (SAST/DAST, vulnerability scanning) | CI/CD integration | Test data & fixtures

**6. DEVELOPMENT.md**: Environment setup (venv, dev deps, pre-commit) | Project structure | Code style (PEP 8, 100% type hints, linters) | Running linters (black/flake8/mypy commands) | Feature workflow (branching, commits, code review) | Building & packaging | Debugging & profiling | Common tasks (run, test, coverage, migrations) | Troubleshooting

**7. CONTRIBUTING.md**: Code of conduct | Fork/clone/branch workflow | Types of contributions | Submitting changes (PR template, code review) | Reporting issues (bug/feature templates) | Documentation contributions | Licensing & CLA | Getting help

**8. CHANGELOG.md**: Semantic versioning | "Keep a Changelog" format | Unreleased section | Per version: Added/Changed/Deprecated/Removed/Fixed/Security | Issue/PR links | Breaking change migration guides | Deprecation policy

**9. FILESYSTEM.md**: Complete ASCII directory tree | Directory purpose table (Path|Purpose|Files|Owner) | Module organization rationale | Test mirroring strategy | Config directories | Build artifacts | Top-level files (pyproject.toml, setup.py, workflows)

**10. FAQ.md**: Setup & installation | Usage & common tasks | Performance & scaling | Integration questions | Troubleshooting | Contributing | Project governance

## Standards

**Quality Gates**: No placeholders ("TODO", "TBD") | All code examples tested & runnable | ≥3 examples per endpoint | Actual implementation, not theoretical | Verified against current code

**Code Examples**: Actual Python code | Runnable with imports | Expected output shown | Error cases included | Tested working

**Diagrams**: Mermaid only (graph TD/LR, classDiagram, sequenceDiagram, stateDiagram-v2, erDiagram) | Self-explanatory nodes/edges

**Cross-References**: Relative links `[text](./FILE.md#section)` | Back-references | Auto-generated TOC

**Format**: Markdown text | Python code blocks | Tables for structured data | Numbered lists for procedures | Bold for key terms

**Maintenance**: Docs reviewed in same PR as code | Updated before release | Last-updated date on each doc | Version-controlled alongside code

## Quality Checklist
- [ ] README complete with all sections & working examples
- [ ] ARCHITECTURE reflects actual design with Mermaid diagrams
- [ ] All code examples tested & runnable
- [ ] All Mermaid syntax valid & rendering
- [ ] API_SPEC has ≥3 payloads per endpoint
- [ ] DEPLOYMENT includes actual resource requirements
- [ ] DEVELOPMENT enables contributor onboarding in 1 hour
- [ ] All links valid & up-to-date
- [ ] No outdated info; verified against actual code
- [ ] Consistent terminology throughout
- [ ] Accessible to unfamiliar readers
- [ ] Professional tone matching audience