from pathlib import Path
import json
# ── helpers ──────────────────────────────────────────────────────────────────

def prompt(msg: str, default: str | None = None) -> str:
    """Prompt user for input, showing default value if provided."""
    if default:
        msg = f"{msg} [{default}]: "
    else:
        msg = f"{msg}: "
    while True:
        value = input(msg).strip()
        if value:
            return value
        if default is not None:
            return default
        print("  ✗ This field is required.")


def confirm(msg: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{msg} [{hint}]: ").strip().lower()
        if raw == "":
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("  ✗ Please enter y or n.")


def section(title: str):
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


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


def select_model() -> str:
    print("\n  Available providers:")
    for key, prov in PROVIDERS.items():
        print(f"    {key}. {prov['name']}")
    print("    0. Enter model string manually")

    prov_choice = input("  Select provider: ").strip()
    if prov_choice == "0":
        return input("  Model string: ").strip()

    provider = PROVIDERS.get(prov_choice)
    if not provider:
        print("  ✗ Invalid choice — using default model.")
        return DEFAULT_API_CONFIG["model"]

    print(f"\n  {provider['name']} models:")
    for key, model in provider["models"].items():
        print(f"    {key}. {model}")

    model_choice = input("  Select model: ").strip()
    model = provider["models"].get(model_choice)
    if not model:
        print("  ✗ Invalid choice — using first model.")
        model = next(iter(provider["models"].values()))
    return model


# ── stage creation ────────────────────────────────────────────────────────────

def create_stage(lips_root: Path, previous_stage_name: str | None) -> str | None:
    """
    Interactively create one stage directory.
    Returns the new stage name, or None if the user chose to stop.
    """
    section("Add a stage  (leave name blank to finish)")
    stage_name = input("  Stage name: ").strip()
    if not stage_name:
        return None

    stage_dir = lips_root / stage_name
    build_dir = stage_dir / "build"
    repo_dir = stage_dir / "repo"

    if stage_dir.exists():
        print(f"  ℹ  Stage '{stage_name}' already exists — skipping creation.")
    else:
        # Create directory structure
        build_dir.mkdir(parents=True, exist_ok=True)
        repo_dir.mkdir(parents=True, exist_ok=True)

        (build_dir / "compile.md").write_text("", encoding="utf-8")
        (repo_dir / "prompt.md").write_text("", encoding="utf-8")
        (repo_dir / ".gitignore").write_text("*.verify.md\n", encoding="utf-8")

        print(f"  ✓ Created stage: {stage_dir}")

    # Patch the *previous* stage's compile.md to point at this stage
    if previous_stage_name:
        prev_compile = lips_root / previous_stage_name / "build" / "compile.md"
        if prev_compile.exists():
            existing = prev_compile.read_text(encoding="utf-8")
            env_block = f"```env\nTARGET={stage_name}\n```\n"
            if f"TARGET={stage_name}" not in existing:
                prev_compile.write_text(env_block + existing, encoding="utf-8")
                print(f"  ✓ Prepended TARGET={stage_name} to {prev_compile}")

    return stage_name


# ── main create flow ──────────────────────────────────────────────────────────

def create():
    print("\n╔══════════════════════════════════════╗")
    print("║       LIPS  Pipeline  Creator        ║")
    print("╚══════════════════════════════════════╝")

    # ── Step 1: workspace root ────────────────────────────────────────────────
    section("Step 1 / 5 — Workspace root")
    workspace_root = Path(prompt("Workspace root folder", default=".")).expanduser()
    if not workspace_root.exists():
        workspace_root.mkdir(parents=True)
        print(f"  ✓ Created {workspace_root}")
    else:
        print(f"  ℹ  Using existing folder: {workspace_root.resolve()}")

    # ── Step 2: pipeline (lips root) ─────────────────────────────────────────
    section("Step 2 / 5 — Pipeline name")
    pipeline_name = prompt("Pipeline name")
    lips_root = workspace_root / pipeline_name

    if lips_root.exists():
        print(f"  ℹ  Pipeline folder already exists: {lips_root.resolve()}")
    else:
        lips_root.mkdir(parents=True)
        print(f"  ✓ Created lips root: {lips_root.resolve()}")

    # ── Step 3 & 4: LLM provider, model, tokens, temperature ─────────────────
    api_config_path = lips_root / "api-config.json"
    if api_config_path.exists():
        print(f"\n  ℹ  api-config.json already exists — skipping LLM configuration.")
    else:
        section("Step 3 / 5 — LLM provider & model")
        model = select_model()

        section("Step 4 / 5 — Generation parameters")
        raw_tokens = prompt("Max tokens", default=str(DEFAULT_API_CONFIG["max_tokens"]))
        try:
            max_tokens = int(raw_tokens)
        except ValueError:
            print("  ✗ Invalid number — using default.")
            max_tokens = DEFAULT_API_CONFIG["max_tokens"]

        raw_temp = prompt("Temperature", default=str(DEFAULT_API_CONFIG["temperature"]))
        try:
            temperature = float(raw_temp)
        except ValueError:
            print("  ✗ Invalid number — using default.")
            temperature = DEFAULT_API_CONFIG["temperature"]

        api_config = {"model": model, "max_tokens": max_tokens, "temperature": temperature}
        api_config = {
            "generate": api_config,
            "api_var": "API_KEY"
        }
        api_config_path.write_text(json.dumps(api_config, indent=2) + "\n", encoding="utf-8")
        print(f"\n  ✓ Saved api-config.json:\n    {json.dumps(api_config, indent=4)}")

    # ── Step 5: API key → .env ────────────────────────────────────────────────
    env_path = lips_root / ".env"
    if env_path.exists():
        print(f"\n  ℹ  .env already exists — skipping API key setup.")
    else:
        section("Step 5 / 5 — API key")
        api_key = prompt("API key (will be stored in .env)")
        env_path.write_text(f"API_KEY={api_key}\n", encoding="utf-8")
        print(f"  ✓ Saved .env")

    # ── Stage loop ────────────────────────────────────────────────────────────
    section("Stage creation  (enter stage names one by one; blank = done)")
    stages: list[str] = []
    previous: str | None = None

    while True:
        name = create_stage(lips_root, previous_stage_name=previous)
        if name is None:
            break
        if name not in stages:
            stages.append(name)
            previous = name

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n╔══════════════════════════════════════╗")
    print(  "║             Done!                    ║")
    print(  "╚══════════════════════════════════════╝")
    print(f"  Pipeline root : {lips_root.resolve()}")
    if stages:
        print(f"  Stages        : {' → '.join(stages)}")
    else:
        print("  Stages        : (none created)")
    print()
