# Exercise 00 — Hello, local LLM! (10 min)

> **The big idea:** an LLM running on your laptop is just a program listening on a
> port. Talking to it is nothing more exotic than an HTTP request to `localhost`.

## What is Ollama, actually?

Ollama is two things:

1. **A model runner** — it loads a model file (ours is ~238 MB) into RAM and does
   the math to generate text, on your CPU. No GPU, no cloud, no account.
2. **A local web server** — it listens on `http://localhost:11434` and exposes a
   tiny REST API. You POST a conversation as JSON, you get the model's reply as JSON.

That's it. There is no magic layer. Every AI app you will build today boils down
to your Python code exchanging JSON with that local server.

Our model is **LittleLamb-ToolCalling** by Multiverse Computing: a 293M-parameter
model (a compressed Qwen3-0.6B, fine-tuned for tool calling). It is tiny on
purpose — it fits in 8 GB of RAM with room to spare and runs at a usable speed
on a CPU.

## Before you start

You did this in the setup step, but double-check:

```
ollama list
```

You should see `littlelamb` in the list. If not:

```
ollama pull hf.co/mradermacher/LittleLamb-ToolCalling-GGUF:Q4_K_M
ollama cp hf.co/mradermacher/LittleLamb-ToolCalling-GGUF:Q4_K_M littlelamb
```

(The `ollama cp` just gives the long name a short alias — same file on disk.)

## Your task

Open `starter.py`. There are three `TODO(you)` blocks:

1. Fill in the model name.
2. Build the `messages` list (a system message + a user message).
3. Extract the reply text from the JSON response.

Then run it **from this folder** (if your terminal is at the repo root, `cd` first):

**Windows (PowerShell):**
```powershell
cd exercises\00_hello_local_llm
python starter.py
```

**macOS / Linux:**
```bash
cd exercises/00_hello_local_llm
python3 starter.py
```

## Expected output

Something like:

```
The capital of France is Paris.
```

Give it a few seconds — this model always "thinks" for ~100 tokens before
answering (Ollama hides the thinking from the reply text, but your CPU still
has to generate it).

## The unplug-the-Wi-Fi moment

Once it works: **turn off your Wi-Fi and run it again.**

It still works. Nothing left your machine. No API key, no billing, no telemetry,
no terms of service. That is the whole point of this workshop: *your AI, your
rules, your data.*

## Experiments (pick at least one)

1. **Make it a pirate.** Change the system message to
   `"You are a pirate. Answer everything in pirate speak."` and ask the same
   question. The system message is how you set an LLM's personality and rules —
   you'll lean on this hard in exercise 01.
2. **Watch it fail honestly.** Ask it "What time is it right now?" — it *cannot*
   know: it's a frozen file from months ago. Then ask about something recent
   (e.g. "Who won the last Euskal Encounter tournament?") or something obscure.
   A 293M-parameter model
   knows *much* less than ChatGPT — expect confidently silly answers. That's not
   a bug, it's a lesson: small models are weak at *knowing things* but, as you'll
   see in exercise 01, they can still be great at *deciding to use tools* that
   know things for them.

## Bonus: streaming

There is a bonus `TODO(you)` at the bottom of `starter.py`: set `"stream": True`
and print tokens as they arrive, ChatGPT-style. The trick: with streaming on,
Ollama sends one small JSON object **per line** (NDJSON) instead of a single
response, so you parse it line by line.
