#!/usr/bin/env python3
"""Theme adapter for light/dark terminal backgrounds"""

from ..config import CONFIG

_LIGHT_SWAPS = [
    ("dim black", "grey70"),
    ("bright_black", "grey50"),
    ("dim white", "dim black"),
    ("on dark_green", "on green"),
    ("on dark_blue", "on blue"),
    ("on black", "on white"),
    ("white", "black"),
    ("black", "white"),
]


def get_style(style: str) -> str:
    if not style or CONFIG.theme == "dark":
        return style
    result = style
    for old, new in _LIGHT_SWAPS:
        result = result.replace(old, new)
    return result
