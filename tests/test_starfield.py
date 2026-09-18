from asciiverse.scenes.starfield import Starfield


def test_render_dimensions():
    s = Starfield(width=40, height=20, seed=1)
    lines = s.render()
    assert len(lines) == 20
    assert all(len(line) == 40 for line in lines)


def test_stars_recycle_instead_of_vanishing():
    s = Starfield(width=40, height=20, seed=2, num_stars=10, speed=0.5)
    for _ in range(50):
        s.step()
    # Every star should have been kept within a sane, positive-z range by
    # the respawn logic -- none should be stuck at or below zero.
    assert all(star.z > 0 for star in s.stars)


def test_deterministic_with_same_seed():
    a = Starfield(width=20, height=10, seed=42)
    b = Starfield(width=20, height=10, seed=42)
    for _ in range(15):
        a.step()
        b.step()
    assert a.render() == b.render()


def test_different_seeds_diverge():
    a = Starfield(width=20, height=10, seed=1)
    b = Starfield(width=20, height=10, seed=2)
    for _ in range(5):
        a.step()
        b.step()
    assert a.render() != b.render()
