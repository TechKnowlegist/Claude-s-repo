"""Turn any video file into an ASCII movie playing in your terminal.

This shells out to ``ffmpeg`` to decode frames as raw PPM images (piped over
stdout -- nothing touches disk) and, optionally, to ``ffplay`` to play the
original audio track alongside the ASCII picture. Everything that can be
tested without an external binary -- PPM parsing and pixel-to-character
conversion -- is a small, pure function so it is unit tested directly;
``ffmpeg``/``ffplay`` orchestration is exercised in integration tests that
skip themselves when those binaries aren't installed.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from typing import BinaryIO, Iterator, Optional

# Brightness ramp from "empty" to "solid ink", darkest to brightest.
RAMP = " .:-=+*#%@"


def ffmpeg_path() -> Optional[str]:
    return shutil.which("ffmpeg")


def ffplay_path() -> Optional[str]:
    return shutil.which("ffplay")


def luminance(r: int, g: int, b: int) -> float:
    return 0.299 * r + 0.587 * g + 0.114 * b


def pixel_to_char(r: int, g: int, b: int, ramp: str = RAMP) -> str:
    idx = int(luminance(r, g, b) / 255 * (len(ramp) - 1))
    return ramp[max(0, min(len(ramp) - 1, idx))]


def frame_to_ascii(
    pixels: bytes,
    width: int,
    height: int,
    target_height: int,
    color: bool = False,
    ramp: str = RAMP,
) -> list[str]:
    """Convert raw RGB ``pixels`` (``width`` x ``height``) into
    ``target_height`` character rows.

    When ``target_height`` is smaller than ``height``, consecutive source
    rows are averaged together -- this is what compensates for terminal
    character cells being roughly twice as tall as they are wide, so a
    circle in the source video doesn't come out looking like an egg.
    """
    if target_height <= 0 or width <= 0 or height <= 0:
        return []
    row_bytes = width * 3
    factor = max(1, height // target_height)
    lines = []
    for out_y in range(target_height):
        row_chars = []
        for x in range(width):
            r_sum = g_sum = b_sum = count = 0
            for dy in range(factor):
                y = out_y * factor + dy
                if y >= height:
                    break
                offset = y * row_bytes + x * 3
                r_sum += pixels[offset]
                g_sum += pixels[offset + 1]
                b_sum += pixels[offset + 2]
                count += 1
            if count == 0:
                continue
            r, g, b = r_sum // count, g_sum // count, b_sum // count
            ch = pixel_to_char(r, g, b, ramp)
            if color:
                row_chars.append(f"\x1b[38;2;{r};{g};{b}m{ch}")
            else:
                row_chars.append(ch)
        if color:
            row_chars.append("\x1b[0m")
        lines.append("".join(row_chars))
    return lines


def _read_token(stream: BinaryIO) -> Optional[bytes]:
    """Read one whitespace-delimited PPM header token, skipping ``#`` comments."""
    token = bytearray()
    in_comment = False
    while True:
        b = stream.read(1)
        if not b:
            return bytes(token) if token else None
        if in_comment:
            if b == b"\n":
                in_comment = False
            continue
        if b == b"#" and not token:
            in_comment = True
            continue
        if b.isspace():
            if token:
                return bytes(token)
            continue
        token += b


def _read_exact(stream: BinaryIO, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = stream.read(n - len(buf))
        if not chunk:
            raise EOFError("unexpected end of stream while reading a PPM frame")
        buf += chunk
    return bytes(buf)


def read_ppm_frame(stream: BinaryIO) -> Optional[tuple[int, int, bytes]]:
    """Read one binary PPM (P6) image from ``stream``. Returns ``None`` at a clean EOF."""
    magic = _read_token(stream)
    if magic is None:
        return None
    if magic != b"P6":
        raise ValueError(f"unsupported PPM header: {magic!r}")
    width = int(_read_token(stream))
    height = int(_read_token(stream))
    maxval = int(_read_token(stream))
    if maxval != 255:
        raise ValueError(f"unsupported PPM maxval: {maxval}")
    data = _read_exact(stream, width * height * 3)
    return width, height, data


def iter_ppm_frames(stream: BinaryIO) -> Iterator[tuple[int, int, bytes]]:
    while True:
        frame = read_ppm_frame(stream)
        if frame is None:
            return
        yield frame


def iter_video_ascii_frames(
    path: str,
    width: int,
    height: int,
    fps: float,
    color: bool = False,
) -> Iterator[list[str]]:
    """Decode ``path`` with ffmpeg and yield ASCII frames, one per video frame."""
    ffmpeg = ffmpeg_path()
    if not ffmpeg:
        raise RuntimeError("ffmpeg was not found on PATH")

    sample_height = height * 2  # see frame_to_ascii's row-averaging note
    vf = f"fps={fps},scale={width}:{sample_height}:flags=area,setsar=1"
    cmd = [
        ffmpeg,
        "-loglevel", "error",
        "-i", path,
        "-vf", vf,
        "-f", "image2pipe",
        "-vcodec", "ppm",
        "-",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    assert proc.stdout is not None
    try:
        for w, h, pixels in iter_ppm_frames(proc.stdout):
            yield frame_to_ascii(pixels, w, h, target_height=height, color=color)
    finally:
        proc.stdout.close()
        proc.terminate()
        proc.wait()


def play_video(
    path: str,
    width: int = 100,
    height: int = 40,
    fps: float = 15.0,
    color: bool = False,
    audio: bool = True,
    out=None,
) -> int:
    """Play ``path`` as an ASCII movie in the current terminal. Returns an exit code."""
    out = sys.stdout if out is None else out

    if ffmpeg_path() is None:
        print(
            "error: ffmpeg was not found on PATH. Install ffmpeg to use `asciiverse play`.",
            file=sys.stderr,
        )
        return 1

    audio_proc = None
    if audio:
        ffplay = ffplay_path()
        if ffplay:
            audio_proc = subprocess.Popen(
                [ffplay, "-nodisp", "-autoexit", "-loglevel", "quiet", path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            print("note: ffplay not found -- playing without sound.", file=sys.stderr)

    delay = 1.0 / fps if fps > 0 else 0
    next_frame_at = time.monotonic()
    try:
        for lines in iter_video_ascii_frames(path, width, height, fps, color=color):
            out.write("\x1b[2J\x1b[H")
            out.write("\n".join(lines))
            out.write("\n")
            out.flush()
            next_frame_at += delay
            sleep_for = next_frame_at - time.monotonic()
            if sleep_for > 0:
                time.sleep(sleep_for)
    except KeyboardInterrupt:
        pass
    finally:
        if audio_proc is not None:
            audio_proc.terminate()
            audio_proc.wait()
    return 0
