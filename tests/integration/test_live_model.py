"""Integration tests against the REAL local model.

These are skipped automatically unless BOTH are true:
  - Ollama is running on localhost:11434, and
  - the "littlelamb" alias exists (see repo setup: `ollama cp ... littlelamb`).

Run them explicitly with:
    Windows:      python -m pytest tests/integration -v
    macOS/Linux:  python3 -m pytest tests/integration -v

Expect them to be SLOW on a CPU-only laptop: LittleLamb thinks for ~100
tokens before every answer, and lesson 04 may legitimately retry.
"""

import json
import re
from pathlib import Path

import pytest
import requests

OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
MODEL_ALIAS = "littlelamb"

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TICKETS_PATH = REPO_ROOT / "exercises" / "04_ticket_triage" / "tickets.json"


def _skip_reason() -> str | None:
    """Return why we must skip, or None if the real model is ready to test."""
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=3)
        response.raise_for_status()
    except Exception:
        return "Ollama is not reachable on localhost:11434"

    model_names = [m.get("name", "") for m in response.json().get("models", [])]
    # ollama lists the alias as "littlelamb:latest"
    if not any(name.split(":")[0] == MODEL_ALIAS for name in model_names):
        return (
            f'model alias "{MODEL_ALIAS}" not found — run: '
            "ollama cp hf.co/mradermacher/LittleLamb-ToolCalling-GGUF:Q4_K_M littlelamb"
        )
    return None


_REASON = _skip_reason()
pytestmark = pytest.mark.skipif(_REASON is not None, reason=_REASON or "")


# ---------------------------------------------------------------------------
# Lesson 01: the hand-built agent rolls a real die, end to end
# ---------------------------------------------------------------------------

def test_ex01_agent_rolls_a_die_end_to_end(ex01, capsys):
    result = ex01.run_agent("Roll a six-sided die for me, please.")

    # run_agent prints the final answer (and may also return it). Ignore the
    # "[agent] calling tool ..." progress lines: they echo the tool arguments
    # (e.g. {'sides': 6}) and would make the digit check pass vacuously.
    printed = capsys.readouterr().out
    answer_lines = [
        line for line in printed.splitlines() if not line.startswith("[agent]")
    ]
    answer = result if isinstance(result, str) else "\n".join(answer_lines)

    assert answer.strip(), "the agent never produced a final answer"
    # The final answer must report a plausible die result (1-6). We search for
    # any standalone digit in range because the model phrases results freely
    # ("You rolled a 4!", "The die shows 4.").
    assert re.search(r"\b[1-6]\b", answer), (
        f"expected a die result between 1 and 6 in the answer, got: {answer!r}"
    )


# ---------------------------------------------------------------------------
# Lesson 04: the triage agent classifies the payments outage as a P1
# ---------------------------------------------------------------------------

def test_ex04_triages_payments_outage_as_p1(ex04):
    tickets = json.loads(TICKETS_PATH.read_text(encoding="utf-8"))
    payments_ticket = next(t for t in tickets if "payments" in t["title"].lower())

    # triage_ticket retries up to 3 times internally, so a single flaky
    # reply from the tiny model does not fail the test.
    verdict = ex04.triage_ticket(payments_ticket)

    assert verdict is not None, "model failed to produce a valid verdict in 3 attempts"
    # A total checkout outage losing sales is unambiguously drop-everything.
    assert verdict["priority"] == "P1"
    assert verdict["team"] in {"backend", "frontend", "platform"}
    assert isinstance(verdict["summary"], str) and verdict["summary"].strip()
