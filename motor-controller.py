import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
import numpy as np
import time
from dataclasses import dataclass

load_dotenv()

@dataclass
class PumpStatus:
	running: bool = True
	speed: int = 0
	
@dataclass
class PumpSettings:
	mode: int = 1
	continuousLevel: int = 1300
	differentialMin: int = 1300
	differentialMax: int = 1999
	differentialPeriod: float = 8.0
	differentialRatio: float = 0.35

# Parameters for the MQTT broker
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT"))
MQTT_TOPIC_SINE_WAVE = os.getenv("MQTT_TOPIC_SINEWAVE")
MQTT_TOPIC_PUMP_CONTROL = os.getenv("MQTT_TOPIC_PUMP_CONTROL")
LOOP_INTERVAL = 0.25			# in seconds

client = mqtt.Client()

status = PumpStatus()
settings = PumpSettings()

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
		setPumpRunning(True)
	elif message == "stopPump":
		setPumpRunning(False)
	elif message == "pumpModeOne":
		setPumpMode(0)
	elif message == "pumpModeTwo":
		setPumpMode(1)

"""
Sets the pump active or inactive depending on the function input's state (boolean)
"""
def setPumpRunning(run):
	global status
	if run and not status.running:
		print("Pump started")
		status.running = True
	elif not run and status.running:
		print("Pump stopped")
		status.running = False

"""
Sets the pump's mode to the given input value
"""
def setPumpMode(mode):
	if mode != 0 and mode != 1:
		return
	
	global settings
	if mode != settings.mode:
		if mode == 0:
			print("Continuous mode selected")
		elif mode == 1:
			print("Differential mode selected")
		settings.mode = mode

"""
Stays in a loop, and while the pump is running, sends a value to the MQTT broker
"""
def controlLoop():
	global status
	while True:
		if status.running:
			status.speed = getPumpSpeed(settings.mode)

			client.publish(MQTT_TOPIC_SINE_WAVE, str(status.speed))
			printPumpSpeed()

		# The value is sent once every interval, sleep in between
		time.sleep(LOOP_INTERVAL)

"""
Selects the pump's value based on its operating mode
"""
def getPumpSpeed(mode):
	if mode == 0:
		return getContinuousSpeed()
	elif mode == 1:
		return getDifferentialSpeed()

"""
Visualizes the pump's speed on the command line by drawing a graph, with min, max and speed values visible
"""
def printPumpSpeed():
	global settings
	global status
	TOTAL_WIDTH = 40
	
	positionPercentage = (status.speed - settings.differentialMin) / (settings.differentialMax - settings.differentialMin)
	lowerPadding = round(TOTAL_WIDTH * positionPercentage)
	upperPadding = TOTAL_WIDTH - lowerPadding

	print(f"{settings.differentialMin} |{' ' * lowerPadding}+{' ' * upperPadding}| {settings.differentialMax} [{status.speed}]")

"""
Returns the pump's speed in continuous mode
"""
def getContinuousSpeed():
	global settings
	return settings.continuousLevel

"""
Returns the pump's speed in differential mode
"""
def getDifferentialSpeed():
	global settings

	timeWithinPeriod = time.time() % settings.differentialPeriod
	risingDuration = settings.differentialPeriod * settings.differentialRatio
	fallingDuration = settings.differentialPeriod - risingDuration

	if timeWithinPeriod < risingDuration:
		# Rising, use 1st quarter of the unit circle
		sinValue = np.sin(np.pi * 0.5 * timeWithinPeriod / risingDuration)
	else:
		# Falling, use 3rd quarter of the unit circle
		sinValue = np.sin(np.pi + np.pi * 0.5 * (timeWithinPeriod - risingDuration) / fallingDuration) + 1.0
	
	# Scale the value from 0..1 -> differentialMin..differentialMax
	scaledValue = settings.differentialMin + sinValue * (settings.differentialMax - settings.differentialMin)
	return int(scaledValue)

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
