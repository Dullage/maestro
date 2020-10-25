from .bouncing_ball import BouncingBall
from .bouncing_balls import BouncingBalls
from .fade_sequence import FadeSequence
from .fire import Fire
from .police import Police
from .sparkle import Sparkle

animations = [
    BouncingBall,
    BouncingBalls,
    FadeSequence,
    Fire,
    Police,
    Sparkle,
]


def get(animation_name):
    """Return an animation class definition where the class name matches the
    declared value. Matches are case insensitive.

    Raises a ValueError if no match found.
    """
    for animation in animations:
        if animation.__name__.lower() == animation_name.lower():
            return animation
    raise ValueError(f"Unknown animation '{animation_name}'")
