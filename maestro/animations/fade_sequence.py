import typing

from light import Light
from marshmallow import Schema, fields, post_load, validate

from .animation_interface import AnimationInterface


class FadeSequenceConfig:
    def __init__(self, sequence, target_rgb, speed, clear_first):
        self.sequence = sequence
        self.target_rgb = target_rgb
        self.speed = speed
        self.clear_first = clear_first


class FadeSequenceConfigSchema(Schema):
    sequence = fields.List(
        fields.Int(validate=validate.Range(min=0)),
        validate=validate.Length(min=1),
        required=True,
    )
    target_rgb = fields.List(
        fields.Int(validate=validate.Range(min=0, max=255)),
        validate=validate.Length(equal=3),
        missing=[255, 255, 255],
    )
    speed = fields.Int(validate=validate.Range(min=1), missing=20)
    clear_first = fields.Boolean(missing=True)

    @post_load
    def make_config(self, data, **kwargs):
        return FadeSequenceConfig(**data)


class FadeSequence(AnimationInterface):
    def __init__(self, light: Light, config: typing.Dict):
        self.light = light
        config_schema = FadeSequenceConfigSchema()
        self.config = config_schema.load(config)

        # Drop any indexes out of range
        self.config.sequence = [
            idx for idx in self.config.sequence if idx <= light.max_index
        ]

        self._step = 0
        self._cleared = False

    def set_next_frame(self):
        if self._cleared is False and self.config.clear_first is True:
            self.light.clear_leds()
            self._cleared = True

        led_idx = self.config.sequence[self._step]
        cur_rgb = self.light._state[led_idx].copy()
        for col_idx, col in enumerate(cur_rgb):
            if col > self.config.target_rgb[col_idx]:
                cur_rgb[col_idx] = max(
                    [col - self.config.speed, self.config.target_rgb[col_idx]]
                )
            elif col < self.config.target_rgb[col_idx]:
                cur_rgb[col_idx] = min(
                    [col + self.config.speed, self.config.target_rgb[col_idx]]
                )
        self.light.set_led(led_idx, cur_rgb)

        if cur_rgb == self.config.target_rgb:
            self._step += 1
            if self._step > len(self.config.sequence) - 1:
                return True

        return False
