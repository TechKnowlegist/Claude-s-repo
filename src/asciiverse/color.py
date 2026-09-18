"""Minimal 24-bit ANSI color helpers for scenes/films that want to paint in
more than one color. Kept separate from the plain-text scene/film machinery
(which assumes one character == one grid cell of visible width) because a
colored line embeds escape codes that don't count toward its visible width.
"""

from __future__ import annotations

from typing import Optional

RGB = tuple[int, int, int]

RESET = "\x1b[0m"
_FG_DEFAULT = "\x1b[39m"
_BG_DEFAULT = "\x1b[49m"


def fg(rgb: RGB) -> str:
    r, g, b = rgb
    return f"\x1b[38;2;{r};{g};{b}m"


def bg(rgb: RGB) -> str:
    r, g, b = rgb
    return f"\x1b[48;2;{r};{g};{b}m"


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_color(c1: RGB, c2: RGB, t: float) -> RGB:
    t = max(0.0, min(1.0, t))
    return (
        int(round(lerp(c1[0], c2[0], t))),
        int(round(lerp(c1[1], c2[1], t))),
        int(round(lerp(c1[2], c2[2], t))),
    )


# A cell is (character, foreground-rgb-or-None, background-rgb-or-None).
# None means "leave this channel at the terminal's default".
Cell = tuple[str, Optional[RGB], Optional[RGB]]


def render_row(cells: list[Cell]) -> str:
    """Turn a row of (char, fg, bg) cells into one ANSI-colored string,
    emitting a color-change escape only when a channel actually changes."""
    out = []
    cur_fg: Optional[RGB] = None
    cur_bg: Optional[RGB] = None
    touched = False
    for ch, f, b in cells:
        if f != cur_fg:
            out.append(fg(f) if f is not None else _FG_DEFAULT)
            cur_fg = f
            touched = touched or f is not None
        if b != cur_bg:
            out.append(bg(b) if b is not None else _BG_DEFAULT)
            cur_bg = b
            touched = touched or b is not None
        out.append(ch)
    if touched:
        out.append(RESET)
    return "".join(out)


def visible_length(s: str) -> int:
    """Length of ``s`` ignoring ANSI escape sequences -- for width checks."""
    out = 0
    i = 0
    while i < len(s):
        if s[i] == "\x1b" and i + 1 < len(s) and s[i + 1] == "[":
            j = s.index("m", i)
            i = j + 1
        else:
            out += 1
            i += 1
    return out
