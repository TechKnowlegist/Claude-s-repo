import io

from asciiverse.cli import build_parser, main, run_headless
from asciiverse.scenes import SCENES


def test_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["life"])
    assert args.scene == "life"
    assert args.width == 80
    assert args.height == 24


def test_parser_rejects_unknown_scene():
    parser = build_parser()
    try:
        parser.parse_args(["not-a-real-scene"])
    except SystemExit as e:
        assert e.code != 0
    else:
        raise AssertionError("expected SystemExit for an invalid scene name")


def test_run_headless_writes_correct_frame_count():
    scene = SCENES["life"](width=10, height=5, seed=1)
    out = io.StringIO()
    run_headless(scene, num_frames=3, fps=0, out=out)
    output = out.getvalue()
    # Each frame clears the screen (\x1b[2J\x1b[H) before drawing.
    assert output.count("\x1b[2J\x1b[H") == 3


def test_main_headless_end_to_end(capsys):
    exit_code = main(["starfield", "--width", "12", "--height", "6", "--frames", "2", "--fps", "0", "--seed", "1"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.count("\x1b[2J\x1b[H") == 2
