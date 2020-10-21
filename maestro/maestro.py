from json import JSONDecodeError

import paho.mqtt.client as mqtt
import yaml
import animations
from light import Light
from logger import log
from marshmallow import Schema, ValidationError, fields, validate


class ConfigSchemaMQTT(Schema):
    """Schema for the MQTT section of the YAML config file."""

    host = fields.String(required=True)
    port = fields.Int(validate=validate.Range(min=0, max=65535), missing=1883)
    base_topic = fields.String(missing="maestro")
    client_id = fields.String(missing="maestro")


class ConfigSchemaLight(Schema):
    """Schema for the light section of the YAML config file."""

    host = fields.String(required=True)
    port = fields.Int(validate=validate.Range(min=0, max=65535), missing=21324)
    num_leds = fields.Int(validate=validate.Range(min=1), required=True)
    animation_fps = fields.Int(missing=30)


class ConfigSchema(Schema):
    """Main schema for the YAML config file."""

    mqtt = fields.Nested(ConfigSchemaMQTT)
    lights = fields.Dict(
        keys=fields.String(),
        values=fields.Nested(ConfigSchemaLight),
        validate=validate.Length(min=1),
    )


class AnimationStartSchema(Schema):
    """Schema for the JSON MQTT payload to start an animation."""

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
        # Load Config
        self.config = self.load_config()

        # Initialise Lights
        self.lights = {}
        for name, config in self.config["lights"].items():
            host = config["host"]
            port = config["port"]
            num_leds = config["num_leds"]
            animation_fps = config["animation_fps"]

            self.lights[name] = Light(host, port, num_leds, animation_fps)

            log.info(
                f"Initialised light '{name}' ({num_leds} LEDs at {host}:{port})"  # noqa
            )

        # Create MQTT Client
        self.mqtt_client = mqtt.Client(self.config["mqtt"]["client_id"])
        self.mqtt_client.on_connect = self.mqtt_on_connect
        self.mqtt_client.on_message = self.mqtt_on_message

    def load_config(self):
        """Load and validate YAML config file."""
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
        schema = ConfigSchema()
        return schema.load(config)

    def run(self):
        """Connect to the MQTT server and loop forever."""
        self.mqtt_client.connect(
            self.config["mqtt"]["host"], self.config["mqtt"]["port"]
        )
        self.mqtt_client.loop_forever()

    def get_topics_for_light(self, light_name):
        """Return a list of topics to subscribe to for a particular light
        name.
        """
        base_topic_for_light = "/".join(
            [self.config["mqtt"]["base_topic"], light_name]
        )

        topics = [
            "/".join([base_topic_for_light, self.ON_INSTRUCTION]),
            "/".join([base_topic_for_light, self.OFF_INSTRUCTION]),
        ]

        for sub_instruction in [self.ANIMATION_START, self.ANIMATION_STOP]:
            topics.append(
                "/".join(
                    [
                        base_topic_for_light,
                        self.ANIMATION_INSTRUCTION,
                        sub_instruction,
                    ]
                )
            )
        return topics

    def mqtt_on_connect(self, client, userdata, flags, rc):
        """Subscribe to relevant topics upon connection to MQTT server."""
        for light_name in self.lights.keys():
            for topic in self.get_topics_for_light(light_name):
                log.info(f"Subscribed to '{topic}'")
                client.subscribe(topic)

    def animation_finished_callback(self, data):
        """Publish an MQTT message signalling that an animation has
        finished.
        """
        self.mqtt_client.publish(
            "/".join(
                [
                    self.config["mqtt"]["base_topic"],
                    data["light_name"],
                    self.ANIMATION_INSTRUCTION,
                    "finished",
                ]
            ),
            payload=data,
        )

    def mqtt_on_message(self, client, userdata, msg):
        """Parse MQTT messages and perform the specified action."""
        topic = msg.topic.split("/")
        light_name, instruction = topic[1], topic[2]
        light = self.lights[light_name]

        # Instructions
        if instruction == self.ON_INSTRUCTION:
            log.info(f"Turning on '{light_name}'")
            light.on()

        elif instruction == self.OFF_INSTRUCTION:
            log.info(f"Turning off '{light_name}'")
            light.off()

        elif instruction == self.ANIMATION_INSTRUCTION:
            anim_instruction = topic[3]  # TODO: Check behaviour if blank
            payload = msg.payload.decode("utf-8")

            # Start
            if anim_instruction == self.ANIMATION_START:
                try:
                    validated_payload = self.animation_start_schema.loads(
                        payload
                    )
                except ValidationError as e:
                    log.error(e.messages)
                    return
                except JSONDecodeError as e:
                    log.error(e)
                    return

                try:
                    Animation = animations.get(validated_payload["animation"])
                except ValueError as e:
                    log.error(e)
                    return

                animation = Animation(light, validated_payload["config"])
                log.info(
                    f"Starting animation '{animation.name}' on '{light_name}'"  # noqa
                )
                light.start_animation(
                    animation,
                    callback=self.animation_finished_callback,
                    callback_data=payload,
                )

            # Stop
            elif anim_instruction == self.ANIMATION_STOP:
                log.info(f"Stopping animation on '{light_name}'")
                light.stop_animation()


if __name__ == "__main__":
    maestro = Maestro()
    maestro.run()
