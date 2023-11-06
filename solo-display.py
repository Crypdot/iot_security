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

plt.rcParams['toolbar'] = 'None'

# Motor's speed values are stored in this list
speedList = []
speedSize = 40 # The "size" of the list

# Pressure's values
pressureList = []
pressureSize = 40

# Flow sensor values
flowInValue = 0
flowOutValue = 0

"""
Adds the speed topic's value to a list. The last value is removed once a threshold is reached. 
"""
def speedMessage(client, userdata, message):
    value = int(message.payload)
    speedList.append(value)
    if len(speedList) > speedSize:
        speedList.pop(0)

def flowMessage(client, userdata, message):
    global flowInValue
    flowInValue = int(message.payload)

def pressureMessage(client, userdata, message):
    value = int(message.payload)
    pressureList.append(value)
    if len(pressureList) > pressureSize:
        pressureList.pop(0)

"""
Creates a matplotlib animation of line graph, using the list of values. Animation function uses one argument, 
"""
def animateGraph(i):
    plt.cla() # Clear the figure
    plt.plot(range(len(speedList)), speedList, marker="") # Place new data on figure
    
    # Labeling the figure
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.title(BOX_ID)
    plt.xticks([]) # Remove X-axis values

    # Set the min-max values that will always be shown
    plt.ylim(1250, 2049)
    plt.xlim(0, speedSize + 10)

def animateGraphs(i):
    ax1.clear()
    ax1.plot(range(len(speedList)), speedList, marker="")

    ax1.set_ylim(1250, 2049)
    ax1.set_xlim(0, pressureSize + (pressureSize / 4))
    ax1.set_xlabel("Time")
    ax1.set_ylabel("Value")
    ax1.set_xticks([])
    ax1.set_title("Speed", loc="left")

    ax2.clear()
    ax2.plot(range(len(pressureList)), pressureList, marker="")

    ax2.set_ylim(0, 9999)
    ax2.set_xlim(0, pressureSize + (pressureSize / 4))
    ax2.set_xlabel("Time")
    ax2.set_ylabel("Value")
    ax2.set_xticks([])
    ax2.set_title("Pressure", loc="left")

    ax3.clear()
    ax3.text(0, 1, f"Flow in: {flowInValue}", fontsize=24)
    ax3.text(0, 0.5, f"Flow out: {flowInValue}", fontsize=24)
    ax3.set_xticks([])
    ax3.set_yticks([])



"""
When figure is closed, gracefully disconnects MQTT
"""
def onClose(event):
    plt.close()
    client.disconnect()

if __name__ == "__main__":
    global running
    client = mqtt.Client()

    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)

    # Subscribe to the box's topic and start receiving data
    MOTOR_TOPIC = BOX_ID + "/motor/speed/out/"
    
    client.subscribe([(f"{BOX_ID}/+/+/+/", 1)])
    client.message_callback_add(MOTOR_TOPIC, speedMessage)
    client.message_callback_add(f"{BOX_ID}/+/flow/out/", flowMessage)
    client.message_callback_add(f"{BOX_ID}/+/pressure/out/", pressureMessage)

    client.loop_start()

    # Matplotlib initialization
    # fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
    fig = plt.figure()
    ax1 = fig.add_subplot(2, 1, 1)
    ax2 = fig.add_subplot(2, 2, 3)
    ax3 = fig.add_subplot(3, 2, 6, frameon=False)

    fig.canvas.mpl_connect('close_event', onClose)
    ani = FuncAnimation(fig, animateGraphs, interval=50, frames=20)
    fig.suptitle(BOX_ID, fontsize=24)
    try:
        plt.tight_layout()
        plt.show()
    except KeyboardInterrupt:
        client.disconnect()