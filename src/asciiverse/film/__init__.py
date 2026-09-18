"""A tiny "director's toolkit" for scripted ASCII short films.

A :class:`Film` is a sequence of :class:`Shot` objects. Each shot knows how
to render itself for a given local frame number; the film just tracks which
shot is current and hands frames off to it. A ``Film`` exposes the same
``step()`` / ``render()`` interface as the scenes in :mod:`asciiverse.scenes`,
so the exact same CLI playback code (headless or curses) can drive both.
"""

from __future__ import annotations

from typing import Callable, Optional, Sequence

Grid = list[str]
SceneFactory = Callable[[int, int], object]  # (width, height) -> a Scene-like object


def _center(text: str, width: int) -> str:
    if len(text) >= width:
        return text[:width]
    left = (width - len(text)) // 2
    right = width - len(text) - left
    return " " * left + text + " " * right


def _fade_factor(local_tick: int, duration: int, fade_frames: int) -> float:
    if fade_frames <= 0 or duration <= 0:
        return 1.0
    if local_tick < fade_frames:
        return local_tick / fade_frames
    remaining = duration - 1 - local_tick
    if remaining < fade_frames:
        return max(0.0, remaining / fade_frames)
    return 1.0


def dither_fade(lines: Grid, factor: float) -> Grid:
    """Fade ``lines`` toward blank. ``factor`` 1.0 is fully visible, 0.0 is blank.

    Uses a fixed ordered dither (a hash of each cell's position) rather than
    randomness, so a given (lines, factor) pair always fades the same way --
    handy for both visual stability across frames and for tests.
    """
    if factor >= 0.999:
        return lines
    if factor <= 0.001:
        return [" " * len(line) for line in lines]
    threshold = factor * 100
    out = []
    for y, line in enumerate(lines):
        chars = []
        for x, ch in enumerate(line):
            if ch == " ":
                chars.append(" ")
                continue
            h = (x * 928371 + y * 719393 + 104729) % 100
            chars.append(ch if h < threshold else " ")
        out.append("".join(chars))
    return out


def composite(background: Grid, art: Sequence[str], x: int, y: int) -> Grid:
    """Overlay ``art`` onto ``background`` at (x, y). Spaces in ``art`` are transparent."""
    grid = [list(line) for line in background]
    height = len(grid)
    width = len(grid[0]) if grid else 0
    for row_idx, art_row in enumerate(art):
        gy = y + row_idx
        if not (0 <= gy < height):
            continue
        for col_idx, ch in enumerate(art_row):
            gx = x + col_idx
            if ch != " " and 0 <= gx < width:
                grid[gy][gx] = ch
    return ["".join(row) for row in grid]


def draw_text_block(background: Grid, lines: Sequence[str], top: int, width: int) -> Grid:
    """Return a copy of ``background`` with each of ``lines`` centered, starting at row ``top``."""
    grid = [list(row) for row in background]
    height = len(grid)
    for i, text in enumerate(lines):
        row = top + i
        if 0 <= row < height:
            grid[row] = list(_center(text, width))
    return ["".join(row) for row in grid]


class Shot:
    """One beat of a film: a fixed number of frames, rendered on demand."""

    duration: int = 1

    def enter(self, width: int, height: int) -> None:
        """Called once, right before this shot's first frame is rendered."""

    def frame(self, local_tick: int, width: int, height: int) -> Grid:
        raise NotImplementedError


class TitleCard(Shot):
    """A blank canvas with centered text -- title cards, credits, "THE END"."""

    def __init__(self, lines: Sequence[str], duration: int, fade_frames: int = 6):
        self.lines = list(lines)
        self.duration = duration
        self.fade_frames = fade_frames

    def frame(self, local_tick: int, width: int, height: int) -> Grid:
        blank = [" " * width for _ in range(height)]
        top = max(0, (height - len(self.lines)) // 2)
        lines = draw_text_block(blank, self.lines, top, width)
        factor = _fade_factor(local_tick, self.duration, self.fade_frames)
        return dither_fade(lines, factor)


class SceneShot(Shot):
    """A shot backed by one of the generative scenes, with optional subtitles and a sprite.

    ``subtitles`` is a list of ``(start_tick, end_tick, text)`` triples (end
    exclusive); ``sprite`` is small ASCII art composited over the backdrop,
    positioned each frame by ``sprite_path(local_tick, width, height) -> (x, y)``.
    """

    def __init__(
        self,
        scene_factory: SceneFactory,
        duration: int,
        subtitles: Optional[Sequence[tuple[int, int, str]]] = None,
        sprite: Optional[Sequence[str]] = None,
        sprite_path: Optional[Callable[[int, int, int], tuple[int, int]]] = None,
        fade_frames: int = 0,
        dim: float = 1.0,
    ):
        self.scene_factory = scene_factory
        self.duration = duration
        self.subtitles = list(subtitles or [])
        self.sprite = sprite
        self.sprite_path = sprite_path
        self.fade_frames = fade_frames
        self.dim = dim
        self.scene = None

    def enter(self, width: int, height: int) -> None:
        self.scene = self.scene_factory(width, height)

    def frame(self, local_tick: int, width: int, height: int) -> Grid:
        if local_tick > 0:
            self.scene.step()
        lines = self.scene.render()
        if self.dim < 1.0:
            lines = dither_fade(lines, self.dim)
        if self.sprite is not None and self.sprite_path is not None:
            x, y = self.sprite_path(local_tick, width, height)
            lines = composite(lines, self.sprite, x, y)
        for start, end, text in self.subtitles:
            if start <= local_tick < end:
                lines = draw_text_block(lines, [text], height - 2, width)
        factor = _fade_factor(local_tick, self.duration, self.fade_frames)
        return dither_fade(lines, factor)


class Crawl(Shot):
    """A Star-Wars-style scrolling text crawl, optionally over a dimmed backdrop."""

    def __init__(
        self,
        lines: Sequence[str],
        duration: int,
        backdrop_factory: Optional[SceneFactory] = None,
        backdrop_dim: float = 0.35,
    ):
        self.text_lines = list(lines)
        self.duration = duration
        self.backdrop_factory = backdrop_factory
        self.backdrop_dim = backdrop_dim
        self.backdrop = None

    def enter(self, width: int, height: int) -> None:
        self.backdrop = self.backdrop_factory(width, height) if self.backdrop_factory else None
        self.start_row = height
        self.end_row = -len(self.text_lines) - 1

    def frame(self, local_tick: int, width: int, height: int) -> Grid:
        if self.backdrop is not None:
            if local_tick > 0:
                self.backdrop.step()
            base = dither_fade(self.backdrop.render(), self.backdrop_dim)
        else:
            base = [" " * width for _ in range(height)]
        progress = local_tick / max(1, self.duration - 1)
        top = round(self.start_row + (self.end_row - self.start_row) * progress)
        return draw_text_block(base, self.text_lines, top, width)


class Film:
    """A sequence of shots, played back like a scene (``step()`` / ``render()``)."""

    def __init__(self, shots: Sequence[Shot], width: int, height: int, fps: int = 12, title: str = "untitled"):
        if not shots:
            raise ValueError("a film needs at least one shot")
        self.shots = list(shots)
        self.width = width
        self.height = height
        self.fps = fps
        self.title = title
        self._shot_idx = 0
        self._local_tick = 0
        self._entered = False
        self.tick = 0
        self.finished = False

    @property
    def total_frames(self) -> int:
        return sum(s.duration for s in self.shots)

    def render(self) -> Grid:
        current = self.shots[self._shot_idx]
        if not self._entered:
            current.enter(self.width, self.height)
            self._entered = True
        return current.frame(self._local_tick, self.width, self.height)

    def step(self) -> None:
        if self.finished:
            return
        self.tick += 1
        self._local_tick += 1
        current = self.shots[self._shot_idx]
        if self._local_tick >= current.duration:
            if self._shot_idx + 1 < len(self.shots):
                self._shot_idx += 1
                self._local_tick = 0
                self._entered = False
            else:
                self.finished = True


__all__ = [
    "Film",
    "Shot",
    "TitleCard",
    "SceneShot",
    "Crawl",
    "composite",
    "dither_fade",
    "draw_text_block",
]
