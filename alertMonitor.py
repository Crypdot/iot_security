import sys
import time
import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv()

# Parameters for the MQTT broker
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT"))
SAMPLE_RATE = 0.2

# Define alertable ranges for temperature, pressure and flowrates
TEMP_HI = 28.0
TEMP_LO = 26.0

PRESS_HI = 3000.0
PRESS_LO = 500.0

FLOW_HI = 100.0
FLOW_LO = 0.0

# Check alerts
def alertTemperatureRange(message: str)-> str:
    if float(message) > TEMP_HI:
        print("Temperature High!")
        return "TH"
    elif float(message) < TEMP_LO:
        print("Temperature LOW!")
        return "TL"
    #return "NA"

def alertPressure(message: str) -> str:
    if float(message) > PRESS_HI:
        return "PH"
    elif float(message) < PRESS_LO:
        return "PL"
    elif float(message) < 0.0:
        return "PZ"
    #return "NA"

def alertFlowRate(message: str) -> str:
    if float(message) >= FLOW_HI:
        return "FH"
    elif float(message) <= FLOW_LO:
        return "FL"
    #return "NA"

# Process Messages
def onConnect(client, metadata, flags, rc):
    client.subscribe('+/+/+/out/')
    print(f"Using MQTT broker at {MQTT_BROKER_HOST} at {str(MQTT_BROKER_PORT)}")

def onDisconnect(client, metadata, flags, rc):
	print("MQTT Disconnected :: Reconnecting")
	try:
		client.reconnect()
	except Exception as error:
		print(f"Something went wrong :: {error}")

"""
This might benefit from waiting for the confirmation from alertManager using the QoS-parameters.

That way we won't just spam "ALERTALERTALERT" over to the channel unnecessarily. Just the one message should be enough, if the manager responds with a "yeah I'm on it".
"""
def publishAlert(box: str, device: str, error: str):
    try:
        client.publish('system/alerts', f"{box},{device},{error}")
    except Exception as error:
        print(f"Something went wrong {error}")

def onMessage(client,userdata,message):
    topicComponents = message.topic.split("/")[0:]
    if len(topicComponents) >= 3:
        box = topicComponents[0]
        device = topicComponents[1]
        dataType = topicComponents[2]
        dataValue = message.payload.decode("UTF-8")
    
    if dataType == "temperature":
        check = alertTemperatureRange(dataValue)
        if check:
            publishAlert(box,device,check)
            print("ALERT TEMPERATURE!")
    elif dataType == "diffPressure": 
        check = alertPressure(dataValue)
        if check: 
            publishAlert(box,device,check)
            print("ALERT PRESSURE")
    elif dataType == "inflowRate":
        check = alertPressure(dataValue)
        if check: 
            publishAlert(box,device,check)
            print("ALERT INFLOW")
    elif dataType == "outflowRate":
        check = alertPressure(dataValue)
        if check: 
            publishAlert(box,device,check)
            print("ALERT PRESSURE")

    #print(f"Got these values\nBox :: {box}\nDevice :: {device}\nData Type :: {dataType}\nData Value :: {dataValue}\n")


client = mqtt.Client()
client.on_connect = onConnect
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=0, bind_address="")
client.on_message = onMessage
client.loop_forever()

print("Shutting down")
