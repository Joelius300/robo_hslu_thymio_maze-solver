from enum import Flag, auto


class Direction(Flag):
    STOP = 0
    STRAIGHT = auto()
    LEFT = auto()
    RIGHT = auto()
    U_TURN = auto()
