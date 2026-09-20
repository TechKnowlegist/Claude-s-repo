#!/usr/bin/env python3
"""ORBITAL -- a standalone ~30 second original ASCII short film.

A title card, a scrolling text crawl over a starfield, a hand-drawn ship
flying through with subtitled dialogue, and a fireworks finale. Entirely
original, entirely generated, no dependencies, no install.

Run:  python ascii_film_orbital.py
Quit: Ctrl+C
"""

import math
import random
import sys
import time

WIDTH = 90
HEIGHT = 28
FPS = 12

# ---------------------------------------------------------------------------
# Tiny compositing helpers
# ---------------------------------------------------------------------------


def blank(width, height):
    return [" " * width for _ in range(height)]


def center(text, width):
    if len(text) >= width:
        return text[:width]
    left = (width - len(text)) // 2
    return " " * left + text + " " * (width - len(text) - left)


def draw_text_block(background, lines, top, width):
    grid = [list(row) for row in background]
    for i, text in enumerate(lines):
        row = top + i
        if 0 <= row < len(grid):
            grid[row] = list(center(text, width))
    return ["".join(row) for row in grid]


def composite(background, art, x, y):
    grid = [list(row) for row in background]
    height, width = len(grid), (len(grid[0]) if grid else 0)
    for row_idx, art_row in enumerate(art):
        gy = y + row_idx
        if not (0 <= gy < height):
            continue
        for col_idx, ch in enumerate(art_row):
            gx = x + col_idx
            if ch != " " and 0 <= gx < width:
                grid[gy][gx] = ch
    return ["".join(row) for row in grid]


def dither_fade(lines, factor):
    if factor >= 0.999:
        return lines
    if factor <= 0.001:
        return [" " * len(line) for line in lines]
    threshold = factor * 100
    out = []
    for y, line in enumerate(lines):
        chars = []
        for x, ch in enumerate(line):
            if ch == " ":
                chars.append(" ")
                continue
            h = (x * 928371 + y * 719393 + 104729) % 100
            chars.append(ch if h < threshold else " ")
        out.append("".join(chars))
    return out


def fade_factor(local_tick, duration, fade_frames):
    if fade_frames <= 0:
        return 1.0
    if local_tick < fade_frames:
        return local_tick / fade_frames
    remaining = duration - 1 - local_tick
    if remaining < fade_frames:
        return max(0.0, remaining / fade_frames)
    return 1.0


# ---------------------------------------------------------------------------
# Starfield backdrop
# ---------------------------------------------------------------------------

BRIGHTNESS = ".,-~:;=!*#@"


class Star:
    __slots__ = ("x", "y", "z")

    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z


class Starfield:
    def __init__(self, width, height, rng, num_stars=140, speed=0.02):
        self.width, self.height, self.rng, self.speed = width, height, rng, speed
        self.stars = [self._spawn(fresh=False) for _ in range(num_stars)]

    def _spawn(self, fresh):
        x = self.rng.uniform(-1.0, 1.0)
        y = self.rng.uniform(-1.0, 1.0)
        z = self.rng.uniform(0.05, 1.0) if fresh else self.rng.uniform(0.001, 1.0)
        return Star(x, y, z)

    def step(self):
        for star in self.stars:
            star.z -= self.speed
            if star.z <= 0.001:
                fresh = self._spawn(fresh=True)
                star.x, star.y, star.z = fresh.x, fresh.y, fresh.z

    def render(self):
        grid = [[" "] * self.width for _ in range(self.height)]
        half_w, half_h = self.width / 2, self.height / 2
        for star in self.stars:
            px = int(half_w + (star.x / star.z) * half_w)
            py = int(half_h + (star.y / star.z) * half_h)
            if 0 <= px < self.width and 0 <= py < self.height:
                idx = min(len(BRIGHTNESS) - 1, int((1.0 - star.z) * len(BRIGHTNESS)))
                grid[py][px] = BRIGHTNESS[idx]
        return ["".join(row) for row in grid]


# ---------------------------------------------------------------------------
# Fireworks backdrop
# ---------------------------------------------------------------------------

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
        self.life = self.max_life = life


class Fireworks:
    def __init__(self, width, height, rng, launch_chance=0.15, max_rockets=4):
        self.width, self.height, self.rng = width, height, rng
        self.launch_chance, self.max_rockets = launch_chance, max_rockets
        self.rockets, self.particles = [], []

    def step(self):
        if len(self.rockets) < self.max_rockets and self.rng.random() < self.launch_chance:
            x = self.rng.uniform(self.width * 0.15, self.width * 0.85)
            target = self.rng.uniform(self.height * 0.3, self.height * 0.8)
            self.rockets.append(Rocket(x=x, y=float(self.height - 1), vy=-target / 12.0))

        still_flying = []
        for rocket in self.rockets:
            rocket.y += rocket.vy
            rocket.vy += GRAVITY * 0.5
            if rocket.vy >= -0.05 or rocket.y <= 0:
                for _ in range(self.rng.randint(20, 36)):
                    angle = self.rng.uniform(0, 2 * math.pi)
                    speed = self.rng.uniform(0.3, 1.4)
                    vx, vy = speed * math.cos(angle), speed * math.sin(angle)
                    self.particles.append(
                        Particle(rocket.x, rocket.y, vx, vy, self.rng.randint(8, 16))
                    )
            else:
                still_flying.append(rocket)
        self.rockets = still_flying

        still_alive = []
        for p in self.particles:
            p.x += p.vx
            p.y += p.vy
            p.vy += GRAVITY
            p.life -= 1
            if p.life > 0 and 0 <= p.x < self.width and 0 <= p.y < self.height:
                still_alive.append(p)
        self.particles = still_alive

    def render(self):
        grid = [[" "] * self.width for _ in range(self.height)]
        for rocket in self.rockets:
            x, y = int(rocket.x), int(rocket.y)
            if 0 <= x < self.width and 0 <= y < self.height:
                grid[y][x] = "|"
        for p in self.particles:
            x, y = int(p.x), int(p.y)
            if 0 <= x < self.width and 0 <= y < self.height:
                idx = min(len(SPARK_CHARS) - 1, int((p.life / p.max_life) * len(SPARK_CHARS)))
                grid[y][x] = SPARK_CHARS[idx]
        return ["".join(row) for row in grid]


# ---------------------------------------------------------------------------
# The film: title card, crawl, ship flyby, fireworks, end card
# ---------------------------------------------------------------------------

SHIP = ["   /\\", "  /--\\", " <==>>", "  \\--/"]
SHIP_W, SHIP_H = max(len(r) for r in SHIP), len(SHIP)


def shot_title(local_tick, width, height, lines, duration, fade_frames):
    top = max(0, (height - len(lines)) // 2)
    frame = draw_text_block(blank(width, height), lines, top, width)
    return dither_fade(frame, fade_factor(local_tick, duration, fade_frames))


def shot_crawl(local_tick, width, height, backdrop, lines, duration):
    if local_tick > 0:
        backdrop.step()
    base = dither_fade(backdrop.render(), 0.35)
    start_row, end_row = height, -len(lines) - 1
    progress = local_tick / max(1, duration - 1)
    top = round(start_row + (end_row - start_row) * progress)
    return draw_text_block(base, lines, top, width)


def shot_ship(local_tick, width, height, backdrop, duration, subtitles):
    if local_tick > 0:
        backdrop.step()
    lines = backdrop.render()
    progress = local_tick / max(1, duration - 1)
    x = int(-SHIP_W + progress * (width + 2 * SHIP_W))
    y = height // 2 - SHIP_H // 2 + int(round(1.5 * math.sin(local_tick / 6.0)))
    lines = composite(lines, SHIP, x, y)
    for start, end, text in subtitles:
        if start <= local_tick < end:
            lines = draw_text_block(lines, [text], height - 2, width)
    return lines


def shot_fireworks(local_tick, width, height, backdrop, duration, subtitle, fade_frames):
    if local_tick > 0:
        backdrop.step()
    lines = backdrop.render()
    lines = draw_text_block(lines, [subtitle], height - 2, width)
    return dither_fade(lines, fade_factor(local_tick, duration, fade_frames))


def main():
    rng = random.Random(3)
    ship_rng = random.Random(11)
    fw_rng = random.Random(5)

    title_duration = FPS * 4
    crawl_duration = FPS * 9
    contact_duration = FPS * 6
    fireworks_duration = FPS * 5
    end_duration = FPS * 4
    total = title_duration + crawl_duration + contact_duration + fireworks_duration + end_duration

    crawl_backdrop = Starfield(WIDTH, HEIGHT, rng, speed=0.015)
    ship_backdrop = Starfield(WIDTH, HEIGHT, ship_rng, num_stars=90, speed=0.03)
    fw_backdrop = Fireworks(WIDTH, HEIGHT, fw_rng)

    crawl_lines = [
        "Year 41 of the Long Silence.",
        "",
        "The relay station STILL POINT",
        "has not answered a hail",
        "in eleven thousand cycles.",
        "",
        "Command sends one ship --",
        "and one pilot who volunteered",
        "before anyone could stop her.",
    ]
    subtitles = [
        (0, FPS * 2, "KESTREL: Still Point, this is Kestrel. Do you copy?"),
        (FPS * 2, FPS * 4, "..."),
        (FPS * 4, FPS * 6, "STILL POINT: Copy that, Kestrel. We copy."),
    ]

    delay = 1.0 / FPS
    tick = 0
    # Clear once and hide the cursor, then just home the cursor each frame
    # instead of clearing every time -- clearing every frame makes most
    # terminals flash blank before each redraw, which looks like flicker.
    sys.stdout.write("\x1b[2J\x1b[?25l")
    try:
        while tick < total:
            if tick < title_duration:
                lines = shot_title(
                    tick, WIDTH, HEIGHT,
                    ["O R B I T A L", "", "a short by asciiverse"],
                    title_duration, FPS,
                )
            elif tick < title_duration + crawl_duration:
                lines = shot_crawl(tick - title_duration, WIDTH, HEIGHT, crawl_backdrop, crawl_lines, crawl_duration)
            elif tick < title_duration + crawl_duration + contact_duration:
                lines = shot_ship(
                    tick - title_duration - crawl_duration, WIDTH, HEIGHT,
                    ship_backdrop, contact_duration, subtitles,
                )
            elif tick < title_duration + crawl_duration + contact_duration + fireworks_duration:
                lines = shot_fireworks(
                    tick - title_duration - crawl_duration - contact_duration, WIDTH, HEIGHT,
                    fw_backdrop, fireworks_duration,
                    "Lights, all at once. Still Point wakes up.", FPS // 2,
                )
            else:
                local = tick - (title_duration + crawl_duration + contact_duration + fireworks_duration)
                lines = shot_title(
                    local, WIDTH, HEIGHT,
                    ["THE END", "", "an original ascii short", "made with asciiverse"],
                    end_duration, FPS,
                )

            sys.stdout.write("\x1b[H")
            sys.stdout.write("\n".join(lines))
            sys.stdout.write("\n")
            sys.stdout.flush()
            time.sleep(delay)
            tick += 1
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[?25h\n")


if __name__ == "__main__":
    main()
