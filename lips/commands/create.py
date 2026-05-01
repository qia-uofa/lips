from pathlib import Path
import json
import sys
from dataclasses import dataclass

# ── ANSI styling ──────────────────────────────────────────────────────────────

RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
GREEN   = "\033[32m"
CYAN    = "\033[36m"
YELLOW  = "\033[33m"
RED     = "\033[31m"
MAGENTA = "\033[35m"
WHITE   = "\033[97m"


def ok(msg: str):   print(f"  {GREEN}✔{RESET}  {msg}")
def info(msg: str): print(f"  {CYAN}ℹ{RESET}  {msg}")
def warn(msg: str): print(f"  {YELLOW}⚠{RESET}  {msg}")
def err(msg: str):  print(f"  {RED}✘{RESET}  {msg}")


def step(n: int, total: int, title: str):
    bar = f"{CYAN}{'█' * n}{'░' * (total - n)}{RESET}"
    print(f"\n  {bar}  {BOLD}{WHITE}{title}{RESET}")
    print(f"  {DIM}{'─' * 52}{RESET}")


def section(title: str):
    print(f"\n  {BOLD}{MAGENTA}▸ {title}{RESET}")
    print(f"  {DIM}{'─' * 48}{RESET}")


def banner():
    print()
    print(f"  {BOLD}{CYAN}┌─────────────────────────────────────────────┐{RESET}")
    print(f"  {BOLD}{CYAN}│{RESET}   {BOLD}{WHITE}LIPS  Pipeline  Creator{RESET}                   {BOLD}{CYAN}│{RESET}")
    print(f"  {BOLD}{CYAN}└─────────────────────────────────────────────┘{RESET}")
    print()


def _input(label: str) -> str:
    try:
        return input(label).strip()
    except (EOFError, KeyboardInterrupt):
        print(f"\n\n  {YELLOW}Interrupted.{RESET}\n")
        sys.exit(0)


def prompt(msg: str, default: str | None = None) -> str:
    hint = f" {DIM}[{default}]{RESET}" if default is not None else ""
    while True:
        value = _input(f"  {CYAN}?{RESET} {msg}{hint}: ")
        if value:
            return value
        if default is not None:
            return default
        err("This field is required.")


# ── LLM provider / model catalogue ───────────────────────────────────────────

PROVIDERS = {
    "1": {
        "name": "Mistral",
        "models": {
            "1": "mistral/mistral-large-latest",
            "2": "mistral/mistral-medium-latest",
            "3": "mistral/mistral-small-latest",
        },
    },
    "2": {
        "name": "OpenAI",
        "models": {
            "1": "openai/gpt-4o",
            "2": "openai/gpt-4o-mini",
            "3": "openai/gpt-4-turbo",
        },
    },
    "3": {
        "name": "Anthropic",
        "models": {
            "1": "anthropic/claude-opus-4-5",
            "2": "anthropic/claude-sonnet-4-5",
            "3": "anthropic/claude-haiku-4-5",
        },
    },
    "4": {
        "name": "Google",
        "models": {
            "1": "google/gemini-2.0-flash",
            "2": "google/gemini-2.0-pro",
        },
    },
}

DEFAULT_API_CONFIG = {
    "model": "mistral/mistral-large-latest",
    "max_tokens": 20000,
    "temperature": 0,
}

MESSAGES_BLOCK = [
    {"role": "user",      "content": "[write:<env:SOURCE_MASK>](<env:SOURCE_PATH>)"},
    {"role": "assistant", "content": "I see. This is the current state of the input repo. I will use it as the source material to generate or update the output repo."},
    {"role": "user",      "content": "[write:<env:TARGET_MASK>](<env:TARGET_PATH>)"},
    {"role": "assistant", "content": "I see. This is the current state of the output repo. I will use input repo as the source material to generate or update it."},
    {"role": "user",      "content": "<env:BUILD_PROMPT>"},
    {"role": "assistant", "content": "I see. This is the main instruction for generating/updating the repo of the target repo."},
    {"role": "user",      "content": "<env:FORMAT_PROMPT>"},
    {"role": "assistant", "content": "I see. This is the output format for generating/updating the repo of <target.name>."},
    {"role": "user",      "content": "Start."},
]

FORMAT_BLOCK = (
    "Generate only the files that need to be created or updated. "
    "Use the following XML format with absolute paths:\n\n"
    "<file path=\"./file-1.txt\">\nfile content here\n...\n</file>\n\n"
    "<file path=\"./file-2.json\">\n{\n    \"key1\": \"value1\",\n    \"key2\": \"value2\"\n}\n</file>\n\n"
    "Rules:\n"
    "- Start by analyzing and breaking down the problem before doing anything else.\n"
    "- Before generating each file, write down your reasoning through the logic and its impact on the overall repository structure.\n"
    "- Every file tag must contain the complete file contents — no partial files, no placeholders.\n"
    "- Use relative paths for all files, beginning with \"./\", which is the \"<masked-path-to-output-repo>\". \n"
    "- Only include files that are new or modified.\n"
    "- If an image file needs to be generated, generate a prompt file with the extension \".prompt.md\". "
    "For example, if 'icon.png' needs to be generated, instead, generate 'icon.png.prompt.md', "
    "which includes a elaborate prompt for further generation of the image. \n"
    "- Respect my last prompt message, only generate or update files specofied by it. \n"
    "- The output files might be partially generated already. In that case, only generate the missing files. \n"
    "- If the output files already meet the generation standard, opt out and don't generate anything. \n\n"
    "- You can delete a file by overwriting an STRICTLY empty (no spaces, no endlines) file to it:\n"
    "<file path=\"./deleted-file.ext\"></file>\n\n"
    "- When overwriting, remember to mirror the exact path of the ovverwriten file, but replace the masked path with \"./\". "
    "For example, overwrite <file path=\"<masked-path-to-output-repo>/to-be-overwritten-file.ext\">...</file> "
    "with <file path=\"./to-be-overwritten-file.ext\">...</file>"
)

BUILD_PROMPT_TRANSFORM = (
    "Your task is to transform the repository <env:SOURCE> to <env:TARGET> by generating files. "
)
BUILD_PROMPT_FINAL = (
    "Your task is to update the repository <env:SOURCE> by generating files needed to be updated. "
)

DEFAULT_BUILD_FILE       = "compile.md"
DEFAULT_BUILD_FILE_LAST  = "identity.md"


# ── model selection ───────────────────────────────────────────────────────────

def select_model() -> str:
    print()
    print(f"  {BOLD}Available providers:{RESET}")
    for key, prov in PROVIDERS.items():
        print(f"    {CYAN}{key}{RESET}.  {prov['name']}")
    print(f"    {DIM}0.  Enter model string manually{RESET}")

    prov_choice = _input(f"\n  {CYAN}?{RESET} Select provider: ")
    if prov_choice == "0":
        return _input(f"  {CYAN}?{RESET} Model string: ")

    provider = PROVIDERS.get(prov_choice)
    if not provider:
        warn("Invalid choice — using default model.")
        return DEFAULT_API_CONFIG["model"]

    print(f"\n  {BOLD}{provider['name']} models:{RESET}")
    for key, model in provider["models"].items():
        print(f"    {CYAN}{key}{RESET}.  {DIM}{model}{RESET}")

    model_choice = _input(f"\n  {CYAN}?{RESET} Select model: ")
    model = provider["models"].get(model_choice)
    if not model:
        warn("Invalid choice — using first model.")
        model = next(iter(provider["models"].values()))
    ok(f"Selected: {BOLD}{model}{RESET}")
    return model


# ── stage data ────────────────────────────────────────────────────────────────

@dataclass
class StageSpec:
    name: str
    build_file: str   # e.g. "compile.md" or "build.sh"
    is_final: bool = False


# ── helpers ───────────────────────────────────────────────────────────────────

def _stem_exists_on_disk(lips_root: Path, stage_name: str, stem: str) -> bool:
    """True if any file in <stage>/build/ already has the given stem."""
    build_dir = lips_root / stage_name / "build"
    if not build_dir.exists():
        return False
    return any(f.stem == stem for f in build_dir.iterdir() if f.is_file())


# ── collect stage specs (NO disk writes) ─────────────────────────────────────

def collect_stages(lips_root: Path) -> list[StageSpec]:
    """
    Prompt stage name then build file alternately.
    '/' as build file marks the stage as final and ends collection.
    Nothing is written to disk here.
    """
    section("Stage collection")
    info(f"Enter stage names one by one.  Leave name blank to finish.  Enter {BOLD}/{RESET} as build file to mark a stage as final.")

    specs: list[StageSpec] = []

    while True:
        print()
        stage_name = _input(f"  {CYAN}+{RESET} Stage name {DIM}(blank = done){RESET}: ")
        if not stage_name:
            break

        build_file, is_final = _ask_build_file(lips_root, stage_name, queue=specs)
        if build_file is None:
            warn(f"Skipping stage '{stage_name}' — resolve the conflict and re-run.")
            continue

        specs.append(StageSpec(name=stage_name, build_file=build_file, is_final=is_final))
        ok(f"Queued  {BOLD}{stage_name}{RESET}  →  build/{build_file}" + (f"  {YELLOW}[final]{RESET}" if is_final else ""))

        if is_final:
            break

    # If the last stage was added normally (not via '/'), swap compile.md → identity.md
    if specs and not specs[-1].is_final and specs[-1].build_file == DEFAULT_BUILD_FILE:
        old = specs[-1].build_file
        specs[-1] = StageSpec(name=specs[-1].name, build_file=DEFAULT_BUILD_FILE_LAST, is_final=False)
        info(f"Last stage build file changed from '{old}' to '{DEFAULT_BUILD_FILE_LAST}'")

    return specs


def _ask_build_file(
    lips_root: Path,
    stage_name: str,
    queue: list[StageSpec],
) -> tuple[str | None, bool]:
    """
    Ask for a build file name.  Returns (filename, is_final).

    - Default is "compile.md".
    - '/' → use DEFAULT_BUILD_FILE_LAST ("identity.md") and mark as final.
    - Conflict check covers both files on disk AND stems already in the queue
      for the same stage name.
    - If user accepts default and default stem is already taken → return (None, False).
    """
    default      = DEFAULT_BUILD_FILE
    default_stem = Path(default).stem

    # Stems already queued for this stage name
    queued_stems = {Path(s.build_file).stem for s in queue if s.name == stage_name}

    while True:
        raw = _input(f"  {DIM}↵{RESET} Build file {DIM}[{default}]  / = final{RESET}: ")

        # '/' → final stage with identity.md default
        if raw == "/":
            final_file = DEFAULT_BUILD_FILE_LAST
            final_stem = Path(final_file).stem
            if final_stem in queued_stems or _stem_exists_on_disk(lips_root, stage_name, final_stem):
                warn(
                    f"Stem '{final_stem}' already exists for stage '{stage_name}'.  "
                    f"Enter a custom build file name instead of '/'."
                )
                continue
            return final_file, True

        if not raw:
            # Accepted default
            if default_stem in queued_stems or _stem_exists_on_disk(lips_root, stage_name, default_stem):
                warn(
                    f"Build file stem '{default_stem}' already exists for stage '{stage_name}'.  "
                    f"Please use a different stage name or enter a custom build file."
                )
                return None, False
            return default, False

        # Custom name — check stem against queue and disk
        chosen_stem = Path(raw).stem
        if chosen_stem in queued_stems or _stem_exists_on_disk(lips_root, stage_name, chosen_stem):
            warn(
                f"Build file stem '{chosen_stem}' already exists for stage '{stage_name}'.  "
                f"Enter a different build file name."
            )
            continue

        return raw, False


# ── build file content ────────────────────────────────────────────────────────

def _build_file_content(build_file: str, next_stage: str | None) -> str:
    """
    Return content for the build file.
    Only .md files receive the env block + one-liner prompt.
    All other extensions are created empty.
    """
    if Path(build_file).suffix.lower() != ".md":
        return ""

    if next_stage is not None:
        # Intermediate stage: env block at head + transform prompt
        env_block = f"```env\nTARGET={next_stage}\n```"
        return f"{env_block}\n{BUILD_PROMPT_TRANSFORM}\n"
    else:
        # Final stage: no env block, update prompt only
        return f"{BUILD_PROMPT_FINAL}\n"


# ── workspace lips-config.json ───────────────────────────────────────────────

def touch_lips_config(lips_root: Path, specs: list[StageSpec]):
    """
    Create or update <workspace>/lips-config.json with the pipeline graph.
    Graph shape:
      { "pipelines": { "<pipeline>": { "graph": { "<stage>": { "<buildfile>": "<next_stage|null>" } } } } }
    Merges into any existing content; never clobbers unrelated keys.
    """
    workspace = lips_root.parent
    config_path = workspace / "lips-config.json"

    # Load existing or start fresh
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            warn("lips-config.json is malformed — overwriting.")
            data = {}
    else:
        data = {}

    # Build graph for this pipeline
    graph = {}
    for i, spec in enumerate(specs):
        is_final = spec.is_final or (i == len(specs) - 1)
        next_stage = specs[i + 1].name if not is_final and i + 1 < len(specs) else spec.name
        graph[spec.name] = {spec.build_file: next_stage}

    # Merge
    pipelines = data.setdefault("pipelines", {})
    pipeline_name = lips_root.name
    pipelines.setdefault(pipeline_name, {})["graph"] = graph

    config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    ok(f"Updated  {BOLD}{config_path}{RESET}")


# ── materialise all stages at once ───────────────────────────────────────────

def materialise_stages(lips_root: Path, specs: list[StageSpec]):
    """
    Given the collected specs, create directories and files on disk.

    - If a stage directory does NOT exist: create full scaffold + build file.
    - If a stage directory DOES exist: only create the build file (build/ subdir
      is created if missing).
    """
    if not specs:
        return

    section("Creating pipeline structure")

    for i, spec in enumerate(specs):
        is_final = spec.is_final or (i == len(specs) - 1)
        next_stage = specs[i + 1].name if not is_final and i + 1 < len(specs) else None

        stage_dir = lips_root / spec.name
        build_dir = stage_dir / "build"
        repo_dir  = stage_dir / "repo"

        if not stage_dir.exists():
            # Full scaffold for a brand-new stage
            build_dir.mkdir(parents=True, exist_ok=True)
            repo_dir.mkdir(parents=True, exist_ok=True)
            ok(f"Created stage  {BOLD}{spec.name}{RESET}")
        else:
            info(f"Stage '{BOLD}{spec.name}{RESET}' exists — adding build file only.")
            build_dir.mkdir(parents=True, exist_ok=True)

        # Write the build file
        build_path = build_dir / spec.build_file
        content = _build_file_content(spec.build_file, next_stage)
        build_path.write_text(content, encoding="utf-8")
        ok(f"Wrote  {BOLD}{spec.name}/build/{spec.build_file}{RESET}")

    touch_lips_config(lips_root, specs)


# ── summary ───────────────────────────────────────────────────────────────────

def print_summary(lips_root: Path, specs: list[StageSpec]):
    print()
    print(f"  {BOLD}{GREEN}┌─────────────────────────────────────────────┐{RESET}")
    print(f"  {BOLD}{GREEN}│{RESET}   {BOLD}{WHITE}All done!{RESET}                                 {BOLD}{GREEN}│{RESET}")
    print(f"  {BOLD}{GREEN}└─────────────────────────────────────────────┘{RESET}")
    print()
    print(f"  {DIM}Pipeline root{RESET}  {BOLD}{lips_root.resolve()}{RESET}")
    if specs:
        chain = f" {DIM}→{RESET} ".join(
            f"{CYAN}{s.name}{RESET}{DIM}({s.build_file}){RESET}" for s in specs
        )
        print(f"  {DIM}Stages{RESET}         {chain}")
    else:
        print(f"  {DIM}Stages{RESET}         {DIM}(none created){RESET}")
    print()


# ── main ──────────────────────────────────────────────────────────────────────

def create(pipeline_path: str):
    banner()
    TOTAL_STEPS = 4

    lips_root = Path(pipeline_path).expanduser().resolve()
    pipeline_exists = lips_root.exists()
    info(f"Pipeline path: {BOLD}{lips_root}{RESET}")

    if pipeline_exists:
        info(f"Pipeline already exists: {lips_root.resolve()}")
    else:
        lips_root.mkdir(parents=True)
        ok(f"Created pipeline root: {lips_root.resolve()}")

    # ── Steps 1–3: config + API key (skip entirely for existing pipelines) ────
    config_path = lips_root / "config.json"
    env_path    = lips_root / ".env"

    if pipeline_exists:
        info("Existing pipeline — skipping config and API key setup.")
    else:
        step(1, TOTAL_STEPS, "LLM provider & model")
        model = select_model()

        step(2, TOTAL_STEPS, "Generation parameters")
        raw_tokens = prompt("Max tokens", default=str(DEFAULT_API_CONFIG["max_tokens"]))
        try:
            max_tokens = int(raw_tokens)
        except ValueError:
            warn("Invalid number — using default.")
            max_tokens = DEFAULT_API_CONFIG["max_tokens"]

        raw_temp = prompt("Temperature", default=str(DEFAULT_API_CONFIG["temperature"]))
        try:
            temperature = float(raw_temp)
        except ValueError:
            warn("Invalid number — using default.")
            temperature = DEFAULT_API_CONFIG["temperature"]

        # Derive api_var from model string: "mistral/..." → "MISTRAL_API_KEY"
        provider_prefix = model.split("/")[0].upper()
        api_var = f"{provider_prefix}_API_KEY"

        config = {
            "generate": {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            "api_var": api_var,
            "messages": MESSAGES_BLOCK,
            "format": FORMAT_BLOCK,
        }
        config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        ok(f"Saved config.json  {DIM}(api_var: {api_var}){RESET}")

        step(3, TOTAL_STEPS, "API key")
        if env_path.exists():
            info(".env already exists — skipping.")
        else:
            api_key = _input(f"  {CYAN}?{RESET} API key {DIM}(blank to skip){RESET}: ")
            env_path.write_text(f"{api_var}={api_key}\n", encoding="utf-8")
            if api_key:
                ok("Saved .env")
            else:
                ok(f"Saved .env  {DIM}(empty — fill in {api_var} later){RESET}")

    # ── Collect all stage specs (no disk writes yet) ──────────────────────────
    specs = collect_stages(lips_root)

    # ── Materialise everything at once ────────────────────────────────────────
    materialise_stages(lips_root, specs)

    print_summary(lips_root, specs)
