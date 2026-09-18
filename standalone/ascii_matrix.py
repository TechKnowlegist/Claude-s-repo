#!/usr/bin/env python3
"""Standalone ASCII digital-rain animation. No dependencies, no install.

Run:  python ascii_matrix.py
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


class Column:
    __slots__ = ("head", "length", "speed", "progress")

    def __init__(self, head, length, speed):
        self.head = head
        self.length = length
        self.speed = speed
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
    grid = [[" "] * width for _ in range(height)]
    for x, col in enumerate(columns):
        head_row = int(col.head)
        for offset in range(col.length):
            row = head_row - offset
            if 0 <= row < height:
                grid[row][x] = rng.choice(GLYPHS)
    return ["".join(row) for row in grid]


def main():
    rng = random.Random(SEED)
    columns = [spawn_column(rng, HEIGHT, randomize_head=True) for _ in range(WIDTH)]
    delay = 1.0 / FPS
    try:
        while True:
            sys.stdout.write("\x1b[2J\x1b[H")
            sys.stdout.write("\n".join(render(columns, rng, WIDTH, HEIGHT)))
            sys.stdout.write("\n")
            sys.stdout.flush()
            step(columns, rng, HEIGHT)
            time.sleep(delay)
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()
