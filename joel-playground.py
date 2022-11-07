import time

from thymio_python.thymiodirect import ThymioObserver, SingleSerialThymioRunner
from thymio_python.thymiodirect.thymio_constants import PROXIMITY_FRONT_BACK, MOTOR_LEFT, MOTOR_RIGHT, BUTTON_CENTER, LEDS_TOP


class HandAvoider(ThymioObserver):
    def __init__(self):
        super().__init__()
        self.prox_prev = None

    def _update(self):
        prox = (self.th[PROXIMITY_FRONT_BACK][5] - self.th[PROXIMITY_FRONT_BACK][2]) // 10

        if prox != self.prox_prev:
            self.th[MOTOR_LEFT] = prox
            self.th[MOTOR_RIGHT] = prox
            print(prox)
            if prox > 5:
                self.th[LEDS_TOP] = [0, 32, 0]
            elif prox < -5:
                self.th[LEDS_TOP] = [32, 32, 0]
            elif abs(prox) < 3:
                self.th[LEDS_TOP] = [0, 0, 32]
            self.prox_prev = prox
        if self.th[BUTTON_CENTER]:
            print("Center button pressed")
            self.stop()


if __name__ == "__main__":
    # absolute minimum
    SingleSerialThymioRunner({BUTTON_CENTER, PROXIMITY_FRONT_BACK, MOTOR_LEFT, MOTOR_RIGHT}, HandAvoider(), 0.1).run()

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
