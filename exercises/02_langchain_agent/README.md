# Exercise 02 — Same agent, production style (15 min)

In exercise 01 you built a tool-calling agent **by hand**: you wrote the JSON tool
schemas, injected them into the system prompt, regex-parsed `<tool_call>` tags out
of the model's reply, and formatted `<tool_response>` blocks yourself.

Now you'll build the **exact same agent** (same `roll_dice` and `get_time` tools)
with [LangChain](https://docs.langchain.com/oss/python/integrations/chat/ollama).
Nothing new happens conceptually — that's the whole point.

## The plumbing disappears, the loop stays

| Piece of the agent                          | ex01 (by hand)                       | ex02 (LangChain)                          |
|---------------------------------------------|--------------------------------------|-------------------------------------------|
| Tool schema (name, args, description)        | ~15 lines of JSON you typed          | auto-generated from docstring + type hints |
| System prompt with the `<tools>` block       | ~10 lines you maintained             | gone — Ollama's chat template injects it   |
| Parsing `<tool_call>` out of the reply       | ~15 lines of string splitting        | `ai_msg.tool_calls` — already a parsed list |
| Sending the result back as `<tool_response>` | ~8 lines of careful formatting       | `ToolMessage(...)` (or `tool.invoke(tool_call)`) |
| The think → act → observe loop               | ~15 lines                            | ~15 lines. **This part never goes away.** |

You wrote the plumbing once, in ex01. Now the framework carries it. But under the
hood, LangChain + Ollama are producing *byte-for-byte the same prompt format* you
built by hand — you can prove it, because you built it.

> **Does `bind_tools` even work with a 293M model?** Yes — LittleLamb was
> fine-tuned for tool calling and its chat template has a native tools block, so
> Ollama accepts the `tools` parameter directly (verified on Ollama 0.31.1).
> Many small models are NOT so lucky: with them, `invoke()` fails with
> HTTP 400 `"<model> does not support tools"`, because the framework *assumes*
> the model was trained for this. The standard fallback in that case is
> prompt-based tool calling — i.e. **exactly what you built in ex01**. Frameworks
> automate the pattern; they don't replace understanding it.

## When to use a framework (and when not)

**Use one when** you need swappable models, many tools, streaming, retries,
tracing — the boring production stuff you don't want to hand-maintain.

**Skip it when** you're learning (ex01!), debugging a weird prompt issue, or
shipping something tiny where 100 lines of stdlib beats a dependency tree.
The framework is a convenience, not a requirement — you proved that an agent
is just a loop, a parser, and an HTTP call.

## Setup

**Already done** if you ran `pip install -r requirements.txt` during setup — skip ahead.
Otherwise (same command in PowerShell and macOS/Linux, inside your virtualenv):

```
pip install "langchain-ollama>=1.1.0,<2.0" "langchain>=1.0,<2.0"
```

(Do this while you still have internet. Everything else is offline.)

Make sure Ollama is running and the model alias exists (done in exercise 00):

```
ollama list
```

You should see `littlelamb` in the output.

## Run it

Windows (PowerShell):

```powershell
python .\exercises\02_langchain_agent\starter.py
```

macOS / Linux:

```bash
python3 exercises/02_langchain_agent/starter.py
```

Fill in the `TODO(you)` markers in `starter.py`. Stuck? The finished version is
in `solutions/ex02_langchain_agent.py`.

Note: the **first** call includes loading the model into RAM and can take a few
seconds on the workshop laptops. After that, Ollama keeps it warm for 5 minutes.

## Experiment (if you finish early)

Open the solution and look at the two lines that create the model:

```python
from langchain_ollama import ChatOllama
llm = ChatOllama(model="littlelamb", temperature=0)
```

Now imagine swapping them for a cloud provider:

```python
# from langchain_anthropic import ChatAnthropic   # <-- DO NOT run this here
# llm = ChatAnthropic(model="claude-...", api_key="...")
```

That import swap is **the exact moment** every prompt, every tool result, and
every user message would start leaving your laptop for someone else's server.
Two lines. The rest of the agent wouldn't change at all — which is precisely
why it's so easy not to notice. Today, we won't: your AI, your rules, your data.
