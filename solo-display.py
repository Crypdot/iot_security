import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt


valuesList = []
valuesSize = 50
load_dotenv()

BOX_ID = os.getenv("BOX_ID")
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT"))

def onMessage(client, userdata, message):
    value = int(message.payload)
    valuesList.append(value)
    if len(valuesList) > valuesSize:
        valuesList.pop(0)

def updateGraph():
    plt.clf()
    plt.plot(range(len(valuesList)), valuesList, marker="o")
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.title("Display")
    plt.grid()
    plt.draw()
    plt.pause(0.1)    

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_message = onMessage

    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)

    MQTT_TOPIC = BOX_ID + "/motor/speed/out/"

    client.subscribe(MQTT_TOPIC)

    client.loop_start()
    plt.ion()
    plt.figure()
    updateGraph()
    try:
        while True:
            updateGraph()
    except KeyboardInterrupt:
        client.disconnect()
        client.loop_stop()