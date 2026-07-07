"""
SOLUTION — Exercise 00: Hello, local LLM!

The whole "AI" part of this workshop is just this: an HTTP POST to a server
running on YOUR machine. Ollama listens on localhost:11434 and speaks JSON.

Flow:
  1. Build a JSON payload: which model + the conversation so far ("messages").
  2. POST it to http://localhost:11434/api/chat
  3. Read the reply text out of the JSON response.

Run:
  Windows:      python ex00_hello_local_llm.py
  macOS/Linux:  python3 ex00_hello_local_llm.py
"""

import requests

# Ollama's chat endpoint. This URL never changes — it's your own machine.
OLLAMA_URL = "http://localhost:11434/api/chat"

# TODO(you) #1 — solved: the short alias we created during setup with
#   ollama cp hf.co/mradermacher/LittleLamb-ToolCalling-GGUF:Q4_K_M littlelamb
MODEL = "littlelamb"

# TODO(you) #2 — solved: a conversation is a list of {"role", "content"}
# dicts. The system message sets the rules; the user message is the question.
messages = [
    {"role": "system", "content": "You are a helpful assistant. Answer briefly."},
    {"role": "user", "content": "What is the capital of France?"},
]

payload = {
    "model": MODEL,
    "messages": messages,
    # stream=False means: wait and send me ONE complete JSON response.
    "stream": False,
    # temperature 0 = always pick the most likely next token. For a tiny
    # 293M model this keeps answers stable and reproducible across the room.
    "options": {"temperature": 0},
}

print(f"[you -> {MODEL}] sending request... (first run loads the model, be patient)")
response = requests.post(OLLAMA_URL, json=payload, timeout=300)
response.raise_for_status()  # crash loudly if Ollama returned an error
data = response.json()

# TODO(you) #3 — solved: the reply text lives at data["message"]["content"].
#
# Tricky detail: this model ALWAYS "thinks" before answering (~100 tokens).
# Ollama separates that into data["message"]["thinking"], so "content" stays
# clean. Do NOT try to disable thinking with "think": false — with this
# model's template that leaks the reasoning (plus a stray </think>) into
# content. Just leave thinking on and ignore it.
reply = data["message"]["content"]

print()
print(reply)


# ---------------------------------------------------------------------------
# BONUS — solved: streaming, ChatGPT-style.
#
# With "stream": True, Ollama sends one small JSON object PER LINE (NDJSON:
# newline-delimited JSON) instead of a single response, so we parse the body
# line by line as it arrives. Note the silent pause before text appears —
# those first chunks are the model thinking (they fill "thinking", not
# "content", so we print nothing for them).
# ---------------------------------------------------------------------------
import json  # noqa: E402  (kept here so the bonus is self-contained)

print("\n--- bonus: same question, streamed ---")
stream_payload = dict(payload, stream=True)

# stream=True on the requests side too, so we can read line by line.
response = requests.post(OLLAMA_URL, json=stream_payload, stream=True, timeout=300)
response.raise_for_status()

for line in response.iter_lines():
    if not line:
        continue  # skip keep-alive blank lines
    chunk = json.loads(line)  # one line = one small piece of the reply
    # .get() with defaults: the final chunk has no "message" text, just stats.
    print(chunk.get("message", {}).get("content", ""), end="", flush=True)
print()
