"""Lesson 04 — The Monday-morning agent: automatic ticket triage. (SOLUTION)

The pattern in this file is STRUCTURED OUTPUT + VALIDATION + RETRY, and it is
the single most useful trick for putting a tiny local model into a real
workflow:

    1. Ask the model to answer with ONLY a JSON object in a fixed shape.
    2. Check that JSON with plain Python code (validate_verdict).
    3. If the check fails, tell the model exactly WHAT was wrong and ask again
       (up to 3 times).

Why this matters: a 293M-parameter model like LittleLamb is not reliable
enough to trust blindly, but it IS reliable enough that "check + one retry"
almost always lands on a valid answer. The validation code is boring, ordinary
Python — and that is the point. The model decides, your code verifies and acts.
This is the same muscle as the tavern keeper in lesson 03: the model never
touches your data directly; it only produces text that your code inspects.

Run it (Ollama must be running and the model pulled — see the README):
    Windows:      python ..\\..\\solutions\\ex04_ticket_triage.py
    macOS/Linux:  python3 ../../solutions/ex04_ticket_triage.py
"""

import json
from datetime import datetime
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/chat"

# "littlelamb" is the short alias we created during setup with:
#   ollama cp hf.co/mradermacher/LittleLamb-ToolCalling-GGUF:Q4_K_M littlelamb
MODEL = "littlelamb"

# The only values our workflow accepts. Everything else is a validation error.
VALID_PRIORITIES = {"P1", "P2", "P3"}
VALID_TEAMS = {"backend", "frontend", "platform"}

# How many times we let the model try before giving up on a ticket.
MAX_ATTEMPTS = 3

# Where triage results are appended. Lives next to this script by default.
DEFAULT_LOG_PATH = Path("triage_log.json")

# The system prompt pins down the exact output shape. LittleLamb was
# fine-tuned to emit small JSON objects (that is literally what a tool call
# is), so asking for "only a JSON object" plays to its strengths.
#
# The priority/team definitions are deliberately concrete ("outage, data
# loss, money loss..."): a 293M model cannot infer your team's conventions
# from "P1 (drop everything)" alone — spell the rubric out or it will hedge
# everything to P2. Try improving it (see the README experiments)!
SYSTEM_PROMPT = """\
You are a ticket triage assistant for a software team.
Read the ticket and reply with ONLY a JSON object, nothing else, in exactly
this shape:
{"priority": "P1|P2|P3", "team": "backend|frontend|platform", "summary": "<one line>"}

Rules:
- "priority" must be exactly one of:
  P1 = an outage, data loss, money loss, security, or a legal deadline. Drop everything.
  P2 = a real bug or slowdown that users feel, but nothing is lost. Fix this week.
  P3 = typos, cosmetic issues, and feature requests. Nobody is blocked. Someday.
- "team" is the engineering team that should FIX the issue. It must be exactly
  one of: backend (server code, APIs, database queries), frontend (anything
  visual: pages, layout, text), platform (login/SSO, servers, backups,
  compliance). Never invent another team name.
- "summary" is ONE short sentence a manager can read in two seconds.
Do not add explanations, markdown, or extra keys."""


# ---------------------------------------------------------------------------
# Talking to the model
# ---------------------------------------------------------------------------

def build_user_prompt(ticket: dict) -> str:
    """Turn one ticket dict into the text the model will read.

    Note what we DON'T include: the reporter. Found the hard way — telling
    the model 'reported by Maite (customer support)' made it answer
    "team": "customer support", copying the reporter's department instead of
    picking the team that should fix the bug. With a tiny model, every word
    in the prompt is a word it might latch onto: only feed it what it needs.
    (The reporter still goes into the log — that's for humans.)
    """
    return (
        f"Ticket {ticket['id']}\n"
        f"Title: {ticket['title']}\n"
        f"Body: {ticket['body']}"
    )


def chat(messages: list) -> str:
    """Send a conversation to Ollama and return the assistant's reply text.

    temperature 0 makes the model deterministic, which is what you want when
    the output must match a strict format. LittleLamb always "thinks" before
    answering, but Ollama separates that into message["thinking"] for us —
    message["content"] contains only the actual reply, so we read just that.
    """
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,  # one complete reply, not a token stream — easier to parse
        "options": {
            "temperature": 0,
            # SEATBELT: cap how many tokens one reply may generate. At
            # temperature 0 this model occasionally falls into an endless
            # repetition loop while "thinking" (a known greedy-decoding
            # failure of its Qwen3 family). Without a cap that one request
            # generates forever and — since local Ollama serves one request
            # at a time — blocks everything behind it. With the cap, a stuck
            # reply comes back truncated/empty, fails validation, and the
            # retry loop below recovers. 700 is plenty: a normal verdict is
            # ~150 thinking tokens + ~60 tokens of JSON.
            "num_predict": 700,
        },
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()["message"]["content"]


# ---------------------------------------------------------------------------
# The production trick: extract -> validate -> retry
# ---------------------------------------------------------------------------

def extract_json(text: str) -> dict | None:
    """Pull the first {...} JSON object out of the model's reply.

    Small models sometimes wrap the JSON in prose ("Sure! Here it is: {...}").
    Instead of failing on that, we grab everything between the first '{' and
    the last '}' and try to parse it. Returns None if there is no parseable
    JSON object — the retry loop turns that None into feedback for the model.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    # A JSON array or bare string is not what we asked for either.
    return parsed if isinstance(parsed, dict) else None


def validate_verdict(verdict: object) -> str | None:
    """Check a triage verdict. Return None if valid, else a human-readable error.

    The error string is written FOR THE MODEL: on a failed attempt we feed it
    back verbatim ("you said 'P5', that is not a valid priority") so the model
    knows exactly what to fix. Specific feedback is what makes retries work —
    a bare "try again" barely helps a 293M model.
    """
    if not isinstance(verdict, dict):
        return "The reply was not a JSON object."

    for key in ("priority", "team", "summary"):
        if key not in verdict:
            return f'The JSON object is missing the "{key}" key.'

    priority = verdict["priority"]
    if priority not in VALID_PRIORITIES:
        return (
            f'You said "{priority}", that is not a valid priority. '
            f"Valid priorities are exactly: P1, P2, P3."
        )

    team = verdict["team"]
    if team not in VALID_TEAMS:
        return (
            f'You said "{team}", that is not a valid team. '
            f"Valid teams are exactly: backend, frontend, platform."
        )

    summary = verdict["summary"]
    if not isinstance(summary, str) or not summary.strip():
        return 'The "summary" must be a non-empty one-line string.'

    return None  # everything checks out


def triage_ticket(ticket: dict, max_attempts: int = MAX_ATTEMPTS) -> dict | None:
    """Ask the model to triage one ticket, retrying on invalid output.

    Returns the validated verdict dict, or None if the model failed
    max_attempts times in a row. The caller decides what a None means
    (here: print a FAILED row so a human picks the ticket up).
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(ticket)},
    ]

    for attempt in range(1, max_attempts + 1):
        reply = chat(messages)

        verdict = extract_json(reply)
        if verdict is None:
            error = "I could not find a JSON object in your reply."
        else:
            error = validate_verdict(verdict)

        if error is None:
            return verdict  # success — usually on attempt 1

        # Invalid: keep the bad reply in the conversation (so the model can
        # see its own mistake) and append our specific complaint, then loop.
        messages.append({"role": "assistant", "content": reply})
        messages.append(
            {
                "role": "user",
                "content": (
                    f"That answer was not valid: {error} "
                    "Reply again with ONLY the corrected JSON object."
                ),
            }
        )

    return None  # gave up after max_attempts — a human should look at this one


# ---------------------------------------------------------------------------
# Acting on the verdict (the "code acts" half of the pattern)
# ---------------------------------------------------------------------------

def log_incident(ticket: dict, verdict: dict, log_path: Path = DEFAULT_LOG_PATH) -> None:
    """Append one triage result to a JSON log file.

    We keep the log as a JSON list: read the whole list, append, write it
    back. That is perfectly fine for a workshop-sized log; a real system
    would use a database or append-only JSONL.
    """
    log_path = Path(log_path)
    if log_path.exists():
        entries = json.loads(log_path.read_text(encoding="utf-8"))
    else:
        entries = []

    entries.append(
        {
            "ticket_id": ticket["id"],
            "title": ticket["title"],
            "priority": verdict["priority"],
            "team": verdict["team"],
            "summary": verdict["summary"],
            "triaged_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    log_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main loop — guarded so tests can import the functions above without
# accidentally triaging anything.
# ---------------------------------------------------------------------------

def main() -> None:
    tickets_path = Path(__file__).parent.parent / "exercises" / "04_ticket_triage" / "tickets.json"
    tickets = json.loads(tickets_path.read_text(encoding="utf-8"))

    print(f"Triaging {len(tickets)} tickets with {MODEL} (all local, no cloud)...\n")
    print(f"{'ID':<8} {'PRIO':<5} {'TEAM':<10} SUMMARY")
    print("-" * 70)

    for ticket in tickets:
        verdict = triage_ticket(ticket)
        if verdict is None:
            # After 3 bad attempts we do NOT guess — we flag it for a human.
            print(f"{ticket['id']:<8} {'??':<5} {'??':<10} FAILED — needs a human")
            continue
        log_incident(ticket, verdict)
        print(f"{ticket['id']:<8} {verdict['priority']:<5} {verdict['team']:<10} {verdict['summary']}")

    print(f"\nDone. Full log appended to {DEFAULT_LOG_PATH.resolve()}")


if __name__ == "__main__":
    main()
