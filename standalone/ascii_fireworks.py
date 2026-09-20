#!/usr/bin/env python3
"""Standalone ASCII fireworks animation. No dependencies, no install.

Run:  python ascii_fireworks.py
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

SPARK_CHARS = "*+.oO@"
GRAVITY = 0.05


class Rocket:
    __slots__ = ("x", "y", "vy")

    def __init__(self, x, y, vy):
        self.x, self.y, self.vy = x, y, vy


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life")

    def __init__(self, x, y, vx, vy, life):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = life
        self.max_life = life


def maybe_launch(rng, rockets, width, height):
    if len(rockets) < MAX_ROCKETS and rng.random() < LAUNCH_CHANCE:
        x = rng.uniform(width * 0.15, width * 0.85)
        target_height = rng.uniform(height * 0.3, height * 0.8)
        vy = -target_height / 12.0
        rockets.append(Rocket(x=x, y=float(height - 1), vy=vy))


def explode(rng, rocket, particles):
    for _ in range(rng.randint(20, 36)):
        angle = rng.uniform(0, 2 * math.pi)
        speed = rng.uniform(0.3, 1.4)
        vx, vy = speed * math.cos(angle), speed * math.sin(angle)
        particles.append(Particle(rocket.x, rocket.y, vx, vy, rng.randint(8, 16)))


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
    grid = [[" "] * width for _ in range(height)]
    for rocket in rockets:
        x, y = int(rocket.x), int(rocket.y)
        if 0 <= x < width and 0 <= y < height:
            grid[y][x] = "|"
    for p in particles:
        x, y = int(p.x), int(p.y)
        if 0 <= x < width and 0 <= y < height:
            fraction = p.life / p.max_life
            idx = min(len(SPARK_CHARS) - 1, int(fraction * len(SPARK_CHARS)))
            grid[y][x] = SPARK_CHARS[idx]
    return ["".join(row) for row in grid]


def main():
    rng = random.Random(SEED)
    rockets, particles = [], []
    delay = 1.0 / FPS
    # Clear once and hide the cursor, then just home the cursor each frame
    # instead of clearing every time -- clearing every frame makes most
    # terminals flash blank before each redraw, which looks like flicker.
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
        sys.stdout.write("\x1b[?25h\n")


if __name__ == "__main__":
    main()
