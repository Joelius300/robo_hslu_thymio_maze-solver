import time

from direction import Direction
from guide import Guide
from maze_walker import MazeWalker
from ordered_instructions_guide import OrderedInstructionsGuide
from right_hand_guide import RightHandGuide
from thymio_python.thymiodirect import ThymioObserver, SingleSerialThymioRunner
from thymio_python.thymiodirect.thymio_constants import PROXIMITY_FRONT_BACK, MOTOR_LEFT, MOTOR_RIGHT, BUTTON_CENTER


class GoStraightGuide(Guide):
    def on_detected_crossing(self, options: Direction) -> Direction:
        if Direction.STRAIGHT in options:
            return Direction.STRAIGHT

        return Direction.STOP


class TurnObserver(ThymioObserver):
    def __init__(self):
        super().__init__()
        self.time_clicked = 0
        self.running = False

    def _update(self):
        if self.th[BUTTON_CENTER]:
            # self.running = not self.running
            self.running = True

            if self.running:
                self._set_motors(-100, 100)
            else:
                self._set_motors(0, 0)

            clicked = time.time_ns()
            delta = clicked - self.time_clicked
            if delta // 1000000 < 500:
                return  # only over .5 seconds

            print(delta)
            self.time_clicked = clicked

    def _set_motors(self, left: int, right: int):
        self.th[MOTOR_LEFT] = left
        self.th[MOTOR_RIGHT] = right


if __name__ == "__main__":
    # absolute minimum
    guide = GoStraightGuide()
    guide = RightHandGuide()
    directions = [
        Direction.RIGHT,
        Direction.RIGHT,
        Direction.LEFT,
        Direction.LEFT
    ]
    guide = OrderedInstructionsGuide(directions)
    observer = MazeWalker(guide)
    # observer = TurnObserver()
    SingleSerialThymioRunner({BUTTON_CENTER, PROXIMITY_FRONT_BACK, MOTOR_LEFT, MOTOR_RIGHT}, observer, 0.1).run()

    # for more customized scenarios (e.g. simulated Thymio), slightly more boilerplate is required

    # observer = HandAvoider()
    #
    # def on_error(error):
    #     print(error)
    #     observer.stop()
    #
    # thymio = Thymio(use_tcp=True, host="127.0.0.1", tcp_port=35287, on_comm_error=on_error, discover_rate=0.1,
    #                 refreshing_coverage={BUTTON_CENTER, PROXIMITY_FRONT_BACK, MOTOR_LEFT, MOTOR_RIGHT})
    #
    # with thymio, observer:
    #     thymio.connect()
    #
    #     time.sleep(2)  # wait until connected
    #
    #     observer.run(thymio, thymio.first_node())  # blocks until done
