import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
import requests
import jwt
import time

load_dotenv()

# Parameters for the MQTT broker
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT"))

client = mqtt.Client()

# Parameters for the Influx database
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_TABLE = os.getenv("DATABASE_TABLE")
DATABASE_PORT = 8086
SECRET_KEY = os.getenv("SECRET_KEY")
INFLUX_USERNAME = os.getenv("INFLUX_USERNAME")

# Parsed url for API requests
influx_url = f"http://{DATABASE_HOST}:{DATABASE_PORT}/write?db={DATABASE_NAME}"
token = ""

"""
Subscribed topics are parsed through and relevant types are forwarded to the database.
"""
def onMessage(client, userdata, message):
    topic = (message.topic).split("/")
    value = message.payload

    topicFilter = ["config", "command"]

    if topic[2] not in topicFilter:
        publishToInflux(topic, float(value))

"""
Influx acts as an API. Data can be sent with HTTP POST requests to tables.
MQTT data is parsed and posted to Influx API. Influx responds with 204 if successful. 
Authentication implemented with JWT, a shared secret key and configured users with specific privileges.
Requests by unauthorized users yield the HTTP 403 Forbidden response.
"""
def publishToInflux(tags, value):
    global token
    parsedData = f"{DATABASE_TABLE},box={tags[0]},sensor={tags[1]},type={tags[2]} value={value}"

    # JWT token is used to authenticate and publish data. Token is created every time something is published. 
    # TODO: Sign token once and use it. e.g. At start up, token is created for X amount of time and renewed once expired.
    #token = jwt.encode({"username": INFLUX_USERNAME, "exp": (int(time.time()) + 7200)}, SECRET_KEY, algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(influx_url, data=parsedData, headers=headers)

    if response.status_code == 204:
        print("Data inserted successfully.")
    elif response.status_code == 401:
        print("Invalid token.")
        authenticate()
        publishToInflux(tags, value)
    else:
        print(f"Failed to insert data. Status code: {response.status_code}")

def authenticate():
    global token
    print("Authentication token created.")
    token = jwt.encode({"username": INFLUX_USERNAME, "exp": (int(time.time()) + 5)}, SECRET_KEY, algorithm="HS256")

def controlLoop():
    while True:
        continue

if __name__ == "__main__":
    try:
        # Check if database exists
        requests.get(f"http://{DATABASE_HOST}:{DATABASE_PORT}")

        client.on_message = onMessage
        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 0)

        # Only "out" data is relevant. '#' wildcards must be at last level --> must use '+' in this case
        MQTT_TOPIC = "+/+/+/out/"

        authenticate()

        client.subscribe(MQTT_TOPIC)

        client.loop_start()
        print("Connected")
        try:
            controlLoop()
        except KeyboardInterrupt:
            client.disconnect()
        except Exception as e:
            print("An unexpected error occurred: " + str(e))

    except requests.exceptions.ConnectTimeout:
        print(f"HTTP connection to DATABASE_HOST {DATABASE_HOST} timed out.")
    except TimeoutError:
        print(f"MQTT connection to MQTT_BROKER_HOST {MQTT_BROKER_HOST} timed out.")
    except Exception as e:
        print(f"Unknown exception occurred: {str(e)}")