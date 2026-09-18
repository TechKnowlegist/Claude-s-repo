import io
import shutil

import pytest

from asciiverse import video


def _ppm_bytes(width: int, height: int, pixel: bytes) -> bytes:
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    return header + pixel * (width * height)


def test_pixel_to_char_maps_black_to_darkest_and_white_to_brightest():
    assert video.pixel_to_char(0, 0, 0) == video.RAMP[0]
    assert video.pixel_to_char(255, 255, 255) == video.RAMP[-1]


def test_frame_to_ascii_dimensions_and_solid_color():
    # A uniformly white 4x4 image, downsampled to 2 rows, should be all the
    # brightest ramp character.
    pixels = bytes([255, 255, 255]) * (4 * 4)
    lines = video.frame_to_ascii(pixels, width=4, height=4, target_height=2)
    assert len(lines) == 2
    assert all(len(line) == 4 for line in lines)
    assert all(ch == video.RAMP[-1] for line in lines for ch in line)


def test_frame_to_ascii_color_wraps_each_row_in_ansi_codes():
    pixels = bytes([10, 20, 30]) * (2 * 2)
    lines = video.frame_to_ascii(pixels, width=2, height=2, target_height=1, color=True)
    assert len(lines) == 1
    assert lines[0].startswith("\x1b[38;2;10;20;30m")
    assert lines[0].endswith("\x1b[0m")


def test_read_ppm_frame_parses_header_and_pixels():
    data = _ppm_bytes(2, 2, bytes([1, 2, 3]))
    stream = io.BytesIO(data)
    frame = video.read_ppm_frame(stream)
    assert frame is not None
    width, height, pixels = frame
    assert (width, height) == (2, 2)
    assert pixels == bytes([1, 2, 3]) * 4


def test_read_ppm_frame_skips_comments_in_header():
    raw = b"P6\n# a comment\n2 2\n255\n" + bytes([9, 9, 9]) * 4
    width, height, pixels = video.read_ppm_frame(io.BytesIO(raw))
    assert (width, height) == (2, 2)


def test_read_ppm_frame_returns_none_at_clean_eof():
    assert video.read_ppm_frame(io.BytesIO(b"")) is None


def test_read_ppm_frame_rejects_unsupported_maxval():
    raw = b"P6\n1 1\n65535\n" + bytes([0, 0])
    with pytest.raises(ValueError):
        video.read_ppm_frame(io.BytesIO(raw))


def test_iter_ppm_frames_reads_multiple_concatenated_frames():
    stream = io.BytesIO(_ppm_bytes(1, 1, bytes([1, 1, 1])) + _ppm_bytes(1, 1, bytes([2, 2, 2])))
    frames = list(video.iter_ppm_frames(stream))
    assert len(frames) == 2
    assert frames[0][2] == bytes([1, 1, 1])
    assert frames[1][2] == bytes([2, 2, 2])


def test_play_video_reports_a_clear_error_without_ffmpeg(monkeypatch):
    monkeypatch.setattr(video, "ffmpeg_path", lambda: None)
    out = io.StringIO()
    exit_code = video.play_video("nonexistent.mp4", audio=False, out=out)
    assert exit_code == 1
    assert out.getvalue() == ""  # nothing was rendered


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="requires ffmpeg to be installed")
def test_iter_video_ascii_frames_end_to_end_with_synthetic_clip(tmp_path):
    import subprocess

    clip = tmp_path / "test.mp4"
    subprocess.run(
        [
            "ffmpeg", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=1:size=64x64:rate=5",
            str(clip),
        ],
        check=True,
    )
    frames = list(video.iter_video_ascii_frames(str(clip), width=16, height=8, fps=5))
    assert len(frames) >= 3
    for frame in frames:
        assert len(frame) == 8
        assert all(len(line) == 16 for line in frame)
