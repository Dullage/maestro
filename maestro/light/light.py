import math
import socket
import time
from threading import Thread


class Light:
    def __init__(
        self,
        ip_address,
        port,
        num_leds,
        animation_fps=30,
    ):
        self.ip_address = ip_address
        self.port = port
        self.num_leds = num_leds
        self.animation_fps = animation_fps

        self._animation_thread = None
        self._stop_animation = False
        self._server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self._state = []
        self.clear_leds()

    def update(self):
        protocol = 2  # DRGB
        timeout = 255  # Disabled
        message = bytes(
            [protocol, timeout] + [col for led in self._state for col in led]
        )
        self._server.sendto(message, (self.ip_address, self.port))

    def set_led(self, led_idx, rgb, brightness=1):
        self._state[led_idx] = self._col_at_bri(rgb, brightness)

    def set_leds(self, rgb, brightness=1):
        self._state = [
            self._col_at_bri(rgb, brightness) for led in range(self.num_leds)
        ]

    def on(self):
        self.stop_animation()
        self.set_leds([255, 255, 255])
        self.update()

    def clear_leds(self):
        self.set_leds([0, 0, 0])

    def off(self):
        self.stop_animation()
        self.clear_leds()
        self.update()

    @classmethod
    def _linspace(cls, start, stop, count):
        step = (stop - start) / float(count)
        return [round(start + i * step) for i in range(count)]

    def set_gradient(self, start_rgb, end_rgb):
        lin_r = self._linspace(start_rgb[0], end_rgb[0], self.num_leds)
        lin_g = self._linspace(start_rgb[1], end_rgb[1], self.num_leds)
        lin_b = self._linspace(start_rgb[2], end_rgb[2], self.num_leds)
        self._state = [
            [lin_r[i], lin_g[i], lin_b[i]] for i in range(self.num_leds)
        ]

    def set_percentage(self, percentage, on_rgb, off_rgb=[0, 0, 0]):
        num_on_leds = math.ceil((self.num_leds / 100) * percentage)
        num_off_leds = self.num_leds - num_on_leds
        self._state = [on_rgb for led in range(num_on_leds)] + [
            off_rgb for led in range(num_off_leds)
        ]

    def start_animation(self, animation, callback=None, callback_data=None):
        self.stop_animation()
        self._animation_thread = Thread(
            target=self._start_animation,
            args=(animation, callback, callback_data),
        )
        self._animation_thread.start()

    def _start_animation(self, animation, callback=None, callback_data=None):
        frame_duration = 1 / self.animation_fps
        while self._stop_animation is False:
            finished = animation.set_next_frame()
            self.update()
            if finished is True:
                break
            else:
                time.sleep(frame_duration)
        if self._stop_animation is False and callback is not None:
            callback(callback_data)
        self._stop_animation = False

    def stop_animation(self):
        if self._animation_thread is not None:
            self._stop_animation = True
            while self._animation_thread.is_alive():
                pass
            self._stop_animation = False
            self._animation_thread = None

    @classmethod
    def _col_at_bri(cls, rgb, brightness):
        return [
            round(rgb[0] * brightness),
            round(rgb[1] * brightness),
            round(rgb[2] * brightness),
        ]

    @property
    def max_index(self):
        return self.num_leds - 1
