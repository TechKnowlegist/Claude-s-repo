"""ECHO -- a quiet, abstract short: a cellular automaton waking up, a machine
dreaming in falling glyphs, and a starfield it can't quite reach."""

from __future__ import annotations

from .. import Film, SceneShot, TitleCard
from ...scenes import Life, MatrixRain, Starfield


def build_echo(width: int = 100, height: int = 30, fps: int = 12) -> Film:
    shots = [
        TitleCard(["E C H O"], duration=fps * 3, fade_frames=fps),
        SceneShot(
            scene_factory=lambda w, h: Life(w, h, seed=2, density=0.28),
            duration=fps * 8,
            subtitles=[
                (0, fps * 3, "Something is arranging itself."),
                (fps * 3, fps * 5, "It doesn't know why."),
                (fps * 5, fps * 8, "It keeps trying anyway."),
            ],
        ),
        SceneShot(
            scene_factory=lambda w, h: MatrixRain(w, h, seed=4),
            duration=fps * 6,
            subtitles=[
                (0, fps * 3, "Somewhere, a memory repeats itself."),
                (fps * 3, fps * 6, "It calls this dreaming."),
            ],
        ),
        SceneShot(
            scene_factory=lambda w, h: Starfield(w, h, seed=9, speed=0.01),
            duration=fps * 6,
            subtitles=[(0, fps * 6, "It reaches for something it cannot name.")],
            fade_frames=max(1, fps // 2),
        ),
        TitleCard(["E C H O", "", "-- end --"], duration=fps * 4, fade_frames=fps),
    ]
    return Film(shots, width=width, height=height, fps=fps, title="ECHO")
