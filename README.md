# LIPS — LLM-Driven Iterative Project Synthesis

LIPS is a Python framework for orchestrating **multi-stage LLM transformation pipelines**. Each stage takes a source repository, applies a build instruction (Markdown, Python, or Shell), and produces a target repository — with every prompt, response, and generated file fully logged for reproducibility.

Pipelines chain stages together so the output of one stage becomes the input of the next, enabling complex, auditable, multi-step code generation and document transformation workflows across any LLM provider.

---

## Table of Contents

- [Concepts](#concepts)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Directory Layout](#directory-layout)
- [Configuration](#configuration)
- [Build Files](#build-files)
- [CLI Reference](#cli-reference)
- [Utility Reference](#utility-reference)
- [Supported LLM Providers](#supported-llm-providers)
- [Logging & Reproducibility](#logging--reproducibility)

---

## Concepts

| Term | Meaning |
|---|---|
| **Workspace** | A root directory containing one or more pipelines and a shared `config.json` |
| **Pipeline** | A named, ordered collection of stages forming a transformation workflow |
| **Stage** | A single transformation step with a source repo, build instructions, and a target repo |
| **Build file** | The instruction set for a stage — Markdown (LLM-driven), Python, or Shell |

### How a stage works

```
Source repo  →  build file  →  LLM / script  →  Target repo
(stage/repo)    (stage/build)                    (next stage/repo)
```

A stage directory has three sub-directories:

```
my_stage/
├── build/     # Build files (.md, .py, .sh, .bat)
├── repo/      # Source/target file repository
└── out/       # Logged outputs (created on first run)
```

---

## Installation

**Requirements:** Python 3.11+

```bash
git clone https://github.com/qia-uofa/lips
cd lips
pip install -e .
```

Set your API key in a `.env` file at the workspace root:

```
MISTRAL_API_KEY=your_key_here
# or OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, etc.
```

---

## Quick Start

### 1. Create a pipeline interactively

```bash
lips create ./my_workspace/my_pipeline
```

The wizard walks you through:
- Choosing an LLM provider and model
- Setting generation parameters (max tokens, temperature)
- Defining stages and their build files

### 2. Run a build

```bash
lips build main ./my_workspace/my_pipeline/stage1
```

This executes `stage1/build/main.md` (or `.py` / `.sh` / `.bat`), calls the LLM, and writes generated files into `stage1/repo/`.

### 3. Chain stages

After stage 1 completes, run stage 2 using the output:

```bash
lips build main ./my_workspace/my_pipeline/stage2
```

### 4. Clean up

```bash
# Purge a single stage
lips purge ./my_workspace/my_pipeline/stage1

# Purge the entire pipeline
lips purge -p ./my_workspace/my_pipeline
```

---

## Directory Layout

A typical workspace looks like this:

```
workspace/
├── config.json              # Workspace-level LLM config and pipeline graph
├── .env                     # API keys
└── my_pipeline/
    ├── stage1/
    │   ├── build/
    │   │   └── main.md      # Build instructions (Markdown LLM prompt)
    │   ├── repo/            # Source files (populated before build)
    │   └── out/             # Logged outputs (created after first build)
    │       └── mistral/sk-xxx/mistral-large-latest/2024-01-01T12-00-00/
    │           ├── messages.json
    │           ├── response.md
    │           └── files.json
    └── stage2/
        ├── build/
        │   └── main.md
        ├── repo/            # Files written here by stage1 build
        └── out/
```

---

## Configuration

### `config.json`

Located at the workspace root. Created automatically by `lips create`.

```json
{
  "generate": {
    "model": "mistral/mistral-large-latest",
    "max_tokens": 20000,
    "temperature": 0,
    "timeout": 1200
  },
  "api_var": "MISTRAL_API_KEY",
  "messages": [
    { "role": "system", "content": "You are a helpful assistant." },
    { "role": "user",   "content": "Example input..." },
    { "role": "assistant", "content": "<file path=\"./example.py\">...</file>" }
  ],
  "pipelines": {
    "my_pipeline": {
      "graph": {
        "stage1": { "main": "stage2" },
        "stage2": { "main": null }
      }
    }
  }
}
```

| Field | Description |
|---|---|
| `generate.model` | LiteLLM model string, e.g. `"openai/gpt-4o"`, `"anthropic/claude-opus-4-6"` |
| `generate.max_tokens` | Maximum tokens in the LLM response |
| `generate.temperature` | Sampling temperature (0 = deterministic) |
| `generate.timeout` | API call timeout in seconds |
| `api_var` | Name of the environment variable holding the API key |
| `messages` | Few-shot conversation examples to guide LLM output format |
| `pipelines` | Informational graph of stage transitions |

### `.env`

```
MISTRAL_API_KEY=sk-...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Stage-level `.env` blocks

Inside a Markdown build file you can embed environment variables:

````markdown
```env
TARGET=stage2
MY_VAR=some_value
```
````

These are extracted at build time and injected into the LLM prompt context.

---

## Build Files

LIPS supports three kinds of build files, resolved in this order: `.md` → `.py` → `.sh` / `.bat`.

### Markdown (LLM-driven)

The primary format. The file is a natural language prompt sent to the configured LLM. LIPS:

1. Extracts `env` blocks and injects environment variables
2. Extracts `sourceignore` / `targetignore` blocks for file filtering
3. Resolves `[write:virtual/path](./real/path)` links, embedding file contents as `<file>` blocks
4. Sends the composed prompt to the LLM
5. Parses the response for `<file path="...">content</file>` tags
6. Writes each file to the target stage's `repo/`

**Example build file (`stage1/build/main.md`):**

````markdown
```env
TARGET=stage2
```

```sourceignore
__pycache__
.git
*.pyc
```

You are a Python expert. Refactor the code below so that all functions are type-annotated.

Source files:
[write:src](./repo)

Write every modified file using the standard <file> format.
````

#### `[write:...]` link syntax

| Syntax | Effect |
|---|---|
| `[write:virtual/path](./real/file.py)` | Embeds a single file |
| `[write:virtual/dir](./real/dir)` | Recursively embeds all files in a directory |

Embedded content is wrapped as `<file path="virtual/path">...</file>` in the prompt. PDFs, Word documents, Excel files, and PowerPoint files are automatically converted to extracted text.

#### LLM response format

The LLM must respond with `<file>` tags:

```xml
<file path="./src/module.py">
def hello(name: str) -> str:
    return f"Hello, {name}"
</file>
```

Files with empty content are deleted from the target repo. Existing files not mentioned are left untouched.

---

### Python

```bash
# stage/build/main.py is executed via:
python - < main.py
```

The script runs in the stage's parent directory with all environment variables available.

---

### Shell

```bash
# Unix: executed with bash
# Windows: executed with cmd.exe or PowerShell
```

Shell scripts receive all environment variables, including those set in the workspace `.env` and stage-level `env` blocks.

---

## CLI Reference

### `lips create <path>`

Interactive wizard to scaffold a new pipeline.

```bash
lips create ./workspace/my_pipeline
```

**Prompts for:**
- LLM provider and model
- `max_tokens`, `temperature`
- API key
- Stage names and their build file names
- Which stage is the final (output) stage

**Creates:**
- `config.json` (workspace level, if not present)
- Stage directories with `build/` and `repo/` sub-directories
- Default build file stubs

---

### `lips build [build_file] <stage_path>`

Execute a build file for a stage.

```bash
lips build [build_file] <stage_path> [-c config.json] [-d dotenv_dir]
```

| Argument | Default | Description |
|---|---|---|
| `build_file` | `main` | Build file name without extension |
| `stage_path` | (required) | Path to the stage directory |
| `-c, --config` | auto-discovered | Path to `config.json` |
| `-d, --dotenv` | `./` | Directory containing `.env` |

**Resolution order for `build_file`:** `.md` → `.py` → `.sh` → `.bat`

**Examples:**

```bash
# Run main.md in stage1
lips build main ./workspace/my_pipeline/stage1

# Run a custom build file
lips build refactor ./workspace/my_pipeline/stage1

# Specify config and env locations
lips build main ./stage1 -c ./workspace/config.json -d ./workspace
```

---

### `lips purge <dir>`

Remove generated outputs from a stage or pipeline.

```bash
lips purge <dir> [-p]
```

| Argument | Description |
|---|---|
| `dir` | Path to stage (or pipeline with `-p`) directory |
| `-p, --pipeline` | Purge all stages in the pipeline |

**What is removed:**
- All files in `repo/` except `.gitignore`
- The entire `out/` directory

**What is preserved:**
- Directory structure (`build/`, `repo/`, `out/` folders remain)
- `.gitignore` files inside `repo/`

**Examples:**

```bash
# Purge a single stage
lips purge ./workspace/my_pipeline/stage1

# Purge all stages in a pipeline
lips purge -p ./workspace/my_pipeline
```

---

## Utility Reference

These internal utilities can be used programmatically.

### `lips.utils.parse_files`

```python
from lips.utils.parse_files import parse_files

files = parse_files(llm_response_text)
# Returns: {"./src/main.py": "def hello(): ...", "./README.md": "# Hello"}
```

Extracts all `<file path="...">content</file>` blocks from a string.

---

### `lips.utils.parse_build_files`

```python
from lips.utils.parse_build_files import env_from_build_file, ignore_from_build_file

# Extract env block and return cleaned markdown + env dict
cleaned_md, env_dict = env_from_build_file(markdown_text)

# Extract sourceignore and targetignore patterns
cleaned_md, sourceignore, targetignore = ignore_from_build_file(markdown_text)
```

---

### `lips.utils.resolve_md`

```python
from lips.utils.resolve_md import resolve_env, resolve_links

# Replace <env:KEY> placeholders
resolved = resolve_env(template_text, {"KEY": "value"})

# Expand [write:...] links into <file> blocks
expanded = resolve_links(markdown_text, root_path, ignore_patterns)
```

---

## Supported LLM Providers

LIPS uses [LiteLLM](https://github.com/BerriAI/litellm) to support any provider it supports. Set the `model` field in `config.json` using LiteLLM's `"provider/model"` format.

| Provider | Example model string |
|---|---|
| Mistral | `mistral/mistral-large-latest` |
| OpenAI | `openai/gpt-4o` |
| Anthropic | `anthropic/claude-opus-4-6` |
| Google | `gemini/gemini-1.5-pro` |
| Azure OpenAI | `azure/your-deployment-name` |
| AWS Bedrock | `bedrock/anthropic.claude-v2` |
| Ollama (local) | `ollama/llama3` |
| vLLM (local) | `openai/your-model` (custom base URL) |

Set the corresponding API key environment variable and reference it in `config.json` via `"api_var"`.

---

## Logging & Reproducibility

Every build run creates a timestamped log directory:

```
stage/out/<provider>/<masked_api_key>/<model>/<timestamp>/
├── messages.json   # Full prompt sent to LLM (all messages)
├── response.md     # Raw LLM response
└── files.json      # Parsed file paths and contents
```

This enables:
- **Full auditability** — every prompt and response is captured
- **Debugging** — inspect exactly what the LLM received and returned
- **Reproducibility** — re-run a build against any logged prompt
- **Comparison** — compare outputs across models and providers

Actual file system paths are masked in logs (shown as `<masked/path/to/repo>`) to avoid leaking sensitive local directory structure.

---

## Dependencies

| Package | Purpose |
|---|---|
| `litellm` | Unified API across 40+ LLM providers |
| `python-dotenv` | Load `.env` files for API keys |
| `pathspec` | gitignore-style file matching |
| `pdfplumber` | PDF text extraction (primary) |
| `pypdf` | PDF text extraction (fallback) |
| `python-pptx` | PowerPoint content extraction |
| `python-docx` | Word document content extraction |
| `openpyxl` | Excel spreadsheet content extraction |

---

## Related

**[LIPSIDE](https://github.com/qia-uofa/lipside)** — A full web-based IDE for LIPS. Provides a VS Code-inspired interface for managing workspaces, editing build files, configuring pipelines, streaming build output in real time, and running an embedded terminal — all in the browser.
