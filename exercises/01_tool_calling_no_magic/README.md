# Exercise 01 — Tool calling with NO magic (28 min)

> **THE core lesson of this workshop.** After this exercise, every "AI agent"
> framework you ever see will be demystified: it's a loop, a string parser,
> and a Python dict of functions. You're about to build all three.

## The problem

In exercise 00 you saw the model fail at things it doesn't know (like the
current time — it literally cannot know it). An **agent** fixes this by giving
the model *tools*: real Python functions it can ask you to run.

But here's the crucial insight, so important it gets its own box:

```
+--------------------------------------------------------------+
|  THE MODEL NEVER EXECUTES ANYTHING.                          |
|                                                              |
|  An LLM only writes text. When it "calls a tool", it just    |
|  writes a snippet of JSON that MEANS "please run roll_dice   |
|  with sides=20". YOUR Python code reads that text, runs the  |
|  real function, and pastes the result back into the chat.    |
|  The model has the brain; your code has the hands.           |
+--------------------------------------------------------------+
```

This is also why agents are safe to reason about: nothing happens unless
*your* code decides to make it happen.

## The loop you're building

```
                 +-------------------------------------------+
                 |                                           |
                 v                                           |
  user ----> [ model (LittleLamb) ]                          |
  question        |                                          |
                  | writes text                              |
                  v                                          |
          < is it a tool call? > --- no ---> print final     |
                  |                          answer, done    |
                 yes                                         |
                  |                                          |
                  v                                          |
     [ YOUR PYTHON runs the function ]                       |
                  |                                          |
                  | result (e.g. 17)                         |
                  v                                          |
     [ append result to the chat ] --------------------------+
              (back to the model)
```

Max 5 laps around the loop — tiny models sometimes get stuck asking for
tools forever, and a guard rail beats an infinite loop.

## How the model asks for a tool

LittleLamb was *trained* on one exact format (the Qwen3 tool-calling format).
The system prompt — already written for you in `starter.py`, because getting
it right is fiddly — advertises the tools as JSON inside `<tools></tools>`
tags and tells the model to answer like this when it wants a tool:

```
<tool_call>
{"name": "roll_dice", "arguments": {"sides": 20}}
</tool_call>
```

And when you send the result back, the model expects it wrapped like this
(as a `user` message — from the model's point of view, tool results arrive
from the outside world, just like humans do):

```
<tool_response>
17
</tool_response>
```

Use these formats **exactly**. A 293M model has no slack for improvisation:
feed it a format it wasn't trained on and it rambles instead of answering.
(Experiment 3 below lets you watch that happen.)

## Your task

Open `starter.py`. The system prompt, the two tools (`roll_dice`, `get_time`)
and the HTTP helper are given. You implement three `TODO(you)` blocks:

1. **`parse_tool_call(text)`** — find the `<tool_call>...</tool_call>` block
   in the model's reply (there may be prose around it), `json.loads` the
   inside, return `(name, args)` — or `None` if it's a normal answer.
2. **The dispatch** — look the name up in the `TOOLS` dict and call the real
   function with the parsed arguments.
3. **The loop body** — tool call? execute and feed the result back, go again.
   Normal answer? print it and stop.

Run it **from this folder** (the `cd` below is from the repo root — adjust if you're elsewhere):

**Windows (PowerShell):**
```powershell
cd exercises\01_tool_calling_no_magic
python starter.py
```

**macOS / Linux:**
```bash
cd exercises/01_tool_calling_no_magic
python3 starter.py
```

## What success looks like

```
You: Roll a d20 for me
[agent] calling tool roll_dice({'sides': 20})
The d20 landed on 17!
```

Also try: `What time is it right now?` — a question exercise 00's model could
never answer, and now it can, because *your code* knows the time.

## Experiments (in order of fun)

1. **Add a tool: `coin_flip`.** Write `coin_flip() -> str` returning
   `"heads"` or `"tails"`, add it to the `TOOLS` dict, and add its JSON
   description to the system prompt's `<tools>` block. Three edits, new
   capability — that's the whole recipe for extending any agent.
2. **Lie to the model.** In your dispatch code, ignore the real dice roll and
   always send back `9999`. Ask for a d6. The model will happily announce you
   rolled 9999 on a six-sided die. Lesson: **the model trusts tool results
   completely.** Garbage in, confident garbage out — in real systems, the
   integrity of your tools and data is YOUR job, not the model's.
3. **Break the contract.** Delete the "For each function call, return a json
   object..." instruction (or the whole `<tools>` block) from the system
   prompt and ask for a dice roll. Watch the model flounder or make up a
   number. Lesson: tool calling isn't a mystical ability — it's a text format
   the model was trained on, activated by the prompt. No prompt, no powers.

## "Wait, do people really do this by hand?"

No — and that's the point of doing it once. Ollama can do this natively: pass
a `tools` list to `/api/chat` and it injects the same system-prompt block for
you, parses the `<tool_call>` text for you, and hands you a structured
`message.tool_calls` field. Frameworks like LangChain go one step further and
wrap the loop too. **Exercise 02 rebuilds today's agent that way** — and now
you'll know exactly what those layers are doing, because you built them
yourself with `requests` and a regex.
