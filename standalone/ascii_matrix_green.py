#!/usr/bin/env python3
"""Standalone ASCII digital rain in the classic green look: a bright
near-white head glyph per column fading down through green to near-black.

No dependencies, no install. Needs a terminal that supports ANSI color
(Windows Terminal, modern cmd.exe/PowerShell on Windows 10+, or any Mac/
Linux terminal).

Run:  python ascii_matrix_green.py
Quit: Ctrl+C
"""

import random
import sys
import time

WIDTH = 90
HEIGHT = 30
FPS = 20
SEED = None  # set an int here for a reproducible run

GLYPHS = "01ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄ+-*/<>|=."

HEAD_COLOR = (215, 255, 220)
BRIGHT_GREEN = (45, 220, 95)
DARK_GREEN = (0, 40, 15)

RESET = "\x1b[0m"
FG_DEFAULT = "\x1b[39m"
BG_DEFAULT = "\x1b[49m"


def fg(rgb):
    r, g, b = rgb
    return f"\x1b[38;2;{r};{g};{b}m"


def bg(rgb):
    r, g, b = rgb
    return f"\x1b[48;2;{r};{g};{b}m"


def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(c1[i] + (c2[i] - c1[i]) * t)) for i in range(3))


def render_row(cells):
    out = []
    cur_fg = cur_bg = None
    touched = False
    for ch, f, b in cells:
        if f != cur_fg:
            out.append(fg(f) if f is not None else FG_DEFAULT)
            cur_fg = f
            touched = touched or f is not None
        if b != cur_bg:
            out.append(bg(b) if b is not None else BG_DEFAULT)
            cur_bg = b
            touched = touched or b is not None
        out.append(ch)
    if touched:
        out.append(RESET)
    return "".join(out)


class Column:
    __slots__ = ("head", "length", "speed", "progress")

    def __init__(self, head, length, speed):
        self.head, self.length, self.speed = head, length, speed
        self.progress = 0.0


def spawn_column(rng, height, randomize_head):
    length = rng.randint(3, max(4, height // 2))
    speed = rng.uniform(0.4, 1.4)
    head = rng.uniform(-height, 0) if randomize_head else -length
    return Column(head=head, length=length, speed=speed)


def step(columns, rng, height):
    for i, col in enumerate(columns):
        col.progress += col.speed
        while col.progress >= 1.0:
            col.head += 1
            col.progress -= 1.0
        if col.head - col.length > height:
            columns[i] = spawn_column(rng, height, randomize_head=False)


def render(columns, rng, width, height):
    grid = [[[" ", None, None] for _ in range(width)] for _ in range(height)]
    for x, col in enumerate(columns):
        head_row = int(col.head)
        for offset in range(col.length):
            row = head_row - offset
            if 0 <= row < height:
                glyph = rng.choice(GLYPHS)
                color = HEAD_COLOR if offset == 0 else lerp_color(BRIGHT_GREEN, DARK_GREEN, offset / col.length)
                grid[row][x][0] = glyph
                grid[row][x][1] = color
    return [render_row([(c[0], c[1], c[2]) for c in row]) for row in grid]


def main():
    rng = random.Random(SEED)
    columns = [spawn_column(rng, HEIGHT, randomize_head=True) for _ in range(WIDTH)]
    delay = 1.0 / FPS
    sys.stdout.write("\x1b[2J\x1b[?25l")
    try:
        while True:
            sys.stdout.write("\x1b[H")
            sys.stdout.write("\n".join(render(columns, rng, WIDTH, HEIGHT)))
            sys.stdout.write("\n")
            sys.stdout.flush()
            step(columns, rng, HEIGHT)
            time.sleep(delay)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(RESET + "\x1b[?25h\n")


if __name__ == "__main__":
    main()
