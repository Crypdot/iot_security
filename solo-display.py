import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

load_dotenv()

# Parameters for the MQTT broker
BOX_ID = os.getenv("BOX_ID")
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT"))

# Motor's speed values are stored in this list
valuesList = []
valuesSize = 40 # The "size" of the list

"""
Function is called every time subscribed topic is received. 
Adds the subscribed topic's value to a list. The last value is removed once a threshold is reached. 
"""
def onMessage(client, userdata, message):
    value = int(message.payload)
    valuesList.append(value)
    if len(valuesList) > valuesSize:
        valuesList.pop(0)

"""
Creates a matplotlib animation of line graph, using the list of values. Animation function uses one argument, 
"""
def animateGraph(i):
    plt.cla() # Clear the figure
    plt.plot(range(len(valuesList)), valuesList, marker="") # Place new data on figure
    
    # Labeling the figure
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.title(BOX_ID)
    plt.xticks([]) # Remove X-axis values

    # Set the min-max values that will always be shown
    plt.ylim(1250, 2049)
    plt.xlim(0, valuesSize + 10)

"""
When figure is closed, gracefully disconnects MQTT
"""
def onClose(event):
    plt.close()
    client.disconnect()

if __name__ == "__main__":
    global running
    client = mqtt.Client()
    client.on_message = onMessage

    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)

    # Subscribe to the box's topic and start receiving data
    MQTT_TOPIC = BOX_ID + "/motor/speed/out/"
    client.subscribe(MQTT_TOPIC)
    client.loop_start()

    # Matplotlib initialization
    fig, ax = plt.subplots()
    fig.canvas.mpl_connect('close_event', onClose)
    ani = FuncAnimation(fig, animateGraph, interval=50, frames=20)
    try:
        plt.show()
    except KeyboardInterrupt:
        client.disconnect()