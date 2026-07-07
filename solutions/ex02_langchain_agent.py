"""Solution 02 — the ex01 agent, rebuilt with LangChain. 100% local.

Same two tools (roll_dice, get_time), same think -> act -> observe loop.
LangChain + Ollama now generate the tool schemas, parse the model's
<tool_call> tags, and format the <tool_response> blocks — all the plumbing
you wrote by hand in exercise 01.

Before running:
    pip install "langchain-ollama>=1.1.0,<2.0" "langchain>=1.0,<2.0"
    (and `ollama list` must show the `littlelamb` alias from exercise 00)
"""

import random
from datetime import datetime

from langchain.tools import tool  # turns a plain function into a tool
from langchain_core.messages import ToolMessage
from langchain_ollama import ChatOllama

# ---------------------------------------------------------------------------
# 1. Tools.
#
# The docstring is NOT just a comment here: LangChain sends it to the model,
# and it is how the model decides WHEN to use the tool. One clear line is
# ideal — our model is tiny (293M params) and long descriptions confuse it.
# The type hints (sides: int) become the JSON schema you wrote by hand in ex01.
# ---------------------------------------------------------------------------


@tool
def roll_dice(sides: int) -> str:
    """Roll a dice with the given number of sides and return the result."""
    result = random.randint(1, sides)
    return f"You rolled a {result} on a {sides}-sided dice."


@tool
def get_time() -> str:
    """Get the current date and time."""
    return f"The current date and time is {datetime.now():%Y-%m-%d %H:%M:%S}."


# A name -> tool dict, so we can find the right tool when the model asks for
# one by name. Same trick as your dispatch dict in ex01.
TOOLS = {"roll_dice": roll_dice, "get_time": get_time}

# ---------------------------------------------------------------------------
# 2. The model, with tools attached.
# ---------------------------------------------------------------------------

llm = ChatOllama(
    model="littlelamb",  # the alias you created with `ollama cp` in ex00
    temperature=0,  # tiny models need this to stay on-script
    num_predict=512,  # hard cap per reply: if a tiny model falls into an
    # endless "thinking" loop, this turns a multi-minute hang into seconds
    validate_model_on_init=True,  # typo in the name -> clear error right away
)

# bind_tools() returns a new model object that sends the tools' JSON schemas
# with every request. In ex01 YOU pasted those schemas into the system prompt
# inside <tools> tags — Ollama's chat template now does exactly that for us.
llm_with_tools = llm.bind_tools([roll_dice, get_time])

# ---------------------------------------------------------------------------
# 3. The agent loop: think -> act -> observe -> repeat.
#    This is the one part frameworks never remove, because the loop IS the agent.
# ---------------------------------------------------------------------------


def run_agent(question: str) -> str:
    """Answer one question, calling tools as needed. Returns the final text."""
    messages = [{"role": "user", "content": question}]

    for _ in range(5):  # safety cap: tiny models can get stuck calling tools forever
        ai_msg = llm_with_tools.invoke(messages)

        # Keep the model's reply (including its tool request!) in the history,
        # BEFORE appending any tool results. Order matters: request, then result.
        messages.append(ai_msg)

        if not ai_msg.tool_calls:
            break  # no tool wanted -> this is the final answer

        for tool_call in ai_msg.tool_calls:
            # tool_call is a dict: {"name": ..., "args": {...}, "id": ..., ...}
            # NOTE: "args" is already a parsed dict here — NOT a JSON string
            # like in OpenAI's API. No json.loads() needed.
            selected = TOOLS.get(tool_call["name"])

            if selected is None:
                # Tiny models sometimes invent tool names. Tell the model
                # instead of crashing, so it can recover on the next turn.
                messages.append(
                    ToolMessage(
                        content=f"Error: no tool named {tool_call['name']!r}",
                        tool_call_id=tool_call["id"],
                    )
                )
                continue

            # "Observe": run the tool and feed the result back to the model.
            # We pass the WHOLE tool_call dict (not just tool_call["args"]):
            # that returns a ToolMessage already carrying the matching
            # tool_call_id, which is how the model pairs result with request.
            messages.append(selected.invoke(tool_call))

    # .content is the final answer text. (The model also "thinks" before
    # answering — Ollama separates that out for us, so .content stays clean.)
    return ai_msg.content


if __name__ == "__main__":
    # Two questions: one per tool. The first call also loads the model into
    # RAM, so it takes a few extra seconds — that's normal.
    for question in ["Roll a 20-sided dice for me!", "What time is it?"]:
        print(f"\nYou:   {question}")
        print(f"Agent: {run_agent(question)}")
