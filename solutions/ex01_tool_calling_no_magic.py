"""
SOLUTION — Exercise 01: Tool calling with NO magic.

What happens on every turn, in 5 steps:

  1. We send the model a system prompt that lists our tools and the exact
     text format to use when it wants one, plus the user's question.
  2. The model replies with TEXT. If it wants a tool, that text contains
     <tool_call>{"name": "...", "arguments": {...}}</tool_call>.
  3. OUR Python parses that text and runs the real function. The model
     never executes anything — it only writes; our code has the hands.
  4. We append the function's result to the conversation, wrapped in
     <tool_response>...</tool_response> (the format the model was trained
     to recognize), and go back to step 2.
  5. When the reply contains no tool call, it's the final answer: print it.
     A max of 5 laps protects us if the tiny model gets stuck in a loop.

Note: Ollama can do all of this natively (pass "tools" to /api/chat and it
injects the prompt block and parses the reply for you) — exercise 02 uses
that path. We build it by hand ONCE so it is never magic again.

Run:
  Windows:      python ex01_tool_calling_no_magic.py
  macOS/Linux:  python3 ex01_tool_calling_no_magic.py
"""

import datetime
import json
import random
import re

import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "littlelamb"  # alias created during setup with `ollama cp`

# How many model round-trips we allow per question. Tiny models can get
# stuck calling tools forever; a guard rail beats an infinite loop.
MAX_STEPS = 5


# ---------------------------------------------------------------------------
# The tools: plain Python functions. Nothing special about them.
# ---------------------------------------------------------------------------

def roll_dice(sides: int) -> int:
    """Roll a die with the given number of sides. Returns 1..sides."""
    return random.randint(1, sides)


def get_time() -> str:
    """Return the current local time, e.g. '2026-07-25 17:03'."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


# name -> function. This dict is the ONLY bridge between the model's words
# and real code. If a name isn't in here, nothing runs. That's your safety.
TOOLS = {
    "roll_dice": roll_dice,
    "get_time": get_time,
}


# ---------------------------------------------------------------------------
# The system prompt.
#
# This is the exact format LittleLamb (base: Qwen3) was TRAINED on:
#   - tool definitions as JSON inside <tools></tools> XML tags
#   - the instruction to answer with JSON inside <tool_call></tool_call> tags
# Don't paraphrase it. A 293M-parameter model has zero tolerance for
# improvised formats. (This block is also exactly what Ollama generates
# internally when you use the native "tools" parameter.)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a helpful assistant.

# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
{"type": "function", "function": {"name": "roll_dice", "description": "Roll a die with the given number of sides and return the result.", "parameters": {"type": "object", "properties": {"sides": {"type": "integer", "description": "Number of sides on the die, e.g. 6 or 20."}}, "required": ["sides"]}}}
{"type": "function", "function": {"name": "get_time", "description": "Get the current local date and time.", "parameters": {"type": "object", "properties": {}, "required": []}}}
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{"name": <function-name>, "arguments": <args-json-object>}
</tool_call>"""


def chat(messages: list) -> str:
    """Send the conversation to Ollama, return the model's reply text.

    Same HTTP call as exercise 00. We deliberately do NOT use Ollama's
    native "tools" parameter — today we do the plumbing ourselves.
    """
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        # temperature 0: tiny model + tool calls must be deterministic —
        # we need valid JSON, not creativity. (If your machine ever gets
        # stuck repeating itself, the fallback is temperature 0.6.)
        "options": {"temperature": 0},
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=300)
    response.raise_for_status()
    # The model always "thinks" first; Ollama puts that in
    # message["thinking"] and keeps message["content"] clean. We only
    # want content — the <tool_call> tags (if any) appear right there.
    return response.json()["message"]["content"]


def parse_tool_call(text: str):
    """If `text` contains a tool call, return (name, args). Otherwise None."""
    # TODO(you) #1 — solved.
    # re.DOTALL makes .*? match across the newlines inside the tags, and
    # the lazy .*? stops at the FIRST </tool_call> — so surrounding prose
    # (before or after the tags) is simply ignored.
    match = re.search(r"<tool_call>(.*?)</tool_call>", text, re.DOTALL)
    if match is None:
        return None  # no tags anywhere -> it's a normal answer

    try:
        call = json.loads(match.group(1))
    except ValueError:
        # Tags were there but the JSON inside is broken (tiny models do
        # this occasionally). Treating it as a normal answer is the safest
        # move — the user sees the raw text instead of a crash.
        return None

    # .get() instead of [] so a malformed-but-valid-JSON payload (e.g.
    # missing "arguments") still gives us something callable-ish.
    return call["name"], call.get("arguments", {})


def run_agent(user_input: str) -> None:
    """The agent loop: model -> (tool -> model)* -> final answer."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]

    for _step in range(MAX_STEPS):
        reply = chat(messages)
        parsed = parse_tool_call(reply)

        # TODO(you) #2 + #3 — solved.
        if parsed is None:
            # No tool call -> this is the final, human-readable answer.
            print(reply)
            return

        name, args = parsed

        # Guard: the model can only invent names that exist in OUR dict.
        # (Rare with temperature 0, but never trust generated text blindly.)
        if name not in TOOLS:
            messages.append({"role": "assistant", "content": reply})
            messages.append({
                "role": "user",
                "content": f"<tool_response>\nError: unknown tool '{name}'\n</tool_response>",
            })
            continue

        print(f"[agent] calling tool {name}({args})")

        # THE DISPATCH — this line is the entire "agent" magic. **args
        # unpacks {"sides": 20} into sides=20. The model chose the name and
        # args by writing text; THIS line does the doing.
        result = TOOLS[name](**args)

        # Keep the model's tool request in the history so it remembers
        # what it asked for...
        messages.append({"role": "assistant", "content": reply})

        # ...and send the result back in the EXACT trained format: a
        # user-role message wrapped in <tool_response> tags, with real
        # newlines around the payload. This mirrors what Ollama's template
        # does for role:"tool" messages in native mode. Get it wrong and
        # the 293M model rambles instead of answering.
        messages.append({
            "role": "user",
            "content": f"<tool_response>\n{json.dumps(result)}\n</tool_response>",
        })
        # The for-loop now sends the updated conversation back to the model.

    print("[agent] hit the 5-step limit — tiny model got stuck. Try rephrasing.")


if __name__ == "__main__":
    print("Local agent ready. Try: 'Roll a d20 for me' or 'What time is it?'")
    print("(empty line or 'quit' to exit)\n")
    while True:
        question = input("You: ").strip()
        if question in ("", "quit", "exit"):
            break
        run_agent(question)
        print()
