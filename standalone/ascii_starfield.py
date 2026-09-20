#!/usr/bin/env python3
"""Standalone ASCII starfield animation. No dependencies, no install.

Run:  python ascii_starfield.py
Quit: Ctrl+C
"""

import random
import sys
import time

WIDTH = 90
HEIGHT = 30
NUM_STARS = 160
SPEED = 0.02
FPS = 24
SEED = None  # set an int here for a reproducible run

BRIGHTNESS = ".,-~:;=!*#@"


class Star:
    __slots__ = ("x", "y", "z")

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


def spawn_star(rng, fresh):
    x = rng.uniform(-1.0, 1.0)
    y = rng.uniform(-1.0, 1.0)
    z = rng.uniform(0.05, 1.0) if fresh else rng.uniform(0.001, 1.0)
    return Star(x, y, z)


def step(stars, rng, speed):
    for star in stars:
        star.z -= speed
        if star.z <= 0.001:
            fresh = spawn_star(rng, fresh=True)
            star.x, star.y, star.z = fresh.x, fresh.y, fresh.z


def render(stars, width, height):
    grid = [[" "] * width for _ in range(height)]
    half_w, half_h = width / 2, height / 2
    for star in stars:
        px = int(half_w + (star.x / star.z) * half_w)
        py = int(half_h + (star.y / star.z) * half_h)
        if 0 <= px < width and 0 <= py < height:
            idx = min(len(BRIGHTNESS) - 1, int((1.0 - star.z) * len(BRIGHTNESS)))
            char = BRIGHTNESS[idx]
            existing = grid[py][px]
            if existing == " " or BRIGHTNESS.index(char) > (
                BRIGHTNESS.index(existing) if existing in BRIGHTNESS else -1
            ):
                grid[py][px] = char
    return ["".join(row) for row in grid]


def main():
    rng = random.Random(SEED)
    stars = [spawn_star(rng, fresh=False) for _ in range(NUM_STARS)]
    delay = 1.0 / FPS
    # Clear once and hide the cursor, then just home the cursor each frame
    # instead of clearing every time -- clearing every frame makes most
    # terminals flash blank before each redraw, which looks like flicker.
    sys.stdout.write("\x1b[2J\x1b[?25l")
    try:
        while True:
            sys.stdout.write("\x1b[H")
            sys.stdout.write("\n".join(render(stars, WIDTH, HEIGHT)))
            sys.stdout.write("\n")
            sys.stdout.flush()
            step(stars, rng, SPEED)
            time.sleep(delay)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[?25h\n")


if __name__ == "__main__":
    main()
