from typing import List, Tuple

from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from direction import Direction


def get_directions(path: List[Tuple[int, int]]) -> List[Direction]:
    """
    Transforms a list of maze coordinates to a list of turn instructions (one per intersection).
    """
    last_direction = (path[0][0] - path[1][0], path[0][1] - path[1][1])
    last_node = path[0]

    directions = []

    for node in path[1:]:
        x_difference = last_node[0] - node[0]
        y_difference = last_node[1] - node[1]

        direction = (x_difference, y_difference)

        # Change in Direction, example: last_direction = (0, -1)  direction = (-1, 0)
        if direction[0] != last_direction[0] and last_direction[0] == 0:
            if direction[0] == -1 and last_direction[1] == 1 or direction[0] == 1 and last_direction[1] == -1:
                directions.append(Direction.RIGHT)
            else:
                directions.append(Direction.LEFT)

        # Change in Direction, example: last_direction = (-1, 0)  direction = (0, -1)
        if direction[1] != last_direction[1] and last_direction[1] == 0:
            if direction[1] == 1 and last_direction[0] == -1 or direction[1] == -1 and last_direction[0] == 1:
                directions.append(Direction.LEFT)
            else:
                directions.append(Direction.RIGHT)

        last_direction = direction
        last_node = node

    return directions


def find_path(maze: List[List[int]], start_node: Tuple[int, int], end_node: Tuple[int, int]) -> List[Tuple[int, int]]:
    """
    Finds a path through the maze using A* from start_node to end_node.

    Parameter
    ----------
    maze:
    Nested array of 0 and 1, where 1 means walkable and 0 means blocked (wall).
    You could also provide values higher than 1 which would indicate a weighted walkable tile so it's walkable but
    potentially more expensive than other tiles.

    start_node:
    Point (x/y tuple) indicating the start position in the maze.

    end_node:
    Point (x/y tuple) indicating the end position in the maze.

    Returns
    -------
    The path as a list of 2d points (x/y tuples) for nodes to stay on.
    """
    grid = Grid(matrix=maze)

    start = grid.node(start_node[0], start_node[1])
    end = grid.node(end_node[0], end_node[1])

    finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
    path, runs = finder.find_path(start, end, grid)

    print('operations:', runs, 'path length:', len(path))
    print(grid.grid_str(path=path, start=start, end=end))

    return path


def test_get_directions():
    path = [(1, 6), (1, 5), (1, 4), (1, 3), (2, 3), (3, 3), (4, 3), (4, 2), (4, 1), (3, 1), (2, 1), (1, 1), (1, 0),
            (0, 0)]
    directions = [
        Direction.RIGHT,
        Direction.LEFT,
        Direction.LEFT,
        Direction.RIGHT,
        Direction.LEFT
    ]

    assert directions == get_directions(path)

    path = [
        (7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (6, 5), (5, 5), (4, 5), (3, 5), (3, 4), (3, 3), (2, 3), (1, 3),
        (1, 4), (1, 5), (1, 6)
    ]

    directions = [
        Direction.RIGHT,
        Direction.RIGHT,
        Direction.LEFT,
        Direction.LEFT
    ]

    assert directions == get_directions(path)


def test_find_path():
    maze = \
        [[0, 0, 0, 0, 0, 0, 0, 1, 0],
         [0, 1, 1, 1, 1, 1, 0, 1, 0],
         [0, 1, 0, 0, 0, 1, 0, 1, 0],
         [0, 1, 1, 1, 1, 1, 0, 1, 0],
         [0, 1, 0, 1, 0, 0, 0, 1, 0],
         [0, 1, 0, 1, 1, 1, 1, 1, 0],
         [0, 1, 0, 0, 0, 0, 0, 0, 0]]

    start = (7, 0)
    end = (1, 6)

    path = [
        (7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (6, 5), (5, 5), (4, 5), (3, 5), (3, 4), (3, 3), (2, 3), (1, 3),
        (1, 4), (1, 5), (1, 6)
    ]

    assert path == find_path(maze, start, end)


if __name__ == "__main__":
    test_get_directions()
    test_find_path()
