# LIPS — LLM-driven Iterative Project Synthesizer

LIPS is a pipeline framework that uses large language models to iteratively generate, refine, and verify software projects. You define stages and build modes using plain Markdown files; LIPS handles the rest.

---

## How It Works

LIPS organizes work into **pipelines** and **stages**. Each stage has a `repo/` directory (the working files) and a `build/` directory (the prompt instructions). When you run a build, LIPS assembles a message from the source stage's repo, optionally the target stage's repo, and the prompt file, then asks an LLM to generate or update files.

```
workspace/
└── my-pipeline/
    ├── .env
    ├── api-config.json
    ├── stage-a/
    │   ├── build/
    │   │   └── compile.md        ← prompt for this build mode
    │   └── repo/
    │       └── ...               ← source files
    └── stage-b/
        ├── build/
        │   └── compile.md
        └── repo/
            └── ...               ← generated/updated files
```

---

## Getting Started

### 1. Install

```bash
pip install lips
```

Or clone and install locally:

```bash
git clone https://github.com/your-org/lips
cd lips
pip install -e .
```

### 2. Create a pipeline

Run the interactive wizard from any directory:

```bash
python3 -m lips create
```

This prompts you for a workspace root, pipeline name, LLM provider and model, API key, and the names of your stages. It writes the directory structure, an `api-config.json`, and a `.env` file.

### 3. Configure

LIPS reads two config files from your **working directory** when you invoke it — so you can keep them anywhere, as long as you `cd` there first (or pass `--api-config` to point to them explicitly).

**`.env`**
```
API_KEY=sk-...
```

**`api-config.json`**
```json
{
  "model": "mistral/mistral-large-latest",
  "max_tokens": 20000,
  "temperature": 0
}
```

Any model string supported by [LiteLLM](https://docs.litellm.ai/docs/providers) works here.

### 4. Build

```bash
python3 -m lips build <path/to/stage>
```

This runs the default `compile` mode, reading `build/compile.md` from the given stage. The `TARGET` variable in that file determines which stage receives the generated output.

---

## Build Modes

Every `.md` file you place in a stage's `build/` directory becomes a build mode. The file name (without extension) is the mode name.

```bash
python3 -m lips build my-mode path/to/stage
```

This reads `path/to/stage/build/my-mode.md` as the prompt. You can define as many modes as you like — `compile.md`, `verify.md`, `patch.md`, `refactor.md`, etc.

Inside each prompt file, a small `env` block tells LIPS where the output goes:

````markdown
```env
TARGET=stage-b
```

Your prompt instructions here...
````

---

## Example Pipeline: `python-project`

A realistic four-stage pipeline for generating, specifying, implementing, and verifying a Python project:

```
workspace/
└── python-project/
    ├── prompt/          ← seed idea, written by hand
    ├── specs/           ← LLM-generated specification
    └── target/          ← LLM-generated implementation
```

### Stage flow

```
prompt ──compile──▶ specs ──compile──▶ target
                                          │
      ┌───────────────────────────────────┘
      │
     verify mode  →  writes *.verify.md into target/repo/
      │
     redeem mode   →  reads *.verify.md, fixes files, clears *.verify.md
```

**`prompt/build/compile.md`** — instructs the LLM to read the raw idea and produce a structured specification in `specs/repo/`.

**`specs/build/compile.md`** — instructs the LLM to read the spec and produce a full implementation in `target/repo/`.

**`target/build/verify.md`** — instructs the LLM to review the current repo, check for bugs, inconsistencies, or incomplete logic, and write its findings to a `*.verify.md` file inside `target/repo/`. These files are gitignored so they don't pollute the actual output.

**`target/build/patch.md`** — instructs the LLM to read the `*.verify.md` files, fix the identified problems, overwrite the affected source files, and then overwrite each `*.verify.md` with an empty string to signal the issues are resolved.

Running a full cycle:

```bash
cd workspace/python-project
python3 -m lips build prompt
python3 -m lips build specs
python3 -m lips build target
python3 -m lips build verify target
# Optionally, skip the above step and write the `*.verify.md` file manually
python3 -m lips build redeem target
```

Repeat the `verify` / `redeem` cycle until no issues remain.

---

## CLI Reference

```
python3 -m lips build [mode] <stage-path> [--api-config <path>]
python3 -m lips purge <stage-path>
python3 -m lips purge --pipeline <pipeline-path>
python3 -m lips create
```

| Command | Description |
|---|---|
| `build [mode] <stage>` | Run a build mode against a stage. Defaults to `compile`. |
| `purge <stage>` | Delete all generated files in a stage's `repo/` (preserves `.gitignore`). |
| `purge --pipeline <dir>` | Purge all stages in a pipeline. |
| `create` | Interactive wizard to scaffold a new pipeline. |

The `--api-config` flag defaults to `api-config.json` in your current working directory. The `.env` file is also loaded from the working directory. This means you can store both files at the pipeline root and simply `cd` there before invoking LIPS — or keep a shared config elsewhere and pass the path explicitly.

---

## Supported Providers

LIPS uses [LiteLLM](https://docs.litellm.ai) under the hood, so any provider it supports works out of the box. The `lips create` wizard offers shortcuts for:

| Provider | Example model string |
|---|---|
| Mistral | `mistral/mistral-large-latest` |
| OpenAI | `openai/gpt-4o` |
| Anthropic | `anthropic/claude-opus-4-6` |
| Google | `google/gemini-2.0-flash` |

For any other provider, enter the model string manually when prompted.

---

## File Format

Generated files are returned by the LLM in a simple XML envelope:

```xml
<file path="/absolute/path/to/file.py">
# file contents here
</file>
```

LIPS parses these blocks and writes each file to disk. Your prompt files can include an `ignore` block to exclude patterns from the repo snapshot sent to the model:

````markdown
```ignore
*.verify.md
__pycache__/
```
````

---

## License

MIT