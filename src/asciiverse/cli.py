from __future__ import annotations

import argparse
import sys
import time

from .scenes import SCENES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="asciiverse",
        description="Generative ASCII scenes for your terminal.",
    )
    parser.add_argument(
        "scene",
        choices=sorted(SCENES),
        help="which scene to run",
    )
    parser.add_argument("--width", type=int, default=80, help="grid width in columns")
    parser.add_argument("--height", type=int, default=24, help="grid height in rows")
    parser.add_argument("--fps", type=float, default=24.0, help="target frames per second")
    parser.add_argument("--seed", type=int, default=None, help="random seed for reproducible output")
    parser.add_argument(
        "--frames",
        type=int,
        default=None,
        help="render this many frames to stdout and exit, instead of an interactive curses session",
    )
    return parser


def run_headless(scene, num_frames: int, fps: float, out=None) -> None:
    out = sys.stdout if out is None else out
    delay = 1.0 / fps if fps > 0 else 0
    for i in range(num_frames):
        out.write("\x1b[2J\x1b[H")  # clear screen, home cursor
        out.write("\n".join(scene.render()))
        out.write("\n")
        out.flush()
        scene.step()
        if delay and i < num_frames - 1:
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
            time.sleep(delay)

    curses.wrapper(loop)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    scene_cls = SCENES[args.scene]
    scene = scene_cls(width=args.width, height=args.height, seed=args.seed)

    if args.frames is not None:
        run_headless(scene, num_frames=args.frames, fps=args.fps)
    else:
        try:
            run_interactive(scene, fps=args.fps)
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
