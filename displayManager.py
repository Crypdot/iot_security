import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import TextBox, Button

load_dotenv()

# Parameters for the MQTT broker
BOX_ID = os.getenv("BOX_ID")
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT"))

TEMP_TOPIC = f"{BOX_ID}/+/temp/out/" # Topic for the speed graph
PRESSURE_TOPIC = f"{BOX_ID}/+/pressure/out/" # Topic for the pressure graph
FLOW_TOPIC = f"{BOX_ID}/+/flow/out/" # Topic for flow numbers

plt.rcParams["toolbar"] = "None"

max_size = 40

# Pressure's values
pressureList = []

# Flow sensor values
flowInList = []
flowOutList = []

# Temperature
temperatureValue = None


def tempMessage(client, userdata, message):
    global temperatureValue
    temperatureValue = int(message.payload)

def flowMessage(client, userdata, message):
    appendToList(flowInList, message.payload)
    appendToList(flowOutList, (-1 * float(message.payload)))

def pressureMessage(client, userdata, message):
    appendToList(pressureList, message.payload)

"""
Adds a value to a list, discards values if over limit. 
Used by line graphs. 
"""
def appendToList(listToAdd: list, data):
    value = float(data)
    listToAdd.append(value)
    if len(listToAdd) > max_size:
        listToAdd.pop(0)

"""
Creates a matplotlib animation of line graphs and values. Animation function passes one argument. 
"""
def animateGraphs(i):
    # Flow i/o graphs
    # Clear and build the graphs
    ax1.clear()
    ax1.plot(range(len(flowInList)), flowInList, marker="", label="Flow in", color="blue")
    ax1.plot(range(len(flowOutList)), flowOutList, marker="", label="Flow out", color="red")
    
    # Graph configurations
    ax1.set_ylim(-40, 40)
    ax1.set_xlim(0, max_size + (max_size / 4))
    ax1.set_xlabel("Time")
    ax1.set_ylabel("Value")
    ax1.set_xticks([])
    ax1.set_title("Flow", loc="left")
    ax1.legend()

    # Pressure graph
    # Clear and build the graph
    ax2.clear()
    ax2.plot(range(len(pressureList)), pressureList, marker="")

    # Graph configurations
    ax2.set_ylim(-1, 1) # Min and max values shown on the graph
    ax2.set_xlim(0, max_size + (max_size / 4))
    ax2.set_xlabel("Time")
    ax2.set_ylabel("Value")
    ax2.set_xticks([])
    ax2.set_title("Pressure", loc="left")

    # Temperature number
    ax3.clear()
    ax3.text(0, 1, f"Temp: {temperatureValue}°C", fontsize=24)
    ax3.set_xticks([])
    ax3.set_yticks([])

def changeBox(val):
    global BOX_ID
    global pressureList
    global flowInList
    global flowOutList
    global temperatureValue
    pressureList = []
    flowInList = []
    flowOutList = []
    temperatureValue = 0

    client.unsubscribe(f"{BOX_ID}/+/+/+/")
    BOX_ID = val
    client.subscribe([(f"{BOX_ID}/+/+/+/", 1)])
    client.loop_start()


"""
When figure is closed, gracefully disconnects MQTT
"""
def onClose(event):
    plt.close()
    client.disconnect()

if __name__ == "__main__":
    global running
    client = mqtt.Client()

    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 0)

    # Subscribe to the box's topic and bind different topics to functions
    client.subscribe([(f"{BOX_ID}/+/+/+/", 1)])
    client.message_callback_add(TEMP_TOPIC, tempMessage)
    client.message_callback_add(FLOW_TOPIC, flowMessage)
    client.message_callback_add(PRESSURE_TOPIC, pressureMessage)

    client.loop_start()

    # Matplotlib initialization
    fig = plt.figure()
    ax1 = fig.add_subplot(2, 1, 1)
    ax2 = fig.add_subplot(2, 2, 3)
    ax3 = fig.add_subplot(3, 2, 6, frameon=False)

    graphBox = fig.add_axes([0.1, 0.025, 0.8, 0.05])
    textbox = TextBox(graphBox, "Box ID:", initial=BOX_ID)
    textbox.on_submit(changeBox)

    fig.canvas.mpl_connect('close_event', onClose)
    ani = FuncAnimation(fig, animateGraphs, interval=50, frames=20)
    fig.suptitle(BOX_ID, fontsize=24)
    try:
        plt.show()
    except KeyboardInterrupt:
        client.disconnect()