"""
Animation Steps:
  1. Top      Blue    Up
  2. Top      Blue    Down
  3. Top      White   Up
  4. Top      White   Down
  5. Bottom   Blue    Up
  6. Bottom   Blue    Down
  7. Bottom   White   Up
  8. Bottom   White   Down
"""
import typing

from light import Light
from marshmallow import Schema, fields, post_load, validate

from .animation_interface import AnimationInterface


class PoliceConfig:
    def __init__(self, speed_multiplier):
        self.speed_multiplier = speed_multiplier


class PoliceConfigSchema(Schema):
    speed_multiplier = fields.Float(validate=validate.Range(min=0), missing=1)

    @post_load
    def make_config(self, data, **kwargs):
        return PoliceConfig(**data)


class Police(AnimationInterface):
    def __init__(self, light: Light, config: typing.Dict):
        self.light = light
        config_schema = PoliceConfigSchema()
        self.config = config_schema.load(config)

        self._col_bri = 1
        self._top_not_bottom = True
        self._blue_not_white = True
        self._bri_up_not_down = True
        self._frame_wait_count = 0

    def set_next_frame(self):
        # Flip the side at the end of steps 4 & 8
        if (
            self._col_bri == 0
            and self._blue_not_white is False
            and self._bri_up_not_down is False
        ):
            if self._frame_wait_count <= round(self.light.animation_fps / 10):
                self._frame_wait_count += 1
                return
            else:
                self._top_not_bottom = not self._top_not_bottom
                self._frame_wait_count = 0

        # Change brightness direction at edges
        if self._col_bri == 255:
            self._bri_up_not_down = False
        elif self._col_bri == 0:
            self._bri_up_not_down = True
            # Also change the colour at 0 brightness
            self._blue_not_white = not self._blue_not_white

        # Calculate the next colour brightness
        col_bri_step = round(
            (90 * self.config.speed_multiplier)
            * (30 / self.light.animation_fps)
        )
        if self._bri_up_not_down is True:
            self._col_bri += col_bri_step
        else:
            self._col_bri -= col_bri_step

        # Trim overflow
        if self._col_bri > 255:
            self._col_bri = 255
        elif self._col_bri < 0:
            self._col_bri = 0

        # Assemble the target colour
        target_col = (
            [0, 0, self._col_bri]
            if self._blue_not_white is True
            else [self._col_bri, self._col_bri, self._col_bri]
        )

        # Update the light state
        if self._top_not_bottom is True:
            self.light.set_percentage(50, [0, 0, 0], target_col)
        else:
            self.light.set_percentage(50, target_col)
