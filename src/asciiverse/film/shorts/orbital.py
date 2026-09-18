"""ORBITAL -- a very small sci-fi short about a first contact, made entirely
of generated ASCII: a starfield crawl, a hand-drawn ship, and fireworks."""

from __future__ import annotations

import math

from .. import Crawl, Film, SceneShot, TitleCard
from ...scenes import Fireworks, Starfield

_SHIP = [
    "   /\\",
    "  /--\\",
    " <==>>",
    "  \\--/",
]
_SHIP_W = max(len(row) for row in _SHIP)
_SHIP_H = len(_SHIP)


def build_orbital(width: int = 100, height: int = 30, fps: int = 12) -> Film:
    contact_duration = fps * 6

    def ship_path(local_tick: int, w: int, h: int) -> tuple[int, int]:
        progress = local_tick / max(1, contact_duration - 1)
        x = int(-_SHIP_W + progress * (w + 2 * _SHIP_W))
        bob = int(round(1.5 * math.sin(local_tick / 6.0)))
        y = h // 2 - _SHIP_H // 2 + bob
        return x, y

    shots = [
        TitleCard(
            ["O R B I T A L", "", "a short by asciiverse"],
            duration=fps * 4,
            fade_frames=fps,
        ),
        Crawl(
            lines=[
                "Year 41 of the Long Silence.",
                "",
                "The relay station STILL POINT",
                "has not answered a hail",
                "in eleven thousand cycles.",
                "",
                "Command sends one ship --",
                "and one pilot who volunteered",
                "before anyone could stop her.",
            ],
            duration=fps * 9,
            backdrop_factory=lambda w, h: Starfield(w, h, seed=3, speed=0.015),
        ),
        SceneShot(
            scene_factory=lambda w, h: Starfield(w, h, seed=11, num_stars=90, speed=0.03),
            duration=contact_duration,
            sprite=_SHIP,
            sprite_path=ship_path,
            subtitles=[
                (0, fps * 2, "KESTREL: Still Point, this is Kestrel. Do you copy?"),
                (fps * 2, fps * 4, "..."),
                (fps * 4, fps * 6, "STILL POINT: Copy that, Kestrel. We copy."),
            ],
        ),
        SceneShot(
            scene_factory=lambda w, h: Fireworks(w, h, seed=5, launch_chance=0.15, max_rockets=4),
            duration=fps * 5,
            subtitles=[(0, fps * 5, "Lights, all at once. Still Point wakes up.")],
            fade_frames=max(1, fps // 2),
        ),
        TitleCard(
            ["THE END", "", "an original ascii short", "made with asciiverse"],
            duration=fps * 4,
            fade_frames=fps,
        ),
    ]
    return Film(shots, width=width, height=height, fps=fps, title="ORBITAL")
