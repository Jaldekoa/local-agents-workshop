"""The Rusty Flagon's stock room. Pure data + two helper functions.

This file is COMPLETE — you don't need to edit it. It exists to make a point:
the game's state (prices, stock, gold) lives in plain Python, where it is
exact, testable, and impossible for the model to hallucinate.

The language model never touches this file directly. It only sees the strings
that the tools in starter.py build FROM this data.
"""

# How much gold the player starts with. The iron_sword costs 35... choose wisely.
STARTING_GOLD = 50

# Each item: base_price (gold), stock (how many are on the shelf), and a
# description Grunk can quote at customers.
ITEMS: dict[str, dict] = {
    "health_potion": {
        "base_price": 20,
        "stock": 5,
        "description": (
            "Red, fizzy, restores your hit points. Brewed on-site. "
            "Grunk swears the floating bits are 'herbs'."
        ),
    },
    "iron_sword": {
        "base_price": 35,
        "stock": 2,
        "description": (
            "A no-nonsense iron sword. Previous owner returned it, "
            "citing 'too much adventure'. Lightly used, heavily dented."
        ),
    },
    "mystery_stew": {
        "base_price": 8,
        "stock": 12,
        "description": (
            "Today's special. Nobody knows what's in it, including Grunk. "
            "It has never killed anyone who mattered."
        ),
    },
    "room_for_night": {
        "base_price": 15,
        "stock": 3,
        "description": (
            "A bed upstairs. The mattress is straw, the neighbors snore in "
            "Dwarvish, and checkout is whenever Grunk starts yelling."
        ),
    },
    "dragon_repellent": {
        "base_price": 40,
        "stock": 1,
        "description": (
            "A murky flask that allegedly repels dragons. No refunds, because "
            "no complaining customer has ever come back. Make of that what you will."
        ),
    },
}


def get_item(name: str) -> dict | None:
    """Look up an item by name. Returns None if Grunk doesn't stock it."""
    # Forgive sloppy typing from the model: "Iron Sword " -> "iron_sword".
    # Small models pass whatever the customer typed, so normalize hard.
    return ITEMS.get(name.strip().lower().replace(" ", "_"))


def format_inventory() -> str:
    """Render the shelf as a compact list: name, price, stock.

    On purpose NO descriptions here: this string gets fed to a tiny language
    model, and in testing a wall of flavor text sent it into endless
    rambling-thinking loops. The descriptions are served one at a time by
    the ask_price tool instead — small bites for a small model.
    """
    lines = [
        f"- {name}: {item['base_price']} gold ({item['stock']} in stock)"
        for name, item in ITEMS.items()
    ]
    return "\n".join(lines)
