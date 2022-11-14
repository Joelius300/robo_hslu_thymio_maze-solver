from direction import Direction
from guide import Guide


class OrderedInstructionsGuide(Guide):
    def __init__(self, instructions: list[Direction]):
        self._instructions = instructions
        self._instruction_index = 0

    def on_detected_crossing(self, options: Direction) -> Direction:
        if self._instruction_index >= len(self._instructions):
            return Direction.STOP

        dir = self._instructions[self._instruction_index]
        if dir not in options:
            print(f"Could not submit instruction {self._instruction_index}: {dir} as it's not available on "
                  "the current intersection.")
            return Direction.STOP

        self._instruction_index += 1

        return dir
