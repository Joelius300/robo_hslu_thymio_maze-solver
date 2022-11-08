import time
from abc import ABC, abstractmethod
from enum import Flag, auto
from typing import Optional

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
        elif Direction.LEFT in options:
            return Direction.LEFT

        return Direction.U_TURN


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

    It goes straight and corrects a bit if necessary (and if it has accurate reference points (walls) for it).
    Once it sees an opening to the left or right, or it sees a dead end coming up, it keeps moving but remembers that
    it saw an opening/dead end.
    Once it doesn't see that opening anymore, or it's standing in front of a wall, it's positioned almost perfectly on
    the intersection (or just before the wall in the case of a dead end).
    It now asks the guide what direction it should take and stores that direction as "current_turn". The possible
    directions it gives to the guide, are the ones it saw when it first spotted the intersection.
    If a direction is being taken, it sets the motors to opposite speeds and uses predefined and well tested (TM)
    time durations to turn -90, 90 or 180 degrees. Once those time durations have elapsed, it sets itself to go straight
    again.

    Important:
    - Currently it queries the guide on which direction it should take only when it's on the intersection, not as soon
      as it sees there is one. This shouldn't be an issue generally speaking but something to keep in mind.
    - In situations where there is an intersection with paths going left AND right, the sensors need to pick up both of
      them at the same time otherwise it might not consider the other as possibility. Since we're using the right hand
      rule in one of the guides, it checks right before left so in the event of collision, right is more likely to be
      picked up correctly which is more important than correctly seeing the left opening.
    """

    # comes from quite a bit of testing witThymio 17, can be adjusted slightly depending on the weather
    ninety_degree_time_ns = 2247700724 * .95
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
        self.opening_prox_threshold = 100  # below what value should you consider a proximity value to indicate an opening in the maze
        self.on_intersection_prox_threshold = 2000  # above what proximity value should left and right indicate that you have reached the intersection
        self.front_space_prox_threshold = 3200  # front is more sensitive so if we want to be able to drive closer to the wall we need a higher threshold
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

        opening_left = prox_front_left < self.opening_prox_threshold
        opening_right = prox_front_right < self.opening_prox_threshold
        opening_front = prox_front_center < self.opening_prox_threshold

        diff = prox_front_left - prox_front_right  # positive if left wall is closer -> correction right

        # only do correction if in a corridor and not waiting for an intersection or dead end
        if not opening_left and not opening_right and abs(diff) > self.diff_threshold and not self.waiting_until_intersection_in_direction:
            correction = round(diff / 50)
            self._set_motors(self.base_speed + correction, self.base_speed - correction)
        else:
            self._set_motors_straight()

        # get all possible directions we can currently see in -> potential turns
        possible_dirs = _get_directions(opening_left, opening_right, opening_front)

        is_on_intersection = False
        # either waiting on dead end, or we see there will be a dead end soon in which case we don't want the side
        # sensors as they hit the front wall too early so use the front center sensor
        if self.waiting_until_intersection_in_direction == Direction.STRAIGHT or not opening_front:
            is_on_intersection = prox_front_center > self.front_space_prox_threshold
        # we're waiting on an intersection to the right, check if we see the perpendicular wall right
        elif self.waiting_until_intersection_in_direction == Direction.RIGHT:
            is_on_intersection = prox_front_right > self.on_intersection_prox_threshold
        # we're waiting on an intersection to the left, check if we see the perpendicular wall left
        elif self.waiting_until_intersection_in_direction == Direction.LEFT:
            is_on_intersection = prox_front_left > self.on_intersection_prox_threshold

        if is_on_intersection:
            # We just reached the center of the intersection we were waiting for.
            # Now we can ask the guide where we should go next and initiate the turn the guide instructs us to take.
            # Of course, we need to give it the possible directions we queried when we first saw the intersection
            # because now that direction is not deemed possible anymore because we can see the wall again.
            self.waiting_until_intersection_in_direction = None
            if Direction.STRAIGHT in self.last_possible_directions and not opening_front:
                print("Didn't see front blockade when spotting the intersection; removing STRAIGHT from possibilities.")
                self.last_possible_directions &= ~Direction.STRAIGHT
            self.current_turn = self.guide.on_detected_crossing(self.last_possible_directions)
            self.turn_initiation_time = time.time_ns()
            print("On intersection; ready to take a turn.")
            print(f"Chose {self.current_turn} from {{{self.last_possible_directions}}}")
        # awaiting a dead end may be overridden if we encounter an actual intersection -> also updates the possible directions to take
        elif not self.waiting_until_intersection_in_direction or self.waiting_until_intersection_in_direction == Direction.STRAIGHT:
            # we are not waiting until we are on an intersection, check if we should be
            if Direction.RIGHT in possible_dirs:
                self.waiting_until_intersection_in_direction = Direction.RIGHT
            elif Direction.LEFT in possible_dirs:
                self.waiting_until_intersection_in_direction = Direction.LEFT
            elif Direction.STRAIGHT not in possible_dirs:  # handle dead ends the same way as intersections
                self.waiting_until_intersection_in_direction = Direction.STRAIGHT

            # store options the thymio has for taking a turn once it's on the intersection.
            # we could also query the guide here just so you know.
            if self.waiting_until_intersection_in_direction:
                print(f"Intersection in sight: {self.waiting_until_intersection_in_direction}")
                print(f"Possible directions as of now: {possible_dirs}")
                self.last_possible_directions = possible_dirs
        else:
            # we are still waiting to get to the middle of the intersection but not there yet, so just keep on moving.
            print(f"Moving to the center of the intersection: {self.waiting_until_intersection_in_direction}")

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
