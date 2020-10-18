import typing

from marshmallow import Schema, fields, post_load, validate

from light import Light

from .animation_interface import AnimationInterface


class BouncingBallConfig:
    def __init__(
        self,
        bounciness,
        terminal_velocity,
        gravity,
        colour,
        trail_length,
        max_height,
        starting_height,
        invert,
    ):
        self.bounciness = bounciness
        self.terminal_velocity = terminal_velocity
        self.gravity = gravity
        self.colour = colour
        self.trail_length = trail_length
        self.max_height = max_height
        self.starting_height = starting_height
        self.invert = invert


class BouncingBallConfigSchema(Schema):
    bounciness = fields.Float(
        validate=validate.Range(min=0, max=1), missing=0.8
    )
    terminal_velocity = fields.Int(validate=validate.Range(min=0), missing=3)
    gravity = fields.Float(validate=validate.Range(min=0), missing=0.05)
    colour = fields.List(
        fields.Int(validate=validate.Range(min=0, max=255)),
        validate=validate.Length(equal=3),
        missing=[255, 255, 255],
    )
    trail_length = fields.Int(validate=validate.Range(min=0), missing=3)
    max_height = fields.Int(validate=validate.Range(min=0), missing=None)
    starting_height = fields.Int(validate=validate.Range(min=0), missing=None)
    invert = fields.Bool(missing=False)

    @post_load
    def make_config(self, data, **kwargs):
        return BouncingBallConfig(**data)


class BouncingBall(AnimationInterface):
    def __init__(self, light: Light, config: typing.Dict, clear_light=True):
        self.light = light
        config_schema = BouncingBallConfigSchema()
        self.config = config_schema.load(config)
        self.clear_light = clear_light

        if (
            self.config.max_height is None
            or self.config.max_height > self.light.max_index
        ):
            self.config.max_height = self.light.max_index

        if (
            self.config.starting_height is None
            or self.config.starting_height > self.light.max_index
        ):
            self.config.starting_height = self.config.max_height

        self._falling = True
        self._cur_speed = 0
        self._cur_height = self.config.starting_height
        self._finished = False

    def adjust_acceleration(self):
        # Falling
        if self._falling is True:
            self._cur_speed = min(
                self.config.terminal_velocity,
                self._cur_speed + self.config.gravity,
            )
        # Going up
        else:
            self._cur_speed = max(0, self._cur_speed - self.config.gravity)
            if self._cur_speed == 0:
                self._falling = True
                if self._cur_height_round == 0:
                    self._finished = True

    def set_new_position(self):
        # Falling
        if self._falling is True:
            self._cur_height -= self._cur_speed
            if self._cur_height <= 0:
                self._cur_height = 0
                self._falling = False
                self._cur_speed = self._cur_speed * self.config.bounciness
        # Going up
        else:
            self._cur_height += self._cur_speed
            # TODO: Do I need a limit here?

    @property
    def _cur_height_round(self):
        return round(self._cur_height)

    @property
    def _led_idx(self):
        return (
            self._cur_height_round
            if self.config.invert is False
            else self.light.max_index - self._cur_height_round
        )

    def add_ball_to_light(self):
        if self.clear_light is True:
            self.light.clear_leds()

        self.light.set_led(self._led_idx, self.config.colour)

    def add_trail_to_light(self):
        # Calculate a speed adjusted trail length
        adj_trail_length = round(
            self.config.trail_length
            * (self._cur_speed / self.config.terminal_velocity)
        )

        if adj_trail_length > 0:
            cur_trail_led = self._led_idx
            distance_from_end = adj_trail_length + 1
            for trail_led in range(adj_trail_length):
                # Goto the next led in the trail
                if self.config.invert == self._falling:
                    cur_trail_led -= 1
                else:
                    cur_trail_led += 1
                distance_from_end -= 1

                # Calculate the brightness
                brightness = (1 / (adj_trail_length + 1)) * distance_from_end

                # Update the light state
                if (
                    cur_trail_led >= 0
                    and cur_trail_led <= self.light.max_index
                ):
                    self.light.set_led(
                        cur_trail_led, self.config.colour, brightness
                    )
            pass

    def set_next_frame(self):
        self.set_new_position()
        self.adjust_acceleration()
        self.add_ball_to_light()
        self.add_trail_to_light()
        return self._finished
