# asciiverse

A little terminal full of generative ASCII scenes, scripted short films, and
a real video-to-ASCII player.

```
$ asciiverse scene starfield
$ asciiverse film orbital
$ asciiverse play your_video.mp4
```

## Scenes

Four small, dependency-free simulations, each rendered as plain text:

- **starfield** — a warp-speed 3D starfield
- **matrix** — falling glyph rain
- **life** — Conway's Game of Life on a wrapping grid
- **fireworks** — rockets that launch, explode, and scatter fading sparks

```
asciiverse scene <name> [--width] [--height] [--fps] [--seed] [--frames]
```

In interactive mode (the default, no `--frames`), press `q` or `Esc` to quit.

Example — a fixed, reproducible run you can pipe or diff:

```
asciiverse scene life --width 40 --height 20 --seed 1 --frames 5 --fps 0
```

## Films

Two original short films, built entirely out of the scenes above plus a
small compositing/title-card/subtitle/scroll-crawl toolkit — no video files,
no external assets, just code:

- **orbital** — a ~30s sci-fi short: title card, a Star-Wars-style crawl over
  a starfield, a hand-drawn ship flying through with subtitled dialogue, and
  fireworks.
- **echo** — a quieter, more abstract piece: a cellular automaton waking up,
  a machine dreaming in falling glyphs, and a starfield it can't quite reach.

```
asciiverse film --list
asciiverse film orbital
asciiverse film echo --width 100 --height 30
```

Films play through the same interactive/headless machinery as scenes and
stop automatically at the end (or press `q`/`Esc` to bail early).

## Play (real video → ASCII, with audio)

Give it any video file and it'll decode it with `ffmpeg` and play it back as
a live ASCII movie in your terminal, with the original audio track playing
alongside it via `ffplay`:

```
asciiverse play path/to/video.mp4
asciiverse play path/to/video.mp4 --width 120 --height 45 --color
asciiverse play path/to/video.mp4 --mute
```

Requires `ffmpeg` (and, for audio, `ffplay`) to be installed and on `PATH`.
Nothing is written to disk — frames are streamed straight out of an `ffmpeg`
subprocess as raw PPM images and converted to characters on the fly.

| Flag      | Default | Meaning                                    |
|-----------|---------|---------------------------------------------|
| `--width`  | `100`  | output width in characters                   |
| `--height` | `40`   | output height in characters                  |
| `--fps`    | `15`   | playback frame rate                          |
| `--color`  | off    | render in 24-bit ANSI color instead of plain ASCII |
| `--mute`   | off    | don't play the audio track                   |

## Install

```
pip install -e ".[dev]"
```

## Design

Every scene's simulation (`asciiverse/scenes/*.py`) and every film primitive
(`asciiverse/film/*.py`) is plain Python with no terminal dependency:
`step()` advances the state and `render()` returns a list of fixed-width
strings. A `Film` exposes that same interface, backed internally by a list
of `Shot`s (title cards, scene backdrops with subtitles and sprites, and
scroll crawls). `cli.py` is the only module that touches `curses`; `video.py`
is the only module that shells out to `ffmpeg`/`ffplay`. Keeping those
boundaries is what makes almost everything else straightforward to unit
test without a real terminal or a video file — see `tests/`.

## Test

```
pytest
```

The one test that needs `ffmpeg` installed (a real decode of a synthetic
clip) skips itself automatically when `ffmpeg` isn't on `PATH`.
