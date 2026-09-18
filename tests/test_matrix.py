from asciiverse.scenes.matrix import MatrixRain


def test_render_dimensions():
    m = MatrixRain(width=30, height=15, seed=1)
    lines = m.render()
    assert len(lines) == 15
    assert all(len(line) == 30 for line in lines)


def test_one_column_per_width():
    m = MatrixRain(width=17, height=12, seed=3)
    assert len(m.columns) == 17


def test_heads_move_downward_over_time():
    m = MatrixRain(width=10, height=50, seed=5)
    starting_heads = [c.head for c in m.columns]
    for _ in range(30):
        m.step()
    ending_heads = [c.head for c in m.columns]
    # A column may have respawned (head reset), but on average things move
    # down: at least some columns should have advanced past their start.
    assert any(end > start for start, end in zip(starting_heads, ending_heads))


def test_deterministic_with_same_seed():
    a = MatrixRain(width=25, height=10, seed=99)
    b = MatrixRain(width=25, height=10, seed=99)
    for _ in range(20):
        a.step()
        b.step()
    assert a.render() == b.render()
