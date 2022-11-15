from direction import Direction
from guide import Guide


class RightHandGuide(Guide):
    """
    A Guide implementing the right hand rule (always follow the right wall).
    """
    def on_detected_crossing(self, options: Direction) -> Direction:
        if Direction.RIGHT in options:
            return Direction.RIGHT
        elif Direction.STRAIGHT in options:
            return Direction.STRAIGHT
        elif Direction.LEFT in options:
            return Direction.LEFT

        return Direction.U_TURN
