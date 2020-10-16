import typing

from light import Light


class AnimationInterface:
    def __init__(self, light: Light, config: typing.Dict):
        pass

    def set_next_frame(self):
        return True
