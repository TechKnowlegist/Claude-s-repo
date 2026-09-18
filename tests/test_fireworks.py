from asciiverse.scenes.fireworks import Fireworks


def test_render_dimensions():
    fw = Fireworks(width=30, height=20, seed=1)
    lines = fw.render()
    assert len(lines) == 20
    assert all(len(line) == 30 for line in lines)


def test_rockets_eventually_launch_and_explode_into_particles():
    fw = Fireworks(width=40, height=20, seed=1, launch_chance=1.0, max_rockets=1)
    fw.step()
    assert len(fw.rockets) == 1
    assert fw.particles == []

    # Run until the rocket explodes into particles.
    for _ in range(200):
        fw.step()
        if fw.particles:
            break
    assert fw.particles, "rocket never exploded into particles"


def test_particles_eventually_die_out():
    fw = Fireworks(width=40, height=20, seed=2, launch_chance=1.0, max_rockets=1)
    for _ in range(30):
        fw.step()
    assert fw.particles, "expected some particles mid-simulation"

    # Stop new launches so the existing particles can fully decay.
    fw.launch_chance = 0.0
    fw.rockets = []
    for _ in range(200):
        fw.step()
    assert fw.particles == []


def test_deterministic_with_same_seed():
    a = Fireworks(width=25, height=15, seed=123, launch_chance=1.0)
    b = Fireworks(width=25, height=15, seed=123, launch_chance=1.0)
    for _ in range(50):
        a.step()
        b.step()
    assert a.render() == b.render()
