from asciiverse.color import visible_length
from asciiverse.scenes import SCENES
from asciiverse.scenes.fireworks_color import FireworksColor
from asciiverse.scenes.matrix_color import MatrixColor


def test_color_scenes_are_registered_and_flagged():
    assert SCENES["fireworks-color"] is FireworksColor
    assert SCENES["matrix-green"] is MatrixColor
    assert FireworksColor(10, 5).color is True
    assert MatrixColor(10, 5).color is True


def test_fireworks_color_renders_valid_width_and_uses_multiple_hues():
    fw = FireworksColor(width=40, height=20, seed=1, launch_chance=1.0, max_rockets=3)
    seen_colors = set()
    for _ in range(120):
        for line in fw.render():
            assert visible_length(line) == 40
        # Collect every distinct 24-bit fg escape we emit, to confirm this
        # isn't secretly rendering in one color.
        for line in fw.render():
            start = 0
            while True:
                idx = line.find("\x1b[38;2;", start)
                if idx == -1:
                    break
                end = line.index("m", idx)
                seen_colors.add(line[idx:end])
                start = end
        fw.step()
    assert len(seen_colors) > 3


def test_matrix_color_head_is_brighter_than_tail():
    from asciiverse.color import lerp_color

    m = MatrixColor(width=10, height=30, seed=3)
    # Force one column to a known, long trail so head vs. tail is unambiguous.
    col = m.columns[0]
    col.head = 15
    col.length = 10
    lines = m.render()
    assert visible_length(lines[0]) == 10

    tail_color = lerp_color((45, 220, 95), (0, 40, 15), 9 / 10)
    # The tail should be much darker than the near-white head color.
    assert sum(tail_color) < sum((215, 255, 220))


def test_matrix_color_deterministic_dimensions_over_time():
    m = MatrixColor(width=20, height=12, seed=5)
    for _ in range(50):
        lines = m.render()
        assert len(lines) == 12
        assert all(visible_length(line) == 20 for line in lines)
        m.step()
