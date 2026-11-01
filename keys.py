"""Keyboard vocabulary for shortcut combos.

Shortcuts are written in content files as plain, space-separated tokens,
for example ``"cmd shift 4"`` or ``"ctrl cmd space"``. This module turns
those strings into ``Key`` objects that the templates render as keycaps.

Modifier glyphs (⌘ ⌥ ⌃ ⇧ …) are drawn as small inline SVG icons instead of
font characters. Open Sans has no glyphs for them, and icons render the same
on every computer, including the CI runner that builds the PNG cheat sheets.
"""

from __future__ import annotations

from dataclasses import dataclass

# SVG path data on a 24x24 grid, drawn with a 2px round stroke.
ICON_PATHS: dict[str, str] = {
    "command": "M15 6v12a3 3 0 1 0 3-3H6a3 3 0 1 0 3 3V6a3 3 0 1 0-3 3h12a3 3 0 1 0-3-3",
    "option": "M3 5h6l6 14h6M14 5h7",
    "control": "M6 15l6-6 6 6",
    "shift": "M9 20v-7H4.5L12 4.5l7.5 8.5H15v7z",
    "delete": "M21 5H9l-6 7 6 7h12zM12 9l6 6M18 9l-6 6",
    "globe": "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18M3 12h18M12 3c-3 3.2-3 14.8 0 18M12 3c3 3.2 3 14.8 0 18",
    "left": "M19 12H5M11 6l-6 6 6 6",
    "right": "M5 12h14M13 6l6 6-6 6",
    "up": "M12 19V5M6 11l6-6 6 6",
    "down": "M12 5v14M6 13l6 6 6-6",
}


@dataclass(frozen=True)
class Key:
    """One physical key in a shortcut combo."""

    name: str  # spoken name, used for screen readers and the legend
    text: str = ""  # characters printed on the keycap
    icon: str = ""  # key into ICON_PATHS, if the key shows a symbol
    wide: bool = False  # True for keys like Space that need a wider cap
    separator: bool = False  # True for the "/" between alternative keys
    symbol: str = ""  # Unicode stand-in for the icon, for email where SVG can't go

    @property
    def plain(self) -> str:
        """How the key reads as plain text: the symbol, else the printed text."""
        return self.symbol or self.text


ALTERNATIVE = Key("or", text="/", separator=True)


# Named keys, in the order Apple lists modifiers (⌃ ⌥ ⇧ ⌘).
NAMED_KEYS: dict[str, Key] = {
    "ctrl": Key("Control", icon="control", symbol="⌃"),
    "opt": Key("Option", icon="option", symbol="⌥"),
    "shift": Key("Shift", icon="shift", symbol="⇧"),
    "cmd": Key("Command", icon="command", symbol="⌘"),
    "fn": Key("Globe (fn)", icon="globe", symbol="fn"),
    "delete": Key("Delete", icon="delete", symbol="⌫"),
    "left": Key("Left Arrow", icon="left", symbol="←"),
    "right": Key("Right Arrow", icon="right", symbol="→"),
    "up": Key("Up Arrow", icon="up", symbol="↑"),
    "down": Key("Down Arrow", icon="down", symbol="↓"),
    "space": Key("Space bar", text="Space", wide=True),
    "tab": Key("Tab", text="Tab", wide=True),
    "esc": Key("Escape", text="esc", wide=True),
    "return": Key("Return", text="return", wide=True),
}

# Single characters whose spoken name differs from the character itself.
SPOKEN_PUNCTUATION: dict[str, str] = {
    ",": "Comma",
    "`": "Grave accent",
    "+": "Plus",
    "-": "Minus",
    "=": "Equals",
    "0": "Zero",
}

# Characters shown differently on the keycap than in the source text.
DISPLAY_TEXT: dict[str, str] = {"-": "–"}


def parse_key(token: str, combo: str) -> Key:
    """Turn one token such as ``"cmd"`` or ``"V"`` into a ``Key``."""
    lowered = token.lower()
    if lowered in NAMED_KEYS:
        return NAMED_KEYS[lowered]
    if len(token) == 1:
        label = token.upper()
        return Key(SPOKEN_PUNCTUATION.get(token, label), text=DISPLAY_TEXT.get(token, label))
    known = ", ".join(sorted(NAMED_KEYS))
    raise ValueError(f"Unknown key {token!r} in {combo!r}. Known names: {known}")


def parse_combo(combo: str) -> list[Key]:
    """Turn ``"cmd shift 4"`` into a list of keys.

    A slash offers alternatives for the last key: ``"opt left/right"``
    renders as ⌥ ← / →.

    Raises ``ValueError`` for an unknown multi-character token, so a typo
    such as ``"cmmd C"`` fails the build instead of printing "CMMD".
    """
    keys: list[Key] = []
    for token in combo.split():
        alternatives = token.split("/") if len(token) > 1 else [token]
        for index, alternative in enumerate(alternatives):
            if index > 0:
                keys.append(ALTERNATIVE)
            keys.append(parse_key(alternative, combo))
    if not keys:
        raise ValueError("Empty shortcut combo")
    return keys


def spoken(combo: str) -> str:
    """Readable name for a combo, e.g. ``"Command Shift 4"``."""
    return " ".join(key.name for key in parse_combo(combo))
