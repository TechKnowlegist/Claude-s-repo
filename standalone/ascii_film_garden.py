#!/usr/bin/env python3
"""GARDEN -- a standalone, original color ASCII short film.

Dawn breaks over a plot of ground while a handful of flowers grow in and
fireflies drift by. Uses real 24-bit ANSI color (background-painted sky and
ground, colored stems and blossoms). No dependencies, no install.

Needs a terminal that supports ANSI color -- Windows Terminal, modern
cmd.exe / PowerShell on Windows 10+, or any Mac/Linux terminal all work.

Run:  python ascii_film_garden.py
Quit: Ctrl+C
"""

import random
import sys
import time

WIDTH = 100
HEIGHT = 32
FPS = 12
SEED = 7

SKY_NIGHT = (12, 14, 40)
SKY_DAWN_TOP = (60, 70, 130)
SKY_DAWN_HORIZON = (255, 175, 120)
GROUND_DARK = (40, 28, 20)
GROUND_LIT = (70, 48, 30)
STEM = (70, 150, 70)
LEAF = (95, 180, 100)
BLOSSOM_COLORS = [(230, 90, 130), (250, 205, 80), (190, 110, 230), (250, 140, 90)]
STAR = (230, 230, 255)
FIREFLY = (255, 225, 140)
TEXT_COLOR = (255, 255, 255)

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


class Plant:
    def __init__(self, x, max_height, growth_rate, blossom_color):
        self.x, self.max_height, self.growth_rate = x, max_height, growth_rate
        self.height = 0.0
        self.blossom_color = blossom_color

    def step(self):
        if self.height < self.max_height:
            self.height = min(self.max_height, self.height + self.growth_rate)


def main():
    rng = random.Random(SEED)
    horizon = int(HEIGHT * 0.72)

    title_duration = FPS * 3
    grow_duration = FPS * 18
    end_duration = FPS * 4
    total = title_duration + grow_duration + end_duration

    num_plants = max(4, WIDTH // 14)
    plants = []
    for i in range(num_plants):
        x = int((i + 0.5) * WIDTH / num_plants) + rng.randint(-2, 2)
        x = max(0, min(WIDTH - 1, x))
        max_height = rng.randint(4, max(5, horizon - 2))
        duration_frames = grow_duration * rng.uniform(0.55, 0.95)
        growth_rate = max_height / max(1, duration_frames)
        plants.append(Plant(x, max_height, growth_rate, rng.choice(BLOSSOM_COLORS)))

    fireflies = [
        [rng.uniform(0, WIDTH), rng.uniform(2, max(3, horizon - 4)), rng.uniform(-0.25, 0.25), rng.uniform(-0.08, 0.08)]
        for _ in range(5)
    ]
    stars = [(rng.uniform(0, WIDTH), rng.uniform(0, horizon - 1)) for _ in range(30)]

    delay = 1.0 / FPS
    tick = 0
    try:
        while tick < total:
            sky_t = 0.0 if tick < title_duration else min(1.0, (tick - title_duration) / grow_duration)
            sky_top = lerp_color(SKY_NIGHT, SKY_DAWN_TOP, sky_t)
            sky_horizon = lerp_color(SKY_NIGHT, SKY_DAWN_HORIZON, sky_t)

            grid = [[[" ", None, None] for _ in range(WIDTH)] for _ in range(HEIGHT)]

            for y in range(horizon):
                row_t = y / max(1, horizon - 1)
                sky_color = lerp_color(sky_top, sky_horizon, row_t)
                for x in range(WIDTH):
                    grid[y][x][2] = sky_color

            star_alpha = max(0.0, 1.0 - sky_t * 1.4)
            if star_alpha > 0.02:
                for sx, sy in stars:
                    x, y = int(sx), int(sy)
                    if 0 <= x < WIDTH and 0 <= y < horizon:
                        star_color = lerp_color(grid[y][x][2], STAR, star_alpha)
                        grid[y][x][0] = "."
                        grid[y][x][1] = star_color

            for y in range(horizon, HEIGHT):
                shade = GROUND_DARK if (y - horizon) % 2 == 0 else GROUND_LIT
                for x in range(WIDTH):
                    grid[y][x][2] = shade
                    if (x * 7 + y * 13) % 23 == 0:
                        grid[y][x][0] = ","
                        grid[y][x][1] = lerp_color(shade, (120, 90, 60), 0.6)

            for p in plants:
                grown = int(round(p.height))
                for i in range(grown):
                    row = horizon - 1 - i
                    if not (0 <= row < HEIGHT):
                        continue
                    if i == grown - 1 and p.height >= p.max_height:
                        grid[row][p.x][0] = "@"
                        grid[row][p.x][1] = p.blossom_color
                    elif i == grown - 1:
                        grid[row][p.x][0] = "~"
                        grid[row][p.x][1] = LEAF
                    else:
                        grid[row][p.x][0] = "|"
                        grid[row][p.x][1] = STEM

            if tick >= title_duration:
                for fl in fireflies:
                    fl[0] = (fl[0] + fl[2]) % WIDTH
                    fl[1] += fl[3]
                    if fl[1] < 1 or fl[1] > horizon - 2:
                        fl[3] *= -1
                for fx, fy, _, _ in fireflies:
                    x, y = int(fx), int(fy)
                    if 0 <= x < WIDTH and 0 <= y < horizon:
                        grid[y][x][0] = "o"
                        grid[y][x][1] = FIREFLY
                for p in plants:
                    p.step()

            title_lines = None
            if tick < title_duration:
                title_lines = ["G A R D E N", "", "a short by asciiverse"]
            elif tick >= total - end_duration:
                title_lines = ["-- bloom --"]
            if title_lines:
                top = max(0, (HEIGHT - len(title_lines)) // 2)
                for i, text in enumerate(title_lines):
                    row = top + i
                    if 0 <= row < HEIGHT:
                        for x, ch in enumerate(center(text, WIDTH)):
                            if ch != " ":
                                grid[row][x][0] = ch
                                grid[row][x][1] = TEXT_COLOR

            lines = [render_row([(c[0], c[1], c[2]) for c in row]) for row in grid]
            sys.stdout.write("\x1b[2J\x1b[H")
            sys.stdout.write("\n".join(lines))
            sys.stdout.write("\n")
            sys.stdout.flush()
            time.sleep(delay)
            tick += 1
    except KeyboardInterrupt:
        print(RESET)


if __name__ == "__main__":
    main()
