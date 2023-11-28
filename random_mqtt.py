import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from random import randint
import time

"""
Used to publish random data. Mainly to demo 'displayManager.py' functionality. 
"""

load_dotenv()

BOX_ID = os.getenv("BOX_ID")
LOOP_INTERVAL = float(os.getenv("MOTOR_LOOP_INTERVAL"))		# seconds

MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT"))
TOPIC = f"{BOX_ID}/sensor/flow/out/"

client = mqtt.Client()

def onConnect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT Broker at: {MQTT_BROKER_HOST}")
    else:
        print("Connection to MQTT Broker failed")

def controlLoop():
    try:
        while True:
            publishingData = randint(1, 40)
            print(publishingData)

            client.publish(TOPIC, str(publishingData))

			# The value is sent once every interval, sleep in between
            time.sleep(LOOP_INTERVAL)
    except KeyboardInterrupt:
        client.disconnect()
    except Exception as e:
        print("An unexpected error occurred: " + str(e))

if __name__ == "__main__":
    client.on_connect = onConnect
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 0)

    client.loop_start()
    controlLoop()
