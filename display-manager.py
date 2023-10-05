import time
import paho.mqtt.client as mqtt

MQTT_BROKER_HOST = "172.17.170.119"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "sine_wave_data"

client = mqtt.Client()
"""
Function "on_connect" creates a connection between MQTT_BROKER and the client application.
"""
def on_connect(clinet, userdata, dlags, rc):
    if rc == 0:
        print(f"Connected to MQTT Broker at: {MQTT_BROKER_HOST}")
    else:
        print("Connection to MQTT Broker failed")

"""
Function "on_message" is a callback function that reads messages once the subscribed topic publishes a new message.
"""
def on_message(client, userdata, message):
    print("Message received: ", str(message.payload.decode("utf-8")))
    print(f"Message topic: {message.topic}")


"""
Main function does the following:
- creates a connection to the MQTT_BROKER,
- subscribes to the desired topic
- sets the callback function "on_message" for when messages are received
Currently the function ends the loop prematurely. This is purely for debugging purposes.
"""
if __name__=="__main__":
    client.on_connect = on_connect
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
    client.on_message=on_message
    client.subscribe(MQTT_TOPIC)
    client.loop_start()
    time.sleep(30)
    client.loop_stop()