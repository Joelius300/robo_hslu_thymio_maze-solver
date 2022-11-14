from abc import ABC, abstractmethod

from direction import Direction


class Guide(ABC):
    # TODO could also use some sort of matrix with has 1's in the places where you could go and 0's where there are walls.
    # Not sure how helpful that is though.
    @abstractmethod
    def on_detected_crossing(self, options: Direction) -> Direction:
        """Returns the direction the Thymio should turn."""
        pass
