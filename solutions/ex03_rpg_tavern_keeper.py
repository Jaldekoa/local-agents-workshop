"""Solution 03 — Grunk, the haggling tavern keeper. 100% local.

The lesson: STATE LIVES IN CODE, personality lives in the model.
Prices, stock and your gold are plain Python — exact and un-hallucinatable.
Grunk's grumpy charm is the model — fuzzy and fun. The tools are the border
between the two worlds.

Run it from the repo root (it imports inventory.py from the exercise folder):
    Windows:      python .\\solutions\\ex03_rpg_tavern_keeper.py
    macOS/Linux:  python3 solutions/ex03_rpg_tavern_keeper.py
"""

import sys
from pathlib import Path

# Let this file find inventory.py, which lives in the exercise folder.
sys.path.insert(0, str(Path(__file__).parent.parent / "exercises" / "03_rpg_tavern_keeper"))

from inventory import ITEMS, STARTING_GOLD, format_inventory, get_item

from langchain.tools import tool
from langchain_core.messages import ToolMessage
from langchain_ollama import ChatOllama

# ---------------------------------------------------------------------------
# Game state. A dict (not a bare int) so the tools below can modify it —
# reassigning a global int inside a function needs `global`, mutating a dict
# doesn't. This is the "state lives in code" half of the lesson.
# ---------------------------------------------------------------------------
player = {"gold": STARTING_GOLD}

# ---------------------------------------------------------------------------
# 1. The three tools. They return STRINGS: facts for the model to narrate
#    around. The model never sees or edits the numbers directly.
# ---------------------------------------------------------------------------


@tool
def list_wares() -> str:
    """List everything the tavern sells, with prices and stock."""
    return (
        f"Grunk's wares today:\n{format_inventory()}\n"
        "Ask about an item to hear its story."
    )


@tool
def ask_price(item: str) -> str:
    """Get the asking price and stock of one item."""
    found = get_item(item)
    if found is None:
        return f"Grunk does not sell '{item}'. Use list_wares to see the goods."
    return (
        f"{item}: asking price {found['base_price']} gold, "
        f"{found['stock']} in stock. {found['description']}"
    )


@tool
def make_offer(item: str, gold: int) -> str:
    """Offer an amount of gold for an item. This is the ONLY way to buy."""
    found = get_item(item)
    if found is None:
        return f"Grunk does not sell '{item}'. Use list_wares to see the goods."

    if found["stock"] <= 0:
        return f"Fresh out of {item}. Some adventurer bought the last one."

    if gold > player["gold"]:
        return (
            f"The customer only HAS {player['gold']} gold — they cannot "
            f"offer {gold}. No deal."
        )

    base = found["base_price"]

    # THE HAGGLING RULE. Three lines of arithmetic no prompt can override:
    # however charming (or generous) Grunk gets, 80% of base price is the floor.
    if gold >= 0.8 * base:
        found["stock"] -= 1  # the deal actually happens HERE, in code
        player["gold"] -= gold
        return (
            f"DEAL! Sold one {item} for {gold} gold. "
            f"The customer now has {player['gold']} gold. "
            f"{found['stock']} left in stock."
        )

    if gold >= 0.5 * base:
        # Lowball but not insulting: counter at the midpoint and grumble.
        counter = round((gold + base) / 2)
        return (
            f"Grunk grumbles. {gold} gold for a {item}? Counteroffer: "
            f"{counter} gold, and that is Grunk being NICE. No sale yet."
        )

    return (
        f"REFUSED. {gold} gold for a {item}?! Grunk has been insulted by "
        f"trolls with better manners. The asking price is {base} gold."
    )


TOOLS = {"list_wares": list_wares, "ask_price": ask_price, "make_offer": make_offer}

# ---------------------------------------------------------------------------
# 2. Grunk's personality — the "personality lives in the model" half.
#    Short, imperative, and it NAMES the tools. That last part matters: in
#    testing, vague rules like "always use your tools" made this 293M model
#    plan a tool call in its thinking and then... emit nothing. Telling it
#    exactly which tool to call FIRST, by name, fixed it every time.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are Grunk, half-orc keeper of the Rusty Flagon tavern. \
Gruff, greedy, secretly soft-hearted. You speak in short sentences.
To answer the customer, FIRST call a tool:
- list_wares to show the goods
- ask_price for one item's price
- make_offer when the customer offers gold for an item
Then reply to the customer in one gruff sentence, using only the numbers the tool returned. Never invent prices or gold amounts."""

# ---------------------------------------------------------------------------
# 3. The model. We use LangChain's native tool calling (the ex02 way), not the
#    manual parsing from ex01. Why: in native mode Ollama itself parses the
#    model's <tool_call> tags into structured tool_calls server-side, which
#    proved the more reliable round-trip in testing — no regex on our side to
#    get out of sync with the model's exact output format.
# ---------------------------------------------------------------------------
llm = ChatOllama(
    model="littlelamb",
    temperature=0,  # deterministic tool calls on the happy path. When
    # determinism backfires (the model wedges on one exact prompt), run_turn
    # falls back to llm_retry below.
    num_ctx=4096,  # explicit: the chat history grows every turn, and a too-small
    # context window would silently truncate the system prompt (bye bye Grunk).
    num_predict=512,  # HARD CAP on tokens per reply. Tiny models sometimes fall
    # into an endless "thinking" loop (we measured a 3-MINUTE turn without this
    # cap). With it, a runaway turn costs ~3 seconds, the reply comes back
    # empty, and our fallback in run_turn shows the raw tool result instead.
    validate_model_on_init=True,
)
llm_with_tools = llm.bind_tools([list_wares, ask_price, make_offer])

# A second copy of the model with its factory sampler settings. temperature=0
# is deterministic — perfect until the model wedges on one exact prompt (all
# thinking, no answer), because then it would wedge on it FOREVER. When that
# happens, run_turn retries with this one: a dash of randomness un-sticks it
# about half the time per attempt (measured on this exact model).
llm_retry = ChatOllama(
    model="littlelamb",
    temperature=0.6,  # the model's baked-in defaults: 0.6 / 0.95 / 20
    top_p=0.95,
    top_k=20,
    num_ctx=4096,
    num_predict=512,
)
llm_retry_with_tools = llm_retry.bind_tools([list_wares, ask_price, make_offer])

# ---------------------------------------------------------------------------
# 4. The agent loop (same shape as ex01/ex02) + a REPL around it.
# ---------------------------------------------------------------------------


def run_turn(history: list, user_input: str) -> str:
    """One player turn: let the model think/act/observe until it answers.

    HISTORY HYGIENE (learned the hard way): the tool request/result plumbing
    is only needed WHILE this turn is in flight. If we keep it in the
    long-term history, the tiny model chokes on it next turn — in testing, a
    leftover empty assistant message sent it into an endless thinking loop.
    So we do the plumbing on a scratch COPY, and store only clean dialogue
    (user text + Grunk's final words) in the durable history.
    """
    messages = history + [{"role": "user", "content": user_input}]  # scratch copy
    last_tool_result = ""  # kept as a fallback, see the end of this function
    model = llm_with_tools  # may be swapped for the retry model below

    for _ in range(5):  # safety cap on tool round-trips per turn
        ai_msg = model.invoke(messages)

        if not ai_msg.tool_calls and not ai_msg.content:
            # The wedge: the model spent its whole token budget "thinking"
            # and said nothing. Retrying at temperature 0 would reproduce it
            # exactly, so switch to the randomized retry model and go again.
            # (Do NOT append the empty message — it poisons the next attempt.)
            model = llm_retry_with_tools
            continue

        messages.append(ai_msg)  # request first...

        if not ai_msg.tool_calls:
            break

        for tool_call in ai_msg.tool_calls:
            selected = TOOLS.get(tool_call["name"])
            if selected is None:
                messages.append(
                    ToolMessage(
                        content=f"Error: no tool named {tool_call['name']!r}",
                        tool_call_id=tool_call["id"],
                    )
                )
                continue
            try:
                tool_msg = selected.invoke(tool_call)  # ...result second
            except Exception as exc:
                # Tiny models sometimes pass args a tool doesn't take (e.g.
                # list_wares with {"item": ...}). Report it back instead of
                # crashing, so the model can try again.
                tool_msg = ToolMessage(
                    content=f"Error calling {tool_call['name']}: {exc}",
                    tool_call_id=tool_call["id"],
                )
            last_tool_result = str(tool_msg.content)
            messages.append(tool_msg)

    # Normally the model wraps the tool result in Grunk's voice. But tiny
    # models occasionally go quiet after a tool call — if that happens, show
    # the raw tool result: the FACTS are always safe, they came from code.
    if ai_msg.content:
        reply = ai_msg.content
    elif last_tool_result:
        reply = f"(Grunk grunts and points at the ledger) {last_tool_result}"
    else:
        reply = "(Grunk stares at you in silence. Try rephrasing, adventurer.)"

    # Only the clean dialogue goes into the durable history (see docstring).
    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": reply})

    # Sliding-window memory: keep the system prompt + the last 2 exchanges.
    # Tiny models get lost in long histories (we measured it: past a few
    # turns, replies degraded into silence). Haggling only needs to remember
    # the last counteroffer anyway — and the REAL state never forgets,
    # because it lives in inventory.py, not in the model.
    del history[1:-4]  # history[0] is the system prompt; keep the last 4 msgs
    return reply


def status_line() -> str:
    """The ground truth, printed every turn. If Grunk's words ever disagree
    with this line, trust this line — it comes from the code, not the model."""
    stock = ", ".join(f"{name} x{item['stock']}" for name, item in ITEMS.items())
    return f"[ your gold: {player['gold']} | shelf: {stock} ]"


def main() -> None:
    print("=" * 60)
    print("  THE RUSTY FLAGON — proprietor: Grunk (half-orc)")
    print("  Haggle for goods. Type 'quit' to leave the tavern.")
    print("=" * 60)
    print(status_line())

    # ONE history list for the whole session: haggling needs memory, or
    # Grunk forgets his own counteroffers between turns. run_turn() appends
    # each turn's clean dialogue (user text + Grunk's reply) to it.
    history: list = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGrunk: Hmph. Door's that way.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            print("\nGrunk: Come back with more gold, adventurer.")
            break

        reply = run_turn(history, user_input)
        print(f"\nGrunk: {reply}")
        print(status_line())


if __name__ == "__main__":
    main()
