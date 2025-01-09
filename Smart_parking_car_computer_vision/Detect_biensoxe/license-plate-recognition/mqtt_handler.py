import paho.mqtt.client as mqtt
import yaml
from PyQt6.QtCore import QThread, pyqtSignal

class MQTTHandler(QThread):
    def __init__(self, config_file="config.yaml"):
        self.load_config(config_file)
        self.client = mqtt.Client()
        self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.tls_set()

    def load_config(self, config_file):
        with open(config_file, "r") as file:
            config = yaml.safe_load(file)
        self.broker = config.get("mqtt_host")
        self.port = config.get("mqtt_port")
        self.username = config.get("mqtt_username")
        self.password = config.get("mqtt_password")
        self.sub_topic = config.get("mqtt_sub_topic")
        self.sub_topic_rfid_in = config.get("mqtt_rfid_send_in")
        self.sub_topic_rfid_out = config.get("mqtt_rfid_send_out")
        self.mqtt_open_door_in = config.get("mqtt_open_door_in")
        self.mqtt_open_door_out = config.get("mqtt_open_door_out")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
            client.subscribe(self.sub_topic)
            client.subscribe(self.sub_topic_rfid_in)
            client.subscribe(self.sub_topic_rfid_out)
            client.subscribe(self.sub_topic_rfid_out)
        else:
            print(f"Failed to connect, return code {rc}")

    def on_message(self, client, userdata, msg):
        print(f"Received message from {msg.topic}: {msg.payload.decode()}")

    def start(self):
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_forever()

if __name__ == "__main__":
    mqtt_handler = MQTTHandler()
    mqtt_handler.start()

