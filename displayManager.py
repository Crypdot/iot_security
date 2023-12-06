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
MQTT_TOPIC_SENSOR_OUTFLOW_OUT = os.getenv("MQTT_TOPIC_SENSOR_OUTFLOW_OUT")
MQTT_TOPIC_SENSOR_INFLOW_OUT = os.getenv("MQTT_TOPIC_SENSOR_INFLOW_OUT")
MQTT_TOPIC_SENSOR_DP_OUT = os.getenv("MQTT_TOPIC_SENSOR_DP_OUT")
MQTT_TOPIC_SENSOR_TEMP_OUT = os.getenv("MQTT_TOPIC_SENSOR_TEMP_OUT")

TEMP_TOPIC = f"{BOX_ID}/+{MQTT_TOPIC_SENSOR_TEMP_OUT}" # Topic for the speed graph
PRESSURE_TOPIC = f"{BOX_ID}/+{MQTT_TOPIC_SENSOR_DP_OUT}"
OUTFLOW_TOPIC = f"{BOX_ID}/+{MQTT_TOPIC_SENSOR_OUTFLOW_OUT}"
INFLOW_TOPIC = f"{BOX_ID}/+{MQTT_TOPIC_SENSOR_INFLOW_OUT}" # Topic for flow numbers

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
    temperatureValue = float(message.payload)

def flowMessage(client, userdata, message):
    fields = message.topic.split("/")[0:]
    if fields[2] == "inflowRate":
        appendToList(flowInList, message.payload)
    elif fields[2] == "outflowRate":
        appendToList(flowOutList, message.payload)
    else:
        print(f"Something went wrong.")
#    appendToList(flowInList, message.payload)
#    appendToList(flowOutList, message.payload)

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
    ax1.set_ylim(-160, 160)
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
    ax2.set_ylim(-100, 100) # Min and max values shown on the graph
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
    client.message_callback_add(INFLOW_TOPIC, flowMessage)
    client.message_callback_add(OUTFLOW_TOPIC, flowMessage)
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