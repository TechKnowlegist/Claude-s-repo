from __future__ import annotations

from .base import Scene

_GLYPHS = "01アイウエオカキクケコサシスセソタチツテト+-*/<>|=."


class _Column:
    __slots__ = ("head", "length", "speed", "_progress")

    def __init__(self, head: float, length: int, speed: float) -> None:
        self.head = head
        self.length = length
        self.speed = speed
        self._progress = 0.0


class MatrixRain(Scene):
    """Falling glyph columns, à la digital rain."""

    name = "matrix"

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
        grid = self._blank_grid()
        for x, col in enumerate(self.columns):
            head_row = int(col.head)
            for offset in range(col.length):
                row = head_row - offset
                if 0 <= row < self.height:
                    glyph = self.rng.choice(_GLYPHS)
                    grid[row][x] = glyph
        return self._grid_to_lines(grid)
