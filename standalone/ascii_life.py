#!/usr/bin/env python3
"""Standalone Conway's Game of Life (ASCII, wrapping grid). No dependencies.

Run:  python ascii_life.py
Quit: Ctrl+C
"""

import random
import sys
import time

WIDTH = 80
HEIGHT = 30
DENSITY = 0.25
FPS = 12
SEED = None  # set an int here for a reproducible run

NEIGHBOR_OFFSETS = [
    (-1, -1), (0, -1), (1, -1),
    (-1, 0), (1, 0),
    (-1, 1), (0, 1), (1, 1),
]


def randomize(width, height, rng, density):
    return {
        (x, y)
        for y in range(height)
        for x in range(width)
        if rng.random() < density
    }


def neighbor_count(alive, width, height, x, y):
    count = 0
    for dx, dy in NEIGHBOR_OFFSETS:
        if ((x + dx) % width, (y + dy) % height) in alive:
            count += 1
    return count


def step(alive, width, height, rng):
    candidates = set(alive)
    for x, y in alive:
        for dx, dy in NEIGHBOR_OFFSETS:
            candidates.add(((x + dx) % width, (y + dy) % height))

    next_alive = set()
    for x, y in candidates:
        n = neighbor_count(alive, width, height, x, y)
        if (x, y) in alive:
            if n in (2, 3):
                next_alive.add((x, y))
        elif n == 3:
            next_alive.add((x, y))

    if not next_alive:  # an extinct board is boring -- reseed it
        return randomize(width, height, rng, DENSITY)
    return next_alive


def render(alive, width, height):
    grid = [[" "] * width for _ in range(height)]
    for x, y in alive:
        grid[y][x] = "#"
    return ["".join(row) for row in grid]


def main():
    rng = random.Random(SEED)
    alive = randomize(WIDTH, HEIGHT, rng, DENSITY)
    delay = 1.0 / FPS
    try:
        while True:
            sys.stdout.write("\x1b[2J\x1b[H")
            sys.stdout.write("\n".join(render(alive, WIDTH, HEIGHT)))
            sys.stdout.write("\n")
            sys.stdout.flush()
            alive = step(alive, WIDTH, HEIGHT, rng)
            time.sleep(delay)
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()
