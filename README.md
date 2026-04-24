# LIPS — LLM-driven Iterative Pipeline System

LIPS is a CLI tool for building multi-stage, LLM-powered file transformation pipelines. Each stage reads a source repository, sends it to a language model with a prompt, and writes the generated output to a target repository. Stages can chain together to form fully automated code/content generation workflows.

---

## How It Works

```
workspace/
└── my-pipeline/
    ├── api-config.json       # Model, max_tokens, temperature
    ├── .env                  # API_KEY=...
    ├── stage-a/
    │   ├── config/
    │   │   └── compile.md    # Prompt + TARGET=stage-b (env block)
    │   └── repo/             # Source files for this stage
    └── stage-b/
        ├── config/
        │   └── compile.md
        └── repo/             # Output files written here
```

A **pipeline** is a folder inside the workspace. A **stage** is a subfolder of a pipeline. Each stage has:
- `repo/` — the working file tree (input or output)
- `config/<mode>.md` — a prompt file with an embedded `TARGET` env block pointing to the destination stage

When you run `build`, LIPS:
1. Reads the source stage's `repo/` and serializes it into a message
2. Reads the target stage's `repo/` (current state)
3. Sends both, plus the prompt, to the configured LLM
4. Parses the model's response into files and writes them to the target `repo/`

---

## Installation

```bash
pip install -e .
```

Requires Python 3.10+ and a [LiteLLM](https://github.com/BerriAI/litellm)-compatible API key.

---

## Quick Start

### 1. Create a pipeline interactively

```bash
python -m lips create
```

This wizard walks you through:
- Workspace and pipeline naming
- LLM provider and model selection
- Max tokens and temperature
- API key (saved to `.env`)
- Stage creation

### 2. Edit your prompt

Open `<pipeline>/<stage>/config/compile.md` and write your prompt. Add an env block at the top to declare the target stage:

````markdown
```env
TARGET=stage-b
```

You are a senior engineer. Given the files in stage-a, generate a complete test suite for stage-b.
````

### 3. Build

```bash
python -m lips build <path/to/stage>
```

Or with a custom build mode (uses `config/<mode>.md`):

```bash
python -m lips build review path/to/stage
```

### 4. Purge generated files

Clear a stage's `repo/` and `out/` directories:

```bash
python -m lips purge path/to/stage
```

Clear an entire pipeline at once:

```bash
python -m lips purge --pipeline path/to/pipeline
```

---

## CLI Reference

```
lips build [mode] <stage>  [--api-config <path>]
lips purge [--pipeline] <dir>
lips create
```

| Argument | Description |
|---|---|
| `mode` | Config file to use (`compile` by default) |
| `stage` | Path to the source stage directory |
| `--api-config` | Path to `api-config.json` (default: `./api-config.json`) |
| `--pipeline` | When purging, target the whole pipeline instead of a single stage |

---

## Supported LLM Providers

LIPS uses [LiteLLM](https://github.com/BerriAI/litellm) under the hood, so any provider it supports works. The `create` wizard includes shortcuts for:

| Provider | Example models |
|---|---|
| Mistral | `mistral-large-latest`, `mistral-small-latest` |
| OpenAI | `gpt-4o`, `gpt-4o-mini` |
| Anthropic | `claude-opus-4-5`, `claude-sonnet-4-5`, `claude-haiku-4-5` |
| Google | `gemini-2.0-flash`, `gemini-2.0-pro` |

You can also enter any model string manually.

---

## Configuration Files

### `api-config.json`

```json
{
  "model": "mistral/mistral-large-latest",
  "max_tokens": 20000,
  "temperature": 0
}
```

### `.env`

```
API_KEY=your_api_key_here
```

### `config/compile.md` (prompt file)

````markdown
```env
TARGET=stage-b
IGNORE=*.test.js
```

Your prompt here...
````

The `TARGET` key specifies which stage receives the generated output. The optional `IGNORE` key is a gitignore-style pattern to exclude files from the source message.

---

## Output Logs

Every build run saves logs to `<stage>/out/`:

| File | Contents |
|---|---|
| `messages_<timestamp>.json` | Full message list sent to the LLM |
| `response_<timestamp>.md` | Raw model response |
| `files_dict_<timestamp>.json` | Parsed file map written to target repo |

---

## Project Structure

```
lips/
├── __main__.py           # CLI entry point
├── lips.py               # Lips, Pipeline, Stage classes
├── commands/
│   └── create.py         # Interactive pipeline creator
└── utils/
    ├── message_from_files.py
    ├── parse_md.py        # env/ignore block parsing
    ├── parse_files.py     # LLM response → file dict
    └── prompts.py         # update_files_prompt builder
```

---

## License

MIT