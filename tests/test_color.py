from asciiverse.color import lerp_color, render_row, visible_length


def test_lerp_color_endpoints_and_midpoint():
    a, b = (0, 0, 0), (100, 200, 40)
    assert lerp_color(a, b, 0.0) == a
    assert lerp_color(a, b, 1.0) == b
    assert lerp_color(a, b, 0.5) == (50, 100, 20)


def test_lerp_color_clamps_t_outside_zero_one():
    a, b = (0, 0, 0), (10, 10, 10)
    assert lerp_color(a, b, -5) == a
    assert lerp_color(a, b, 5) == b


def test_render_row_plain_cells_have_no_escapes():
    row = [("a", None, None), ("b", None, None)]
    result = render_row(row)
    assert result == "ab"
    assert visible_length(result) == 2


def test_render_row_embeds_fg_and_bg_and_resets_at_end():
    row = [("x", (255, 0, 0), (0, 0, 255))]
    result = render_row(row)
    assert "\x1b[38;2;255;0;0m" in result
    assert "\x1b[48;2;0;0;255m" in result
    assert result.endswith("\x1b[0m")
    assert visible_length(result) == 1


def test_visible_length_ignores_embedded_escapes():
    colored = render_row([("h", (1, 2, 3), None), ("i", None, None)])
    assert visible_length(colored) == 2


def test_render_row_only_changes_escapes_when_color_changes():
    # Three cells, same color throughout -- the color codes should only be
    # emitted once (at the start), not per character.
    color = (10, 20, 30)
    row = [("a", color, None), ("b", color, None), ("c", color, None)]
    result = render_row(row)
    assert result.count("\x1b[38;2;10;20;30m") == 1
