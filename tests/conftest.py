"""Shared pytest fixtures for the workshop test suite.

Two things live here, and BOTH are worth reading even if you never write a
test yourself:

1. `load_solution()` — imports a file from solutions/ by its lesson prefix,
   so tests exercise the exact code attendees can peek at.

2. `fake_ollama` — a stand-in for the real Ollama server. It monkeypatches
   `requests.post`, so the solution code runs completely unchanged while the
   tests script exactly what "the model" says. This is why the whole suite
   passes on a machine with NO Ollama installed — and it doubles as
   documentation of what real LittleLamb replies look like on the wire.
"""

import copy
import importlib.util
import sys
from pathlib import Path

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
SOLUTIONS_DIR = REPO_ROOT / "solutions"


# ---------------------------------------------------------------------------
# Importing solution files
# ---------------------------------------------------------------------------
# Solution files are standalone scripts (ex01_no_magic.py, ...), not an
# installed package, so we import them by path with importlib. We re-execute
# the module for every test so module-level state (like the tavern keeper's
# player["gold"] in lesson 03) starts fresh each time.

def load_solution(prefix: str):
    """Import the solutions/ file whose name starts with `prefix` (e.g. "ex03")."""
    matches = sorted(SOLUTIONS_DIR.glob(f"{prefix}*.py"))
    if not matches:
        pytest.skip(f"no solution file matching solutions/{prefix}*.py yet")
    path = matches[0]
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclasses/pickling/etc. can find the module.
    sys.modules[path.stem] = module
    try:
        spec.loader.exec_module(module)  # runs the file top-to-bottom (main()
        # is guarded by `if __name__ == "__main__"`, so nothing interactive runs)
    except ModuleNotFoundError as missing:
        # e.g. LangChain not installed on this machine — skip those lessons'
        # tests instead of erroring; `pip install -r requirements.txt` fixes it.
        pytest.skip(f"{path.name} needs a package that is not installed: {missing.name}")
    except SyntaxError:
        raise  # a broken solution file must FAIL loudly, never skip
    except Exception as boom:
        # Anything else at import time (e.g. a solution that pings Ollama on
        # import) — skip, loudly. The suite must pass with no Ollama running.
        pytest.skip(f"{path.name} could not be imported offline: {boom!r}")
    return module


@pytest.fixture
def ex01():
    """Fresh import of the lesson 01 solution (manual, no-magic agent)."""
    return load_solution("ex01")


@pytest.fixture
def ex03():
    """Fresh import of the lesson 03 solution (tavern keeper). Fresh matters
    here: make_offer mutates module-level player["gold"] and item stock."""
    return load_solution("ex03")


@pytest.fixture
def ex04():
    """Fresh import of the lesson 04 solution (ticket triage)."""
    return load_solution("ex04")


# ---------------------------------------------------------------------------
# The fake Ollama server
# ---------------------------------------------------------------------------
# All workshop code talks to Ollama the same way:
#
#     requests.post("http://localhost:11434/api/chat", json=payload, ...)
#
# and reads response.json()["message"]["content"]. So to fake the model we
# only need to fake `requests.post`. Each test scripts a queue of replies
# ("what the model will say"), and the fake pops one per call.
#
# The reply format below mirrors a REAL Ollama /api/chat response for
# LittleLamb (a Qwen3-based model):
#
#   {
#     "model": "littlelamb",
#     "message": {
#       "role": "assistant",
#       "thinking": "...",     <- the model ALWAYS reasons first; Ollama
#                                 separates it out so "content" stays clean
#       "content": "..."       <- the actual reply. In lesson 01's manual
#                                 mode, a tool call appears here verbatim as:
#                                 <tool_call>
#                                 {"name": "get_weather", "arguments": {"city": "Paris"}}
#                                 </tool_call>
#     },
#     "done": true
#   }


class FakeResponse:
    """The tiny slice of `requests.Response` that workshop code uses."""

    def __init__(self, payload: dict):
        self._payload = payload
        self.status_code = 200
        self.ok = True

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        pass  # status is always 200 — the fake server never errors


class FakeOllama:
    """Scripted stand-in for the Ollama server.

    - `replies`:  queue of strings; each requests.post() pops the next one
                  and returns it as message["content"].
    - `requests`: every JSON payload the code under test sent, in order —
                  tests inspect this to check e.g. that a tool result or a
                  retry error message was actually sent back to the model.
    """

    def __init__(self):
        self.replies: list[str] = []
        self.requests: list[dict] = []

    def add_reply(self, content: str) -> None:
        self.replies.append(content)

    def post(self, url, json=None, timeout=None, **kwargs) -> FakeResponse:
        # Signature mirrors requests.post(url, json=..., timeout=...).
        # Deep-copy the payload: real HTTP serializes it at send time, so a
        # later mutation of the caller's `messages` list must not rewrite
        # what we recorded for earlier requests.
        self.requests.append(copy.deepcopy(json))
        assert self.replies, (
            "The code under test called Ollama, but the fake has no scripted "
            "reply left. Add more replies with fake_ollama.add_reply(...)."
        )
        content = self.replies.pop(0)
        return FakeResponse(
            {
                "model": "littlelamb",
                "message": {
                    "role": "assistant",
                    # Real LittleLamb always emits ~100+ tokens of thinking;
                    # correct code must IGNORE this field and read "content".
                    "thinking": "(fake chain-of-thought — your code should never parse this)",
                    "content": content,
                },
                "done": True,
            }
        )


@pytest.fixture
def fake_ollama(monkeypatch):
    """Replace requests.post with the scripted fake for the duration of a test.

    Works because solution code does `import requests` and then calls
    `requests.post(...)` — the attribute is looked up at call time, so
    patching it on the shared `requests` module reaches every importer.
    """
    fake = FakeOllama()
    monkeypatch.setattr(requests, "post", fake.post)
    return fake
