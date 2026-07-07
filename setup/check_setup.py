"""Workshop doctor: checks that your laptop is ready for the exercises.

Run it with:   python setup/check_setup.py

It uses ONLY the Python standard library on purpose, so it works even
before you run `pip install -r requirements.txt`.

It checks, in order:
  1. Python is 3.10 or newer.
  2. The Ollama server answers on http://localhost:11434.
  3. The LittleLamb model has been pulled (and suggests the short alias).
  4. The model can actually generate a token (smoke test).

Output uses plain ASCII markers ([OK] / [FAIL]) instead of emoji because
some Windows consoles use the cp1252 codepage and crash on fancy characters.
"""

# Lets this script at least START on old Pythons (3.7+), so it can print a
# friendly "your Python is too old" message instead of a syntax/type error.
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

OLLAMA_URL = "http://localhost:11434"

# The full name Ollama registers when you pull straight from Hugging Face.
FULL_MODEL_NAME = "hf.co/mradermacher/LittleLamb-ToolCalling-GGUF:Q4_K_M"
# The short alias all workshop code uses. Create it once with:
#   ollama cp hf.co/mradermacher/LittleLamb-ToolCalling-GGUF:Q4_K_M littlelamb
# (it is a zero-cost alias — both names point at the same 238 MB blob)
ALIAS = "littlelamb"

PULL_COMMAND = f"ollama pull {FULL_MODEL_NAME}"
ALIAS_COMMAND = f"ollama cp {FULL_MODEL_NAME} {ALIAS}"


def ok(message: str) -> None:
    print(f"[OK]   {message}")


def fail(message: str, hint: str) -> None:
    print(f"[FAIL] {message}")
    # Indent the hint so it reads as part of the failure.
    for line in hint.splitlines():
        print(f"       {line}")


def check_python() -> bool:
    """The langchain packages (and modern typing) need Python 3.10+."""
    version = sys.version_info
    pretty = f"{version.major}.{version.minor}.{version.micro}"
    if version >= (3, 10):
        ok(f"Python {pretty} (3.10+ required)")
        return True
    fail(
        f"Python {pretty} is too old — this workshop needs 3.10 or newer.",
        "Windows: install from https://www.python.org/downloads/ and tick\n"
        '"Add python.exe to PATH", then reopen your terminal.\n'
        "macOS: install from python.org or run: brew install python\n"
        "Then run this script again with the new interpreter.",
    )
    return False


def check_ollama_running() -> bool:
    """Ollama serves a tiny status page on port 11434 when it is alive."""
    try:
        with urllib.request.urlopen(OLLAMA_URL, timeout=5) as response:
            response.read()
        ok(f"Ollama server is running at {OLLAMA_URL}")
        return True
    except (urllib.error.URLError, OSError):
        fail(
            f"Cannot reach Ollama at {OLLAMA_URL}.",
            "Ollama is probably not running.\n"
            "Windows: look for the llama icon in the system tray; if it is\n"
            "not there, start Ollama from the Start menu.\n"
            "macOS: open the Ollama app, or run `ollama serve` in a\n"
            "separate terminal and leave it open.\n"
            "Not installed yet? Get it from https://ollama.com/download",
        )
        return False


def check_model_present() -> str | None:
    """Ask Ollama which models are installed (GET /api/tags).

    Returns the model name we should use for the smoke test, or None.
    Prefers the short 'littlelamb' alias; falls back to the full name.
    """
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=5) as response:
            data = json.loads(response.read())
    except (urllib.error.URLError, OSError, ValueError):
        fail(
            "Could not list installed models (GET /api/tags failed).",
            "Is Ollama still starting up? Wait a few seconds and retry.",
        )
        return None

    # Names come back like "littlelamb:latest" — compare on the part
    # before the tag, and also on the full name with tag.
    installed = {m.get("name", "") for m in data.get("models", [])}
    installed |= {name.split(":", 1)[0] for name in installed}

    has_alias = ALIAS in installed
    has_full = FULL_MODEL_NAME in installed or FULL_MODEL_NAME.lower() in installed

    if has_alias:
        ok(f"Model '{ALIAS}' is installed")
        return ALIAS
    if has_full:
        ok(f"Model is installed under its long name: {FULL_MODEL_NAME}")
        print(f"       Tip: create the short alias the workshop code expects:")
        print(f"         {ALIAS_COMMAND}")
        return FULL_MODEL_NAME
    fail(
        "The LittleLamb model is not installed.",
        "Pull it (238 MB — needs internet, only this once):\n"
        f"  {PULL_COMMAND}\n"
        "Then give it the short name the workshop code uses:\n"
        f"  {ALIAS_COMMAND}\n"
        "Both commands are identical in PowerShell and macOS/Linux shells.",
    )
    return None


def check_generation(model: str) -> bool:
    """Smoke test: ask the model for a single token via /api/generate.

    If this works, the whole stack (Ollama + model + your CPU) is healthy.
    First call may take ~30s while the model loads into RAM — that is normal.
    """
    payload = json.dumps(
        {
            "model": model,
            "prompt": "Hi",
            "stream": False,
            # 1 token is all we need to prove the model runs.
            "options": {"num_predict": 1},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    print("       (loading the model into RAM — first run can take ~30s)")
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            json.loads(response.read())
        ok("The model generated a token — your setup works end to end")
        return True
    except (urllib.error.URLError, OSError, ValueError) as error:
        fail(
            f"Generation smoke test failed: {error}",
            "Try running the model once by hand to see the real error:\n"
            f"  ollama run {model}\n"
            "If Ollama complains about the model, re-pull it:\n"
            f"  {PULL_COMMAND}",
        )
        return False


def main() -> int:
    print("Workshop setup check")
    print("=" * 40)

    all_good = check_python()

    if check_ollama_running():
        model = check_model_present()
        if model is None:
            all_good = False
        else:
            all_good = check_generation(model) and all_good
    else:
        all_good = False
        print("[SKIP] Model and generation checks (Ollama is not reachable)")

    print("=" * 40)
    if all_good:
        print("All checks passed. You are ready — see you at exercise 00!")
        return 0
    print("Some checks failed. Follow the hints above, then run this again.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
