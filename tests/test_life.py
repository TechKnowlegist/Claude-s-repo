from asciiverse.scenes.life import Life


def test_render_dimensions():
    life = Life(width=20, height=10, seed=1)
    lines = life.render()
    assert len(lines) == 10
    assert all(len(line) == 20 for line in lines)


def test_blinker_oscillates_with_period_two():
    life = Life(width=5, height=5, seed=0, density=0.0)
    assert life.alive == set()
    # A horizontal blinker in the middle row.
    life.alive = {(1, 2), (2, 2), (3, 2)}
    life.step()
    assert life.alive == {(2, 1), (2, 2), (2, 3)}
    life.step()
    assert life.alive == {(1, 2), (2, 2), (3, 2)}


def test_block_still_life_is_stable():
    life = Life(width=6, height=6, seed=0, density=0.0)
    block = {(2, 2), (3, 2), (2, 3), (3, 3)}
    life.alive = set(block)
    life.step()
    assert life.alive == block


def test_wraps_around_edges():
    # A glider-adjacent single-row pattern that straddles the border should
    # still interact with cells on the opposite edge (toroidal topology).
    life = Life(width=4, height=4, seed=0, density=0.0)
    life.alive = {(3, 1), (0, 1), (1, 1)}  # horizontal blinker wrapping x
    life.step()
    assert life.alive == {(0, 0), (0, 1), (0, 2)}


def test_extinct_board_reseeds_instead_of_staying_empty():
    life = Life(width=10, height=10, seed=7, density=0.0)
    assert life.alive == set()
    life.step()
    assert life.alive != set()
    assert life.generation == 0  # reseeding resets the generation counter
