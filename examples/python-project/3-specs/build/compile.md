```env
TARGET=4-target
```


# Development Implementation Prompt (50-line version)

**Role**: Transform Technical Specifications into production-ready Python code.

## Deliverables

1. **Complete Python Code**: Implement all API_SPEC.md functions with full type hints, async/await, docstrings, custom exceptions, error handling. Keep files ≤300 lines; use dependency injection; no hard-coded values.

2. **Test Suite**: pytest with >80% coverage using pytest-asyncio. Mirror src/ structure in tests/unit/; add tests/integration/ for cross-module. Mock external services; test happy paths and errors.

3. **Configuration**: src/config.py loads from environment variables via os.getenv(). Create .env.example template. No secrets in code.

4. **Logging**: src/logger.py with daily rotating logs to logs/ directory. Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`. No print statements.

5. **run.sh Script**: Check Python ≥3.11, create venv, install dependencies. Support: `start`, `test`, `lint`, `format`, `clean`. Exit codes: 0 (success), 1 (error), 130 (signal).

6. **README.md**: Quick start (3 steps), project structure, test/lint commands, config guide, troubleshooting (~200 lines).

## Directory Structure
```
project/
├── src/ (main.py, config.py, logger.py, exceptions.py, models.py, <modules>/)
├── tests/ (conftest.py, unit/, integration/)
├── config/ (default.yaml, development.yaml, production.yaml)
├── logs/ (.gitignore'd, auto-created)
├── .env.example, .gitignore, requirements.txt, pyproject.toml, run.sh, README.md
```

## Code Standards
- Full type hints (Python 3.11+ TypedDict, Protocol, Generic)
- Async/await for all I/O; sync code justified
- Custom exceptions with code and message
- Dependency injection; no circular imports; absolute imports from src.
- Google-style docstrings (Args, Returns, Raises, Examples)
- Format with black; lint with flake8; type-check with mypy

## Configuration Pattern
```python
# src/config.py
import os
class Config:
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    @classmethod
    def validate(cls) -> None:
        if not cls.ENVIRONMENT in ["development", "production"]:
            raise ValueError("Invalid ENVIRONMENT")
```

## Success Criteria
1. All API_SPEC.md functions implemented with correct signatures
2. >80% test coverage; all tests pass
3. `./run.sh start|test|lint|format` work without manual steps
4. README sufficient for new developer to contribute
5. mypy passes; no `Any` without justification
6. Single responsibility; DI; no global state; clean code