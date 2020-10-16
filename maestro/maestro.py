from json import JSONDecodeError

import paho.mqtt.client as mqtt
import yaml
from marshmallow import Schema, ValidationError, fields

from animations import animations
from light import Light
from logger import log


class AnimationStartSchema(Schema):
    animation = fields.Str(required=True)
    config = fields.Dict(missing={})


class Maestro:
    ON_INSTRUCTION = "on"
    OFF_INSTRUCTION = "off"
    ANIMATION_INSTRUCTION = "animation"
    ANIMATION_START = "start"
    ANIMATION_STOP = "stop"
    animation_start_schema = AnimationStartSchema()

    def __init__(self):
        self._config = self._load_config()

        self._lights = {}
        for name, config in self._config["lights"].items():
            host = config["host"]
            port = config["port"]
            num_leds = config["num_leds"]
            animation_fps = config["animation_fps"]

            self._lights[name] = Light(host, port, num_leds, animation_fps)

            log.info(
                f"Loaded light '{name}' ({num_leds} LEDs at {host}:{port})"
            )

        for animation_name in animations.keys():
            log.info(f"Loaded animation '{animation_name}'")

        self._mqtt_client = None

    def _load_config(self):
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)

    def run(self):
        self._mqtt_client = mqtt.Client(self._config["mqtt"]["client_id"])
        self._mqtt_client.on_connect = self._mqtt_on_connect
        self._mqtt_client.on_message = self._mqtt_on_message
        self._mqtt_client.connect(
            self._config["mqtt"]["host"], self._config["mqtt"]["port"]
        )
        self._mqtt_client.loop_forever()

    def _topics_for_light_name(self, light_name):
        base_topic_for_light = "/".join(
            [self._config["mqtt"]["base_topic"], light_name]
        )
        topics = []

        topics.append("/".join([base_topic_for_light, self.ON_INSTRUCTION]))
        topics.append("/".join([base_topic_for_light, self.OFF_INSTRUCTION]))
        topics.append(
            "/".join(
                [
                    base_topic_for_light,
                    self.ANIMATION_INSTRUCTION,
                    self.ANIMATION_START,
                ]
            )
        )
        topics.append(
            "/".join(
                [
                    base_topic_for_light,
                    self.ANIMATION_INSTRUCTION,
                    self.ANIMATION_STOP,
                ]
            )
        )
        return topics

    def _mqtt_on_connect(self, client, userdata, flags, rc):
        for light_name in self._lights.keys():
            for topic in self._topics_for_light_name(light_name):
                log.info(f"Subscribed to '{topic}'")
                client.subscribe(topic)

    def _animation_finished_callback(self, data):
        self._mqtt_client.publish(
            "/".join(
                [
                    self._config["mqtt"]["base_topic"],
                    self.ANIMATION_INSTRUCTION,
                    "finished",
                ]
            ),
            payload=data["animation_name"],
        )

    def _mqtt_on_message(self, client, userdata, msg):
        topic = msg.topic.split("/")
        light_name, instruction = topic[1], topic[2]
        light = self._lights[light_name]

        # Instructions
        if instruction == self.ON_INSTRUCTION:
            log.info(f"Turning on '{light_name}'")
            light.on()

        elif instruction == self.OFF_INSTRUCTION:
            log.info(f"Turning off '{light_name}'")
            light.off()

        elif instruction == self.ANIMATION_INSTRUCTION:
            anim_instruction = topic[3]  # TODO: Check behaviour if blank

            # Start
            if anim_instruction == "start":
                try:
                    validated_payload = self.animation_start_schema.loads(
                        msg.payload.decode("utf-8")
                    )
                except ValidationError as e:
                    print(e.messages)  # TODO
                    return
                except JSONDecodeError as e:
                    print(e)  # TODO
                    return

                animation_name = validated_payload["animation"]
                config = validated_payload["config"]

                try:
                    animation = animations[animation_name](light, config)
                    log.info(
                        f"Starting animation '{animation_name}' on '{light_name}'"  # noqa
                    )
                    light.start_animation(
                        animation,
                        callback=self._animation_finished_callback,
                        callback_data={"animation_name": animation_name},
                    )
                except KeyError:
                    log.error(f"Unknown animation '{animation_name}'")
                    return

            # Stop
            elif anim_instruction == "stop":
                log.info(f"Stopping animation on '{light_name}'")
                light.stop_animation()


if __name__ == "__main__":
    maestro = Maestro()
    maestro.run()
