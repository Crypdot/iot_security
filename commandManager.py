import json
import paho.mqtt.client as mqtt

with open('config.json', 'r') as configFile:
    config = json.load(configFile)

# Parameters for the MQTT broker
MQTT_BROKER_HOST = config["mqttBrokerHost"]  
MQTT_BROKER_PORT = config["mqttBrokerPort"]
MQTT_TOPIC_PUMP_CONTROL = config["mqttTopicPumpControl"]

client = mqtt.Client()

def onConnect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT Broker at: {MQTT_BROKER_HOST}")
    else:
        print("Connection to MQTT Broker failed")

"""
The main program. Doesn't take any inputs. Can call on the mode_menu() function if needed.
The intent is to likely make this one main function, so this mostly acts as a POC for the testing phase. Splitting the code just enough to keep it easily readable.
"""
def mainMenu():
    while True:
        print("\nMain Menu:")
        print("1: Start the pump!")
        print("2: Stop the pump!")
        print("3: Change operating mode")
        print("4: Quit")

        choice = input("Enter your choice: ")

        if choice == '1':
            print("Starting the pump!")
            client.publish(MQTT_TOPIC_PUMP_CONTROL, "startPump")
        elif choice == '2':
            print("Stopping the pump!")
            client.publish(MQTT_TOPIC_PUMP_CONTROL, "stopPump")
        elif choice == '3':
            modeMenu()
        elif choice == '4':
            print("Quitting the application!")
            break
        else:
            print("Invalid choice. Please select a valid option.")
"""
Mode menu acts as a selector for the different modes the pump can be set into, such as continuous flow and others.
"""
def modeMenu():
    while True:
        print("Mode Menu:")
        print("1: Select Mode 1")
        print("2: Select Mode 2")
        print("3: Select Mode 3")
        print("4: Back")

        choice = input("Enter your choice: ")

        if choice == '1':
            print("Mode 1 selected!")
            client.publish(MQTT_TOPIC_PUMP_CONTROL, "pumpModeOne")
        elif choice == '2':
            print("Mode 2 selected!")
            client.publish(MQTT_TOPIC_PUMP_CONTROL, "pumpModeTwo")
        elif choice == '3':
            print("Mode 3 selected!")
            client.publish(MQTT_TOPIC_PUMP_CONTROL, "pumpModeThree")
        elif choice == '4':
            break
        else:
            print("Invalid choice. Please select a valid option.")

if __name__ == "__main__":
    client.on_connect = onConnect
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 0)
    mainMenu()