# 04 — The Monday-morning agent: automatic ticket triage (14 min)

It is Monday, 9:00. Eight tickets landed over the weekend. Someone has to read
them all, decide what is on fire and what can wait, and route each one to the
right team. That someone is about to be a 238 MB model running on your laptop.

For every ticket in `tickets.json`, your agent asks LittleLamb for a verdict:

```json
{"priority": "P1", "team": "backend", "summary": "Checkout is down, losing sales."}
```

and prints a triage table plus a `triage_log.json` audit file.

## Same muscle as the tavern, professional edition

In lesson 03 the model *decided* ("accept the offer") and your code *acted*
(moved the gold). Here it is the exact same split, dressed for the office:

- **The model decides**: priority, team, one-line summary.
- **Your code acts**: validates the verdict, writes the log, prints the table.

The model never touches your data directly. It only produces text, and your
plain-Python code is the gatekeeper that inspects it before anything happens.

## The production trick: structured output + validation + retry

A 293M-parameter model is not reliable enough to trust blindly. It IS reliable
enough that this loop almost always lands on a valid answer:

1. **Structured output** — ask for ONLY a JSON object in a fixed shape.
   LittleLamb was fine-tuned to emit small JSON objects (a tool call is
   exactly that), so this plays to its strengths.
2. **Validation** — check the JSON with boring, ordinary Python:
   are the keys there? is `"priority"` one of P1/P2/P3? is `"team"` a real team?
3. **Retry with feedback** — on failure, do not just say "try again".
   Say *what* was wrong: `you said "P5", that is not a valid priority`.
   Up to 3 attempts, then flag the ticket for a human instead of guessing.

This validate-and-retry loop is the difference between a demo and something
you would actually let loose on your inbox. Cloud systems built on models
1000x this size use the very same pattern — they just hide it from you.

## Your three TODOs (in `starter.py`)

| # | Function | What you write | Priority |
|---|----------|----------------|----------|
| 1 | `validate_verdict` | the five checks, returning `None` or a specific error string | core — do this |
| 2 | `triage_ticket` retry loop | call → extract → validate → feed the error back, max 3 tries | core — do this |
| 3 | `log_incident` | append the verdict to a JSON list on disk | if time remains |

The lesson lives in #1 and #2 — that pair IS the validate-and-retry pattern.
If the clock is against you, copy `log_incident` straight from
`solutions/ex04_ticket_triage.py` with zero guilt: it's plain file I/O,
nothing agent-shaped about it.

The prompt, the Ollama call, the JSON extractor, and the main loop are
already written for you.

## Run it

Ollama must be running and the `littlelamb` alias created (see the repo
setup). Then, from this folder:

**Windows (PowerShell):**
```powershell
python starter.py
```

**macOS/Linux:**
```bash
python3 starter.py
```

To see the finished behaviour at any time, run the solution instead:

**Windows (PowerShell):**
```powershell
python ..\..\solutions\ex04_ticket_triage.py
```

**macOS/Linux:**
```bash
python3 ../../solutions/ex04_ticket_triage.py
```

Expect a few seconds per ticket on a CPU-only laptop — LittleLamb always
"thinks" for ~100 tokens before answering. That is normal; watch the table
fill in row by row.

## What success looks like

```
ID       PRIO  TEAM       SUMMARY
----------------------------------------------------------------------
T-101    P1    backend    Checkout returns 500 on every payment, blocking sales.
T-102    P1    platform   SSO login broken for the whole office.
T-103    P3    frontend   Typo "Copyrigth" in the site footer.
...
```

Your rows will not match this word for word — the summaries are the model's
own, and a 293M model's *judgment* is imperfect (it likes to hedge minor
tickets up to P2). That is fine: validation guarantees the *format* is always
legal, not that the *opinion* is right. What must match: valid priorities,
valid teams, and a `triage_log.json` that grows by one entry per ticket.

You may also see a ticket take an extra attempt or two: at temperature 0 this
model can wander into a repetition loop while thinking, come back truncated
(that is our `num_predict` seatbelt), fail validation, and get rescued by
YOUR retry loop. When that happens live, you are watching the whole point of
this lesson work.

## Experiments (if you finish early)

1. **Add a `security` team.** Put `"security"` into `VALID_TEAMS`, mention it
   in `SYSTEM_PROMPT`, and add a ticket to `tickets.json` about, say, an
   exposed API key in a public repo. Does the model route it correctly?
2. **Tune the rubric.** The model hedges typos and feature requests up to P2?
   Edit the priority definitions in `SYSTEM_PROMPT` and re-run. Careful: we
   tried adding "a typo is ALWAYS P3, never P2" and the model started calling
   *failing backups* P3 too. Prompt engineering on tiny models is a seesaw —
   move one word, watch every ticket.
3. **Two-stage agent.** After a successful verdict, make a *second* model call
   that drafts a short, polite reply to the reporter ("We've triaged your
   ticket as P1 and the backend team is on it"). Classify first, write second
   — chaining small focused calls beats one big vague one.
4. **Hunt the ambiguous ticket.** T-106 (slow CSV export) was written to sit
   on the fence between `backend` and `platform` — even the reporter is not
   sure. Triage just that ticket 5 times in a row. With `temperature: 0` you
   should see the same verdict every time; now switch the options to
   `{"temperature": 0.6, "top_p": 0.95, "top_k": 20}` and run it 5 times
   again. Discuss: is either answer *wrong*? What should a triage system do
   when reasonable people (and models) disagree? This is why real pipelines
   log verdicts instead of silently acting on them.
