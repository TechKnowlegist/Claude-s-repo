from __future__ import annotations

from .base import Scene

# Characters used from farthest to nearest.
_BRIGHTNESS = ".,-~:;=!*#@"


class Star:
    __slots__ = ("x", "y", "z")

    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z


class Starfield(Scene):
    """A warp-speed 3D starfield, projected onto a 2D character grid."""

    name = "starfield"

    def __init__(
        self,
        width: int,
        height: int,
        seed: int | None = None,
        num_stars: int = 140,
        speed: float = 0.02,
    ) -> None:
        super().__init__(width, height, seed)
        self.speed = speed
        self.stars = [self._spawn_star(fresh=False) for _ in range(num_stars)]

    def _spawn_star(self, fresh: bool = True) -> Star:
        x = self.rng.uniform(-1.0, 1.0)
        y = self.rng.uniform(-1.0, 1.0)
        z = self.rng.uniform(0.05, 1.0) if fresh else self.rng.uniform(0.001, 1.0)
        return Star(x, y, z)

    def step(self) -> None:
        super().step()
        for star in self.stars:
            star.z -= self.speed
            if star.z <= 0.001:
                fresh = self._spawn_star(fresh=True)
                star.x, star.y, star.z = fresh.x, fresh.y, fresh.z

    def render(self) -> list[str]:
        grid = self._blank_grid()
        half_w = self.width / 2
        half_h = self.height / 2
        for star in self.stars:
            px = int(half_w + (star.x / star.z) * half_w)
            py = int(half_h + (star.y / star.z) * half_h)
            if 0 <= px < self.width and 0 <= py < self.height:
                brightness_idx = min(
                    len(_BRIGHTNESS) - 1,
                    int((1.0 - star.z) * len(_BRIGHTNESS)),
                )
                existing = grid[py][px]
                char = _BRIGHTNESS[brightness_idx]
                # Keep the brighter (nearer) character if two stars collide.
                if existing == " " or _BRIGHTNESS.index(char) > (
                    _BRIGHTNESS.index(existing) if existing in _BRIGHTNESS else -1
                ):
                    grid[py][px] = char
        return self._grid_to_lines(grid)
