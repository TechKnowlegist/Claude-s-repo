#!/usr/bin/env python3
"""Standalone ASCII fireworks, in color -- each burst picks a random hue
from a small palette and fades toward the night sky as it burns out.

No dependencies, no install. Needs a terminal that supports ANSI color
(Windows Terminal, modern cmd.exe/PowerShell on Windows 10+, or any Mac/
Linux terminal).

Run:  python ascii_fireworks_color.py
Quit: Ctrl+C
"""

import math
import random
import sys
import time

WIDTH = 90
HEIGHT = 30
LAUNCH_CHANCE = 0.08
MAX_ROCKETS = 3
FPS = 24
SEED = None  # set an int here for a reproducible run

NIGHT_SKY = (8, 8, 22)
TRAIL_COLOR = (255, 240, 190)
GRAVITY = 0.05
SPARK_SHAPES = "*+.oO@"

FIREWORK_COLORS = [
    (255, 90, 90),    # red
    (255, 200, 70),   # gold
    (110, 230, 130),  # green
    (110, 170, 255),  # blue
    (210, 130, 255),  # violet
    (110, 235, 235),  # cyan
    (255, 130, 210),  # pink
    (245, 245, 255),  # silver
]

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


class Rocket:
    __slots__ = ("x", "y", "vy", "color")

    def __init__(self, x, y, vy, color):
        self.x, self.y, self.vy, self.color = x, y, vy, color


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color")

    def __init__(self, x, y, vx, vy, life, color):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.color = color


def maybe_launch(rng, rockets, width, height):
    if len(rockets) < MAX_ROCKETS and rng.random() < LAUNCH_CHANCE:
        x = rng.uniform(width * 0.15, width * 0.85)
        target_height = rng.uniform(height * 0.3, height * 0.8)
        vy = -target_height / 12.0
        rockets.append(Rocket(x=x, y=float(height - 1), vy=vy, color=rng.choice(FIREWORK_COLORS)))


def explode(rng, rocket, particles):
    for _ in range(rng.randint(24, 42)):
        angle = rng.uniform(0, 2 * math.pi)
        speed = rng.uniform(0.3, 1.5)
        vx, vy = speed * math.cos(angle), speed * math.sin(angle)
        particles.append(Particle(rocket.x, rocket.y, vx, vy, rng.randint(9, 18), rocket.color))


def step(rng, rockets, particles, width, height):
    maybe_launch(rng, rockets, width, height)

    still_flying = []
    for rocket in rockets:
        rocket.y += rocket.vy
        rocket.vy += GRAVITY * 0.5
        if rocket.vy >= -0.05 or rocket.y <= 0:
            explode(rng, rocket, particles)
        else:
            still_flying.append(rocket)
    rockets[:] = still_flying

    still_alive = []
    for p in particles:
        p.x += p.vx
        p.y += p.vy
        p.vy += GRAVITY
        p.life -= 1
        if p.life > 0 and 0 <= p.x < width and 0 <= p.y < height:
            still_alive.append(p)
    particles[:] = still_alive


def render(rockets, particles, width, height):
    grid = [[[" ", None, NIGHT_SKY] for _ in range(width)] for _ in range(height)]
    for rocket in rockets:
        x, y = int(rocket.x), int(rocket.y)
        if 0 <= x < width and 0 <= y < height:
            grid[y][x][0] = "|"
            grid[y][x][1] = TRAIL_COLOR
    for p in particles:
        x, y = int(p.x), int(p.y)
        if 0 <= x < width and 0 <= y < height:
            fraction = p.life / p.max_life
            idx = min(len(SPARK_SHAPES) - 1, int(fraction * len(SPARK_SHAPES)))
            grid[y][x][0] = SPARK_SHAPES[idx]
            grid[y][x][1] = lerp_color(NIGHT_SKY, p.color, fraction)
    return [render_row([(c[0], c[1], c[2]) for c in row]) for row in grid]


def main():
    rng = random.Random(SEED)
    rockets, particles = [], []
    delay = 1.0 / FPS
    sys.stdout.write("\x1b[2J\x1b[?25l")
    try:
        while True:
            sys.stdout.write("\x1b[H")
            sys.stdout.write("\n".join(render(rockets, particles, WIDTH, HEIGHT)))
            sys.stdout.write("\n")
            sys.stdout.flush()
            step(rng, rockets, particles, WIDTH, HEIGHT)
            time.sleep(delay)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(RESET + "\x1b[?25h\n")


if __name__ == "__main__":
    main()
