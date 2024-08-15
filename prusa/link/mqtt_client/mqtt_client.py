import logging
import configparser             #   for reading and parsing config file
import paho.mqtt.client as mqtt #   paho for mqtt client publishing data
from constants import *

MQTT_CLIENT_CONFIG = "config_mqtt_client.ini"

log = logging.getLogger(__name__)


def on_message(client, userdata, message):
    log.debug(f"received message: {message.payload.decode('utf-8')}")


def setup_mqtt_clients(config_filename: str = MQTT_CLIENT_CONFIG):
    # read PrusaLink config file
    config_mqtt = configparser.ConfigParser()
    config_mqtt.read(config_filename)
    # load printers from config
    mqtt_clients = {}
    for broker_name in config_mqtt.sections():
        section = config_mqtt[broker_name]

        # if missing host, assume MQTT Broker is running locally
        try:
            host = section["host"]
        except KeyError:
            log.info(f"[{broker_name}]No host: assume PrusaLink is running on localhost")
            host = "localhost"

        # if missing port, assume MQTT Broker is running on port 1883.
        try:
            port = int(section["port"])
        except KeyError:
            log.info(f"[{broker_name}]No port: assume MQTT Broker is running on port 1883")
            port = 1883

        # if missing uuid, @TODO:
        try:
            uuid = section["uuid"]
        except KeyError:
            log.info(f"[{broker_name}]No uuid: attempting to fetch uuid from device")
            uuid = "uuid"

        # if missing client_name, @TODO:
        try:
            mqtt_client_name = section["client_name"]
        except KeyError:
            log.info(f"[{broker_name}]No client_name: assume MQTT Broker is with client name prusa2mqtt")
            mqtt_client_name = "prusa2mqtt"

        mqtt_client = mqtt.Client(mqtt_client_name)  # default is MQTT v3.1.1, tcp,
        mqtt_client.on_message = on_message

        # if missing username and password
        try:
            mqtt_username = section["username"]
            mqtt_password = section["password"]
            mqtt_client.username_pw_set(mqtt_username, mqtt_password)
        except Exception as err:
            log.info(f"MQTT[{broker_name}] missing username/password: assume MQTT Broker does not require credentials")
            continue

        # @TODO: currently assume to be http, later should consider with SSL or TLS
        try:
            mqtt_client.connect(host, port)
        except Exception as err:
            log.error(f"MQTT[{broker_name}] Connection Error: {err}")
            continue

        # mqtt_client.subscribe(f'{args.topic}/gcode', 0)   # currently not implemented two-way communication yet; put in on_connect

        # record the mqtt client
        mqtt_clients[broker_name] = {}
        mqtt_clients[broker_name]["client"] = mqtt_client
        mqtt_clients[broker_name]["uuid"] = uuid
    return mqtt_clients