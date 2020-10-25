# maestro

## Overview

maestro allows you to write animations for LED strips (e.g. WS2812B) in Python and stream them to the strip over UDP. All controlled by MQTT.

The UDP protocol used is the "UDP Realtime DRGB" protocol described [here](https://github.com/Aircoookie/WLED/wiki/UDP-Realtime-Control). There are a number of ways to get your LED strip to support this protocol, see [Aircoookie/WLED](https://github.com/Aircoookie/WLED) or [ESPHome](https://esphome.io/) (which is what I use).

## Installation

The reccomended installation method is using Docker:
```bash
git clone https://github.com/Dullage/maestro.git

cd maestro

docker build -t dullage/maestro:latest .

docker run \
  -d \
  -v /path/to/config.yaml:/app/config.yaml \
  --restart unless-stopped \
  dullage/maestro:latest
```

## Example Config
"config.yaml" file to be placed in working directory. If using docker this file can be placed anywhere and mounted as a volume, see example `docker run` command above.

```yaml
mqtt:                           # Required.
  host: 192.168.0.2             # Required.
  port: 1234                    # Optional. Defaults to 1883.
  base_topic: my_maestro        # Optional. Defaults to "maestro".
  client_id: my_maestro_client  # Optional. Defaults to "maestro".

lights:                         # Required.
  my_light_one:                 # At least one required.
    host: 192.168.0.3           # Required.
    port: 12345                 # Optional. Defaults to 21324.
    num_leds: 100               # Required.
    animation_fps: 40           # Optional. Defaults to 30.
```

## MQTT API

### Start an animation:
Target Topic: `<base_topic>/<light_name>/animation/start`

Example Payload:
```json
{
  "animation": "bouncing_ball",
  "config": {
    "bounciness": 0.9
  }
}
```
See the bundled animations in the `animations` directory for details about what animations are available and the relevant config options.

### Get notified when an animation has finished:
*Note: Many of the bundled animations are continuous loops and so will never finish.*

Source Topic: `<base_topic>/<light_name>/animation/finished`

Payload: *The payload of the message that started the animation.*

### Stop an animation:
Target Topic: `<base_topic>/<light_name>/animation/stop`

### Turn all LEDs to white:
Target Topic: `<base_topic>/<light_name>/on`

### Turn all LEDs off:
Target Topic: `<base_topic>/<light_name>/off`

## Writing Animations

This is the interface for an animation class (see animations/animation_interface.py):
```python
class AnimationInterface:
    def __init__(self, light: Light, config: typing.Dict):
        pass

    def set_next_frame(self):
        return True

    @property
    def name(self):
        return self.__class__.__name__
```

To create a new animation:

1. Add a new .py file to the animations directory e.g. `new_animation.py`.
2. In the new file, create a class for your animation and inherit from the interface e.g. `class NewAnimation(AnimationInterface):`.
3. Within your class, implement the `__init__` and `set_next_frame` methods described in the interface. See the bundled animations for examples.
4. In `animations/__init__.py`, import your animation and add it to the `animations` list.

## Notes

The bundled `fire` animation isn't quite working yet. This was ported from an animation written in C++ but the output doesn't match. Needs more work.
