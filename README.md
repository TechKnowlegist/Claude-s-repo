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

Four original short films, built entirely out of code — no video files, no
external assets:

- **orbital** — a ~30s sci-fi short: title card, a scrolling text crawl over
  a starfield, a hand-drawn ship flying through with subtitled dialogue, and
  fireworks. Plain ASCII.
- **echo** — a quieter, more abstract piece: a cellular automaton waking up,
  a machine dreaming in falling glyphs, and a starfield it can't quite reach.
  Plain ASCII.
- **garden** — a ~20s color short: dawn breaks (a real 24-bit ANSI color sky
  gradient) over a plot of ground while flowers grow in and fireflies drift
  by. Full color.
- **neon** — a ~19s color short: a synthwave-style skyline, a glowing sun
  behind silhouetted buildings, and a scrolling neon floor grid. Full color.

`orbital` and `echo` are built with a small compositing/title-card/subtitle
/scroll-crawl toolkit (`asciiverse/film/*.py`); `garden` and `neon` paint
directly in 24-bit color (`asciiverse/color.py`) since that toolkit's
plain-text grid doesn't carry color.

```
asciiverse film --list
asciiverse film orbital
asciiverse film garden --width 100 --height 32
```

Films play through the same headless machinery as scenes' `--frames` mode
and stop automatically at the end. The color films need a terminal that
understands ANSI color (any modern terminal, including Windows Terminal /
Windows 10+ `cmd.exe`).

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

## Standalone copies

`standalone/` has every scene and film as one self-contained `.py` file each
— pure stdlib, no `pip install`, no package to clone into. Copy a single
file anywhere and run it:

```
python standalone/ascii_film_garden.py
```

They're kept in sync with the package versions by hand (there are only a
handful), trading a little duplication for "just run this one file."

## Design

Every scene's simulation (`asciiverse/scenes/*.py`) and every film primitive
(`asciiverse/film/*.py`) is plain Python with no terminal dependency:
`step()` advances the state and `render()` returns a list of fixed-width
strings. A `Film` exposes that same interface, backed internally by a list
of `Shot`s (title cards, scene backdrops with subtitles and sprites, and
scroll crawls). The color films (`garden`, `neon`) implement that same
`step()`/`render()` shape directly rather than going through `Film`/`Shot`,
since a colored line embeds ANSI escapes and no longer has "one character
per visible column" — see `asciiverse/color.py`'s `visible_length()` for how
tests measure width on those. `cli.py` is the only module that touches
`curses`; `video.py` is the only module that shells out to `ffmpeg`/`ffplay`.
Keeping those boundaries is what makes almost everything else straightforward
to unit test without a real terminal or a video file — see `tests/`.

## Test

```
pytest
```

The one test that needs `ffmpeg` installed (a real decode of a synthetic
clip) skips itself automatically when `ffmpeg` isn't on `PATH`.
