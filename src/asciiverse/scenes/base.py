"""Shared interface for scenes.

Every scene is a small, self-contained simulation that is completely
independent of how it gets drawn. ``step()`` advances the simulation by one
tick and ``render()`` returns a list of ``height`` strings, each exactly
``width`` characters wide. Keeping the simulation free of any terminal or
curses dependency is what makes the scenes trivial to unit test.
"""

from __future__ import annotations

import random


class Scene:
    name = "scene"

    def __init__(self, width: int, height: int, seed: int | None = None) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.tick = 0

    def step(self) -> None:
        """Advance the simulation by one frame."""
        self.tick += 1

    def render(self) -> list[str]:
        """Return ``self.height`` strings, each ``self.width`` chars wide."""
        raise NotImplementedError

    def _blank_grid(self, fill: str = " ") -> list[list[str]]:
        return [[fill for _ in range(self.width)] for _ in range(self.height)]

    @staticmethod
    def _grid_to_lines(grid: list[list[str]]) -> list[str]:
        return ["".join(row) for row in grid]
