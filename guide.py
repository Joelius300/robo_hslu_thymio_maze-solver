from abc import ABC, abstractmethod

from direction import Direction


class Guide(ABC):
    """
    The Guide is passed to the MazeWalker and tells it which direction to take once it encounters an intersection.
    """
    @abstractmethod
    def on_detected_crossing(self, options: Direction) -> Direction:
        """Returns the direction the MazeWalker should turn, given a set of possible directions."""
        pass
