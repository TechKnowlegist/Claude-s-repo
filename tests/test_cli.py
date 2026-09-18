import io

from asciiverse.cli import build_parser, main, run_headless
from asciiverse.scenes import SCENES


def test_scene_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["scene", "life"])
    assert args.command == "scene"
    assert args.name == "life"
    assert args.width == 80
    assert args.height == 24


def test_parser_rejects_unknown_scene():
    parser = build_parser()
    try:
        parser.parse_args(["scene", "not-a-real-scene"])
    except SystemExit as e:
        assert e.code != 0
    else:
        raise AssertionError("expected SystemExit for an invalid scene name")


def test_film_and_play_subcommands_parse():
    parser = build_parser()
    film_args = parser.parse_args(["film", "orbital", "--fps", "10"])
    assert film_args.command == "film"
    assert film_args.name == "orbital"

    play_args = parser.parse_args(["play", "clip.mp4", "--color", "--mute"])
    assert play_args.command == "play"
    assert play_args.path == "clip.mp4"
    assert play_args.color is True
    assert play_args.mute is True


def test_run_headless_writes_correct_frame_count():
    scene = SCENES["life"](width=10, height=5, seed=1)
    out = io.StringIO()
    run_headless(scene, num_frames=3, fps=0, out=out)
    output = out.getvalue()
    # Each frame clears the screen (\x1b[2J\x1b[H) before drawing.
    assert output.count("\x1b[2J\x1b[H") == 3


def test_run_headless_stops_when_scene_reports_finished():
    class TinyFilm:
        finished = False

        def __init__(self):
            self.n = 0

        def render(self):
            return ["x"]

        def step(self):
            self.n += 1
            if self.n >= 2:
                self.finished = True

    out = io.StringIO()
    run_headless(TinyFilm(), num_frames=None, fps=0, out=out)
    assert out.getvalue().count("\x1b[2J\x1b[H") == 2


def test_main_scene_headless_end_to_end(capsys):
    exit_code = main(["scene", "starfield", "--width", "12", "--height", "6", "--frames", "2", "--fps", "0", "--seed", "1"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.count("\x1b[2J\x1b[H") == 2


def test_main_film_list(capsys):
    exit_code = main(["film", "--list"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "orbital" in captured.out
    assert "echo" in captured.out


def test_main_film_headless_end_to_end(capsys):
    exit_code = main(["film", "echo", "--width", "20", "--height", "10", "--frames", "3", "--fps", "0"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.count("\x1b[2J\x1b[H") == 3
