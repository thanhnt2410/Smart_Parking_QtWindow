import paho.mqtt.client as mqtt
import json
# broke = "192.168.1.94"
class MQTTHandler:
    def __init__(self,broke, port, topic):
        self.broker = broke
        self.port = port
        self.topic = topic
        self.client = mqtt.Client()

        try:
            # Kết nối đến MQTT Broker
            self.client.connect(self.broker, self.port, 60)
            print(f"Connected to MQTT Broker at {self.broker}:{self.port}")
        except Exception as e:
            print(f"Failed to connect to MQTT Broker: {e}")

    def publish(self, payload):
        """
        Đẩy dữ liệu lên MQTT.
        :param payload: Dữ liệu cần gửi (dict hoặc str).
        """
        if isinstance(payload, dict):
            payload = json.dumps(payload)  # Chuyển đổi sang JSON nếu là dict
        try:
            self.client.publish(self.topic, payload)
            print(f"Published to {self.topic}: {payload}")
        except Exception as e:
            print(f"Failed to publish: {e}")
