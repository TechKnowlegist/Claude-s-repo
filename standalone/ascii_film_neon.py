#!/usr/bin/env python3
"""NEON CITY -- a standalone, original color ASCII short film.

A synthwave-style skyline, a glowing sun behind silhouetted buildings, and a
scrolling neon floor grid. Generic retro-futurist look, entirely original.
Uses real 24-bit ANSI color. No dependencies, no install.

Needs a terminal that supports ANSI color -- Windows Terminal, modern
cmd.exe / PowerShell on Windows 10+, or any Mac/Linux terminal all work.

Run:  python ascii_film_neon.py
Quit: Ctrl+C
"""

import random
import sys
import time

WIDTH = 100
HEIGHT = 32
FPS = 12
SEED = 21

SKY_TOP = (20, 8, 45)
SKY_HORIZON = (255, 60, 130)
SUN_BANDS = [(255, 240, 200), (255, 190, 120), (255, 120, 130), (230, 70, 160)]
BUILDING = (18, 10, 30)
WINDOW = (120, 230, 255)
GRID_A = (255, 60, 200)
GRID_B = (60, 220, 255)
STREAK_COLORS = [(120, 230, 255), (255, 90, 200)]
TEXT_COLOR = (235, 245, 255)

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


def center(text, width):
    if len(text) >= width:
        return text[:width]
    left = (width - len(text)) // 2
    return " " * left + text + " " * (width - len(text) - left)


def main():
    rng = random.Random(SEED)
    horizon = int(HEIGHT * 0.62)
    sun_row = int(horizon * 0.45)
    sun_radius = max(3, HEIGHT // 7)

    title_duration = FPS * 3
    city_duration = FPS * 16
    end_duration = FPS * 4
    total = title_duration + city_duration + end_duration

    buildings = []
    x = 0
    while x < WIDTH:
        bw = rng.randint(4, 9)
        bh = max(2, rng.randint(3, horizon - sun_row - 2))
        windows = {
            (dx, dy)
            for dx in range(1, bw - 1, 2)
            for dy in range(1, bh, 2)
            if rng.random() < 0.6
        }
        buildings.append({"x": x, "w": bw, "h": bh, "windows": windows})
        x += bw + rng.randint(0, 2)

    streaks = [
        {
            "y": rng.randint(sun_row + 1, horizon - 2),
            "x": rng.uniform(0, WIDTH),
            "vx": rng.choice([-1, 1]) * rng.uniform(0.6, 1.6),
            "length": rng.randint(4, 8),
            "color": rng.choice(STREAK_COLORS),
        }
        for _ in range(4)
    ]

    grid_scroll = 0.0
    delay = 1.0 / FPS
    tick = 0
    # Clear once and hide the cursor, then just home the cursor each frame
    # instead of clearing every time -- clearing every frame makes most
    # terminals flash blank before each redraw, which looks like flicker.
    sys.stdout.write("\x1b[2J\x1b[?25l")
    try:
        while tick < total:
            grid = [[[" ", None, None] for _ in range(WIDTH)] for _ in range(HEIGHT)]

            for y in range(horizon):
                row_t = y / max(1, horizon - 1)
                sky = lerp_color(SKY_TOP, SKY_HORIZON, row_t)
                for xx in range(WIDTH):
                    grid[y][xx][2] = sky

            cx = WIDTH / 2
            for y in range(max(0, sun_row - sun_radius), min(horizon, sun_row + sun_radius + 1)):
                dy = y - sun_row
                span = sun_radius ** 2 - dy ** 2
                if span < 0:
                    continue
                half_w = int(span ** 0.5)
                if (sun_row + sun_radius - y) % 3 == 0 and dy > -sun_radius * 0.3:
                    continue
                band_t = 1 - (abs(dy) / max(1, sun_radius))
                band = SUN_BANDS[min(len(SUN_BANDS) - 1, int((1 - band_t) * len(SUN_BANDS)))]
                for xx in range(int(cx - half_w), int(cx + half_w) + 1):
                    if 0 <= xx < WIDTH:
                        grid[y][xx][2] = band

            for y in range(horizon, HEIGHT):
                depth = y - horizon
                spacing = max(2, 6 - depth // 2)
                offset = int(grid_scroll) % spacing
                line_here = (depth + offset) % spacing == 0
                for xx in range(WIDTH):
                    grid[y][xx][2] = (10, 4, 20)
                    if line_here:
                        grid[y][xx][0] = "-"
                        grid[y][xx][1] = GRID_A if (xx // 4) % 2 == 0 else GRID_B

            for b in buildings:
                top = horizon - b["h"]
                for dy in range(b["h"]):
                    row = top + dy
                    if not (0 <= row < HEIGHT):
                        continue
                    for dx in range(b["w"]):
                        xx = b["x"] + dx
                        if not (0 <= xx < WIDTH):
                            continue
                        grid[row][xx][2] = BUILDING
                        grid[row][xx][0] = " "
                        if (dx, dy) in b["windows"]:
                            grid[row][xx][0] = "="
                            grid[row][xx][1] = WINDOW

            if tick >= title_duration:
                grid_scroll += 0.5
                for s in streaks:
                    s["x"] = (s["x"] + s["vx"]) % WIDTH
                for s in streaks:
                    for i in range(s["length"]):
                        xx = int(s["x"] - i * (1 if s["vx"] > 0 else -1)) % WIDTH
                        y = s["y"]
                        if 0 <= y < horizon:
                            grid[y][xx][0] = "-"
                            grid[y][xx][1] = s["color"]

            title_lines = None
            if tick < title_duration:
                title_lines = ["N E O N   C I T Y", "", "a short by asciiverse"]
            elif tick >= total - end_duration:
                title_lines = ["THE CITY NEVER SLEEPS"]
            if title_lines:
                top = max(0, (HEIGHT - len(title_lines)) // 2)
                for i, text in enumerate(title_lines):
                    row = top + i
                    if 0 <= row < HEIGHT:
                        for xx, ch in enumerate(center(text, WIDTH)):
                            if ch != " ":
                                grid[row][xx][0] = ch
                                grid[row][xx][1] = TEXT_COLOR

            lines = [render_row([(c[0], c[1], c[2]) for c in row]) for row in grid]
            sys.stdout.write("\x1b[H")
            sys.stdout.write("\n".join(lines))
            sys.stdout.write("\n")
            sys.stdout.flush()
            time.sleep(delay)
            tick += 1
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(RESET + "\x1b[?25h\n")


if __name__ == "__main__":
    main()
