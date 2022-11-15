from maze_solver import get_directions, find_path
from maze_walker import MazeWalker
from ordered_instructions_guide import OrderedInstructionsGuide
from thymio_python.thymiodirect import SingleSerialThymioRunner
from thymio_python.thymiodirect.thymio_constants import BUTTON_CENTER, PROXIMITY_FRONT_BACK

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

walker = MazeWalker(OrderedInstructionsGuide(get_directions(find_path(maze, start, end))))
SingleSerialThymioRunner({BUTTON_CENTER, PROXIMITY_FRONT_BACK}, walker, 0.08).run()
