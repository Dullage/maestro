import random
import typing

from light import Light
from marshmallow import Schema, fields, post_load, validate

from .animation_interface import AnimationInterface


class SparkleConfig:
    def __init__(self, rgb):
        self.rgb = rgb


class SparkleConfigSchema(Schema):
    rgb = fields.List(
        fields.Int(validate=validate.Range(min=0, max=255)),
        validate=validate.Length(equal=3),
        missing=[255, 255, 255],
    )

    @post_load
    def make_config(self, data, **kwargs):
        return SparkleConfig(**data)


class Sparkle(AnimationInterface):
    def __init__(self, light: Light, config: typing.Dict):
        self.light = light
        config_schema = SparkleConfigSchema()
        self.config = config_schema.load(config)

    def set_next_frame(self):
        self.light.clear_leds()
        rand_led_i = random.randint(0, self.light.max_index)
        self.light.set_led(rand_led_i, self.config.rgb)
        return False
