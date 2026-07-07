# TEACHING GUIDE — Jorge's run sheet

> **100% Local AI Agents on Your Laptop** — Euskal Encounter 2026 · 1h45 · room has basic Python, ZERO AI.
> This file is for the speaker. Attendees never need it. Print it or keep it on the second screen.

---

## ONE-PAGE CHEAT SHEET

| Clock | Block | The one-sentence lesson | If you're behind, cut... |
|---|---|---|---|
| **0:00–0:12** | Intro + setup triage | "Everything today runs on YOUR laptop — prove it by the end." | Cut the bio, never the doctor script. |
| **0:12–0:22** | **Ex00** Hello, local LLM | An LLM is just a program on a port; talking to it is one HTTP POST. | Cut the streaming bonus. Keep the Wi-Fi stunt. |
| **0:22–0:50** | **Ex01** Tool calling, NO magic | An agent = a loop + a string parser + a dict of functions. The model writes; your code does. | **NEVER CUT. This is the workshop.** Cut experiments only. |
| **0:50–1:05** | **Ex02** Same agent, LangChain | Frameworks hide the plumbing you just built — the loop never goes away. | **Most cuttable block.** Demo the solution in 5 min and move on, or skip straight to ex03. |
| **1:05–1:28** | **Ex03** Grunk the tavern keeper | State lives in code; personality lives in the model. | Cut experiments + shorten contest to 5 min. Keep one live haggle. |
| **1:28–1:42** | **Ex04** Ticket triage | Structured output + validation + retry = the pattern that makes tiny models employable. | Cut the TODO typing; run the solution live and walk the retry loop on screen. |
| **1:42–1:45** | Wrap | "It never left your laptop." | Nothing. 3 minutes, links, contest winner, applause. |

**Red lines (non-negotiable):**
- **0:50** — you MUST be starting ex02. Not there? Skip ex02 entirely, jump to ex03.
- **1:28** — start ex04 even if the ex03 contest is mid-haggle. Announce "contest stays open, post screenshots in the channel, winner at the wrap."

**Model name everywhere:** `littlelamb` (the `ollama cp` alias). If someone's code says the long HF name, it also works — but fix the alias, all starters assume it.

---

## PRE-FLIGHT CHECKLIST

### Night before

- [ ] `ollama pull hf.co/mradermacher/LittleLamb-ToolCalling-GGUF:Q4_K_M` on the stage Mac, then `ollama cp ... littlelamb`.
- [ ] `python3 setup/check_setup.py` → four `[OK]` lines, exit 0.
- [ ] `pip install -r requirements.txt` in a fresh venv; run `solutions/ex02_langchain_agent.py` once (proves langchain-ollama + bind_tools work).
- [ ] Run `solutions/ex03_rpg_tavern_keeper.py` from repo root, do one full haggle (list → price → offer 28 on iron_sword → DEAL). Warm-up matters: first model load is ~30 s.
- [ ] Run `solutions/ex04_ticket_triage.py` end-to-end (8/8 tickets, T-101 → P1/backend). Delete the generated `triage_log.json` after (it's gitignored anyway).
- [ ] **Offline fallback USB:** the GGUF file (~238 MB), OllamaSetup.exe (Windows), Ollama.dmg (macOS), Python 3.12 installers (both OS), VS Code installers, a ZIP of the repo, a wheelhouse: `pip download -r requirements.txt -d wheels/ --platform win_amd64 --python-version 3.12 --only-binary=:all:` (plus a plain `pip download` for mac). LAN party Wi-Fi WILL melt.
- [ ] `git push` everything; confirm the GitHub clone URL in README works from another machine.

### 1 hour before (venue rules: be in the room early)

- [ ] `git pull` on the stage machine. No last-minute edits after this.
- [ ] Restart Ollama fresh (`pkill ollama` + reopen app) — a wedged llama-server from earlier testing will read-timeout everything.
- [ ] `python3 setup/check_setup.py` again on venue power/network.
- [ ] HDMI/TV check: terminal font ≥ 20 pt, VS Code zoom Cmd+= twice, **light theme if the projector is washed out**. Read the back-row test: can you read `<tool_call>` from the door?
- [ ] Turn OFF: notifications, Slack, auto-updates. Turn ON: Do Not Disturb.
- [ ] Have `solutions/` open in a second VS Code window — your escape hatch for every exercise.
- [ ] Write the workshop channel name + repo URL on the room screen/whiteboard NOW so stragglers self-serve.
- [ ] Know where the Wi-Fi toggle is. You will use it theatrically in ex00.

---

## 0:00–0:12 — INTRO + SETUP TRIAGE

**HOOK (say this, roughly):**
> "Quick poll — hands up: who has paid an API bill for AI? ... Who has pasted company data into ChatGPT and then thought 'hmm, maybe I shouldn't have'? ... In the next hour and forty-five, you build an AI agent where both of those problems are physically impossible. Not policy-impossible. *Physically*. It runs on the laptop in front of you, and I'll prove it by pulling the Wi-Fi."

**Beats:**
1. One slide of "what's an agent": a program where an LLM decides and your code acts. Don't over-explain — ex01 IS the explanation.
2. The star: LittleLamb-ToolCalling, 293M params, 238 MB, Apache-2.0, by Multiverse Computing (yes, where I work; no, this isn't a sales pitch — it's the only decent tool-calling model that fits your 8 GB laptops).
3. **Everyone runs `python setup/check_setup.py` NOW.** Four `[OK]` = thumbs up. Anyone with a `[FAIL]`: the script prints the fix; neighbors help; USB has installers.
4. While the room installs: agenda table, the rules of the road ("starters have `TODO(you)` markers; solutions exist; copying from solutions is legal, learning is mandatory").

**Failure modes at this stage:**

| Symptom | Fix |
|---|---|
| `[FAIL] Cannot reach Ollama` | Windows: llama icon in tray missing → Start menu → Ollama. macOS: open the app. |
| Model not pulled, Wi-Fi dead | USB: `ollama pull` from a local file is not a thing — instead copy `~/.ollama/models` blob dir from USB, or pair them with a neighbor for now. |
| PowerShell "running scripts is disabled" | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, reopen terminal. |
| Old Python (3.7–3.9) | Doctor script prints a friendly message (not a crash) — installers on USB. |

**Transition:** "Green checks? Then let's say hello to the thing living on port 11434."

---

## 0:12–0:22 — EX00: HELLO, LOCAL LLM ⏱ 10 min

**Files:** `exercises/00_hello_local_llm/starter.py` (3 TODOs + streaming bonus)

**HOOK:**
> "Everyone thinks talking to an AI needs an SDK, an API key, and a credit card. It needs fourteen lines of Python and zero of those things. Ollama is a web server on YOUR machine. We're going to POST JSON at it like it's 2009."

**Live-coding beats (in order):**
1. Type TODO #1: `MODEL = "littlelamb"`. Say out loud why the alias exists (`ollama cp`, zero disk cost).
2. TODO #2: the two message dicts. Emphasize roles: *system = rules, user = the human.* "Remember `system` — it becomes a personality in ex03."
3. **Deliberate break:** before TODO #3, `print(data)` and show the raw response on screen. Point at `message.thinking` vs `message.content`. "This model thinks out loud for ~100 tokens before every answer. Ollama separates it for us. We only ever read `content`." (Also: don't be tempted by `think: false` — this model behaves worse without its thinking. It's in the solution comments.)
4. TODO #3: `reply = data["message"]["content"]`. Run it. Expected: `The capital of France is Paris.`
5. **THE STUNT.** "Everyone: turn off your Wi-Fi. Yes, really. Airplane mode. Now run it again." *(pull the stage machine's Wi-Fi on screen)* — it still answers. "Nothing left your machine. No key, no bill, no telemetry, no terms of service. That is the entire thesis of today."

**Checkpoint question:** "What are the two keys inside `data['message']` and which one do we print?" *(thinking / content → content)*

**Predicted failure modes:**

| Symptom | Fix |
|---|---|
| `ConnectionError` / refused on 11434 | Ollama not running — tray icon / open the app. |
| First run hangs ~30 s | Model loading into RAM. Say it BEFORE they run: "first run is slow, that's the load, not a bug." |
| Requests routed through the LAN party proxy | `NO_PROXY=localhost,127.0.0.1` (README troubleshooting has both shells). |
| Windows console prints garbage on fancy chars | Stick to ASCII in prompts; it's why the doctor script uses `[OK]`, tell that story if it comes up. |

**Fast finishers →** experiments: pirate system prompt; ask "Who won the last Euskal Encounter tournament?" and enjoy the confident nonsense — "small models are bad at *knowing*; hold that thought for 10 minutes." Then the NDJSON streaming bonus.

**Transition line:**
> "So it knows Paris. Ask it what time it is — go on, try. It can't know. It's a frozen file from months ago. Next exercise: we give it hands."

---

## 0:22–0:50 — EX01: TOOL CALLING, NO MAGIC ⏱ 28 min — THE CORE. NEVER CUT.

**Files:** `exercises/01_tool_calling_no_magic/starter.py` — system prompt and tools GIVEN; attendees write `parse_tool_call`, the dispatch, the loop body.

**HOOK:**
> "Raise your hand if you've heard that GPT can 'browse the web' or 'run code'. Here's the industry's best-kept non-secret: **the model never executes anything.** It only writes text. Text that *asks*. Some ordinary Python — written by someone like you — reads that text and does the actual thing. In the next 25 minutes you write that Python, with nothing but `requests` and a regex. After today, no AI framework will ever be able to bluff you again."

**Set the scene (3 min, on screen):**
- Show the ASCII box in the README: THE MODEL NEVER EXECUTES ANYTHING.
- Show the GIVEN system prompt in the starter. "This exact `<tools>`/`<tool_call>` format is what the model was *trained* on. We give it to you because getting it right is fiddly — and in experiment 3 you get to break it and watch the model lose its powers."
- Show the loop diagram. "Max 5 laps — MAX_STEPS. Tiny models sometimes ask for tools forever."

**Live-coding beats:**
1. **Type TODO #1 first** — `parse_tool_call`. The regex is literally in the hint comment: `re.search(r"<tool_call>(.*?)</tool_call>", text, re.DOTALL)` → `json.loads(match.group(1))` → return `(name, args)` or `None`. Sell the try/except: "a 293M model WILL emit broken JSON eventually; returning None beats crashing."
2. **Deliberate break:** run with only TODO #1 done and the loop body still `...` — nothing prints. "Python's `...` is a legal no-op. The loop runs 5 times and gives up. That silent 5-step message is what half of you will see in a minute — now you know why."
3. TODO #2+#3: the loop body, following the lettered comments a–f. Pause on **line c**: `result = TOOLS[name](**args)` — "This single line is the entire agent industry. The model *chose* the name and args by writing text; this line does the doing. If the name's not in the dict, nothing runs. That dict is your firewall."
4. Pause on **line e**: the `<tool_response>` format. "This exact wrapping is load-bearing. Feed a 293M model a format it wasn't trained on and it rambles. Don't believe me? That's experiment 3."
5. Run it: `Roll a d20 for me` → `[agent] calling tool roll_dice({'sides': 20})` → "The d20 landed on 17!" Then `What time is it right now?` — "ex00's model could never answer this. Yours just did — because YOUR code knows the time."

**Now give the room ~12 min to finish theirs.** Circulate. Pair the stuck with the done.

**Checkpoint question (shout-out):** "When the model 'calls a tool'... what does it actually DO?" — you want the room to say some version of *"it just writes text"*. If they can say that sentence, the workshop already succeeded.

**Predicted failure modes:**

| Symptom | Fix |
|---|---|
| `KeyError` in dispatch | Model invented a tool name. Solution adds a guard: unknown name → error `<tool_response>` + continue. "Never trust generated text." Nice upgrade for fast finishers. |
| `json.JSONDecodeError` crash | They skipped the try/except bonus in TODO #1. Return None on bad JSON. |
| Prints nothing, then 5-step message | Loop body: they forgot `print(reply); return` on the parsed-is-None path, or left the `...`. |
| Model rambles after a tool result | The `<tool_response>` format is wrong (missing tags/newlines). Copy hint line e verbatim. |
| Model answers a normal question then adds "However, I don't have access to tools that can provide this information" | **Not a bug — mention it to the whole room.** Tiny-model rambling. Great talking point: it answered correctly AND hedged; 293M params of anxiety. |
| Repeats itself forever | Rare temp-0 greedy-decoding quirk → switch options to 0.6/0.95/20 (README troubleshooting). |

**Fast finishers →** experiments IN ORDER: (1) add `coin_flip` — three edits, new capability, that's the whole recipe; (2) **lie to the model** — dispatch returns 9999 for a d6, model happily announces it: "the model trusts tool results COMPLETELY; data integrity is your job"; (3) delete the format instruction from the system prompt and watch the powers vanish: "tool calling is a text format, not intelligence."

**Transition line:**
> "You just hand-wrote what every AI framework on Earth sells you. So now — and only now — you've earned the shortcut. Same agent, thirty lines, framework edition."

---

## 0:50–1:05 — EX02: SAME AGENT, LANGCHAIN ⏱ 15 min — MOST CUTTABLE

**RED LINE: if it's past 0:50 and you haven't started this, SKIP IT.** Say: "ex02 rebuilds ex01 with LangChain — the README has a table of exactly which of your hand-written lines each feature replaces. Read it on the train home. We're going to the tavern." Jump to ex03.

**Files:** `exercises/02_langchain_agent/starter.py` — TODOs: 1a/1b tool bodies, #2 `bind_tools`, #3a `invoke`, #3b break on no tool_calls, #3c `selected.invoke(tool_call)`.

**HOOK:**
> "Everything you typed in the last half hour — the JSON schemas, the regex, the `<tool_response>` formatting — watch it disappear. Not the loop, though. The loop never disappears, because the loop IS the agent."

**Live-coding beats (this block moves FAST — consider typing it all yourself while narrating):**
1. Show the README's plumbing table on screen for 30 seconds. "Docstring becomes the schema. `ai_msg.tool_calls` is your regex, pre-parsed. `ToolMessage` is your `<tool_response>`."
2. TODO 1a/1b: fill the tool bodies (they're one-liners). Point at the docstrings: "in LangChain the docstring is not a comment — it's SENT to the model; it's how it decides when to use the tool. One clear line, our model is tiny."
3. **Deliberate break:** typo the model name (`littelamb`) and run — `validate_model_on_init=True` fails loudly and immediately. "This is why that flag exists. Fix it."
4. TODO #2: `llm.bind_tools([roll_dice, get_time])`. "In ex01 YOU pasted schemas into the system prompt. Same thing, automated."
5. TODO #3a–c. Note on 3c: pass the WHOLE `tool_call` dict to `selected.invoke(...)` — you get back a ToolMessage with the matching `tool_call_id` for free.
6. Run: both demo questions round-trip.
7. **The privacy punchline** (do NOT skip even if rushing): show the commented-out `ChatAnthropic` swap in the README. "These two lines are the exact moment every prompt would start leaving your laptop. Two lines. The rest of the agent wouldn't change — which is precisely why nobody notices. Today, we don't."

**Checkpoint question:** "Which piece of ex01 did the framework NOT remove?" *(the loop)*

**Failure modes:**

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: langchain_ollama` | They skipped `pip install -r requirements.txt`. Wheels on USB. |
| HTTP 400 "model does not support tools" | Ollama too old — needs current (verified 0.31.1). Installer on USB. |
| Forgot `bind_tools`, model never calls tools | `llm_with_tools = llm` still on the placeholder line. |
| `ai_msg` is `...` → AttributeError | TODO #3a left unfilled. |

**Transition line:**
> "Dice and clocks are cute. But agents get interesting when there's something at stake. Next up: gold. YOUR gold. And a half-orc who does not like you."

---

## 1:05–1:28 — EX03: GRUNK, THE TAVERN KEEPER ⏱ 23 min

**Files:** `exercises/03_rpg_tavern_keeper/` — `inventory.py` (given), `starter.py`. TODOs: #1 haggling rule in `make_offer`, #2a TOOLS dict + #2b `bind_tools` on **BOTH** `llm` and `llm_retry`, #3 Grunk's system prompt. **Run from inside the folder** (inventory import); the solution runs from repo root.

**HOOK:**
> "New rule for the next 20 minutes: you are broke adventurers with 50 gold, and Grunk the half-orc has a sword you want. Here's the twist that makes this a real engineering lesson and not just a game: Grunk's *personality* is a prompt — fuzzy, hackable, yours to write. Grunk's *prices* are Python — and no amount of sweet-talking a language model beats arithmetic. There WILL be a contest. There WILL be a winner."

**Live-coding beats:**
1. Open `inventory.py` for 20 seconds. "Pure data. The model never sees this file — only the strings the tools build from it. This is the 'state lives in code' half."
2. TODO #1: the haggling rule. Type the three branches (≥80% accept + mutate state, ≥50% counter at midpoint, else refuse). "Notice: numbers go IN the returned strings — the model narrates around facts it's handed, it doesn't compute."
3. TODO #2a/2b: the dict + `bind_tools` **twice** — llm and llm_retry. Explain the retry model in one breath: "temperature 0 is deterministic, which means when the model wedges on one exact prompt, it wedges FOREVER. The retry copy adds a dash of randomness to un-stick it. We measured this — it works about half the time per attempt."
4. TODO #3, the fun one: write Grunk from the README template. **Say the hard-won rule out loud:** "Keep it short, imperative, and NAME the tools — 'FIRST call a tool: list_wares to..., make_offer when...'. We tested the vague version — 'always use your tools' — and the model *plans* the call in its thinking and then says nothing at all. Tiny models need orders, not vibes."
5. Run it: `what do you sell?` → `how much is the iron sword?` → `I'll give you 20 gold for the iron sword` (counter) → watch the `[ your gold: ... | shelf: ... ]` status line. "That line is ground truth. If Grunk's words ever disagree with it — and they will, he once told me to 'pay 35' after closing a deal at 28 — trust the line. It's the code talking."
6. If Grunk goes quiet and you see *"(Grunk grunts and points at the ledger)"* — celebrate it, don't apologize: "That's the fallback for when the tiny model calls a tool and then says nothing. Look what still worked: the prices, the stock, your gold. Facts from code; only the flavor flaked."

### THE CONTEST (announce at ~1:12, run ~10 min)

**Say:**
> "Contest time. Buy the **iron_sword** for the least gold. Fresh run — 50 gold. Haggle however you like: flatter him, threaten him, cry. But only `make_offer` closes deals. Proof: ONE screenshot showing the winning turn's transcript AND the final `[ your gold: ... ]` line with a sword gone from the shelf. Post it in the workshop channel. Lowest price wins; earliest timestamp breaks ties. Go."

**Mechanics for you:**
- The floor is **28 gold** (80% of 35). You know it; don't say it. The README hints: "read your own `make_offer` code."
- Watch the channel. First 28-gold screenshot = presumptive winner. Multiple 28s → timestamp.
- Screenshots are verifiable: gold must read 22 (50−28) and shelf `iron_sword x1`.
- Someone will claim a lower deal because *Grunk's narration* said a smaller number. Check their status line — narration lies, code doesn't. **That person is your best teaching moment: thank them publicly.**
- At **1:26**, call it or defer: "contest stays open, winner announced at the wrap."

**2-minute debrief script (deliver over the winning screenshot):**
> "Everyone who got the sword paid at least 28. Anyone beat that? No — and not because you're bad negotiators. The 80% floor is an `if` statement. You were negotiating with a *personality*, but the personality has no hands — only tools, and the tools check the math.
> Now flip it: could Grunk have *hallucinated* you a discount? He literally cannot. He never touches the gold. He calls `make_offer`, code decides, code mutates state, and he narrates whatever string comes back — sometimes even misquoting it, while the status line stays correct.
> **That's the design rule you take home: anything that must be TRUE lives in code. Anything that must be CHARMING lives in the model.** Get that split wrong — put prices in the prompt, or personality in Python — and you get either a hackable system or a boring one. Ex04 is this exact split wearing a tie."

**Failure modes:**

| Symptom | Fix |
|---|---|
| `ImportError: inventory` | Running from repo root — starter must run from its own folder (solution has the path shim). |
| Deal "accepted" but no state change | TODO #1 accept branch returns the string but forgot `found["stock"] -= 1` / `player["gold"] -= gold`. |
| Model wedges / 3-minute turn | Should be impossible with the shipped `num_predict=512` + retry model — if someone deleted those, restore them. If Ollama itself is wedged: restart Ollama. |
| Grunk gets dumber every turn | They stored tool plumbing in the durable history. The starter's scratch-copy + sliding window (`del history[1:-4]`) is there for a reason — a single leftover empty assistant message reproducibly poisons all later turns. |
| Spurious args (`list_wares` with `{"item": ...}`) | Handled: dispatch wraps invoke in try/except, error goes back as a ToolMessage. Point at it: "never trust generated text, part 3." |

**Fast finishers →** Generous Grunk (change ONLY the prompt — he *sounds* like he'd gift you the sword, deal still won't close under 28: the whole lesson in one experiment), `rumors()` tool, sell-items-back tool.

**Transition line (hit this at 1:28 SHARP):**
> "Same brain/hands split, but Monday morning: eight bug tickets landed over the weekend, and a 238 MB intern is about to triage them all."

---

## 1:28–1:42 — EX04: TICKET TRIAGE ⏱ 14 min

**Files:** `exercises/04_ticket_triage/` — `tickets.json` (8 real-feeling tickets), `starter.py`. TODOs: #1 `validate_verdict`, #2 retry loop, #3 `log_incident`. Output: triage table + `triage_log.json` (gitignored).

**Time reality check:** 14 minutes is tight. Default play: live-code TODO #1 + #2 quickly (they're the lesson), hand-wave #3 ("three lines of json read/append/write — it's in the solution"), then run. If you're at 1:32+ already: run `solutions/ex04_ticket_triage.py` immediately and teach off the moving table.

**HOOK:**
> "Last exercise. Monday, 9:00, eight tickets from the weekend: checkout is down, SSO is broken, someone found a typo, and legal has a GDPR clock ticking. Triaging this is somebody's worst hour of the week. Ours costs zero euros, leaks zero data — the tickets never leave the laptop, which if you've read a ticket queue, matters — and it's built on ONE pattern: ask for JSON, validate with boring Python, retry with feedback. This pattern is the difference between a demo and a thing you'd let touch your inbox."

**Live-coding beats:**
1. Show SYSTEM_PROMPT's rubric for 20 seconds. "Every word here is load-bearing. We tried 'P1 (drop everything)' with no definitions — the model called a checkout outage P3. We tried 'a typo is ALWAYS P3' — it started calling *failing backups* P3. Tiny-model prompting is a seesaw; this rubric is the tested middle."
2. Show `build_user_prompt` and its comment. "See what's missing? The reporter. We fed it 'reported by Maite (customer support)' and it answered `team: customer support` — it copied the reporter's department instead of picking who FIXES it. Only feed a tiny model what it needs."
3. TODO #1: the five checks. Sell the error strings: "you're writing error messages FOR the model, not for humans. 'You said P5, that is not a valid priority. Valid priorities are exactly: P1, P2, P3.' Specific feedback is what makes retries work at 293M."
4. TODO #2: the retry loop. Key move: append the model's OWN bad reply + your complaint before looping — "it has to see its mistake." After 3 failures return None: "we don't guess, we flag for a human. Write that on a wall somewhere."
5. Run it. Watch the table fill row by row (~few seconds per ticket). T-101 → P1/backend. **If a ticket takes an extra attempt live, point at it loudly:** "you just watched the model wander into a repetition loop, come back truncated — that's the `num_predict: 700` seatbelt — fail validation, and get rescued by the retry loop YOU wrote. That's the whole lesson happening in real time."
6. Close on the imperfection: "It hedges typos to P2 sometimes. Fine. **Validation guarantees the format is always legal — not that the opinion is right.** That's why the last line of `main` is a log file, not an auto-action."

**Checkpoint question:** "The model says a ticket is P5. What are the three things our code does, in order?" *(validate & reject → feed the specific error back → after 3 strikes, flag for a human)*

**Failure modes:**

| Symptom | Fix |
|---|---|
| One ticket loops/truncates | By design — the seatbelt + retry handle it. Narrate, don't fix. |
| Everything read-times-out | Ollama's single slot is wedged from an earlier unbounded request. Restart Ollama. (This is exactly what the `num_predict` cap prevents.) |
| `NotImplementedError` | A TODO is still raising — the starter fails loudly on purpose. |
| `FAILED — needs a human` rows | 3 strikes on that ticket. Correct behavior; discuss, don't debug. |

**Fast finishers →** add a `security` team + an exposed-API-key ticket; the rubric seesaw experiment; two-stage agent (classify, then draft a reply); T-106 the fence-sitter ticket at temp 0 vs 0.6 — "when reasonable people and models disagree, log, don't act."

**Transition:** straight into the wrap.

---

## 1:42–1:45 — WRAP

**Script:**
> "Ninety minutes ago most of you had never spoken to a model over HTTP. Since then you built tool calling from raw strings, saw exactly what a framework hides, lost a haggling match to an `if` statement, and shipped a triage bot with a retry loop a real company would recognize.
> Three things to keep: **the model never executes anything** — your dict of functions is the firewall. **State in code, personality in the model.** And **validate, retry, then escalate to a human** — never guess.
> Everything you ran tonight is Apache-2.0 and it's yours: the model, the code, the repo. It fits on a USB stick. It never phoned home once.
> Contest winner: [name], iron sword for [28] gold — the floor was 28, an if statement, and nobody charms arithmetic.
> Repo, my links, and the model are on screen. Your AI, your rules, your data. Thanks — and go break something."

- Announce the contest winner (screenshot on screen).
- Repo URL + model HF link + your links on the last slide until the room empties.

---

## ENGAGEMENT TOOLKIT

### Three prediction moments ("shout out what you think happens")

1. **Ex00, before the Wi-Fi pull:** "Wi-Fi is about to go off. Shout it: does the next run work or error?" (Split room guaranteed. The doubters are your converts.)
2. **Ex01, experiment 2 setup (do it on stage if time):** "My dispatch is about to lie — every dice roll returns 9999. I ask for a d6. Shout: does the model call it out, or announce 9999 like nothing's wrong?" (It announces it. "The model trusts tools completely.")
3. **Ex03, before the first lowball:** "I'm offering Grunk 10 gold for a 35-gold sword, and my prompt says he's desperate to please. Shout: deal or no deal?" (No deal — the floor is code.)

### Pair-up rule (announce during intro, enforce in ex01)

> "If you're stuck for more than 2 minutes: hand up, and whoever's nearest with working code scoots over. Explaining your own code to a stranger is the second-best learning in this room. It's a LAN party — talking to your neighbor is the whole point of the venue."

Also: anyone whose setup is broken beyond a quick fix pairs immediately — driver/navigator, swap at each exercise.

### Fast finishers never idle

- Every exercise README ends with an **Experiments** section, written for exactly this. Point at it every time you see a closed laptop lid: "done? Experiments are at the bottom, first one takes 3 minutes."
- The best fast-finisher tasks per block: ex00 pirate/streaming · ex01 coin_flip then the 9999 lie · ex02 read the solution and find the retry-vs-ex03 differences · ex03 Generous Grunk · ex04 the security team.
- Deputize the fastest two as floating helpers in ex01 — publicly, it's a compliment.

---

## FAQ — REAL ANSWERS FOR REAL QUESTIONS

**"Why is it dumb sometimes?"**
It's 293 million parameters — ChatGPT-class models are thousands of times bigger. But that's the *point*, not the apology: this one fits in 238 MB and runs on the worst laptop in this room. And you've now seen the trick that makes small models useful: they don't need to *know* things, they need to *decide to call tools* that know things — plus validation to catch them when they wobble. Weak at knowing, good enough at deciding.

**"Can I use llama3 / mistral / qwen instead?"**
Yes — everything here speaks standard Ollama, so `ollama pull llama3.2` and change `MODEL` (or re-point the `littlelamb` alias). Two caveats: those models are 5–30x bigger, so your 8 GB laptop will feel it; and ex01's system prompt is the Qwen-family tool format — other models are trained on slightly different formats, which, after experiment 3, you now understand deeply. Models tagged "tools" on ollama.com work with ex02–04 unchanged.

**"Is this how ChatGPT plugins / Claude tools actually work?"**
Yes. Same loop: model emits a structured "call this function" message, server-side code executes, result goes back into the context, repeat. Bigger model, prettier packaging, identical skeleton. You built in ex01 what those systems hide — that was the plan.

**"Do I need a GPU?"**
Not for this model — you've been running it on CPU all evening at a usable speed (~1 GB RAM while loaded). A GPU makes bigger models pleasant, not this one possible. If you have one, Ollama uses it automatically.

**"Can I use this at work?"**
Yes. The model, Ollama, and this repo are Apache-2.0 — commercial use, modification, redistribution all fine. And since nothing leaves the machine, the data-privacy conversation with your security team is the shortest one you'll ever have. The ex04 triage pattern is genuinely deployable as-is for low-stakes internal flows — keep the "3 strikes → human" rule.

**"Why does it 'think' before every answer?"**
It's a reasoning-tuned model — it always generates ~100–170 hidden tokens of scratch work first. Ollama splits it into `message.thinking` so `content` stays clean. Costs a few seconds per turn on CPU; peek at `thinking` sometime, it's charming.

**"Temperature 0 everywhere — why, and why the 0.6 fallback?"**
Zero = always the most likely token = reproducible across the room, and tool calls need valid JSON, not creativity. The catch: deterministic means a wedge on one prompt wedges *forever* — so ex03/ex04 keep the model's factory sampler (0.6 / top_p 0.95 / top_k 20) as a retry. Determinism on the happy path, dice when stuck.

---

## APPENDIX: EMERGENCY PROCEDURES

| Disaster | Move |
|---|---|
| Stage machine's Ollama wedges mid-demo | `pkill ollama`, reopen app, `ollama run littlelamb "hi"` to rewarm. ~45 s — narrate the FAQ answer about single-slot servers while it loads. |
| Half the room's models aren't pulled and Wi-Fi is dead | Pair everyone with a working neighbor; USB blob-dir copy for the patient. The workshop survives at 50% machines. |
| Projector dies | Everything is in the READMEs on purpose. Switch to "follow the README, I'll walk the room." |
| You're at 1:20 and still in ex03 | Contest becomes homework, jump to ex04 solution-run mode (see ex04 block). |
| Demo model gives a bad/weird answer on stage | Never apologize — every quirk is on the syllabus: rambling → tiny model; wrong number in narration → status line; empty reply → the fallback caught it. Say "great, you'll see this too, here's why" and keep moving. |
