from enum import Flag, auto

from pyamaze import maze,agent,textLabel

from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from direction import Direction

from queue import PriorityQueue


#N, O, S, W
#1 = Open, 0 = Wall
"""
matrix_example1 = \
                [[0, 0, 1, 1, 1, 0],
                [0, 0, 0, 0, 0, 1],
                [1, 1, 1, 1, 0, 1],
                [1, 0, 0, 0, 0, 1],
                [1, 0, 1, 1, 1, 1],
                [0, 0, 1, 0, 0, 0],
                [0, 0, 1, 0, 0, 0]]
"""

maze_example1 = \
                [[1, 1, 0, 0, 0, 1],
                [1, 1, 1, 1, 1, 0],
                [0, 0, 0, 0, 1, 0],
                [0, 1, 1, 1, 1, 0],
                [0, 1, 0, 0, 0, 0],
                [1, 1, 0, 1, 1, 1],
                [1, 1, 0, 1, 1, 1]]


maze_example2 = \
                [[0, 0, 0, 0, 0, 0, 0, 1, 0],
                [0, 1, 1, 1, 1, 1, 0, 1, 0],
                [0, 1, 0, 0, 0, 1, 0, 1, 0],
                [0, 1, 1, 1, 1, 1, 0, 1, 0],
                [0, 1, 0, 1, 0, 0, 0, 1, 0],
                [0, 1, 0, 1, 1, 1, 1, 1, 0],
                [0, 1, 0, 0, 0, 0, 0, 0,0]]




def get_path(matrix, start_node, end_node):
    grid = Grid(matrix=matrix)

    start = grid.node(start_node[0], start_node[1])
    end = grid.node(end_node[0], end_node[1])

    finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
    path, runs = finder.find_path(start, end, grid)

    print('operations:', runs, 'path length:', len(path))
    print(grid.grid_str(path=path, start=start, end=end))

    return path

def get_directions(path):

    last_direction = (path[0][0] - path[1][0], path[0][1] - path[1][1])
    last_node = path[0]

    directions = []

    for node in path[1:]:
        x_difference = last_node[0] - node[0]
        y_difference = last_node[1] - node[1]

        direction = (x_difference, y_difference)

        #Change in Direction, example: last_direction = (0, -1)  direction = (-1, 0)
        if direction[0] != last_direction[0] and last_direction[0] == 0:
            if direction[0] == -1 and last_direction[1] == 1:
                directions.append(Direction.RIGHT)
            else:
                directions.append(Direction.LEFT)

        # Change in Direction, example: last_direction = (-1, 0)  direction = (0, -1)
        if direction[1] != last_direction[1] and last_direction[1] == 0:
            if direction[1] == 1 and last_direction[0] == -1: # and last_direction[0] == 1
                directions.append(Direction.LEFT)
            else:
                directions.append(Direction.RIGHT)

        last_direction = direction
        last_node = node

    print(directions)


def h(cell1,cell2):
    x1,y1=cell1
    x2,y2=cell2

    return abs(x1-x2) + abs(y1-y2)


def aStar(m):
    start=(m.rows,m.cols)
    g_score={cell:float('inf') for cell in m.grid}
    g_score[start]=0
    f_score={cell:float('inf') for cell in m.grid}
    f_score[start]=h(start,(1,1))

    open=PriorityQueue()
    open.put((h(start,(1,1)),h(start,(1,1)),start))
    aPath={}
    while not open.empty():
        currCell=open.get()[2]
        if currCell==(1,1):
            break
        for d in 'ESNW':
            if m.maze_map[currCell][d]==True:
                if d=='E':
                    childCell=(currCell[0],currCell[1]+1)
                if d=='W':
                    childCell=(currCell[0],currCell[1]-1)
                if d=='N':
                    childCell=(currCell[0]-1,currCell[1])
                if d=='S':
                    childCell=(currCell[0]+1,currCell[1])

                temp_g_score=g_score[currCell]+1
                temp_f_score=temp_g_score+h(childCell,(1,1))

                if temp_f_score < f_score[childCell]:
                    g_score[childCell]= temp_g_score
                    f_score[childCell]= temp_f_score
                    open.put((temp_f_score,h(childCell,(1,1)),childCell))
                    aPath[childCell]=currCell
    fwdPath={}
    cell=(1,1)
    while cell!=start:
        fwdPath[aPath[cell]]=cell
        cell=aPath[cell]
    return fwdPath


def maze_example():
    m = maze(10, 10)
    m.CreateMaze()
    path = aStar(m)

    a = agent(m, footprints=True)
    m.tracePath({a: path})
    l = textLabel(m, 'A Star Path Length', len(path) + 1)

    m.run()

if __name__=='__main__':
    #maze_example()

    start_node = [1, 6]
    end_node = [7, 0]

    print(start_node[0], start_node[1])
    path = GetPath(maze_example2, start_node , end_node)
    GetDirections(path)
    print(path)