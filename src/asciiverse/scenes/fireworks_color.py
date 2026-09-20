from __future__ import annotations

import math

from ..color import lerp_color, render_row
from .base import Scene

NIGHT_SKY = (8, 8, 22)
TRAIL_COLOR = (255, 240, 190)
GRAVITY = 0.05
SPARK_SHAPES = "*+.oO@"

# Each firework picks one of these as its base color; sparks fade from that
# color down toward the night sky as they burn out.
FIREWORK_COLORS = [
    (255, 90, 90),    # red
    (255, 200, 70),   # gold
    (110, 230, 130),  # green
    (110, 170, 255),  # blue
    (210, 130, 255),  # violet
    (110, 235, 235),  # cyan
    (255, 130, 210),  # pink
    (245, 245, 255),  # silver
]


class _Rocket:
    __slots__ = ("x", "y", "vy", "color")

    def __init__(self, x, y, vy, color):
        self.x, self.y, self.vy, self.color = x, y, vy, color


class _Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color")

    def __init__(self, x, y, vx, vy, life, color):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.color = color


class FireworksColor(Scene):
    """Fireworks, but each burst picks a random color and fades toward the
    night sky as it burns out, instead of the plain-ASCII version's single
    brightness ramp. Loops forever like the other scenes (Ctrl+C to quit)."""

    name = "fireworks-color"
    color = True

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
            color = self.rng.choice(FIREWORK_COLORS)
            self.rockets.append(_Rocket(x=x, y=float(self.height - 1), vy=vy, color=color))

    def _explode(self, rocket: _Rocket) -> None:
        num_particles = self.rng.randint(24, 42)
        for _ in range(num_particles):
            angle = self.rng.uniform(0, 2 * math.pi)
            speed = self.rng.uniform(0.3, 1.5)
            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)
            life = self.rng.randint(9, 18)
            self.particles.append(_Particle(rocket.x, rocket.y, vx, vy, life, rocket.color))

    def step(self) -> None:
        super().step()
        self._maybe_launch()

        still_flying = []
        for rocket in self.rockets:
            rocket.y += rocket.vy
            rocket.vy += GRAVITY * 0.5
            if rocket.vy >= -0.05 or rocket.y <= 0:
                self._explode(rocket)
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

    def render(self) -> list[str]:
        grid = [[[" ", None, NIGHT_SKY] for _ in range(self.width)] for _ in range(self.height)]

        for rocket in self.rockets:
            x, y = int(rocket.x), int(rocket.y)
            if 0 <= x < self.width and 0 <= y < self.height:
                grid[y][x][0] = "|"
                grid[y][x][1] = TRAIL_COLOR

        for p in self.particles:
            x, y = int(p.x), int(p.y)
            if 0 <= x < self.width and 0 <= y < self.height:
                fraction = p.life / p.max_life
                idx = min(len(SPARK_SHAPES) - 1, int(fraction * len(SPARK_SHAPES)))
                grid[y][x][0] = SPARK_SHAPES[idx]
                grid[y][x][1] = lerp_color(NIGHT_SKY, p.color, fraction)

        return [render_row([(c[0], c[1], c[2]) for c in row]) for row in grid]
