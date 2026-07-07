"""Tests for lesson 03 — the tavern keeper's haggling rule.

Interface under test (solutions/ex03_rpg_tavern_keeper.py):
    make_offer(item: str, gold: int) -> str
        The pricing rule the model calls as a tool (a LangChain @tool, so we
        go through .invoke). Outcomes:
          - unknown item / stock 0        -> no sale, nothing changes
          - offer >= 80% of base_price    -> ACCEPT: stock -1, player pays
          - offer >= 50% but below 80%    -> COUNTER: suggests a price, no change
          - below 50%                     -> REFUSE: no change
    ITEMS: dict[name, {"base_price": int, "stock": int, ...}]
        Re-exported on the module from exercises/03_rpg_tavern_keeper/inventory.py
        ("state lives in code").
    player: {"gold": int}
        The customer's purse; mutates ONLY on an accepted deal.

These tests are pure Python — no model, no fake_ollama. That is the whole
point of the lesson: the model only *chooses* to call make_offer; the rules
that move gold live in code you can unit-test.
"""

import pytest


def offer(mod, item: str, gold: int) -> str:
    """Call make_offer whether it is a LangChain tool or a plain function."""
    tool = mod.make_offer
    if hasattr(tool, "invoke"):  # LangChain StructuredTool
        return tool.invoke({"item": item, "gold": gold})
    return tool(item, gold)


def player_gold(mod) -> int:
    return mod.player["gold"]


@pytest.fixture
def tavern(ex03):
    """The ex03 module with a precisely-priced test item injected so the
    percentage boundaries are exact integers (80% of 100 = 80, no rounding),
    and a rich player so affordability never interferes with the boundaries.

    Keys use underscores like every real item in inventory.py, because
    get_item() normalizes lookups that way ("test sword" -> "test_sword").
    The offers below deliberately use spaces to exercise that normalization."""
    ex03.ITEMS["test_sword"] = {
        "base_price": 100,
        "stock": 2,
        "description": "A sword that exists only in the test suite.",
    }
    ex03.ITEMS["moon_dust"] = {
        "base_price": 50,
        "stock": 0,  # for the out-of-stock case
        "description": "Sold out since the last eclipse.",
    }
    ex03.player["gold"] = 1000
    return ex03


# ---------------------------------------------------------------------------
# The accept boundary: 80% of base price is a deal, 79% is not
# ---------------------------------------------------------------------------

def test_offer_at_80_percent_is_accepted(tavern):
    reply = offer(tavern, "test sword", 80)

    assert isinstance(reply, str) and reply
    # Accept means state changes: the player pays exactly what they offered...
    assert player_gold(tavern) == 1000 - 80
    # ...and one sword leaves the shelf.
    assert tavern.ITEMS["test_sword"]["stock"] == 1


def test_offer_at_79_percent_is_not_accepted(tavern):
    reply = offer(tavern, "test sword", 79)

    assert isinstance(reply, str) and reply
    # One gold piece below the line: NO sale, so nothing may change.
    assert player_gold(tavern) == 1000
    assert tavern.ITEMS["test_sword"]["stock"] == 2
    # 79% is lowball-but-plausible: the keeper counters with a number.
    assert any(ch.isdigit() for ch in reply)


def test_insulting_offer_is_refused_and_changes_nothing(tavern):
    reply = offer(tavern, "test sword", 10)  # 10% of the price

    assert isinstance(reply, str) and reply
    # Refused: gold and stock must not move.
    assert player_gold(tavern) == 1000
    assert tavern.ITEMS["test_sword"]["stock"] == 2


# ---------------------------------------------------------------------------
# Out-of-stock and unknown items
# ---------------------------------------------------------------------------

def test_out_of_stock_item_cannot_be_bought_at_any_price(tavern):
    reply = offer(tavern, "moon dust", 500)  # 10x the price!

    assert isinstance(reply, str) and reply
    assert player_gold(tavern) == 1000, "no gold may change hands for stock 0"
    assert tavern.ITEMS["moon_dust"]["stock"] == 0


def test_unknown_item_does_not_crash_or_sell(tavern):
    reply = offer(tavern, "dragon egg", 999)

    assert isinstance(reply, str) and reply
    assert player_gold(tavern) == 1000


# ---------------------------------------------------------------------------
# The player cannot spend gold they do not have
# ---------------------------------------------------------------------------

def test_cannot_offer_more_gold_than_the_player_has(tavern):
    tavern.player["gold"] = 30
    reply = offer(tavern, "test sword", 100)  # generous, but imaginary money

    assert isinstance(reply, str) and reply
    assert tavern.player["gold"] == 30
    assert tavern.ITEMS["test_sword"]["stock"] == 2


# ---------------------------------------------------------------------------
# Stock actually runs out
# ---------------------------------------------------------------------------

def test_stock_depletes_and_then_sells_out(tavern):
    offer(tavern, "test sword", 100)  # full price: accepted
    offer(tavern, "test sword", 100)  # accepted: shelf now empty
    assert tavern.ITEMS["test_sword"]["stock"] == 0
    assert player_gold(tavern) == 1000 - 200

    reply = offer(tavern, "test sword", 100)  # nothing left to sell
    assert isinstance(reply, str) and reply
    assert player_gold(tavern) == 800  # no phantom sale
    assert tavern.ITEMS["test_sword"]["stock"] == 0
