"""Board coordinates, shed adjacency, and simple pathing. y grows downward
(tiles[y][x]); NORTH decreases y, SOUTH increases y, matching kaggriculture.py's
FARMER_MOVES = {"NORTH": (0,-1), "SOUTH": (0,1), "EAST": (1,0), "WEST": (-1,0)}.
"""
from .constants import MOVE_DIRS


def shed_access_tiles(board_size):
    half = board_size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]


def quadrant_of(x, y, board_size):
    half = board_size // 2
    return ("N" if y < half else "S") + ("W" if x < half else "E")


def is_shed_adjacent(pos, board_size):
    return tuple(pos) in set(shed_access_tiles(board_size))


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def nearest_shed_tile(pos, board_size):
    tiles = shed_access_tiles(board_size)
    return min(tiles, key=lambda t: manhattan(pos, t))


def step_toward(pos, goal):
    """One greedy step direction (no obstacle avoidance needed: locked tiles are
    passable and nothing else blocks movement in this game). Reduces the larger
    axis gap first; ties broken by reducing x first for determinism."""
    dx = goal[0] - pos[0]
    dy = goal[1] - pos[1]
    if dx == 0 and dy == 0:
        return None
    if abs(dx) >= abs(dy):
        return "EAST" if dx > 0 else "WEST"
    return "SOUTH" if dy > 0 else "NORTH"


def path_len(pos, goal):
    return manhattan(pos, goal)


def apply_move(pos, direction, board_size):
    for name, (dx, dy) in MOVE_DIRS:
        if name == direction:
            nx, ny = pos[0] + dx, pos[1] + dy
            if 0 <= nx < board_size and 0 <= ny < board_size:
                return (nx, ny)
            return tuple(pos)
    return tuple(pos)


def quadrant_tiles(quadrant, board_size):
    half = board_size // 2
    y0, y1 = (0, half) if quadrant[0] == "N" else (half, board_size)
    x0, x1 = (0, half) if quadrant[1] == "W" else (half, board_size)
    return [(x, y) for y in range(y0, y1) for x in range(x0, x1)]
