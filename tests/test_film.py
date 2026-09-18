import pytest

from asciiverse.color import visible_length
from asciiverse.film import Crawl, Film, SceneShot, TitleCard, composite, dither_fade, draw_text_block
from asciiverse.film.shorts import SHORTS
from asciiverse.scenes import Starfield


def test_composite_overlays_non_space_chars_and_clips_out_of_bounds():
    background = ["....", "....", "...."]
    art = ["AB", "CD"]
    result = composite(background, art, x=1, y=1)
    assert result == ["....", ".AB.", ".CD."]

    # Off the edge in both directions -- nothing should raise, and nothing
    # visible should change since the whole row is out of bounds.
    result = composite(background, ["XY"], x=3, y=-1)
    assert result == background


def test_dither_fade_bounds():
    lines = ["###", "###"]
    assert dither_fade(lines, 1.0) == lines
    assert dither_fade(lines, 0.0) == ["   ", "   "]
    # Partial fade never introduces a character that wasn't there, and never
    # touches an already-blank cell.
    partial = dither_fade(lines, 0.5)
    for line in partial:
        assert set(line) <= {" ", "#"}


def test_draw_text_block_centers_text():
    background = [" " * 10 for _ in range(3)]
    result = draw_text_block(background, ["hi"], top=1, width=10)
    assert result[1].strip() == "hi"
    assert result[0] == " " * 10
    assert result[2] == " " * 10


def test_title_card_dimensions_and_fade_in_out():
    card = TitleCard(["HELLO"], duration=10, fade_frames=3)
    card.enter(20, 5)
    first = card.frame(0, 20, 5)
    middle = card.frame(5, 20, 5)
    last = card.frame(9, 20, 5)
    assert len(first) == 5 and all(len(line) == 20 for line in first)
    # Fully faded in at the first frame means only a hint of the text (or
    # none) should be visible, while the middle frame should be fully legible.
    assert "HELLO" in "".join(middle)
    assert "HELLO" not in "".join(first)
    assert "HELLO" not in "".join(last)


def test_scene_shot_steps_backdrop_each_frame():
    shot = SceneShot(scene_factory=lambda w, h: Starfield(w, h, seed=1), duration=5)
    shot.enter(30, 10)
    frame0 = shot.frame(0, 30, 10)
    frame1 = shot.frame(1, 30, 10)
    # The backdrop should have advanced between frames (state isn't frozen).
    assert frame0 != frame1


def test_scene_shot_draws_subtitles_in_window():
    shot = SceneShot(
        scene_factory=lambda w, h: Starfield(w, h, seed=1, num_stars=0),
        duration=5,
        subtitles=[(0, 2, "hello")],
    )
    shot.enter(20, 6)
    with_subtitle = shot.frame(0, 20, 6)
    without_subtitle = shot.frame(3, 20, 6)
    assert "hello" in "".join(with_subtitle)
    assert "hello" not in "".join(without_subtitle)


def test_crawl_moves_text_upward_over_time():
    crawl = Crawl(lines=["ONE LINE OF CRAWL TEXT"], duration=20)
    crawl.enter(40, 10)

    def visible_row(tick):
        frame = crawl.frame(tick, 40, 10)
        rows = [i for i, line in enumerate(frame) if line.strip()]
        return rows[0] if rows else None

    early_row = visible_row(3)
    late_row = visible_row(12)
    assert early_row is not None and late_row is not None
    assert late_row < early_row


def test_film_advances_through_shots_and_reports_finished():
    shots = [TitleCard(["A"], duration=2, fade_frames=0), TitleCard(["B"], duration=3, fade_frames=0)]
    film = Film(shots, width=10, height=3, fps=10)
    assert film.total_frames == 5
    seen = []
    for _ in range(film.total_frames):
        seen.append(film.render())
        film.step()
    # Exactly total_frames render/step pairs walks through every frame of
    # every shot, and the final step flips finished.
    assert film.finished
    assert "A" in "".join(seen[0])
    assert "B" in "".join(seen[2])


def test_film_requires_at_least_one_shot():
    with pytest.raises(ValueError):
        Film([], width=10, height=5)


@pytest.mark.parametrize("name", sorted(SHORTS))
def test_shipped_shorts_render_full_length_without_error(name):
    film = SHORTS[name](width=40, height=16, fps=8)
    is_color = getattr(film, "color", False)
    for _ in range(film.total_frames):
        lines = film.render()
        assert len(lines) == 16
        if is_color:
            # Colored lines carry ANSI escapes, so measure visible width
            # rather than raw string length.
            assert all(visible_length(line) == 40 for line in lines)
        else:
            assert all(len(line) == 40 for line in lines)
        film.step()
    assert film.finished
