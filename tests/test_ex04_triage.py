"""Tests for lesson 04 — ticket triage: structured output + validation + retry.

Interface under test (solutions/ex04_ticket_triage.py):
    validate_verdict(verdict) -> str | None      (None = valid, str = error)
    triage_ticket(ticket, max_attempts=3) -> dict | None
    log_incident(ticket, verdict, log_path) -> None

The model is played by the fake_ollama fixture, so this runs without Ollama.
"""

import json

TICKET = {
    "id": "T-101",
    "title": "Payments page returns 500 on checkout",
    "body": "Every customer who clicks 'Pay now' gets an Internal Server Error.",
    "reporter": "Maite (customer support)",
}

VALID_JSON_REPLY = (
    '{"priority": "P1", "team": "backend", '
    '"summary": "Checkout is broken and blocking all payments."}'
)


def make_verdict(**overrides) -> dict:
    """A known-good verdict, with per-test tweaks applied on top."""
    verdict = {"priority": "P1", "team": "backend", "summary": "Checkout is broken."}
    verdict.update(overrides)
    return verdict


# ---------------------------------------------------------------------------
# validate_verdict — shape and enum checks
# ---------------------------------------------------------------------------

def test_valid_verdict_passes(ex04):
    assert ex04.validate_verdict(make_verdict()) is None


def test_all_priority_and_team_combinations_pass(ex04):
    for priority in ("P1", "P2", "P3"):
        for team in ("backend", "frontend", "platform"):
            assert ex04.validate_verdict(make_verdict(priority=priority, team=team)) is None


def test_non_dict_is_rejected(ex04):
    error = ex04.validate_verdict("P1 backend")
    assert isinstance(error, str) and error


def test_missing_key_is_rejected(ex04):
    verdict = make_verdict()
    del verdict["team"]
    error = ex04.validate_verdict(verdict)
    assert isinstance(error, str)
    assert "team" in error  # the error must name what is missing


def test_invalid_priority_is_rejected_and_named(ex04):
    error = ex04.validate_verdict(make_verdict(priority="P5"))
    assert isinstance(error, str)
    # The retry loop feeds this string back to the model, so it must quote
    # the bad value — "you said X" is what makes the retry effective.
    assert "P5" in error


def test_invalid_team_is_rejected_and_named(ex04):
    error = ex04.validate_verdict(make_verdict(team="marketing"))
    assert isinstance(error, str)
    assert "marketing" in error


def test_empty_summary_is_rejected(ex04):
    assert isinstance(ex04.validate_verdict(make_verdict(summary="")), str)
    assert isinstance(ex04.validate_verdict(make_verdict(summary="   ")), str)


# ---------------------------------------------------------------------------
# triage_ticket — the retry loop against the scripted fake model
# ---------------------------------------------------------------------------

def test_valid_on_first_attempt(ex04, fake_ollama):
    fake_ollama.add_reply(VALID_JSON_REPLY)

    verdict = ex04.triage_ticket(TICKET)

    assert verdict == json.loads(VALID_JSON_REPLY)
    assert len(fake_ollama.requests) == 1  # no retry needed


def test_invalid_then_valid_succeeds_on_attempt_two(ex04, fake_ollama):
    # Attempt 1: the model rambles with no JSON at all. Attempt 2: correct.
    fake_ollama.add_reply("This looks urgent, probably the backend team should see it.")
    fake_ollama.add_reply(VALID_JSON_REPLY)

    verdict = ex04.triage_ticket(TICKET)

    assert verdict is not None
    assert verdict["priority"] == "P1"
    assert verdict["team"] == "backend"
    assert len(fake_ollama.requests) == 2

    # The second request must carry the retry conversation: the model's own
    # bad reply plus our complaint, not just the original prompt again.
    first_messages = fake_ollama.requests[0]["messages"]
    second_messages = fake_ollama.requests[1]["messages"]
    assert len(second_messages) > len(first_messages)


def test_bad_enum_error_is_fed_back_to_the_model(ex04, fake_ollama):
    # Attempt 1 is well-formed JSON but invents a team; attempt 2 is correct.
    fake_ollama.add_reply(
        '{"priority": "P1", "team": "payments", "summary": "Checkout is broken."}'
    )
    fake_ollama.add_reply(VALID_JSON_REPLY)

    verdict = ex04.triage_ticket(TICKET)

    assert verdict is not None and verdict["team"] == "backend"
    # The feedback message sent on retry must quote the invalid value so the
    # model knows exactly what to fix.
    second_request = json.dumps(fake_ollama.requests[1])
    assert "payments" in second_request


def test_three_invalid_replies_fail_cleanly(ex04, fake_ollama):
    for _ in range(3):
        fake_ollama.add_reply("I am a model that refuses to emit JSON today.")

    verdict = ex04.triage_ticket(TICKET)

    assert verdict is None  # a clean "needs a human" — never an exception
    assert len(fake_ollama.requests) == 3  # tried exactly max_attempts times
    assert fake_ollama.replies == []  # and consumed every scripted reply


# ---------------------------------------------------------------------------
# log_incident — the "code acts" half
# ---------------------------------------------------------------------------

def test_log_incident_creates_and_appends(ex04, tmp_path):
    log_path = tmp_path / "triage_log.json"
    verdict = make_verdict()

    ex04.log_incident(TICKET, verdict, log_path)
    ex04.log_incident(TICKET, make_verdict(priority="P2"), log_path)

    entries = json.loads(log_path.read_text(encoding="utf-8"))
    assert isinstance(entries, list)
    assert len(entries) == 2  # appended, not overwritten

    first = entries[0]
    assert first["ticket_id"] == "T-101"
    assert first["priority"] == "P1"
    assert first["team"] == "backend"
    assert first["summary"] == verdict["summary"]
    assert entries[1]["priority"] == "P2"
