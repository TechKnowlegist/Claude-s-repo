#!/usr/bin/env python3
"""ECHO -- a standalone, quieter original ASCII short film.

A cellular automaton waking up, a machine dreaming in falling glyphs, and a
starfield it can't quite reach. Entirely original, entirely generated, no
dependencies, no install.

Run:  python ascii_film_echo.py
Quit: Ctrl+C
"""

import random
import sys
import time

WIDTH = 80
HEIGHT = 26
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
# Life backdrop (Conway's Game of Life on a wrapping grid)
# ---------------------------------------------------------------------------

NEIGHBOR_OFFSETS = [
    (-1, -1), (0, -1), (1, -1),
    (-1, 0), (1, 0),
    (-1, 1), (0, 1), (1, 1),
]


class Life:
    def __init__(self, width, height, rng, density=0.28):
        self.width, self.height, self.rng, self.density = width, height, rng, density
        self.alive = self._randomize()

    def _randomize(self):
        return {
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self.rng.random() < self.density
        }

    def _neighbors(self, x, y):
        count = 0
        for dx, dy in NEIGHBOR_OFFSETS:
            if ((x + dx) % self.width, (y + dy) % self.height) in self.alive:
                count += 1
        return count

    def step(self):
        candidates = set(self.alive)
        for x, y in self.alive:
            for dx, dy in NEIGHBOR_OFFSETS:
                candidates.add(((x + dx) % self.width, (y + dy) % self.height))
        next_alive = set()
        for x, y in candidates:
            n = self._neighbors(x, y)
            if (x, y) in self.alive:
                if n in (2, 3):
                    next_alive.add((x, y))
            elif n == 3:
                next_alive.add((x, y))
        self.alive = next_alive if next_alive else self._randomize()

    def render(self):
        grid = [[" "] * self.width for _ in range(self.height)]
        for x, y in self.alive:
            grid[y][x] = "#"
        return ["".join(row) for row in grid]


# ---------------------------------------------------------------------------
# Matrix rain backdrop
# ---------------------------------------------------------------------------

GLYPHS = "01ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄ+-*/<>|=."


class MatrixRain:
    def __init__(self, width, height, rng):
        self.width, self.height, self.rng = width, height, rng
        self.columns = [self._spawn(randomize_head=True) for _ in range(width)]

    def _spawn(self, randomize_head):
        length = self.rng.randint(3, max(4, self.height // 2))
        speed = self.rng.uniform(0.4, 1.4)
        head = self.rng.uniform(-self.height, 0) if randomize_head else -length
        return {"head": head, "length": length, "speed": speed, "progress": 0.0}

    def step(self):
        for i, col in enumerate(self.columns):
            col["progress"] += col["speed"]
            while col["progress"] >= 1.0:
                col["head"] += 1
                col["progress"] -= 1.0
            if col["head"] - col["length"] > self.height:
                self.columns[i] = self._spawn(randomize_head=False)

    def render(self):
        grid = [[" "] * self.width for _ in range(self.height)]
        for x, col in enumerate(self.columns):
            head_row = int(col["head"])
            for offset in range(col["length"]):
                row = head_row - offset
                if 0 <= row < self.height:
                    grid[row][x] = self.rng.choice(GLYPHS)
        return ["".join(row) for row in grid]


# ---------------------------------------------------------------------------
# Starfield backdrop
# ---------------------------------------------------------------------------

BRIGHTNESS = ".,-~:;=!*#@"


class Starfield:
    def __init__(self, width, height, rng, speed=0.01):
        self.width, self.height, self.rng, self.speed = width, height, rng, speed
        self.stars = [self._spawn(fresh=False) for _ in range(140)]

    def _spawn(self, fresh):
        x = self.rng.uniform(-1.0, 1.0)
        y = self.rng.uniform(-1.0, 1.0)
        z = self.rng.uniform(0.05, 1.0) if fresh else self.rng.uniform(0.001, 1.0)
        return [x, y, z]

    def step(self):
        for star in self.stars:
            star[2] -= self.speed
            if star[2] <= 0.001:
                star[:] = self._spawn(fresh=True)

    def render(self):
        grid = [[" "] * self.width for _ in range(self.height)]
        half_w, half_h = self.width / 2, self.height / 2
        for x, y, z in self.stars:
            px = int(half_w + (x / z) * half_w)
            py = int(half_h + (y / z) * half_h)
            if 0 <= px < self.width and 0 <= py < self.height:
                idx = min(len(BRIGHTNESS) - 1, int((1.0 - z) * len(BRIGHTNESS)))
                grid[py][px] = BRIGHTNESS[idx]
        return ["".join(row) for row in grid]


# ---------------------------------------------------------------------------
# The film: title, life, matrix, starfield, closing title
# ---------------------------------------------------------------------------


def shot_title(local_tick, width, height, lines, duration, fade_frames):
    top = max(0, (height - len(lines)) // 2)
    frame = draw_text_block(blank(width, height), lines, top, width)
    return dither_fade(frame, fade_factor(local_tick, duration, fade_frames))


def shot_backdrop(local_tick, width, height, backdrop, subtitles, fade_frames=0, duration=None):
    if local_tick > 0:
        backdrop.step()
    lines = backdrop.render()
    for start, end, text in subtitles:
        if start <= local_tick < end:
            lines = draw_text_block(lines, [text], height - 2, width)
    if fade_frames and duration:
        lines = dither_fade(lines, fade_factor(local_tick, duration, fade_frames))
    return lines


def main():
    title_duration = FPS * 3
    life_duration = FPS * 8
    matrix_duration = FPS * 6
    stars_duration = FPS * 6
    end_duration = FPS * 4
    total = title_duration + life_duration + matrix_duration + stars_duration + end_duration

    life = Life(WIDTH, HEIGHT, random.Random(2))
    matrix = MatrixRain(WIDTH, HEIGHT, random.Random(4))
    stars = Starfield(WIDTH, HEIGHT, random.Random(9))

    life_subs = [
        (0, FPS * 3, "Something is arranging itself."),
        (FPS * 3, FPS * 5, "It doesn't know why."),
        (FPS * 5, FPS * 8, "It keeps trying anyway."),
    ]
    matrix_subs = [
        (0, FPS * 3, "Somewhere, a memory repeats itself."),
        (FPS * 3, FPS * 6, "It calls this dreaming."),
    ]
    stars_subs = [(0, FPS * 6, "It reaches for something it cannot name.")]

    delay = 1.0 / FPS
    tick = 0
    # Clear once and hide the cursor, then just home the cursor each frame
    # instead of clearing every time -- clearing every frame makes most
    # terminals flash blank before each redraw, which looks like flicker.
    sys.stdout.write("\x1b[2J\x1b[?25l")
    try:
        while tick < total:
            if tick < title_duration:
                lines = shot_title(tick, WIDTH, HEIGHT, ["E C H O"], title_duration, FPS)
            elif tick < title_duration + life_duration:
                lines = shot_backdrop(tick - title_duration, WIDTH, HEIGHT, life, life_subs)
            elif tick < title_duration + life_duration + matrix_duration:
                lines = shot_backdrop(tick - title_duration - life_duration, WIDTH, HEIGHT, matrix, matrix_subs)
            elif tick < title_duration + life_duration + matrix_duration + stars_duration:
                local = tick - title_duration - life_duration - matrix_duration
                lines = shot_backdrop(local, WIDTH, HEIGHT, stars, stars_subs, fade_frames=FPS // 2, duration=stars_duration)
            else:
                local = tick - (title_duration + life_duration + matrix_duration + stars_duration)
                lines = shot_title(local, WIDTH, HEIGHT, ["E C H O", "", "-- end --"], end_duration, FPS)

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
