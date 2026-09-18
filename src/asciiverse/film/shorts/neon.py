"""NEON CITY -- an original color short: a synthwave-style skyline, a glowing
sun sinking behind silhouetted buildings, and a scrolling neon floor grid.
Generic retro-futurist aesthetic, entirely original -- no existing IP.
"""

from __future__ import annotations

import random

from ...color import lerp_color, render_row

SKY_TOP = (20, 8, 45)
SKY_HORIZON = (255, 60, 130)
SUN_BANDS = [(255, 240, 200), (255, 190, 120), (255, 120, 130), (230, 70, 160)]
BUILDING = (18, 10, 30)
WINDOW = (120, 230, 255)
GRID_A = (255, 60, 200)
GRID_B = (60, 220, 255)
STREAK_COLORS = [(120, 230, 255), (255, 90, 200)]
TEXT_COLOR = (235, 245, 255)


def _center(text: str, width: int) -> str:
    if len(text) >= width:
        return text[:width]
    left = (width - len(text)) // 2
    return " " * left + text + " " * (width - len(text) - left)


class _Building:
    __slots__ = ("x", "width", "height", "windows")

    def __init__(self, x, width, height, rng):
        self.x, self.width, self.height = x, width, height
        self.windows = {
            (dx, dy)
            for dx in range(1, width - 1, 2)
            for dy in range(1, height, 2)
            if rng.random() < 0.6
        }


class _Streak:
    __slots__ = ("y", "x", "vx", "length", "color")

    def __init__(self, y, x, vx, length, color):
        self.y, self.x, self.vx, self.length, self.color = y, x, vx, length, color


class NeonCity:
    """A color short. Same step()/render()/finished interface as a Scene."""

    color = True

    def __init__(self, width: int = 100, height: int = 32, fps: int = 12, seed: int = 21):
        self.width, self.height, self.fps = width, height, fps
        self.rng = random.Random(seed)
        self.tick = 0
        self.horizon = int(height * 0.62)
        self.sun_row = int(self.horizon * 0.45)
        self.sun_radius = max(3, height // 7)

        self.title_duration = fps * 3
        self.city_duration = fps * 16
        self.end_duration = fps * 4
        self.total_frames = self.title_duration + self.city_duration + self.end_duration
        self.finished = False

        self.buildings = []
        x = 0
        while x < width:
            bw = self.rng.randint(4, 9)
            bh = self.rng.randint(3, self.horizon - self.sun_row - 2)
            bh = max(2, bh)
            self.buildings.append(_Building(x, bw, bh, self.rng))
            x += bw + self.rng.randint(0, 2)

        self.streaks = [
            _Streak(
                y=self.rng.randint(self.sun_row + 1, self.horizon - 2),
                x=self.rng.uniform(0, width),
                vx=self.rng.choice([-1, 1]) * self.rng.uniform(0.6, 1.6),
                length=self.rng.randint(4, 8),
                color=self.rng.choice(STREAK_COLORS),
            )
            for _ in range(4)
        ]
        self.grid_scroll = 0.0

    def step(self) -> None:
        if self.finished:
            return
        self.tick += 1
        if self.tick >= self.title_duration:
            self.grid_scroll += 0.5
            for s in self.streaks:
                s.x = (s.x + s.vx) % self.width
        if self.tick >= self.total_frames:
            self.finished = True

    def render(self) -> list[str]:
        grid = [[[" ", None, None] for _ in range(self.width)] for _ in range(self.height)]

        # Sky gradient.
        for y in range(self.horizon):
            row_t = y / max(1, self.horizon - 1)
            sky = lerp_color(SKY_TOP, SKY_HORIZON, row_t)
            for x in range(self.width):
                grid[y][x][2] = sky

        # Sun: concentric color bands with a few scanline gaps punched through.
        cx = self.width / 2
        for y in range(max(0, self.sun_row - self.sun_radius), min(self.horizon, self.sun_row + self.sun_radius + 1)):
            dy = y - self.sun_row
            span = (self.sun_radius ** 2 - dy ** 2)
            if span < 0:
                continue
            half_w = int(span ** 0.5)
            if (self.sun_row + self.sun_radius - y) % 3 == 0 and dy > -self.sun_radius * 0.3:
                continue  # scanline gap
            band_t = 1 - (abs(dy) / max(1, self.sun_radius))
            band = SUN_BANDS[min(len(SUN_BANDS) - 1, int((1 - band_t) * len(SUN_BANDS)))]
            for x in range(int(cx - half_w), int(cx + half_w) + 1):
                if 0 <= x < self.width:
                    grid[y][x][2] = band

        # Neon floor grid below the horizon, scrolling toward the viewer.
        for y in range(self.horizon, self.height):
            depth = y - self.horizon
            spacing = max(2, 6 - depth // 2)
            offset = int(self.grid_scroll) % spacing
            line_here = (depth + offset) % spacing == 0
            for x in range(self.width):
                grid[y][x][2] = (10, 4, 20)
                if line_here:
                    grid[y][x][0] = "-"
                    grid[y][x][1] = GRID_A if (x // 4) % 2 == 0 else GRID_B

        # Building silhouettes sitting on the horizon.
        for b in self.buildings:
            top = self.horizon - b.height
            for dy in range(b.height):
                row = top + dy
                if not (0 <= row < self.height):
                    continue
                for dx in range(b.width):
                    x = b.x + dx
                    if not (0 <= x < self.width):
                        continue
                    grid[row][x][2] = BUILDING
                    grid[row][x][0] = " "
                    if (dx, dy) in b.windows:
                        grid[row][x][0] = "="
                        grid[row][x][1] = WINDOW

        # Distant light streaks drifting above the horizon.
        if self.tick >= self.title_duration:
            for s in self.streaks:
                for i in range(s.length):
                    x = int(s.x - i * (1 if s.vx > 0 else -1)) % self.width
                    y = s.y
                    if 0 <= y < self.horizon:
                        grid[y][x][0] = "-"
                        grid[y][x][1] = s.color

        if self.tick < self.title_duration:
            self._draw_text(grid, ["N E O N   C I T Y", "", "a short by asciiverse"])
        elif self.tick >= self.total_frames - self.end_duration:
            self._draw_text(grid, ["THE CITY NEVER SLEEPS"])

        return [render_row([(ch, f, b) for ch, f, b in row]) for row in grid]

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


def build_neon(width: int = 100, height: int = 32, fps: int = 12) -> NeonCity:
    return NeonCity(width=width, height=height, fps=fps)
