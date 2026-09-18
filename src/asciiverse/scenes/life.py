from __future__ import annotations

from .base import Scene

_ALIVE = "#"
_DEAD = " "

_NEIGHBOR_OFFSETS = [
    (-1, -1), (0, -1), (1, -1),
    (-1, 0), (1, 0),
    (-1, 1), (0, 1), (1, 1),
]


class Life(Scene):
    """Conway's Game of Life on a wrapping (toroidal) grid."""

    name = "life"

    def __init__(
        self,
        width: int,
        height: int,
        seed: int | None = None,
        density: float = 0.25,
    ) -> None:
        super().__init__(width, height, seed)
        self.alive: set[tuple[int, int]] = set()
        self.generation = 0
        self.randomize(density)

    def randomize(self, density: float) -> None:
        self.alive = {
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self.rng.random() < density
        }
        self.generation = 0

    def _neighbor_count(self, x: int, y: int) -> int:
        count = 0
        for dx, dy in _NEIGHBOR_OFFSETS:
            if ((x + dx) % self.width, (y + dy) % self.height) in self.alive:
                count += 1
        return count

    def step(self) -> None:
        super().step()
        candidates = set(self.alive)
        for x, y in self.alive:
            for dx, dy in _NEIGHBOR_OFFSETS:
                candidates.add(((x + dx) % self.width, (y + dy) % self.height))

        next_alive = set()
        for cell in candidates:
            x, y = cell
            n = self._neighbor_count(x, y)
            if cell in self.alive:
                if n in (2, 3):
                    next_alive.add(cell)
            elif n == 3:
                next_alive.add(cell)

        # An extinct board is boring in a terminal toy: reseed it. Still
        # lifes and oscillators are left alone -- they're the whole point.
        if not next_alive:
            self.randomize(density=0.25)
        else:
            self.alive = next_alive
            self.generation += 1

    def render(self) -> list[str]:
        grid = self._blank_grid(fill=_DEAD)
        for x, y in self.alive:
            if 0 <= x < self.width and 0 <= y < self.height:
                grid[y][x] = _ALIVE
        return self._grid_to_lines(grid)
