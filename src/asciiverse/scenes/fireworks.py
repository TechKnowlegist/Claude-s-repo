from __future__ import annotations

import math

from .base import Scene

_SPARK_CHARS = "*+.oO@"
_GRAVITY = 0.05


class _Rocket:
    __slots__ = ("x", "y", "vy")

    def __init__(self, x: float, y: float, vy: float) -> None:
        self.x = x
        self.y = y
        self.vy = vy


class _Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life")

    def __init__(self, x: float, y: float, vx: float, vy: float, life: int) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life


class Fireworks(Scene):
    """Rockets launch, explode, and scatter fading sparks."""

    name = "fireworks"

    def __init__(
        self,
        width: int,
        height: int,
        seed: int | None = None,
        launch_chance: float = 0.08,
        max_rockets: int = 3,
    ) -> None:
        super().__init__(width, height, seed)
        self.launch_chance = launch_chance
        self.max_rockets = max_rockets
        self.rockets: list[_Rocket] = []
        self.particles: list[_Particle] = []

    def _maybe_launch(self) -> None:
        if len(self.rockets) < self.max_rockets and self.rng.random() < self.launch_chance:
            x = self.rng.uniform(self.width * 0.15, self.width * 0.85)
            target_height = self.rng.uniform(self.height * 0.3, self.height * 0.8)
            vy = -target_height / 12.0
            self.rockets.append(_Rocket(x=x, y=float(self.height - 1), vy=vy))

    def _explode(self, rocket: _Rocket) -> None:
        num_particles = self.rng.randint(20, 36)
        for _ in range(num_particles):
            angle = self.rng.uniform(0, 6.28318)
            speed = self.rng.uniform(0.3, 1.4)
            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)
            life = self.rng.randint(8, 16)
            self.particles.append(_Particle(rocket.x, rocket.y, vx, vy, life))

    def step(self) -> None:
        super().step()
        self._maybe_launch()

        still_flying = []
        for rocket in self.rockets:
            rocket.y += rocket.vy
            rocket.vy += _GRAVITY * 0.5
            if rocket.vy >= -0.05 or rocket.y <= 0:
                self._explode(rocket)
            else:
                still_flying.append(rocket)
        self.rockets = still_flying

        still_alive = []
        for p in self.particles:
            p.x += p.vx
            p.y += p.vy
            p.vy += _GRAVITY
            p.life -= 1
            if p.life > 0 and 0 <= p.x < self.width and 0 <= p.y < self.height:
                still_alive.append(p)
        self.particles = still_alive

    def render(self) -> list[str]:
        grid = self._blank_grid()
        for rocket in self.rockets:
            x, y = int(rocket.x), int(rocket.y)
            if 0 <= x < self.width and 0 <= y < self.height:
                grid[y][x] = "|"
        for p in self.particles:
            x, y = int(p.x), int(p.y)
            if 0 <= x < self.width and 0 <= y < self.height:
                fraction = p.life / p.max_life
                idx = min(len(_SPARK_CHARS) - 1, int(fraction * len(_SPARK_CHARS)))
                grid[y][x] = _SPARK_CHARS[idx]
        return self._grid_to_lines(grid)
