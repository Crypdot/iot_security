import json
import numpy as np
import time
import paho.mqtt.client as mqtt

with open('config.json', 'r') as configFile:
    config = json.load(configFile)

# Parameters for the MQTT broker
MQTT_BROKER_HOST = config["mqttBrokerHost"]  
MQTT_BROKER_PORT = config["mqttBrokerPort"]
MQTT_TOPIC_SINE_WAVE = config["mqttTopicSineWave"]
MQTT_TOPIC_PUMP_CONTROL = config["mqttTopicPumpControl"]

# Pump control parameters
pumpRunning = False
pumpMode = 1	# 1 for continuous, 2 for sine wave, 3 for reserve

# Parameters for the sine wave
amplitude = 1.0
frequency = 1.0  # in Hertz
interval = 0.25  # export interval in seconds

client = mqtt.Client()

"""
Callback function called when the connection to the MQTT broker is established
"""
def onConnect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT Broker at: {MQTT_BROKER_HOST}")
    else:
        print("Connection to MQTT Broker failed")

"""
Callback function for handling pump control messages. Maps the MQTT messages to the various functions of the pump.
"""
def onPumpControl(client, userdata, msg):
	message = msg.payload.decode()
	if message == "startPump":
		setPumpState(True)
	elif message == "stopPump":
		setPumpState(False)
	elif message == "pumpModeOne":
		setPumpMode(1)
	elif message == "pumpModeTwo":
		setPumpMode(2)
	elif message == "pumpModeThree":
		setPumpMode(3)

"""
Sets the pump active or inactive depending on the function input's state (boolean)
"""
def setPumpState(state):
	global pumpRunning
	if state and not pumpRunning:
		print("Pump started")
		pumpRunning = True
	elif not state and pumpRunning:
		print("Pump stopped")
		pumpRunning = False

"""
Sets the pump's mode to the given input value (1, 2 or 3)
"""
def setPumpMode(mode):
	global pumpMode
	if mode != pumpMode:
		if mode == 1:
			print("Continuous mode selected")
		elif mode == 2:
			print("Sinewave mode selected")
		if mode == 3:
			print("Reserved mode selected")
		pumpMode = mode

"""
Stays in a loop, and while the pump is running, sends a value to the MQTT broker
"""
def controlLoop():
	while True:
		if pumpRunning:
			pumpValue = getPumpValue(pumpMode)

			print(f"Publishing '{pumpValue}' to the MQTT broker")
			client.publish(MQTT_TOPIC_SINE_WAVE, str(pumpValue))

		# The value is sent once every interval, sleep in between
		time.sleep(interval)

"""
Selects the pump's value based on its operating mode
"""
def getPumpValue(mode):
	if mode == 1:
		return getContinuousValue()
	elif mode == 2:
		return getSinewaveValue()
	elif mode == 3:
		return 0

"""
Returns the pump's value in continuous mode
"""
def getContinuousValue():
	# Continuous mode returns 1 for now
	return 1

"""
Returns the pump's value in sine wave mode
"""
def getSinewaveValue():
	currentTime = time.time()
	# Calculate the value of the sine wave at the current time
	sineWaveValue = amplitude * np.sin(2 * np.pi * frequency * currentTime)
	return sineWaveValue

"""
Main function: establishes connection to the MQTT broker,
subscribes to the pump control topic and goes to the control loop
"""
if __name__ == "__main__":
	client.on_connect = onConnect
	client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)

	client.subscribe(MQTT_TOPIC_PUMP_CONTROL)
	client.on_message = onPumpControl
    
	client.loop_start()
	controlLoop()
