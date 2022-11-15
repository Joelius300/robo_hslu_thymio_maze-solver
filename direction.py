from enum import Flag, auto


class Direction(Flag):
    """
    Flag enum to encapsulate one or more directions including stopping.
    """
    STOP = 0
    STRAIGHT = auto()
    LEFT = auto()
    RIGHT = auto()
    U_TURN = auto()
