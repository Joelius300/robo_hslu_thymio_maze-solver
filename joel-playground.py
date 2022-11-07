import time
from typing import Optional

from abc import ABC, abstractmethod
from enum import Flag, auto
from thymio_python.thymiodirect import ThymioObserver, SingleSerialThymioRunner
from thymio_python.thymiodirect.thymio_constants import PROXIMITY_FRONT_BACK, MOTOR_LEFT, MOTOR_RIGHT, BUTTON_CENTER


class Direction(Flag):
    STOP = 0
    STRAIGHT = auto()
    LEFT = auto()
    RIGHT = auto()
    U_TURN = auto()


class Guide(ABC):
    # TODO could also use some sort of matrix with has 1's in the places where you could go and 0's where there are walls.
    # Not sure how helpful that is though.
    @abstractmethod
    def on_detected_crossing(self, options: Direction) -> Direction:
        """Returns the direction the Thymio should turn."""
        pass


class GoStraightGuide(Guide):
    def on_detected_crossing(self, options: Direction) -> Direction:
        if Direction.STRAIGHT in options:
            return Direction.STRAIGHT

        return Direction.STOP


class RightHandGuide(Guide):
    def on_detected_crossing(self, options: Direction) -> Direction:
        if Direction.RIGHT in options:
            return Direction.RIGHT
        elif Direction.STRAIGHT in options:
            return Direction.STRAIGHT

        return Direction.U_TURN


def _get_directions(left, right, front):
    dir = Direction.U_TURN
    if left:
        dir |= Direction.LEFT
    if right:
        dir |= Direction.RIGHT
    if front:
        dir |= Direction.STRAIGHT

    return dir


class MazeWalker(ThymioObserver):
    """
    Current implementation:

    It goes straight and corrects a bit if necessary.
    Once it sees and opening to the left or right, it keeps moving but remembers that it saw an opening.
    Once it doesn't see that opening anymore, it's positioned almost perfectly on the intersection.
    It now asks the guide what direction it should take and stores that direction.
    If a direction is being taken, it sets the motors to opposite speeds and uses predefined and well tested (TM)
    time durations to turn -90, 90 or 180 degrees. Once those time durations have elapsed, it sets itself to go straight
    again.

    Important:
    - Currently going right works well (left should too but not tested).
    - The implementation of going to the center of the intersection made it unreactive to dead ends because it doesn't
      really do anything anymore until and opening is found and then closed again which of course doesn't happen when it
      drives straight into the wall. This shouldn't be too hard to fix thought, it's just an additional case to code.
    - Currently it queries the guide on which direction it should take only when it's on the intersection, not as soon
      as it sees there is one. This shouldn't be an issue generally speaking but something to keep in mind.
    - Currently it checks left first, right second when determining whether it's at an intersection and needs to wait
      until the opening disappears. Meaning that if it comes to an intersection where both left and right open at the
      same time, it will wait until the left side is back and then continue with the openings it saw just before the
      left side became visible. If the right side in this case became visible a tick before the left side was, the
      algorithm will think there's no opening on the right side even though it just missed it by a tiny bit.
      Since the right hand rule is one of the use cases, it might make more sense to switch this so right gets priority.
      Still, changes are that this doesn't even pose an issue but I'd rather have it documented.
    """

    ninety_degree_time_ns = 2247700724  # comes from quite a bit of testing with Thymio 17
    turn_timings = {
        Direction.LEFT: {
            "left": -100,
            "right": 100,
            "duration": ninety_degree_time_ns
        },
        Direction.RIGHT: {
            "left": 100,
            "right": -100,
            "duration": ninety_degree_time_ns
        },
        Direction.U_TURN: {
            "left": 100,
            "right": -100,
            "duration": 2 * ninety_degree_time_ns
        }
    }

    def __init__(self, guide: Guide):
        super().__init__()
        self.guide = guide
        self.base_speed = 200
        self.diff_threshold = 75  # above what diff value should you steer to stay parallel
        self.prox_threshold = 100  # below what value should you consider a proximity value to indicate an opening in the maze
        self.front_prox_threshold = 3000  # front is more sensitive so if we want to be able to drive closer to the wall we need a higher threshold
        self.turn_initiation_time = 0
        self.current_turn = Direction.STRAIGHT
        self.waiting_until_intersection_in_direction: Optional[Direction] = None
        self.last_possible_directions: Direction = None

    def _update(self):
        if self.current_turn == Direction.STOP or self.th[BUTTON_CENTER]:
            self.stop()
            return

        if self.current_turn == Direction.LEFT or self.current_turn == Direction.RIGHT or self.current_turn == Direction.U_TURN:
            print("Doing turn:", self.current_turn)
            self.do_turn()
            return

        assert (self.current_turn == Direction.STRAIGHT)

        # prox values = light reflected -> more reflected = higher values = closer
        prox = self.th[PROXIMITY_FRONT_BACK]
        prox_front_left = prox[0]
        prox_front_right = prox[4]
        prox_front_center = prox[2]

        print("Left:", prox_front_left, "|", "Right:", prox_front_right, "|", "Front:", prox_front_center)

        space_left = prox_front_left < self.prox_threshold
        space_right = prox_front_right < self.prox_threshold
        space_front = prox_front_center < self.front_prox_threshold

        diff = prox_front_left - prox_front_right  # positive if left wall is closer -> correction right

        # only do correction if in a corridor
        if not space_left and not space_right and abs(diff) > self.diff_threshold:
            correction = round(diff / 50)
            self._set_motors(self.base_speed + correction, self.base_speed - correction)
        else:
            self._set_motors_straight()

        # get all possible directions we can currently see in -> potential turns
        possible_dirs = _get_directions(space_left, space_right, space_front)

        if not self.waiting_until_intersection_in_direction:
            print("No intersection in sight.")
            # we are not waiting until we are on an intersection, check if we should be
            if Direction.LEFT in possible_dirs:
                self.waiting_until_intersection_in_direction = Direction.LEFT
            elif Direction.RIGHT in possible_dirs:
                self.waiting_until_intersection_in_direction = Direction.RIGHT
        elif self.waiting_until_intersection_in_direction not in possible_dirs:
            # we are waiting until we are on an intersection and just reached the middle of that intersection because
            # the opening that we were looking at earlier isn't visible anymore meaning we're currently located just
            # before the next wall aka on the intersection. Now we can ask the guide where we should go next and
            # initiate the turn the guide instructs us to take. Of course, we need to give it the possible directions
            # we queried the last time because now that direction is not deemed possible anymore because we can see the
            # wall again.
            self.waiting_until_intersection_in_direction = None
            self.current_turn = self.guide.on_detected_crossing(self.last_possible_directions)
            self.turn_initiation_time = time.time_ns()
            print("On intersection; ready to take a turn.")
            print(f"Chose {self.current_turn} from {{{self.last_possible_directions}}}")
        else:
            # we are still waiting to get to the middle of the intersection but currently the opening to the side is
            # still visible meaning we're not there yet, so just keep on moving.
            assert (self.waiting_until_intersection_in_direction in possible_dirs)
            print("Moving to the center of the intersection.")

        self.last_possible_directions = possible_dirs

    def do_turn(self):
        left, right, duration = self._get_timings(self.current_turn)
        if time.time_ns() - self.turn_initiation_time >= duration:
            self.current_turn = Direction.STRAIGHT
            self._set_motors_straight()  # just to be a bit faster / more reactive, it would be set next iteration anyway
        else:
            self._set_motors(left, right)

    def _get_timings(self, direction: Direction):
        timings = self.turn_timings[direction]
        return timings["left"], timings["right"], timings["duration"]

    def _set_motors_straight(self):
        self._set_motors(self.base_speed, self.base_speed)

    def stop(self):
        self._set_motors(0, 0)
        super().stop()

    def _set_motors(self, left: int, right: int):
        self.th[MOTOR_LEFT] = left
        self.th[MOTOR_RIGHT] = right


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
