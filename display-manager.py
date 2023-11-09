import json
import time
import paho.mqtt.client as mqtt

with open('config.json', 'r') as configFile:
    config = json.load(configFile)

MQTT_BROKER_HOST = config["mqttBrokerHost"]
MQTT_BROKER_PORT = config["mqttBrokerPort"]
MQTT_TOPIC = config["mqttTopicSineWave"]

client = mqtt.Client()
"""
Function "on_connect" creates a connection between MQTT_BROKER and the client application.
"""
def onConnect(client, userdata, dlags, rc):
    if rc == 0:
        print(f"Connected to MQTT Broker at: {MQTT_BROKER_HOST}")
    else:
        print("Connection to MQTT Broker failed")

"""
Function "on_message" is a callback function that reads messages once the subscribed topic publishes a new message.
"""
def onMessage(client, userdata, message):
    print("Message received: ", str(message.payload.decode("utf-8")))
    print(f"Message topic: {message.topic}")

"""
Main function does the following:
- creates a connection to the MQTT_BROKER,
- subscribes to the desired topic
- sets the callback function "on_message" for when messages are received
Currently the function ends the loop prematurely. This is purely for debugging purposes.
"""
if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = onConnect
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
    client.on_message = onMessage
    client.subscribe(MQTT_TOPIC)
    client.loop_start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Interrupted by keyboard press. Exiting...")
        client.loop_stop()
        client.disconnect()