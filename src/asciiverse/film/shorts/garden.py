"""GARDEN -- an original color short: dawn breaks over a plot of ground while
a handful of flowers grow in and fireflies drift by. Fully original content,
built with 24-bit ANSI color (background-painted sky/ground, colored stems
and blossoms) rather than the plain-text film toolkit.
"""

from __future__ import annotations

import random

from ...color import lerp_color, render_row, visible_length

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


class _Plant:
    def __init__(self, x, max_height, growth_rate, blossom_color):
        self.x = x
        self.max_height = max_height
        self.growth_rate = growth_rate
        self.height = 0.0
        self.blossom_color = blossom_color

    def step(self):
        if self.height < self.max_height:
            self.height = min(self.max_height, self.height + self.growth_rate)


class _Firefly:
    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy


def _center(text: str, width: int) -> str:
    if len(text) >= width:
        return text[:width]
    left = (width - len(text)) // 2
    return " " * left + text + " " * (width - len(text) - left)


class Garden:
    """Exposes the same step()/render()/finished interface the CLI already
    drives Scenes and Films with, so it plugs into `asciiverse film garden`
    with no other changes -- it just happens to render in color."""

    color = True  # tells nothing in particular yet, but documents intent

    def __init__(self, width: int = 100, height: int = 32, fps: int = 12, seed: int = 7):
        self.width, self.height, self.fps = width, height, fps
        self.rng = random.Random(seed)
        self.tick = 0
        self.horizon = int(height * 0.72)

        self.title_duration = fps * 3
        self.grow_duration = fps * 18
        self.end_duration = fps * 4
        self.total_frames = self.title_duration + self.grow_duration + self.end_duration
        self.finished = False

        num_plants = max(4, width // 14)
        self.plants = []
        for i in range(num_plants):
            x = int((i + 0.5) * width / num_plants) + self.rng.randint(-2, 2)
            x = max(0, min(width - 1, x))
            max_height = self.rng.randint(4, max(5, self.horizon - 2))
            duration_frames = self.grow_duration * self.rng.uniform(0.55, 0.95)
            growth_rate = max_height / max(1, duration_frames)
            color = self.rng.choice(BLOSSOM_COLORS)
            self.plants.append(_Plant(x, max_height, growth_rate, color))

        self.fireflies = [
            _Firefly(
                self.rng.uniform(0, width),
                self.rng.uniform(2, max(3, self.horizon - 4)),
                self.rng.uniform(-0.25, 0.25),
                self.rng.uniform(-0.08, 0.08),
            )
            for _ in range(5)
        ]
        self.stars = [
            (self.rng.uniform(0, width), self.rng.uniform(0, self.horizon - 1))
            for _ in range(30)
        ]

    def step(self) -> None:
        if self.finished:
            return
        self.tick += 1
        if self.tick >= self.title_duration:
            for p in self.plants:
                p.step()
            for f in self.fireflies:
                f.x = (f.x + f.vx) % self.width
                f.y += f.vy
                if f.y < 1 or f.y > self.horizon - 2:
                    f.vy *= -1
        if self.tick >= self.total_frames:
            self.finished = True

    def _sky_progress(self) -> float:
        if self.tick < self.title_duration:
            return 0.0
        t = (self.tick - self.title_duration) / max(1, self.grow_duration)
        return min(1.0, t)

    def render(self) -> list[str]:
        sky_t = self._sky_progress()
        sky_top = lerp_color(SKY_NIGHT, SKY_DAWN_TOP, sky_t)
        sky_horizon = lerp_color(SKY_NIGHT, SKY_DAWN_HORIZON, sky_t)

        # grid[y][x] = [char, fg, bg]
        grid = [[[" ", None, None] for _ in range(self.width)] for _ in range(self.height)]

        for y in range(self.horizon):
            row_t = y / max(1, self.horizon - 1)
            sky_color = lerp_color(sky_top, sky_horizon, row_t)
            for x in range(self.width):
                grid[y][x][2] = sky_color

        # Stars fade out as dawn (sky_t) approaches 1.
        star_alpha = max(0.0, 1.0 - sky_t * 1.4)
        if star_alpha > 0.02:
            for sx, sy in self.stars:
                x, y = int(sx), int(sy)
                if 0 <= x < self.width and 0 <= y < self.horizon:
                    bgc = grid[y][x][2]
                    star_color = lerp_color(bgc, STAR, star_alpha)
                    grid[y][x][0] = "."
                    grid[y][x][1] = star_color

        for y in range(self.horizon, self.height):
            shade = GROUND_DARK if (y - self.horizon) % 2 == 0 else GROUND_LIT
            for x in range(self.width):
                grid[y][x][2] = shade
                if (x * 7 + y * 13) % 23 == 0:
                    grid[y][x][0] = ","
                    grid[y][x][1] = lerp_color(shade, (120, 90, 60), 0.6)

        for p in self.plants:
            x = p.x
            if not (0 <= x < self.width):
                continue
            grown = int(round(p.height))
            for i in range(grown):
                row = self.horizon - 1 - i
                if not (0 <= row < self.height):
                    continue
                if i == grown - 1 and p.height >= p.max_height:
                    grid[row][x][0] = "@"
                    grid[row][x][1] = p.blossom_color
                elif i == grown - 1:
                    grid[row][x][0] = "~"
                    grid[row][x][1] = LEAF
                else:
                    grid[row][x][0] = "|"
                    grid[row][x][1] = STEM

        for f in self.fireflies:
            if self.tick < self.title_duration:
                continue
            x, y = int(f.x), int(f.y)
            if 0 <= x < self.width and 0 <= y < self.horizon:
                grid[y][x][0] = "o"
                grid[y][x][1] = FIREFLY

        if self.tick < self.title_duration:
            self._draw_text(grid, ["G A R D E N", "", "a short by asciiverse"])
        elif self.tick >= self.total_frames - self.end_duration:
            self._draw_text(grid, ["-- bloom --"])

        rows = []
        for row in grid:
            rows.append(render_row([(ch, f, b) for ch, f, b in row]))
        return rows

    def _draw_text(self, grid, lines: list[str]) -> None:
        top = max(0, (self.height - len(lines)) // 2)
        for i, text in enumerate(lines):
            row = top + i
            if not (0 <= row < self.height):
                continue
            centered = _center(text, self.width)
            for x, ch in enumerate(centered):
                if ch != " ":
                    grid[row][x][0] = ch
                    grid[row][x][1] = TEXT_COLOR


def build_garden(width: int = 100, height: int = 32, fps: int = 12) -> Garden:
    return Garden(width=width, height=height, fps=fps)
