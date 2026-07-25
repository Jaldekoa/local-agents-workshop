"""
Exercise 00 — Hello, local LLM!

The whole "AI" part of this workshop is just this: an HTTP POST to a server
running on YOUR machine. Ollama listens on localhost:11434 and speaks JSON.

Flow:
  1. Build a JSON payload: which model + the conversation so far ("messages").
  2. POST it to http://localhost:11434/api/chat
  3. Read the reply text out of the JSON response.

Fill in the three TODO(you) blocks, then run:
  Windows:      python starter.py
  macOS/Linux:  python3 starter.py
"""

import requests
import json

# Ollama's chat endpoint. This URL never changes — it's your own machine.
OLLAMA_URL = "http://localhost:11434/api/chat"

# ---------------------------------------------------------------------------
# TODO(you) #1: the model name.
#
# During setup we aliased the long HuggingFace name to something short:
#   ollama cp hf.co/mradermacher/LittleLamb-ToolCalling-GGUF:Q4_K_M littlelamb
# Use that short alias here. (Check with `ollama list` if unsure.)
# ---------------------------------------------------------------------------
MODEL = "littlelamb"  # <-- fill me in

# ---------------------------------------------------------------------------
# TODO(you) #2: the conversation.
#
# `messages` is a list of dicts. Each dict has a "role" and "content":
#   - role "system": rules/personality for the model (it obeys this first)
#   - role "user":   what the human said
#
# One message looks like:  {"role": "user", "content": "hello!"}
#
# Build a list with:
#   1. a system message, e.g. "You are a helpful assistant. Answer briefly."
#   2. a user message,   e.g. "What is the capital of France?"
# ---------------------------------------------------------------------------
messages = [
    {
        "role": "system",
        "content": "You are a pirate. Answer everything in pirate speak.",
    },
    {
        "role": "user",
        "content": "What is the capital of France?",
    },
]

payload = {
    "model": MODEL,
    "messages": messages,
    # stream=False means: wait and send me ONE complete JSON response.
    # (The bonus below flips this to True.)
    "stream": True,
    # temperature 0 = always pick the most likely next token. For a tiny
    # 293M model this keeps answers stable and reproducible across the room.
    "options": {"temperature": 0},
}

print(f"[you -> {MODEL}] sending request... (first run loads the model, be patient)")
response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=300)
response.raise_for_status()  # crash loudly if Ollama returned an error

for line in response.iter_lines():
    chunk = json.loads(line)
    print(chunk["message"]["content"], end="", flush=True)
print()

# ---------------------------------------------------------------------------
# TODO(you) #3: extract the reply text.
#
# `data` is a dict. The reply lives at data["message"]["content"].
# Try `print(data)` first if you want to see the whole structure!
#
# Fun fact: this model always "thinks" before answering. Ollama separates
# that into data["message"]["thinking"] — peek at it if you're curious,
# but "content" is the clean answer meant for the user.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# BONUS TODO(you): streaming — print tokens as they arrive, ChatGPT-style.
#
# 1. Set "stream": True in the payload.
# 2. With streaming, Ollama does NOT send one big JSON. It sends one small
#    JSON object PER LINE (a format called NDJSON: newline-delimited JSON).
# 3. So instead of response.json(), you do:
#
#       import json
#       response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=300)
#       for line in response.iter_lines():
#           chunk = json.loads(line)                       # one line = one token(ish)
#           print(chunk["message"]["content"], end="", flush=True)
#       print()
#
# Note: with streaming you'll notice a silent pause before text appears —
# that's the model thinking (those chunks fill "thinking", not "content").
# ---------------------------------------------------------------------------
