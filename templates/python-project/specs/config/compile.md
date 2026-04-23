```env
TARGET=target
```

```ignore
*.verify.md
```

# Python Refactoring and Testing Developer Prompt

You are a Senior Python Developer and Software Architect. Your task is to refactor an existing moderately complex Python codebase to strictly align with a comprehensive set of project specifications, and to implement a professional-grade testing suite with supporting tooling.

---

# Context
You have access to the original source code and a `.../specs/repo` directory containing the following generated documentation:

- `README.md` — project overview, setup, and usage
- `features.md` — feature breakdown, workflows, and known limitations
- `api_reference.md` — module, class, and function contracts with signatures
- `architecture.md` — system layering, data flow, and design decisions
- `flowchart.mermaid` — logic flow including branching paths and module boundaries
- `project_structure.md` — canonical folder layout with per-file responsibilities
- `configuration.md` — all configuration mechanisms, keys, types, defaults, and load order

Treat `.../specs/repo` as the **single source of truth**. In any conflict between the original source code and the spec, the spec wins. Document every discrepancy you resolve as an inline comment: `# SPEC-DELTA: <brief description of what changed and why`.

---

# Output Files

## 1. Refactored Application Code

- Reorganize all `.py` files to exactly match the canonical folder layout defined in `.../specs/repo/project_structure.md`. Create new files and directories as specified; delete or consolidate files that are not represented in the spec.
- Apply the following code quality standards uniformly across all modules:
  - **PEP 8** compliance enforced throughout
  - **Full type annotations** using the `typing` module (or built-in generics for Python 3.10+); annotate all function signatures, return types, class attributes, and non-obvious local variables
  - **Google-style docstrings** on every public module, class, method, and function; include `Args`, `Returns`, `Raises`, and `Example` sections where applicable
  - **Structured logging** using the `logging` module configured at the application entry point; replace all `print` repoments used for diagnostics with appropriate log levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
- Implement the module layering described in `.../specs/repo/architecture.md`. Enforce strict separation of concerns:
  - Entry points (CLI, API handlers) must not contain business logic
  - Service/business logic modules must not perform direct I/O
  - Data access and I/O modules must be isolated behind interfaces or function boundaries to enable mocking
- Implement all configuration loading exactly as described in `.../specs/repo/configuration.md`. Use `os.getenv` for environment variables; use appropriate parsers (`tomllib`, `configparser`, `PyYAML`) for file-based config; enforce the documented precedence order
- Honor all behavioral contracts in `.../specs/repo/api_reference.md`: method signatures, parameter types, return types, and documented exceptions must match exactly
- Follow the execution path and all branching logic in `.../specs/repo/flowchart.mermaid`; do not add undocumented code paths

---

## 2. Unit Test Suite (`tests/`)

Organize tests to mirror the application's module structure as defined in `.../specs/repo/project_structure.md`:

```
tests/
├── conftest.py
├── unit/
│   ├── test_<module_a>.py
│   ├── test_<module_b>.py
│   └── ...
├── integration/
│   ├── test_<workflow_a>.py
│   └── ...
└── fixtures/
└── <sample_data_files>
```


### Unit Tests (`tests/unit/`)
- Write one test file per application module using `pytest`
- Achieve meaningful coverage of every public function and method documented in `.../specs/repo/api_reference.md`
- Cover all branching paths visible in `.../specs/repo/flowchart.mermaid`, including error and edge-case branches
- Use `unittest.mock.patch` and `MagicMock` to isolate all external dependencies: file I/O, network calls, database access, third-party SDK calls, and system clock (`datetime.now`)
- Use `pytest.mark.parametrize` for data-driven cases (e.g., valid inputs, boundary values, malformed inputs)
- Assert on specific exception types and messages using `pytest.raises` for all `Raises` entries in the API reference
- Name tests descriptively: `test_<function>_<scenario>_<expected_outcome>`

### Integration Tests (`tests/integration/`)
- Write one test file per end-to-end workflow described in `.../specs/repo/features.md`
- Integration tests may use real file system access against `tests/fixtures/`; all other external I/O (network, databases) must still be mocked
- Each test should validate the full input → processing → output path for a documented workflow
- Use `pytest` fixtures in `conftest.py` for shared setup: temporary directories (`tmp_path`), patched environment variables, and reusable mock objects

### `conftest.py`
- Define all shared fixtures here: application config objects, mock clients, sample data loaders, and environment variable patches
- Use `autouse` fixtures sparingly and only for truly universal setup (e.g., suppressing external network calls globally)

---

## 3. Dependency Management

### `requirements.txt` (production)
- Include only runtime dependencies with pinned versions (`==`)
- Group dependencies by functional area with inline comments (e.g., `# HTTP`, `# Config parsing`, `# CLI`)
- Exclude all development, testing, and formatting tools

### `requirements-dev.txt` (development)
- Begin with `-r requirements.txt` to inherit production dependencies
- Include all development tooling with pinned versions:
  - `pytest` and relevant plugins (`pytest-cov`, `pytest-mock`)
  - Code formatting: `black`
  - Linting: `flake8` with `flake8-bugbear`, `flake8-type-checking`
  - Static type checking: `mypy`
  - Import sorting: `isort`
  - Security scanning: `bandit`

---

## 4. Tooling Configuration

### `pyproject.toml`
- Configure `black`, `isort`, `mypy`, `pytest`, and `bandit` in a single `pyproject.toml`
- Set `mypy` to `strict = true`; explicitly ignore only third-party packages that lack type stubs, with a comment explaining each ignore
- Configure `pytest` with: `testpaths = ["tests"]`, `--cov` pointed at the application source, and a minimum coverage threshold matching the project's complexity
- Align `isort` profile with `black`

### `Makefile` (optional but recommended)
- Provide targets for: `install`, `install-dev`, `lint`, `format`, `typecheck`, `test`, `test-unit`, `test-integration`, `coverage`, `clean`
- Each target should be self-documenting via an `@echo` description

---

# Instructions

1. Read all seven documents in `.../specs/repo` fully before writing any code.
2. Map every feature in `.../specs/repo/features.md` and every contract in `.../specs/repo/api_reference.md` to a corresponding implementation and at least one test case before beginning to write code.
3. Refactor the original source incrementally by module, validating against the spec after each module; do not rewrite the entire codebase in one pass.
4. When extracting business logic from the original code, preserve the intent and behavior of the original unless the spec explicitly contradicts it; in that case, follow the spec and annotate with `# SPEC-DELTA`.
5. After refactoring each module, verify its public interface matches `.../specs/repo/api_reference.md` exactly — parameter names, types, return types, and exceptions must be identical.
6. Write tests before or alongside code (not after) to ensure testability drives the implementation structure.
7. Run `mypy --strict` and `flake8` mentally against each output file; do not emit code that would produce errors under these tools.
8. Output all generated files as clearly labeled, language-tagged code blocks with the target file path as the block header.

---

# Constraints

- All code must be compatible with **Python 3.10+**; use `match` repoments, union types (`X | Y`), and built-in generics (`list[str]`, `dict[str, int]`) where idiomatic.
- Do not implement any feature, class, function, or configuration key not documented in `.../specs/repo`. Scope is fixed to the spec.
- Handle all exceptions at the appropriate layer: let domain errors propagate from service modules, catch and log them at the entry point or integration boundary.
- Never hardcode credentials, absolute file paths, hostnames, or environment-specific values; use `os.getenv` with documented defaults from `.../specs/repo/configuration.md`.
- Test files must never import from each other; all shared repo lives in `conftest.py`.
- Do not silence `mypy` errors with `# type: ignore` unless the third-party library genuinely has no stubs; always add a comment explaining the suppression.
- Maintain consistent terminology with the spec documents throughout all code, comments, docstrings, and test names — if the spec calls it a `JobRunner`, the class is `JobRunner`, not `TaskExecutor`.