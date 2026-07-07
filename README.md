# 100% Local AI Agents on Your Laptop

### Your AI, your rules, your data — Euskal Encounter 2026

Build a real AI **agent** — a program that thinks, calls tools, and acts — running
**entirely on the laptop in front of you**:

- **No cloud.** Once the model is downloaded, unplug the network. Everything still works.
- **No GPU.** The model is 238 MB and runs happily on a plain i7 CPU with 8 GB of RAM.
- **No cost.** No API keys, no tokens, no subscriptions. Apache-2.0 all the way down.
- **No data leaks.** Your prompts, your tickets, your tavern haggling — nothing ever
  leaves `localhost`.

The star of the show is **[LittleLamb-ToolCalling](https://huggingface.co/mradermacher/LittleLamb-ToolCalling-GGUF)**
by [Multiverse Computing](https://multiversecomputing.com): a Qwen3-0.6B compressed
~50% with CompactifAI and fine-tuned for tool calling — 293M parameters that fit in
your pocket and still know how to use tools.

> **The core lesson of this workshop:** tool calling is *not magic*. In lesson 01 you
> will build it yourself with nothing but the Python standard library and `requests`.
> Everything a big framework does, you will have done by hand first.

---

## Prerequisites

Install these **before the workshop** (or during the first 10 minutes — but the
LAN party Wi-Fi thanks you if you come prepared).

| What | Windows 10 | macOS |
|------|-----------|-------|
| **Python 3.10+** | Download from [python.org/downloads](https://www.python.org/downloads/). In the installer, **check "Add python.exe to PATH"**. Verify: `python --version` | Usually preinstalled; otherwise [python.org/downloads](https://www.python.org/downloads/) or `brew install python`. Verify: `python3 --version` |
| **Ollama** (runs the model) | Download **OllamaSetup.exe** from [ollama.com/download/windows](https://ollama.com/download/windows) and run it. Ollama starts automatically in the tray. | Download from [ollama.com/download/mac](https://ollama.com/download/mac), drag to Applications, open once. Or `brew install ollama`. |
| **VS Code** | [code.visualstudio.com](https://code.visualstudio.com/) + the Python extension | Same |
| **This repo** | `git clone https://github.com/GmausDev/local-agents-workshop.git` (or download the ZIP from GitHub) | Same |

### Download the model (one command, ~238 MB — do this while online!)

Same command in PowerShell and macOS/Linux terminals:

```
ollama pull hf.co/mradermacher/LittleLamb-ToolCalling-GGUF:Q4_K_M
```

Then give it a short name so all the workshop code can just say `littlelamb`
(this is a zero-cost alias — no extra disk used):

```
ollama cp hf.co/mradermacher/LittleLamb-ToolCalling-GGUF:Q4_K_M littlelamb
```

**Disk / RAM budget:** 238 MB download, ~1 GB of RAM while running. Your 8 GB,
256 GB-SSD laptop has room to spare. After the pull, **everything is offline**.

### Install the Python packages

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> PowerShell says *"running scripts is disabled"*? Run
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again.

---

## Am I ready?

Run the doctor script (it needs nothing but Python itself — works even before
`pip install`):

```
python setup/check_setup.py
```

It checks your Python version, that Ollama is running, that the model is pulled,
and does a tiny generation as a smoke test. Four `[OK]` lines means you are ready.
Any `[FAIL]` comes with a fix-it hint.

---

## Agenda (1h45)

| # | Exercise | Time | What you'll learn |
|---|----------|------|-------------------|
| 00 | **Hello, local LLM** | 10 min | Talk to a model on `localhost:11434` with plain HTTP. Meet `message.thinking` vs `message.content`. |
| 01 | **Tool calling by hand** | 28 min | THE core lesson. Build the whole agent loop yourself — system prompt with `<tools>`, parse `<tool_call>` from raw text, send results back as `<tool_response>`. stdlib + `requests` only. No magic. |
| 02 | **Same agent with LangChain** | 15 min | Rebuild exercise 01 in ~30 lines. Now that you know what the framework hides, you've earned the shortcut. |
| 03 | **The Tavern Keeper** | 23 min | Fun: an RPG tavern keeper that haggles over prices using tools for inventory and gold. Personality via system prompt. |
| 04 | **Ticket triage agent** | 14 min | Professional: an agent that classifies and routes bug tickets, logging decisions to `triage_log.json`. Take it to work on Monday. |

Each exercise folder has a **starter** with `TODO(you)` markers — enough scaffolding
to finish in the time box — and a full working version in `solutions/` if you get
stuck or want to compare.

---

## Repo map

```
local-agents-workshop/
├── README.md                 <- you are here
├── requirements.txt          <- pip install -r requirements.txt
├── setup/
│   ├── check_setup.py        <- the "am I ready?" doctor script
│   └── Modelfile             <- optional tuning knobs for the model
├── exercises/
│   ├── 00_hello_local_llm/   <- first contact with the model
│   ├── 01_tool_calling_no_magic/ <- the core lesson: no magic
│   ├── 02_langchain_agent/   <- same agent, framework edition
│   ├── 03_rpg_tavern_keeper/ <- the haggling RPG tavern keeper
│   └── 04_ticket_triage/     <- the professional triage agent
├── solutions/                <- full working versions of every exercise
└── tests/                    <- pytest suite (tests/integration needs Ollama running)
```

---

## Troubleshooting quick hits

**"Connection refused" on port 11434 — Ollama isn't running.**
Windows: look for the llama icon in the system tray; if missing, launch Ollama from
the Start menu. macOS/Linux: open the Ollama app, or run `ollama serve` in a terminal
and leave it open.

**Windows Firewall pops up when Ollama starts.**
Click **Allow**. Ollama only listens on `localhost` — nothing is exposed to the
LAN party network.

**"Port 11434 already in use."**
An old Ollama instance is still alive. Windows: quit Ollama from the tray icon and
relaunch. macOS/Linux: `pkill ollama` then start it again. (Nothing else normally
uses 11434 — if the doctor script says the port answers, you're fine.)

**LAN party proxy breaks the model download.**
`ollama pull` needs direct HTTPS to huggingface.co. If the venue network proxies
traffic, set `HTTPS_PROXY` before pulling — PowerShell:
`$env:HTTPS_PROXY="http://proxy:port"`, macOS/Linux: `export HTTPS_PROXY=http://proxy:port`.
Once the pull finishes, the proxy (and the internet) are never needed again.
Also make sure `NO_PROXY=localhost,127.0.0.1` is set — PowerShell:
`$env:NO_PROXY="localhost,127.0.0.1"`, macOS/Linux: `export NO_PROXY=localhost,127.0.0.1` —
or your Python `requests` calls to Ollama may get routed through the proxy and fail.

**The model "thinks" before answering and it feels slow.**
Normal. LittleLamb always reasons for ~100–170 tokens before acting — a few seconds
per turn on these CPUs. The code reads `message.content` and ignores
`message.thinking`.

**The model repeats itself forever.**
Rare Qwen3 greedy-decoding quirk at `temperature 0`. Switch that script to the
model's baked-in defaults: temperature 0.6, top_p 0.95, top_k 20 (see
`setup/Modelfile`).

**"model does not support tools" from Ollama.**
Your Ollama is too old. Install the current version from [ollama.com](https://ollama.com)
(verified on 0.31.1) and it auto-detects the model's tool-calling template.

---

## Credits & links

- **Model:** [LittleLamb-ToolCalling](https://huggingface.co/MultiverseComputingCAI/LittleLamb-ToolCalling)
  by [Multiverse Computing](https://multiversecomputing.com) — GGUF quantization by
  [mradermacher](https://huggingface.co/mradermacher/LittleLamb-ToolCalling-GGUF). Apache-2.0.
- **Base model:** [Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B), compressed with CompactifAI.
- **Runtime:** [Ollama](https://ollama.com).
- **Speaker:** Jorge Quevedo (Multiverse Computing) —
  [github.com/GmausDev](https://github.com/GmausDev) ·
  [picaro.dev](https://picaro.dev) ·
  [LinkedIn](https://www.linkedin.com/in/jorge-quevedo-duran)

Happy hacking — and remember: it never left your laptop.
