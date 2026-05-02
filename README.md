# LIPS — LLM-driven Iterative Project Synthesizer

LIPS is a minimal Python framework for building **file-system pipelines driven by large language models**. You define a sequence of stages; each stage holds a `repo/` of working files and a `build/` of prompt scripts. LIPS assembles the context, calls the LLM, parses its output, and writes the resulting files — giving you a reproducible, version-controllable, iterative LLM workflow without any web UI or heavy framework.

---

## Table of Contents

- [Philosophy](#philosophy)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Directory Layout](#directory-layout)
- [Configuration — `config.json` and `.env`](#configuration)
- [CLI Reference](#cli-reference)
- [Build Script Syntax](#build-script-syntax)
  - [env block](#env-block)
  - [sourceignore / targetignore blocks](#ignore-blocks)
  - [write links](#write-links)
  - [env: variable substitution](#env-variable-substitution)
- [Build Script Types (.md, .py, .sh)](#build-script-types)
- [The Build Conversation](#the-build-conversation)
- [LLM Output Format](#llm-output-format)
- [File Deletion](#file-deletion)
- [Supported Input File Types](#supported-input-file-types)
- [Output Logging](#output-logging)
- [Module Reference](#module-reference)
  - [lips/\_\_main\_\_.py](#lips__main__py)
  - [lips/lips.py](#lipslipspy)
  - [lips/commands/create.py](#lipscommandscreate-py)
  - [lips/utils/message\_from\_files.py](#lipsutilsmessage_from_filespy)
  - [lips/utils/parse\_scripts.py](#lipsutilsparse_scriptspy)
  - [lips/utils/resolve\_md.py](#lipsutilsresolve_mdpy)
  - [lips/utils/parse\_files.py](#lipsutilsparse_filespy)
  - [lips/utils/prompts.py](#lipsutilspromptspy)
- [Supported LLM Providers](#supported-llm-providers)

---

## Philosophy

LIPS is built on a single bet: **the file system is the right interface between a human and an LLM workflow**.

Most LLM tooling abstracts files away behind databases, APIs, or UI state. LIPS does the opposite — every artefact of every stage lives on disk as a plain file, readable and editable by any tool you already use. The pipeline is the directory tree. The prompt is a Markdown file. The output is whatever the LLM writes into `repo/`.

### Why stages?

LLMs produce better results when they work in steps. A model asked to go from "rough idea" to "working code" in one shot will hallucinate more, forget constraints, and produce messier output than one given a concept → specs → implementation chain. LIPS formalises that chain as a sequence of stages, each with its own prompt and its own working directory. You can inspect and edit every intermediate artefact before moving to the next stage.

### Why Markdown for prompts?

Markdown is the natural language of documentation, and documentation is the natural language of prompting. Build scripts in LIPS are just Markdown files. That means you can write them in any editor, render them in any viewer, diff them in git, and share them as-is. There's no special DSL to learn. The only LIPS-specific syntax is a handful of fenced code blocks (`` `env`, `sourceignore`, `targetignore` ``) and a single link macro (`[write:...]`), all of which degrade gracefully when the file is read as plain Markdown.

### The masking convention

Absolute paths are leaked to the LLM as masked placeholders (`<masked/path/to/input/repo>`). This serves two purposes: it prevents the LLM from hard-coding machine-specific paths into generated files, and it keeps the conversation portable — the same logged `messages_*.json` can be replayed on a different machine.

---

## Installation

```bash
# From source
git clone https://github.com/mandelbroetchen/lips
cd lips
pip install -e .
```

**Runtime dependencies** (from `requirements.txt`):

| Package | Purpose |
|---|---|
| `litellm` | Universal LLM API client |
| `python-dotenv` | `.env` file loading |
| `pathspec` | `.gitignore`-style ignore patterns |
| `pdfplumber` | PDF text extraction |
| `python-pptx` | PPTX text extraction |
| `python-docx` | DOCX text extraction |
| `openpyxl` | XLSX text extraction |

---

## Quick Start

```bash
# 1. Scaffold a new pipeline
lips create my-pipeline

# 2. cd into it and fill in your API key
cd my-pipeline
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# 3. Put your seed content into the first stage's repo
echo "Build me a FastAPI CRUD app for managing todos." > 1-prompt/repo/prompt.md

# 4. Build each stage in order
lips build 1-prompt
lips build 2-concept
lips build 3-specs
lips build 4-target
```

---

## Directory Layout

```
my-pipeline/                   ← pipeline root
├── config.json                ← LLM settings, message template, format prompt
├── .env                       ← API key(s)
│
├── 1-prompt/                  ← stage
│   ├── build/
│   │   └── compile.md         ← build script (prompt instructions)
│   ├── repo/                  ← working files (human-authored seed)
│   └── out/                   ← auto-created; logged runs
│       ├── messages_YYYYMMDD_HHMMSS.json
│       ├── response_YYYYMMDD_HHMMSS.md
│       └── files_dict_YYYYMMDD_HHMMSS.json
│
├── 2-concept/
│   ├── build/
│   │   └── compile.md
│   ├── repo/                  ← LLM-generated output from stage 1
│   └── out/
│
└── 3-specs/
    ├── build/
    │   └── compile.md
    ├── repo/
    └── out/
```

A pipeline can have any number of stages with any names. The stage ordering is entirely determined by the `TARGET=` variable in each build script — there is no global ordering file required. A `lips-config.json` is written by `lips create` at the workspace level to record the graph, but LIPS does not read it at runtime.

---

## Configuration

### `config.json`

Created automatically by `lips create`. Must be present in the **current working directory** when you run `lips build` (or pass `--config <path>`).

```json
{
    "generate": {
        "model": "anthropic/claude-sonnet-4-6",
        "max_tokens": 20000,
        "temperature": 0,
        "timeout": 1200
    },
    "api_var": "ANTHROPIC_API_KEY",
    "messages": [
        { "role": "user",      "content": "[write:<env:SOURCE_MASK>](<env:SOURCE_PATH>)" },
        { "role": "assistant", "content": "I see. This is the current state of the input repo. I will use it as the source material to generate or update the output repo." },
        { "role": "user",      "content": "[write:<env:TARGET_MASK>](<env:TARGET_PATH>)" },
        { "role": "assistant", "content": "I see. This is the current state of the output repo. I will use input repo as the source material to generate or update it." },
        { "role": "user",      "content": "<env:BUILD_PROMPT>" },
        { "role": "assistant", "content": "I see. This is the main instruction for generating/updating the repo of the target repo." },
        { "role": "user",      "content": "<env:FORMAT_PROMPT>" },
        { "role": "assistant", "content": "I see. This is the output format for generating/updating the repo of <target.name>." },
        { "role": "user",      "content": "Start." }
    ],
    "format": "Generate only the files that need to be created or updated..."
}
```

| Key | Type | Description |
|---|---|---|
| `generate.model` | string | LiteLLM model string, e.g. `"anthropic/claude-sonnet-4-6"` |
| `generate.max_tokens` | int | Maximum tokens in the LLM response |
| `generate.temperature` | float | Sampling temperature (0 = deterministic) |
| `generate.timeout` | int | Request timeout in seconds |
| `api_var` | string | Name of the environment variable holding the API key |
| `messages` | array | Conversation template. Supports `[write:...]` links and `<env:KEY>` substitution. Resolved at build time. |
| `format` | string | The output format instructions injected as `<env:FORMAT_PROMPT>` |

All keys inside `generate` are passed **verbatim** as kwargs to `litellm.completion()`, so any parameter LiteLLM supports (e.g. `top_p`, `stop`) can be added here.

### `.env`

A standard dotenv file loaded from the current working directory. Contains the API key referenced by `api_var`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

---

## CLI Reference

```
lips build [script] <stage-path> [--config <path>]
lips purge <stage-path>
lips purge --pipeline <pipeline-path>
lips create <pipeline-path>
```

### `lips build [script] <stage-path>`

Runs a build script against a stage.

| Argument | Default | Description |
|---|---|---|
| `script` | `compile` | Name of the build script (without extension). Resolved against `<stage>/build/` with suffix autodetection. |
| `stage-path` | *(required)* | Path to the source stage directory. |
| `--config`, `-a` | `config.json` | Path to the config file. Resolved from the current working directory. |

**Script resolution**: LIPS first checks if `<stage>/build/<script>` exists as-is (i.e. with extension). If not, it tries appending `.md`, `.py`, `.sh`, and `.bat` in that order and uses the first match. If nothing matches, a `FileNotFoundError` is raised.

**Stage resolution**: LIPS constructs a `Lips` workspace from `<stage>/../../`, discovering all pipelines and stages in that subtree. It then matches `stage.root == resolved(stage-path)` to find the correct `Stage` object. This means the stage path must be valid within a proper two-level `workspace/pipeline/stage` hierarchy.

### `lips purge <stage-path>`

Deletes all generated files in `<stage>/repo/`, preserving any `.gitignore` file. Also deletes the entire `out/` directory.

### `lips purge --pipeline <pipeline-path>`

Calls `purge()` on every stage in the pipeline.

### `lips create <pipeline-path>`

Interactive wizard to scaffold a new pipeline. If the pipeline directory does not exist, it is created along with `config.json` and `.env`. If it already exists, the config/API-key steps are skipped and only new stages are added.

---

## Build Script Syntax

Build scripts are files inside a stage's `build/` directory. `.md` scripts are the primary type and support the full LIPS template syntax described below.

### env block

````markdown
```env
TARGET=2-concept
```
````

A fenced code block with the language tag `env`. Defines key-value pairs that control the build. The block is stripped from the prompt text before it is sent to the LLM.

| Variable | Description |
|---|---|
| `TARGET` | Name of the stage that receives the LLM's output. Must be a sibling stage within the same pipeline. If no `env` block is present, `TARGET` defaults to the current stage's own name (i.e. the stage writes back to itself). |

Additional keys can be defined and referenced via `<env:KEY>` substitution anywhere in the prompt.

### ignore blocks

````markdown
```sourceignore
*.verify.md
__pycache__/
*.pyc
```

```targetignore
node_modules/
dist/
```
````

Controls which files from each repo are included in the LLM's context. Uses `.gitignore`-style glob patterns via `pathspec`.

| Block | Applies to |
|---|---|
| `` `sourceignore` `` | Files from the **source** stage's `repo/` |
| `` `targetignore` `` | Files from the **target** stage's `repo/` |

**Default ignores** (applied when no block is present):

```
__pycache__
.git
*.verify.md
```

Both blocks are stripped from the prompt before it is sent to the LLM.

### write links

```markdown
[write:./leitfaden.pdf](./assets/Leitfaden.pdf)
[write:./reference-docs](./assets/docs/)
```

A Markdown link with the label prefix `write:`. Resolved at build time by `resolve_links()`.

- The **label** (`write:<virtual-path>`) is the path shown to the LLM inside the `<file>` tag.
- The **target** (`(real-path)`) is resolved relative to the stage's `build/` directory.
- If the target is a **file**, it is inlined as a single `<file path="<virtual-path>">...</file>` block.
- If the target is a **directory**, every file inside it is recursively inlined, with paths composed as `<virtual-path>/<relative-path-inside-dir>`.
- PDF files are text-extracted (not base64-encoded) before inlining, using `pdfplumber`.

This is the primary mechanism for injecting reference material (style guides, schemas, example files, PDFs) directly into the build prompt.

### env: variable substitution

```markdown
Your task is to transform <env:SOURCE> into <env:TARGET>.
See the source at <env:SOURCE_PATH>.
```

`<env:KEY>` tokens are replaced with the corresponding value from the resolved environment at build time. This substitution is applied to **both the build script text and every message in the `messages` array**.

**Built-in variables available in the `messages` template:**

| Variable | Value |
|---|---|
| `SOURCE` | Name of the current (source) stage |
| `SOURCE_PATH` | Absolute path to the source stage's `repo/` |
| `SOURCE_MASK` | The string `<masked/path/to/input/repo>` |
| `TARGET_PATH` | Absolute path to the target stage's `repo/` |
| `TARGET_MASK` | The string `<masked/path/to/output/repo>` |
| `BUILD_PROMPT` | The fully resolved build script text (after env/ignore stripping and link resolution) |
| `FORMAT_PROMPT` | The `format` string from `config.json` |

Any additional keys defined in the `env` block of the build script are also available as `<env:KEY>`.

---

## Build Script Types

### `.md` — Markdown prompt scripts

The primary type. Full LIPS template syntax applies. The resolved text is injected as `<env:BUILD_PROMPT>` and passed to the LLM via the `messages` conversation template.

### `.py` — Python scripts

Executed directly with `python -` (stdin), with the current working directory set to the stage's `repo/`. Used for deterministic data transformations, compilation steps, or any processing that doesn't require LLM inference. No LIPS template syntax is processed. The `TARGET` concept does not apply.

Example use: extracting measurement data from CSVs into a Python module before the LLM stage that reads it.

### `.sh` — Shell scripts

Executed with `bash -s` (stdin), with cwd set to the stage's `repo/`. Same semantics as `.py` scripts — deterministic, no LLM, no template syntax.

---

## The Build Conversation

When `lips build` runs a `.md` script, it constructs a conversation by resolving the `messages` array from `config.json`. Each message's `content` field is treated as a template:

1. `[write:...]` links are expanded into `<file>` blocks (for file/directory injection).
2. `<env:KEY>` tokens are substituted.

The result is a standard `messages` array passed to `litellm.completion()` with the settings in `generate`.

The default conversation shape produced by `lips create` is:

```
user      → contents of source repo (all files as <file> blocks)
assistant → "I see. This is the current state of the input repo..."
user      → contents of target repo (all files as <file> blocks)
assistant → "I see. This is the current state of the output repo..."
user      → build prompt text
assistant → "I see. This is the main instruction..."
user      → format prompt
assistant → "I see. This is the output format..."
user      → "Start."
```

The interleaved assistant acknowledgements serve as a **conversation priming** technique: by having the assistant "confirm understanding" of each input block, the model is less likely to confuse the source and target repos or misinterpret the format instructions. This is a deliberate prompt engineering choice baked into the default template.

The `messages` array in `config.json` is fully customisable — you can add, remove, or reorder turns to suit your use case.

---

## LLM Output Format

The LLM is instructed to return files using a simple XML envelope:

```xml
<file path="./path/to/file.py">
# complete file contents here
</file>
```

Rules enforced by the format prompt:

- Paths are relative, beginning with `./`, which maps to the target stage's `repo/`.
- Every `<file>` tag must contain the **complete** file contents — no partial files, no ellipsis placeholders.
- Only new or modified files should be included.
- For image files that need to be generated, the LLM is instructed to produce a `<name>.prompt.md` file instead, containing a detailed image generation prompt for a downstream tool.
- If the existing output already meets the specification, the LLM should produce no `<file>` tags.

After the LLM responds, LIPS:

1. Extracts all `<file path="...">...</file>` blocks using `parse_files()`.
2. Resolves each `path` relative to `target.root / 'repo'`.
3. Creates any missing parent directories.
4. Writes each file.
5. Deletes any written files that have **zero bytes** (see below).

---

## File Deletion

To instruct the LLM to delete a file, it writes a strictly empty tag:

```xml
<file path="./obsolete-file.py"></file>
```

LIPS writes this as a zero-byte file, then immediately deletes it in a post-pass that removes all empty files from the target repo. This convention lets the LLM express deletions in the same format as writes, with no special syntax.

---

## Supported Input File Types

`message_from_files()` classifies each file in a repo by MIME type and converts it to the appropriate LLM content block:

| Category | MIME types | LLM representation |
|---|---|---|
| **Text** | Any unrecognised type (source code, `.md`, `.json`, `.csv`, etc.) | `{"type": "text", "text": "<file path=\"...\">...</file>"}` |
| **PDF** | `application/pdf` | Text-extracted via `pdfplumber`; wrapped as `<document path="...">...</document>` |
| **DOCX** | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | Text-extracted (paragraphs + tables); wrapped as `<document>` |
| **XLSX** | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | Text-extracted (all sheets, tab-separated rows); wrapped as `<document>` |
| **PPTX** | `application/vnd.openxmlformats-officedocument.presentationml.presentation` | Text-extracted (all slides, shapes, notes); wrapped as `<document>` |
| **Images** | JPEG, PNG, GIF, WebP, BMP, TIFF, SVG, HEIC, HEIF, AVIF | Base64-encoded as `{"type": "image_url", "image_url": {"url": "data:...;base64,..."}}` wrapped in `<image path="...">` text delimiters |
| **Audio** | MP3, WAV | Base64-encoded as `{"type": "input_audio", "input_audio": {"data": "...", "format": "mp3"/"wav"}}` |

**Document extraction details:**

- `_extract_pdf_text`: page-by-page extraction with `--- Page N ---` separators.
- `_extract_docx_text`: extracts paragraphs and table rows (tab-separated cells).
- `_extract_xlsx_text`: opens in read-only/data-only mode; extracts all sheets with `--- Sheet: <name> ---` headers, skipping all-empty rows.
- `_extract_pptx_text`: extracts per-slide with `--- Slide N ---` headers; includes text frames, tables, and speaker notes.

The `mask` parameter in `content_block_from_file()` allows the real filesystem path to be replaced with a virtual path in the `path` attribute shown to the LLM, implementing the masking convention described above.

---

## Output Logging

Every `.md` build run logs three files to `<source-stage>/out/`, timestamped as `YYYYMMDD_HHMMSS`:

| File | Contents |
|---|---|
| `messages_<timestamp>.json` | The fully resolved `messages` array sent to the LLM (JSON) |
| `response_<timestamp>.md` | The raw text response from the LLM |
| `files_dict_<timestamp>.json` | The parsed `{path: content}` dict extracted from the response |

These logs serve as a complete audit trail. Because `messages_*.json` contains the entire conversation including all file contents, any run can be fully reproduced or inspected without access to the original repo state at that point in time.

---

## Module Reference

### `lips/__main__.py`

The CLI entry point. Registered as the `lips` console script in `pyproject.toml`.

**`parse_args()`** — Builds an `argparse` parser with three subcommands: `build`, `purge`, `create`. Returns the parsed namespace.

**`main()`** — Loads `./.env` via `python-dotenv`, dispatches to the appropriate handler:

- **`build`**: Loads `config.json`, reads the API key from the environment, resolves the stage path, constructs a `Lips` workspace from `<stage>/../../`, finds the matching `Stage` object by comparing resolved paths, auto-detects the script suffix, and calls `stage.build(script, messages, format_prompt, api_key, generate_config)`.
- **`purge`**: Constructs a `Lips` workspace (one level up for `--pipeline`, two levels for stage), finds the matching pipeline or stage, and calls `.purge()`.
- **`create`**: Delegates to `lips.commands.create.create(pipeline_path)`.

**Key design note**: The `Lips` workspace is always reconstructed from the filesystem at runtime. There is no cached or serialised state. The path-matching logic (`stage.root.resolve() == path`) is the only mechanism that ties a CLI argument to an internal object.

---

### `lips/lips.py`

The core domain model. Three classes: `Lips`, `Pipeline`, `Stage`.

#### `class Lips`

```python
Lips(workspace: str | Path)
```

Constructs a workspace by scanning `workspace/` for directories, instantiating one `Pipeline` per directory. Stores them in `self.pipelines: dict[str, Pipeline]`.

#### `class Pipeline`

```python
Pipeline(root: Path)
```

Constructs a pipeline by scanning `root/` for directories, instantiating one `Stage` per directory. Stores them in `self.stages: dict[str, Stage]`.

**`purge()`** — Calls `stage.purge()` on every stage.

#### `class Stage`

```python
Stage(name: str, pipeline: Pipeline)
```

Represents a single stage. `self.root = pipeline.root / name`.

**`repo_message(ignore='', mask='')`** — Collects all files from `repo/` that don't match the `ignore` pattern, then calls `message_from_files()` to produce a single `{"role": "user", "content": [...]}` message. The `mask` string replaces the real repo path in all `path` attributes shown to the LLM.

**`purge()`** — Deletes every file and subdirectory in `repo/` except `.gitignore`. Deletes the entire `out/` directory.

**`build(script, messages, format_prompt, api_key, generate_config)`** — Reads the build script from `build/<script>`, dispatches to `build_md`, `build_py`, or `build_sh` based on suffix.

**`build_py(code)`** — Runs `code` via `python -` with cwd set to `repo/`.

**`build_sh(code)`** — Runs `code` via `bash -s` with cwd set to `repo/`.

**`resolve(text, root, base_env={})`** — Applies the full template pipeline to a text string:
1. `env_from_script(text, stage)` — strips the `env` block, returns `(text, env_dict)`.
2. `ignore_from_script(text)` — strips `sourceignore`/`targetignore` blocks, returns `(text, source_ignore, target_ignore)`.
3. `resolve_env(text, env)` — substitutes `<env:KEY>` tokens from `env_dict`.
4. `resolve_env(text, base_env)` — substitutes from the caller-provided base environment.
5. `resolve_links(text, root)` — expands `[write:...]` links.

**`build_md(md_text, messages, format_prompt, api_key, generate_config)`** — The main LLM build path:
1. Calls `resolve()` on the script text with `base_env = {'SOURCE': self.name}` to get `build_prompt`, `env`, `source_ignore`, `target_ignore`.
2. Resolves `target = self.pipeline.stages[env['TARGET']]`.
3. Iterates over every message in `messages`, calling `resolve()` on each `content` with a base env that injects `BUILD_PROMPT`, `FORMAT_PROMPT`, `SOURCE_MASK`, `TARGET_MASK`, `SOURCE_PATH`, `TARGET_PATH`.
4. Logs the resolved messages to `out/`.
5. Calls `litellm.completion(**generate_config, messages=messages, api_key=api_key, stream=False)`.
6. Logs the raw response text to `out/`.
7. Calls `parse_files()` on the response.
8. Logs the parsed `files_dict` to `out/`.
9. Writes each file to `target.root / 'repo' / path`, creating parent dirs as needed.
10. Deletes zero-byte files.

**`log_json(name, content)`** / **`log_text(name, ext, content)`** — Write timestamped files to `out/`.

---

### `lips/commands/create.py`

The interactive pipeline creation wizard. Entirely self-contained; no dependency on `lips.py`.

**`create(pipeline_path: str)`** — Top-level entry point. Four logical steps:

1. **Config & model** (skipped if pipeline already exists): calls `select_model()`, prompts for `max_tokens` and `temperature`, derives `api_var` from the model string prefix (e.g. `"anthropic/..."` → `"ANTHROPIC_API_KEY"`), writes `config.json` with the full `MESSAGES_BLOCK` and `FORMAT_BLOCK`.
2. **API key** (skipped if `.env` exists): writes `<api_var>=<key>` to `.env`.
3. **Stage collection**: calls `collect_stages()`, which loops prompting for stage names and build file names, with conflict detection against both existing disk files and the in-memory queue.
4. **Materialisation**: calls `materialise_stages()`, which creates directories and writes build files, then calls `touch_lips_config()`.

**`collect_stages(lips_root)`** — Accumulates a list of `StageSpec(name, build_file, is_final)` dataclasses. Special input `"/"` marks a stage as final (uses `identity.md` as the build file name). If the last stage added is not marked final, its build file is renamed from `compile.md` to `identity.md` automatically, signalling that it is the terminal stage.

**`_ask_build_file(lips_root, stage_name, queue)`** — Validates the chosen build file stem against both files already on disk and stems already queued for the same stage name, preventing collisions.

**`materialise_stages(lips_root, specs)`** — For each `StageSpec`, creates `build/` and `repo/` directories (if the stage is new) and writes the build file. New intermediate stages get an `env` block pointing to the next stage plus a one-liner transform prompt. The final stage gets a self-update prompt with no `env` block (so `TARGET` defaults to itself).

**`touch_lips_config(lips_root, specs)`** — Writes or merges a `lips-config.json` at the workspace level, recording the pipeline graph as `{ pipelines: { <name>: { graph: { <stage>: { <buildfile>: <next_stage> } } } } }`. This is a documentation/tooling aid; LIPS does not read it at runtime.

**`select_model()`** — Displays a numbered provider/model menu. Supports manual entry (`0`). Hard-coded provider catalogue:

| # | Provider | Models |
|---|---|---|
| 1 | Mistral | `mistral-large-latest`, `mistral-medium-latest`, `mistral-small-latest` |
| 2 | OpenAI | `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo` |
| 3 | Anthropic | `claude-opus-4-5`, `claude-sonnet-4-5`, `claude-haiku-4-5` |
| 4 | Google | `gemini-2.0-flash`, `gemini-2.0-pro` |

---

### `lips/utils/message_from_files.py`

Converts a list of file paths into a single LLM user message with a multi-part content array.

**`content_block_from_file(file, repo_path, mask='')`**

Classifies `file` by MIME type using `mimetypes.guess_type()`, looks it up in `TYPE_MAP`, and returns one or more content blocks:

- **`text`** (default): reads the file as UTF-8 (replacing errors), returns `{"type": "text", "text": "<file path=\"...\">...</file>"}`.
- **`document`**: calls the matching extractor from `DOCUMENT_EXTRACTORS`, returns `{"type": "text", "text": "<document path=\"...\">...</document>"}`.
- **`image`**: base64-encodes the file, returns a **list** of three blocks: a text opener `<image path="...">`, an `image_url` block, and a text closer `</image>`. Returns a list rather than a dict because the image requires three content blocks, not one.
- **`audio`**: base64-encodes the file, returns `{"type": "input_audio", "input_audio": {"data": ..., "format": ...}}`.

The `display_path` shown to the LLM is computed as `Path(mask) / file.relative_to(repo_path)` when `mask` is set, or just `relative` otherwise.

**`message_from_files(files, repo_path, mask='')`**

Iterates over `files`, calls `content_block_from_file` for each, flattens list results (from image blocks), and returns `{"role": "user", "content": [block, ...]}`.

**Document extractors:**

- `_extract_pdf_text`: `pdfplumber.open()`, joins pages with `--- Page N ---` separators.
- `_extract_docx_text`: `python-docx` `Document`, iterates paragraphs and tables.
- `_extract_xlsx_text`: `openpyxl` `load_workbook(data_only=True, read_only=True)`, iterates all worksheets and rows, skips fully-empty rows.
- `_extract_pptx_text`: `python-pptx` `Presentation`, iterates slides, shapes (text frames + tables), and notes slides.

---

### `lips/utils/parse_scripts.py`

Parses directive blocks out of Markdown build scripts.

**`default_ignore`** — Module-level constant:

```
__pycache__
.git
*.verify.md
```

Applied when no `sourceignore` or `targetignore` block is present.

**`env_from_script(md_text, stage, quot='```')`**

Finds all `` `env\n...\n` `` fenced blocks using the regex `` r"`env\n(.*?)`" `` with `re.DOTALL`. Parses each block as `KEY=VALUE` lines (ignoring comments and lines without `=`). Strips all `env` blocks from the text. Returns `(cleaned_text, env_dict)`. If no `env` block is found, returns `{"TARGET": stage.name}` as the default (the stage targets itself).

**`repo_ignore_from_script(md_text, which, quot='```')`**

Finds `` `{which}ignore\n...\n` `` blocks (i.e. `` `sourceignore` `` or `` `targetignore` ``). Collects all lines into a list. Strips the blocks from the text. Returns `(cleaned_text, ignore_string)`. Falls back to `default_ignore` if no block is found.

**`ignore_from_script(md_text, quot='```')`**

Calls `repo_ignore_from_script` twice — once for `source`, once for `target` — and returns `(text, source_ignore, target_ignore)`.

---

### `lips/utils/resolve_md.py`

Resolves `[write:...]` links and `<env:KEY>` substitutions in Markdown text.

**`LINK_RE`** — Compiled regex: `r'\[write:([^\]]+)\]\(([^)]+)\)'`. Captures the virtual path (label after `write:`) and the real path (link target).

**`_read_text(real_path)`** — Reads a file as text. For `.pdf` files, uses `pdfplumber` (falling back to `pypdf` if not installed). For all other files, reads as UTF-8.

**`_file_block(virtual_path, real_path)`** — Returns a `<file path="...">...</file>` string with the file's text content.

**`_dir_block(virtual_root, real_root)`** — Recursively collects all files under `real_root`, calls `_file_block` for each with a path composed as `<virtual_root>/<relative_path>`, and joins all blocks with newlines.

**`resolve_links(md_text, root)`** — Applies `LINK_RE.sub(replace, md_text)` where `replace()` resolves the real path relative to `root`, dispatches to `_file_block` or `_dir_block`, and returns the expanded string. If the path doesn't exist on disk, the original match is left unchanged.

**`resolve_env(md_text, env)`** — Iterates over `env.items()`, substituting each `<env:KEY>` occurrence with its value using `re.sub`. The lambda wrapper around `str(val)` prevents regex backreference interpretation in the replacement string.

---

### `lips/utils/parse_files.py`

**`parse_files(text)`**

Extracts `<file path="...">...</file>` blocks from an LLM response string using:

```python
pattern = r'<file path="([^"]+)">(.*?)</file>'
re.findall(pattern, text, re.DOTALL)
```

Returns `dict[str, str]` mapping path → content (stripped of leading/trailing whitespace). Zero-byte files (where the LLM wrote an empty tag) are included in the dict with an empty string value; they are deleted by the post-pass in `build_md`.

---

### `lips/utils/prompts.py`

Contains a single module-level constant:

**`output_format_prompt`** — The default format instructions injected as `<env:FORMAT_PROMPT>`. Key rules it communicates to the LLM:

- Use `<file path="./...">` with relative paths starting from `./`.
- Include only new or modified files (not unchanged ones).
- Every file tag must have complete contents — no placeholders.
- Delete a file by writing an empty tag.
- For images that need to be created, write a `<name>.prompt.md` instead.
- If the output already meets the standard, generate nothing.
- Analyse and reason before generating.

This constant is used by `lips/commands/create.py` as the `FORMAT_BLOCK` embedded into newly created `config.json` files, and also remains available for programmatic use.

---

## Supported LLM Providers

LIPS calls `litellm.completion()` directly, so any provider supported by [LiteLLM](https://docs.litellm.ai/docs/providers) works. The `model` string follows LiteLLM's `provider/model-name` convention.

| Provider | Example model string |
|---|---|
| Anthropic | `anthropic/claude-sonnet-4-6` |
| OpenAI | `openai/gpt-4o` |
| Mistral | `mistral/mistral-large-latest` |
| Google | `google/gemini-2.0-flash` |
| Ollama (local) | `ollama/llama3` |
| Any other | Any valid LiteLLM model string |

The API key is read from the environment variable named by `api_var` in `config.json` and passed explicitly to `litellm.completion()` as the `api_key` parameter.

---

## License

MIT
