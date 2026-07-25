"""Lesson 04 — The Monday-morning agent: automatic ticket triage. (STARTER)

You are going to build the pattern that makes tiny local models usable in
real workflows: STRUCTURED OUTPUT + VALIDATION + RETRY.

    1. Ask the model to answer with ONLY a JSON object in a fixed shape.
       (done for you — see SYSTEM_PROMPT below)
    2. Check that JSON with plain Python.            <-- TODO(you) #1
    3. If invalid, tell the model what was wrong
       and ask again, up to 3 times.                 <-- TODO(you) #2
    4. On success, act on it: log + print.           <-- TODO(you) #3

Fill in the three TODO(you) blocks, then run:
    Windows:      python starter.py
    macOS/Linux:  python3 starter.py

Stuck? The finished version is in solutions/ex04_ticket_triage.py.
"""

import json
from datetime import datetime
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Configuration (nothing to change here)
# ---------------------------------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "littlelamb"  # the alias we created in setup with `ollama cp ... littlelamb`

VALID_PRIORITIES = {"P1", "P2", "P3"}
VALID_TEAMS = {"backend", "frontend", "platform"}
MAX_ATTEMPTS = 3
DEFAULT_LOG_PATH = Path("triage_log.json")

# LittleLamb was fine-tuned to emit small JSON objects (that is literally what
# a tool call is), so asking for "only a JSON object" plays to its strengths.
# The rubric is deliberately concrete: a 293M model cannot infer your team's
# conventions from "P1 (drop everything)" alone — spell it out or it hedges.
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
# Talking to the model (given — same shape as lessons 01-03)
# ---------------------------------------------------------------------------


def build_user_prompt(ticket: dict) -> str:
    """Turn one ticket dict into the text the model will read.

    Note what we DON'T include: the reporter. Telling the model 'reported by
    Maite (customer support)' made it answer "team": "customer support" —
    it copied the reporter's department instead of picking who should FIX
    the bug. With a tiny model, only feed it what it needs.
    """
    return f"Ticket {ticket['id']}\nTitle: {ticket['title']}\nBody: {ticket['body']}"


def chat(messages: list) -> str:
    """Send a conversation to Ollama, return the assistant's reply text.

    temperature 0 = deterministic output, which is what you want when the
    reply must match a strict format. LittleLamb always "thinks" first, but
    Ollama puts that in message["thinking"]; message["content"] is clean.
    """
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0,
            # SEATBELT: at temperature 0 this model can fall into an endless
            # repetition loop while "thinking". Without a cap that request
            # would generate forever and block your local Ollama. With it, a
            # stuck reply comes back truncated, fails validation, and YOUR
            # retry loop recovers. This is why we validate!
            "num_predict": 700,
        },
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()["message"]["content"]


def extract_json(text: str) -> dict | None:
    """Pull the first {...} JSON object out of the model's reply.

    Small models sometimes wrap the JSON in prose ("Sure! Here it is: {...}"),
    so we grab everything between the first '{' and the last '}' and try to
    parse it. Returns None if nothing parseable is there.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


# ---------------------------------------------------------------------------
# TODO(you) #1 — validation
# ---------------------------------------------------------------------------


def validate_verdict(verdict: object) -> str | None:
    """Check a triage verdict. Return None if valid, else an error STRING.

    The error string will be sent back to the model, so write it FOR the
    model: be specific, e.g. 'You said "P5", that is not a valid priority.
    Valid priorities are exactly: P1, P2, P3.'
    Specific feedback is what makes retries actually work on a 293M model.

    Checks to write (in this order keeps the errors readable):
      1. verdict is a dict — if not, return an error saying so.
      2. all three keys exist: "priority", "team", "summary".
      3. verdict["priority"] is in VALID_PRIORITIES.
      4. verdict["team"] is in VALID_TEAMS.
      5. verdict["summary"] is a non-empty string.
    """
    # TODO(you): implement the five checks above. Remember: return None
    # when everything is valid, and an error string on the FIRST problem
    # you find (one problem at a time is easier for the model to fix).

    if not isinstance(verdict, dict):
        return "The reply was not a JSON object."

    if "priority" not in verdict:
        return "The JSON object is missing the 'priority' key."

    if "team" not in verdict:
        return "The JSON object is missing the 'team' key."

    if "summary" not in verdict:
        return "The JSON object is missing the 'summary' key."

    if verdict["priority"] not in VALID_PRIORITIES:
        return "You said 'priority', that is not a valid priority. Valid priorities are exactly: P1, P2, P3."

    if verdict["team"] not in VALID_TEAMS:
        return "You said 'team', that is not a valid team. Valid teams are exactly: backend, frontend, platform."

    if not isinstance(verdict["summary"], str) or not verdict["summary"].strip():
        return "The 'summary' must be a non-empty one-line string."

    return None


# ---------------------------------------------------------------------------
# TODO(you) #2 — the retry loop
# ---------------------------------------------------------------------------


def triage_ticket(ticket: dict, max_attempts: int = MAX_ATTEMPTS) -> dict | None:
    """Ask the model to triage one ticket, retrying on invalid output.

    Return the validated verdict dict, or None after max_attempts failures.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(ticket)},
    ]

    # TODO(you): write the retry loop. For each attempt (up to max_attempts):
    #   1. reply = chat(messages)
    #   2. verdict = extract_json(reply)
    #      - if verdict is None, the error is
    #        "I could not find a JSON object in your reply."
    #      - otherwise, error = validate_verdict(verdict)
    #   3. if error is None -> return verdict  (success!)
    #   4. if not, append TWO messages before looping again:
    #      - the model's own bad reply:   {"role": "assistant", "content": reply}
    #        (so the model can see the mistake it made)
    #      - your complaint:              {"role": "user", "content": f"That answer
    #        was not valid: {error} Reply again with ONLY the corrected JSON object."}
    # After the loop, return None — a human should look at this ticket.

    for _steps in range(max_attempts):
        reply = chat(messages)
        verdict = extract_json(reply)

        if not verdict:
            error = "I could not find a JSON object in your reply."
        else:
            error = validate_verdict(verdict)

        if not error:
            return verdict

        messages.append({"role": "assistant", "content": reply})
        messages.append(
            {
                "role": "user",
                "content": f"That answer was not valid: {error} Reply again with ONLY the corrected JSON object.",
            },
        )

    return None


# ---------------------------------------------------------------------------
# TODO(you) #3 — acting on the verdict
# ---------------------------------------------------------------------------


def log_incident(
    ticket: dict, verdict: dict, log_path: Path = DEFAULT_LOG_PATH
) -> None:
    """Append one triage result to a JSON log file (a JSON list on disk).

    Steps:
      1. If log_path exists, read it with json.loads(log_path.read_text());
         otherwise start with an empty list [].
      2. Append a dict with: ticket_id, title, priority, team, summary,
         and triaged_at (use datetime.now().isoformat(timespec="seconds")).
      3. Write the whole list back with json.dumps(entries, indent=2).
    """
    log_path = Path(log_path)
    # TODO(you): implement the three steps above.

    if log_path.exists():
        data = json.loads(log_path.read_text(encoding="utf-8"))
    else:
        data = []

    data.append(
        {
            "ticket_id": ticket["id"],
            "title": ticket["title"],
            "priority": verdict["priority"],
            "team": verdict["team"],
            "summary": verdict["summary"],
            "triaged_at": datetime.now().isoformat(timespec="seconds"),
        }
    )

    log_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Main loop (given) — runs only when you execute this file directly,
# so tests can import your functions without triaging anything.
# ---------------------------------------------------------------------------


def main() -> None:
    tickets = json.loads(
        Path(__file__).with_name("tickets.json").read_text(encoding="utf-8")
    )

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
        print(
            f"{ticket['id']:<8} {verdict['priority']:<5} {verdict['team']:<10} {verdict['summary']}"
        )

    print(f"\nDone. Full log appended to {DEFAULT_LOG_PATH.resolve()}")


if __name__ == "__main__":
    main()
