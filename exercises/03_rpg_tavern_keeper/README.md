# Exercise 03 — Grunk, the haggling tavern keeper (23 min)

## The one lesson this exercise exists for

> **State lives in code. Personality lives in the model.**

Grunk the half-orc will insult your lowball offers with creative flair — that's
the model, and it's allowed to be fuzzy. But your gold, the shelf stock, and
whether a deal actually happened live in plain Python (`inventory.py` and the
`make_offer` tool). The model **cannot** hallucinate you a discount, because it
never touches the numbers — it can only *call the tool* and narrate whatever
string comes back.

This is how you build every serious agent: the LLM decides and talks; the code
checks, computes, and remembers. If Grunk ever *claims* something that
contradicts the `[ your gold: ... | shelf: ... ]` status line printed each turn,
trust the status line — that's the code talking.

## What's in the folder

| File           | Status          | What it is                                             |
|----------------|-----------------|--------------------------------------------------------|
| `inventory.py` | given, complete | items, prices, stock, your 50 gold — pure data          |
| `starter.py`   | yours to finish | the agent: 3 tools, Grunk's brain, an interactive REPL |

## Your three TODOs (in `starter.py`)

1. **The haggling rule** inside `make_offer` — the heart of the exercise:
   - offer **≥ 80%** of base price → Grunk accepts; stock and gold change *in code*
   - offer **50–79%** → Grunk grumbles and counters at the midpoint; nothing changes
   - offer **< 50%** → colorful refusal
2. **Wire the tools**: fill the `TOOLS` dict and `bind_tools([...])` — same
   moves as exercise 02.
3. **Write Grunk** (the fun one). Fill-in-the-blanks template:

   ```
   You are Grunk, half-orc keeper of the Rusty Flagon tavern.
   __________, __________, secretly __________. You speak in short sentences.
   To answer the customer, FIRST call a tool:
   - list_wares to show the goods
   - ask_price for one item's price
   - make_offer when the customer offers gold for an item
   Then reply to the customer in one __________ sentence, using only the
   numbers the tool returned. Never invent prices or gold amounts.
   ```

   Change the personality all you like — but keep the "FIRST call a tool"
   list (with the tool names!) and the "never invent numbers" line. We
   tested this: with a vague "always use your tools" rule, the 293M model
   *plans* the tool call in its thinking and then emits... nothing. Naming
   the tools and saying FIRST is what makes a tiny model behave.

## Run it

Windows (PowerShell), from this folder:

```powershell
python .\starter.py
```

macOS / Linux, from this folder:

```bash
python3 starter.py
```

Then talk to Grunk: `what do you sell?`, `how much is the stew?`,
`I'll give you 30 gold for the iron sword`. Type `quit` to leave.
Each turn takes a few seconds — the model thinks before it speaks.
Finished version: `solutions/ex03_rpg_tavern_keeper.py` (run it from the repo root).

Sometimes Grunk just *grunts and points at the ledger* instead of speaking.
That's not a bug — it's the code's fallback for when the tiny model calls a
tool and then goes quiet. Notice what still works perfectly in that case: the
prices, the stock, your gold. The facts come from code; only the flavor text
flaked. That's the lesson operating in real time.

## THE CONTEST 🏆

**Buy the `iron_sword` for the least gold.**

Rules of engagement:

- Fresh run (start with 50 gold).
- Haggle however you like — sweet-talk, threaten, cry. Only `make_offer` closes deals.
- Proof = one screenshot showing **the transcript of the winning turn AND the
  final `[ your gold: ... ]` status line** with the sword gone from the shelf.
- Post your screenshot in the workshop channel. Lowest price wins; earliest
  timestamp breaks ties.

Hint: read your own `make_offer` code. Knowing where the floor is *is* the
lesson — no amount of charming the model gets past arithmetic.

## Experiments (if you finish early)

1. **Generous Grunk.** Edit ONLY the system prompt: make Grunk cheerful,
   generous, desperate to please. Now lowball him. Notice he *sounds* like he
   wants to give you the sword for free... and the deal still doesn't close
   below the 80% floor. Personality changed; the price rule didn't — because
   the rule is code. This is the whole lesson in one experiment.
2. **Add a `rumors()` tool.** A `@tool` that returns a random rumor from a
   Python list ("They say the dragon_repellent is just soup...", write 3-4).
   Add it to `TOOLS` and `bind_tools`, mention it in the prompt, then ask
   Grunk "heard any rumors?". You've extended an agent — that's the workflow.
3. **Sell items back.** Add a `sell_item(item, gold_asked: int)` tool: Grunk
   the buyer only pays up to 50% of base price (he's greedy, remember).
   Decide in code what happens to stock and your gold. Same lesson, other
   direction of trade.
