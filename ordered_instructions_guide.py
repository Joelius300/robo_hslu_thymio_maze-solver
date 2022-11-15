from direction import Direction
from guide import Guide


class OrderedInstructionsGuide(Guide):
    """
    A Guide that replays a list of specified instructions. As always, one instruction per intersection.
    If an intersection is encountered after all the instructions have already been submitted, the Guide instructs the
    walker to stop.
    If an instruction cannot be submitted because it's not an option at the current intersection, an error is logged
    and the Guide instructs the walker to stop.
    """
    def __init__(self, instructions: list[Direction]):
        self._instructions = instructions
        self._instruction_index = 0

    def on_detected_crossing(self, options: Direction) -> Direction:
        if self._instruction_index >= len(self._instructions):
            return Direction.STOP

        dir = self._instructions[self._instruction_index]
        if dir not in options:
            print(f"Could not submit instruction {self._instruction_index} ({dir}) as it's not available on "
                  "the current intersection.")
            return Direction.STOP

        self._instruction_index += 1

        return dir
