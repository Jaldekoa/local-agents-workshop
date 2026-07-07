"""Tests for lesson 01 — the hand-built, no-magic agent.

Interface under test (solutions/ex01_tool_calling_no_magic.py):
    parse_tool_call(text: str) -> (name, arguments) | None
        Extracts the tool call from a reply containing a
        <tool_call>{"name": ..., "arguments": {...}}</tool_call> block;
        returns None when there is no (parseable) tool call — that means
        the reply is the final answer.
    TOOLS: dict[str, callable]
        Tool registry; the agent dispatches with TOOLS[name](**arguments).
    run_agent(user_message: str)
        Full loop: call model -> if tool call, run tool, send result back,
        repeat -> print (and/or return) the model's final answer.

No Ollama needed: the model is played by the fake_ollama fixture (conftest.py).
"""

import json

# The exact wire format LittleLamb (Qwen3 template) was trained to emit.
VALID_TOOL_CALL = (
    "<tool_call>\n"
    '{"name": "get_weather", "arguments": {"city": "Paris"}}\n'
    "</tool_call>"
)


def as_name_and_args(parsed):
    """Normalize parse_tool_call's result so the tests accept either a
    (name, args) tuple or a {"name": ..., "arguments": ...} dict."""
    if isinstance(parsed, dict):
        return parsed["name"], parsed.get("arguments", {})
    name, args = parsed
    return name, args


# ---------------------------------------------------------------------------
# parse_tool_call — the string-parsing heart of the "no magic" lesson
# ---------------------------------------------------------------------------

def test_parse_valid_tool_call(ex01):
    parsed = ex01.parse_tool_call(VALID_TOOL_CALL)
    assert parsed is not None
    name, args = as_name_and_args(parsed)
    assert name == "get_weather"
    assert args == {"city": "Paris"}


def test_parse_tool_call_wrapped_in_prose(ex01):
    # Small models sometimes chat around the tool call; the parser must
    # still find the block instead of giving up.
    text = (
        "Sure, let me check that for you.\n"
        + VALID_TOOL_CALL
        + "\nI will have the answer in a moment."
    )
    parsed = ex01.parse_tool_call(text)
    assert parsed is not None
    name, args = as_name_and_args(parsed)
    assert name == "get_weather"
    assert args == {"city": "Paris"}


def test_parse_plain_answer_returns_none(ex01):
    # No <tool_call> tags at all -> this is a final answer, not a tool call.
    assert ex01.parse_tool_call("It is sunny and 22°C in Paris today.") is None


def test_parse_malformed_json_returns_none(ex01):
    # Tags present but the JSON inside is broken (unquoted values) — the
    # parser must fail gracefully with None, never raise.
    broken = '<tool_call>\n{"name": "get_weather", "arguments": {city: Paris}}\n</tool_call>'
    assert ex01.parse_tool_call(broken) is None


# ---------------------------------------------------------------------------
# run_agent — the full loop against the scripted fake model
# ---------------------------------------------------------------------------

def test_full_loop_runs_tool_and_returns_final_answer(ex01, fake_ollama, capsys):
    # Register a test tool in the agent's registry so we control both sides:
    # what the "model" asks for, and what the tool returns.
    tool_calls_made = []

    def fake_get_weather(city: str) -> dict:
        """Return the (fake) current weather for a city."""
        tool_calls_made.append(city)
        return {"condition": "sunny", "temp_c": 22}

    ex01.TOOLS["get_weather"] = fake_get_weather

    # Script the conversation: turn 1 the model calls the tool, turn 2
    # (after seeing the tool result) it answers in plain language.
    fake_ollama.add_reply(VALID_TOOL_CALL)
    fake_ollama.add_reply("It is sunny and 22°C in Paris today.")

    result = ex01.run_agent("What is the weather in Paris?")

    # 1) The final answer reached the user — run_agent either returns it
    #    or prints it (the solution prints; both are acceptable here).
    answer = result if isinstance(result, str) else capsys.readouterr().out
    assert "sunny" in answer

    # 2) The Python tool function was actually executed with the model's args.
    assert tool_calls_made == ["Paris"]

    # 3) The agent made exactly two model calls: ask -> tool result -> answer.
    assert len(fake_ollama.requests) == 2

    # 4) The tool RESULT was sent back to the model in the trained format:
    #    either a role:"tool" message (Ollama wraps it) or a user message
    #    already wrapped in <tool_response> tags — both render identically.
    second_request = json.dumps(fake_ollama.requests[1])
    assert "tool_response" in second_request or '"tool"' in second_request
    assert "22" in second_request  # the tool's output actually reached the model
