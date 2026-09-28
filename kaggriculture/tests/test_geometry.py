from agent_lib import geometry as geo


def test_shed_access_tiles_default_board():
    assert geo.shed_access_tiles(10) == [(4, 4), (5, 4), (4, 5), (5, 5)]


def test_quadrant_of_default_board():
    assert geo.quadrant_of(0, 0, 10) == "NW"
    assert geo.quadrant_of(9, 0, 10) == "NE"
    assert geo.quadrant_of(0, 9, 10) == "SW"
    assert geo.quadrant_of(9, 9, 10) == "SE"
    assert geo.quadrant_of(4, 4, 10) == "NW"
    assert geo.quadrant_of(5, 4, 10) == "NE"
    assert geo.quadrant_of(4, 5, 10) == "SW"
    assert geo.quadrant_of(5, 5, 10) == "SE"


def test_is_shed_adjacent():
    assert geo.is_shed_adjacent((4, 4), 10)
    assert geo.is_shed_adjacent((5, 5), 10)
    assert not geo.is_shed_adjacent((0, 0), 10)


def test_step_toward_and_apply_move_reach_goal():
    pos = (0, 0)
    goal = (3, 2)
    steps = 0
    while pos != goal and steps < 20:
        d = geo.step_toward(pos, goal)
        pos = geo.apply_move(pos, d, 10)
        steps += 1
    assert pos == goal


def test_apply_move_off_board_is_noop():
    assert geo.apply_move((0, 0), "WEST", 10) == (0, 0)
    assert geo.apply_move((0, 0), "NORTH", 10) == (0, 0)
    assert geo.apply_move((9, 9), "EAST", 10) == (9, 9)


def test_quadrant_tiles_partition_board():
    board_size = 10
    all_tiles = set()
    for q in ["NW", "NE", "SW", "SE"]:
        tiles = geo.quadrant_tiles(q, board_size)
        assert len(tiles) == 25
        all_tiles.update(tiles)
    assert len(all_tiles) == 100
