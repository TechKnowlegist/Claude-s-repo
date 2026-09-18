from __future__ import annotations

import argparse
import sys
import time

from . import video
from .film.shorts import SHORTS
from .scenes import SCENES


def _add_playback_args(parser: argparse.ArgumentParser, default_fps: float) -> None:
    parser.add_argument("--width", type=int, default=80, help="grid width in columns")
    parser.add_argument("--height", type=int, default=24, help="grid height in rows")
    parser.add_argument("--fps", type=float, default=default_fps, help="target frames per second")
    parser.add_argument(
        "--frames",
        type=int,
        default=None,
        help="render this many frames to stdout and exit, instead of an interactive curses session",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="asciiverse",
        description="Generative ASCII scenes, scripted short films, and a video-to-ASCII player.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scene_p = sub.add_parser("scene", help="run a generative ASCII scene, forever")
    scene_p.add_argument("name", choices=sorted(SCENES), help="which scene to run")
    scene_p.add_argument("--seed", type=int, default=None, help="random seed for reproducible output")
    _add_playback_args(scene_p, default_fps=24.0)

    film_p = sub.add_parser("film", help="play a scripted original ASCII short film")
    film_p.add_argument("name", nargs="?", choices=sorted(SHORTS), help="which film to play")
    film_p.add_argument("--list", action="store_true", help="list available films and exit")
    _add_playback_args(film_p, default_fps=12.0)

    play_p = sub.add_parser(
        "play", help="convert and play a real video file as ASCII, with audio (requires ffmpeg)"
    )
    play_p.add_argument("path", help="path to a video file")
    play_p.add_argument("--width", type=int, default=100, help="output width in characters")
    play_p.add_argument("--height", type=int, default=40, help="output height in characters")
    play_p.add_argument("--fps", type=float, default=15.0, help="playback frame rate")
    play_p.add_argument("--color", action="store_true", help="render in 24-bit color instead of plain ASCII")
    play_p.add_argument("--mute", action="store_true", help="don't play the video's audio track")

    return parser


def run_headless(scene, num_frames: int | None, fps: float, out=None) -> None:
    """Render frames to ``out`` and exit. ``num_frames=None`` runs until ``scene.finished``."""
    out = sys.stdout if out is None else out
    delay = 1.0 / fps if fps > 0 else 0
    i = 0
    while num_frames is None or i < num_frames:
        out.write("\x1b[2J\x1b[H")  # clear screen, home cursor
        out.write("\n".join(scene.render()))
        out.write("\n")
        out.flush()
        scene.step()
        i += 1
        if getattr(scene, "finished", False):
            break
        is_last = num_frames is not None and i >= num_frames
        if delay and not is_last:
            time.sleep(delay)


def run_interactive(scene, fps: float) -> None:
    import curses

    delay = 1.0 / fps if fps > 0 else 0

    def loop(stdscr: "curses.window") -> None:
        curses.curs_set(0)
        stdscr.nodelay(True)
        while True:
            key = stdscr.getch()
            if key in (ord("q"), 27):  # q or ESC
                return
            stdscr.erase()
            for row_idx, line in enumerate(scene.render()):
                try:
                    stdscr.addstr(row_idx, 0, line)
                except curses.error:
                    pass  # last cell of the terminal can raise; harmless
            stdscr.refresh()
            scene.step()
            if getattr(scene, "finished", False):
                return
            time.sleep(delay)

    curses.wrapper(loop)


def _play(scene, frames: int | None, fps: float) -> None:
    if frames is not None:
        run_headless(scene, num_frames=frames, fps=fps)
    else:
        try:
            run_interactive(scene, fps=fps)
        except KeyboardInterrupt:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "scene":
        scene = SCENES[args.name](width=args.width, height=args.height, seed=args.seed)
        _play(scene, args.frames, args.fps)
        return 0

    if args.command == "film":
        if args.list or not args.name:
            for name in sorted(SHORTS):
                print(name)
            return 0
        # The film's own fps sets how many frames each shot was authored to
        # last (its "dramaturgical" pace) -- that's independent of --fps,
        # which only controls how fast we play those frames back here.
        film = SHORTS[args.name](width=args.width, height=args.height)
        frames = args.frames if args.frames is not None else film.total_frames
        _play(film, frames, args.fps)
        return 0

    if args.command == "play":
        return video.play_video(
            args.path,
            width=args.width,
            height=args.height,
            fps=args.fps,
            color=args.color,
            audio=not args.mute,
        )

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
