import typing

from marshmallow import Schema, fields, post_load, validate

from light import Light

from .animation_interface import AnimationInterface
from .bouncing_ball import BouncingBall


class BouncingBallsConfig:
    def __init__(self, balls):
        self.balls = balls


class BouncingBallsConfigSchema(Schema):
    balls = fields.List(
        fields.Dict(),
        validate=validate.Length(min=1),
        missing=[
            {"bounciness": 0.6, "trail_length": 3, "colour": [255, 179, 186]},
            {"bounciness": 0.75, "trail_length": 3, "colour": [186, 255, 201]},
            {"bounciness": 0.9, "trail_length": 3, "colour": [186, 225, 255]},
        ],
    )

    @post_load
    def make_config(self, data, **kwargs):
        return BouncingBallsConfig(**data)


class BouncingBalls(AnimationInterface):
    def __init__(self, light: Light, config: typing.Dict):
        self.light = light
        config_schema = BouncingBallsConfigSchema()
        self.config = config_schema.load(config)

        self.balls = []
        for ball_config in self.config.balls:
            self.balls.append(
                BouncingBall(self.light, ball_config, clear_light=False)
            )

    def set_next_frame(self):
        self.light.clear_leds()
        for ball in self.balls:
            ball.set_next_frame()
        return False
