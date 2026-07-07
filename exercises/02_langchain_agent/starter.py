"""Exercise 02 — the ex01 agent, rebuilt with LangChain. 100% local.

Same two tools (roll_dice, get_time), same think -> act -> observe loop.
The difference: LangChain + Ollama now generate the tool schemas, parse the
model's <tool_call> tags, and format the <tool_response> blocks — all the
plumbing you wrote by hand in exercise 01.

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
    # TODO(you) #1a: roll a random number from 1 to `sides` and return a
    # short sentence like "You rolled a 4 on a 6-sided dice."
    # Hint: random.randint(1, sides)
    return "TODO"


@tool
def get_time() -> str:
    """Get the current date and time."""
    # TODO(you) #1b: return the current time as a readable string.
    # Hint: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return "TODO"


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

# TODO(you) #2: attach the tools. bind_tools() takes a LIST of tools and
# returns a new model object that sends their schemas with every request.
# (In ex01 YOU pasted those schemas into the system prompt. Same thing.)
llm_with_tools = llm  # <-- replace with: llm.bind_tools([...])

# ---------------------------------------------------------------------------
# 3. The agent loop: think -> act -> observe -> repeat.
#    This is the one part frameworks never remove, because the loop IS the agent.
# ---------------------------------------------------------------------------


def run_agent(question: str) -> str:
    """Answer one question, calling tools as needed. Returns the final text."""
    messages = [{"role": "user", "content": question}]

    for _ in range(5):  # safety cap: tiny models can get stuck calling tools forever
        # TODO(you) #3a: ask the model. Hint: ai_msg = llm_with_tools.invoke(messages)
        ai_msg = ...

        # Keep the model's reply (including its tool request!) in the history.
        # If you forget this, the model never "remembers" asking for the tool.
        messages.append(ai_msg)

        # TODO(you) #3b: if ai_msg.tool_calls is empty, the model gave its
        # final answer — break out of the loop.

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

            # TODO(you) #3c: run the tool and feed the result back ("observe").
            # IMPORTANT: pass the WHOLE tool_call dict, not tool_call["args"].
            # That way you get back a ToolMessage that already carries the
            # matching tool_call_id — append it to messages.
            # Hint: messages.append(selected.invoke(tool_call))

    # .content is the final answer text. (The model also "thinks" before
    # answering — Ollama separates that out for us, so .content stays clean.)
    return ai_msg.content


if __name__ == "__main__":
    # Two questions: one per tool. The first call also loads the model into
    # RAM, so it takes a few extra seconds — that's normal.
    for question in ["Roll a 20-sided dice for me!", "What time is it?"]:
        print(f"\nYou:   {question}")
        print(f"Agent: {run_agent(question)}")
