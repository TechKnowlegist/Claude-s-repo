from __future__ import annotations

from ..color import lerp_color, render_row
from .base import Scene

_GLYPHS = "01アイウエオカキクケコサシスセソタチツテト+-*/<>|=."

HEAD_COLOR = (215, 255, 220)  # near-white -- the leading glyph of each column
BRIGHT_GREEN = (45, 220, 95)
DARK_GREEN = (0, 40, 15)


class _Column:
    __slots__ = ("head", "length", "speed", "_progress")

    def __init__(self, head: float, length: int, speed: float) -> None:
        self.head = head
        self.length = length
        self.speed = speed
        self._progress = 0.0


class MatrixColor(Scene):
    """The classic green digital-rain look: a bright near-white head glyph
    per column, fading down through green to near-black along its trail.
    Same falling-column mechanics as the plain MatrixRain scene."""

    name = "matrix-green"
    color = True

    def __init__(self, width: int, height: int, seed: int | None = None) -> None:
        super().__init__(width, height, seed)
        self.columns = [self._spawn_column(randomize_head=True) for _ in range(width)]

    def _spawn_column(self, randomize_head: bool) -> _Column:
        length = self.rng.randint(3, max(4, self.height // 2))
        speed = self.rng.uniform(0.4, 1.4)
        head = self.rng.uniform(-self.height, 0) if randomize_head else -length
        return _Column(head=head, length=length, speed=speed)

    def step(self) -> None:
        super().step()
        for i, col in enumerate(self.columns):
            col._progress += col.speed
            while col._progress >= 1.0:
                col.head += 1
                col._progress -= 1.0
            if col.head - col.length > self.height:
                self.columns[i] = self._spawn_column(randomize_head=False)

    def render(self) -> list[str]:
        grid = [[[" ", None, None] for _ in range(self.width)] for _ in range(self.height)]
        for x, col in enumerate(self.columns):
            head_row = int(col.head)
            for offset in range(col.length):
                row = head_row - offset
                if 0 <= row < self.height:
                    glyph = self.rng.choice(_GLYPHS)
                    if offset == 0:
                        color = HEAD_COLOR
                    else:
                        color = lerp_color(BRIGHT_GREEN, DARK_GREEN, offset / col.length)
                    grid[row][x][0] = glyph
                    grid[row][x][1] = color
        return [render_row([(c[0], c[1], c[2]) for c in row]) for row in grid]
