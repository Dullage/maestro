import typing

from light import Light


class AnimationInterface:
    def __init__(self, light: Light, config: typing.Dict):
        pass

    def set_next_frame(self):
        return True

    @property
    def name(self):
        return self.__class__.__name__
