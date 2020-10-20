"""
Ported to Python from this source:

https://www.tweaking4all.com/hardware/arduino/adruino-led-strip-effects/#LEDStripEffectFire

Original comments and variable names maintained.
"""

import random
import typing

from light import Light
from marshmallow import Schema, fields, post_load, validate

from .animation_interface import AnimationInterface


class FireConfig:
    def __init__(self, cooling, sparking):
        self.cooling = cooling
        self.sparking = sparking


class FireConfigSchema(Schema):
    cooling = fields.Int(validate=validate.Range(min=1), missing=55)
    sparking = fields.Int(validate=validate.Range(min=1), missing=120)

    @post_load
    def make_config(self, data, **kwargs):
        return FireConfig(**data)


class Fire(AnimationInterface):
    def __init__(self, light: Light, config: typing.Dict):
        self.light = light
        config_schema = FireConfigSchema()
        self.config = config_schema.load(config)

    def _set_pixel_heat_colour(self, led, temperature, light):
        # Scale 'heat' down from 0-255 to 0-191
        t192 = round((temperature / 255) * 191)

        # calculate ramp up from
        heatramp = t192 & 63
        heatramp <<= 2  # scale up to 0..252

        # figure out which third of the spectrum we're in:
        if t192 > 128:  # hottest
            light.set_led(led, [255, 255, heatramp])
        elif t192 > 64:  # middle
            light.set_led(led, [255, heatramp, 0])
        else:  # coolest
            light.set_led(led, [heatramp, 0, 0])

    def set_next_frame(self):
        heat = [0 for led in range(self.light.num_leds)]

        # Step 1.  Cool down every cell a little
        for i in range(self.light.num_leds):
            cooldown = random.uniform(
                0, ((self.config.cooling * 10) / self.light.num_leds) + 2
            )

            if cooldown > heat[i]:
                heat[i] = 0
            else:
                heat[i] -= cooldown

        # Step 2.  Heat from each cell drifts 'up' and diffuses a little
        k = self.light.num_leds - 1
        while k >= 2:
            heat[k] = (heat[k - 1] + heat[k - 2] + heat[k - 2]) / 3
            k -= 1

        # Step 3.  Randomly ignite new 'sparks' near the bottom
        if random.randint(0, 255) < self.config.sparking:
            y = random.randint(0, 7)
            heat[y] += random.randint(160, 255)

        # Step 4.  Convert heat to LED colors
        for j in range(self.light.num_leds):
            self._set_pixel_heat_colour(j, heat[j], self.light)

        return False
