import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
import requests

load_dotenv()

# Parameters for the MQTT broker
BOX_ID = os.getenv("BOX_ID")
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT"))

client = mqtt.Client()

# Parameters for the Influx database
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_TABLE = os.getenv("DATABASE_TABLE")
DATABASE_PORT = 8086

# Parsed url for API requests
influx_url = f"http://{DATABASE_HOST}:{DATABASE_PORT}/write?db={DATABASE_NAME}"

"""
Subscribed topics are parsed through and relevant types are forwarded to the database
"""
def onMessage(client, userdata, message):
    topic = (message.topic).split("/")
    value = message.payload

    if topic[2] not in ["config", "command"]:
        publishToInflux(topic, float(value))

"""
Influx acts as an API. Data can be sent with HTTP POST requests to relevant tables.
MQTT data is parsed and posted to Influx API. Influx responds with 204 if successful. 
NOTE: Influx supports some sort of authentication, will look into tokens. 
"""
def publishToInflux(tags, value):
    parsedData = f"{DATABASE_TABLE},box={tags[0]},sensor={tags[1]},type={tags[2]} value={value}"
    response = requests.post(influx_url, data=parsedData)

    if response.status_code == 204:
        print("Data inserted successfully.")
    else:
        print(f"Failed to insert data. Status code: {response.status_code}")

def controlLoop():
    while True:
        continue

if __name__ == "__main__":
    client.on_message = onMessage

    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)

    # Only "out" data is relevant. Pound (#) wildcards must be the last level --> must use +
    MQTT_TOPIC = "+/+/+/out/"
    client.subscribe(MQTT_TOPIC)

    client.loop_start()
    
    try:
        controlLoop()
    except KeyboardInterrupt:
        client.disconnect()
    except Exception as e:
        print("An unexpected error occurred: " + str(e))