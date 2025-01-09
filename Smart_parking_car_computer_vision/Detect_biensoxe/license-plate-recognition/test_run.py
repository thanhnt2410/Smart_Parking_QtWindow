from test import MqttHandler

if __name__ == "__main__":
    mqtt_handler = MqttHandler(
        broker="052e06039773482e81b963e2a3b42fba.s1.eu.hivemq.cloud",
        port=8883,
        username="smartpark",
        password="Smartpark123",
        sub_topic="esp32/slots"
    )
    mqtt_handler.start()
