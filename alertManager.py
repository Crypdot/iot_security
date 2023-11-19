import sys
import time
import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv()

"""
Possible things to consider:
- Could implement an error code system so that we can pull from an enum.
    - For example, if we decide a temp-high alert should set the motor to a specific mode, we could have a variable 'overrideMode = 22', for example.
    - Query as to how useful that would be. Would avoid the repetition we currently have.
"""

# Parameters for the MQTT broker
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT"))
MQTT_TOPIC_MOTOR_COMMAND_IN = os.getenv("MQTT_TOPIC_MOTOR_CONFIG_IN")

# Process Messages
def onConnect(client, metadata, flags, rc):
    client.subscribe('system/alerts')
    print(f"Using MQTT broker at {MQTT_BROKER_HOST} at {str(MQTT_BROKER_PORT)}")

def onDisconnect(client, metadata, flags, rc):
	print("MQTT Disconnected :: Reconnecting")
	try:
		client.reconnect()
	except Exception as error:
		print(f"Something went wrong :: {error}")

def sendOverride(box: str, device: str, setMode: int):
    try:
        # Consider if we want to use our configuration channel for this. Should we have an override channel?
        client(publish(MQTT_TOPIC_MOTOR_COMMAND_IN, f"{setMode},1600,1600,1600,0,0"))
    except Exception as error:
        print(f"Something went wrong :: {error}")

def onMessage(client,userdata,message):
    # Initialize the override mode to 0 (Continuous)
    overrideMode: int = 0
    alert = message.payload.decode("UTF-8").split("/")[0:]
    alertBox = alert[1]
    alertDevice = alert[2]
    alertType = alert[3]
    
    if alertType == "TH":
        overrideMode = 99
        print(f"{alertDevice} :: TEMPERATURE HIGH")
    elif alertType == "TL": 
        print(f"{alertDevice} :: TEMPERATURE LOW")
        overrideMode = 99
    elif alertType == "PH":
        overrideMode = 99
        print(f"{alertDevice} :: PRESSURE HIGH")
    elif alertType == "PL":
        overrideMode = 99
        print(f"{alertDevice} :: PRESSURE LOW")
    elif alertType == "PZ":
        overrideMode = 99
        print(f"{alertDevice} :: PRESSURE ZERO")
    elif alertType == "FH":
        overrideMode = 99
        print(f"{alertDevice} :: FLOW HIGH")
    elif alertType == "FL":
        overrideMode = 99
        print(f"{alertDevice} :: FLOW LOW")
    else:
        print(f"Unknown alert :: {alertBox}, {alertDevice}, {alertType}")
    
    sendOverride(alertBox,alertDevice,overrideMode)
    

client = mqtt.Client()
client.on_connect = onConnect
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=0, bind_address="")
client.on_message = onMessage
client.loop_forever()

print("Shutting down")
