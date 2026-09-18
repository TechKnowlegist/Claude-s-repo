# asciiverse

A little terminal full of generative ASCII scenes.

```
$ asciiverse starfield
```

Four scenes, each a small, dependency-free simulation rendered as plain text:

- **starfield** — a warp-speed 3D starfield
- **matrix** — falling glyph rain
- **life** — Conway's Game of Life on a wrapping grid
- **fireworks** — rockets that launch, explode, and scatter fading sparks

## Install

```
pip install -e ".[dev]"
```

## Run

```
asciiverse <scene> [options]
```

or, without installing:

```
python -m asciiverse <scene> [options]
```

Options:

| Flag       | Default | Meaning                                              |
|------------|---------|-------------------------------------------------------|
| `--width`  | `80`    | grid width in columns                                  |
| `--height` | `24`    | grid height in rows                                    |
| `--fps`    | `24`    | target frames per second                               |
| `--seed`   | random  | seed for reproducible output                           |
| `--frames` | none    | render N frames to stdout and exit (no curses, scriptable) |

In interactive mode (the default, no `--frames`), press `q` or `Esc` to quit.

Example — a fixed, reproducible run you can pipe or diff:

```
python -m asciiverse life --width 40 --height 20 --seed 1 --frames 5 --fps 0
```

## Design

Every scene's simulation (`asciiverse/scenes/*.py`) is plain Python with no
terminal dependency: `step()` advances the state and `render()` returns a
list of fixed-width strings. `cli.py` is the only module that touches
`curses`, which is what makes the scenes straightforward to unit test —
see `tests/`.

## Test

```
pytest
```
