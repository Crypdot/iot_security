import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
import numpy as np
import time
from dataclasses import dataclass

load_dotenv()

@dataclass
class MotorStatus:
	running: bool = False
	speed: int = 0

@dataclass
class MotorConfig:
	mode: int = 1
	continuousLevel: int = 1300
	differentialMin: int = 1300
	differentialMax: int = 1999
	differentialPeriod: float = 8.0
	differentialRatio: float = 0.5

# Parameters for the box's motor
BOX_ID = os.getenv("BOX_ID")
LOOP_INTERVAL = float(os.getenv("MOTOR_LOOP_INTERVAL"))		# seconds
status = MotorStatus()
config = MotorConfig()

# Parameters for the MQTT broker
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT"))
MQTT_TOPIC_MOTOR_SPEED_OUT = BOX_ID + "/motor/speed/out/"
MQTT_TOPIC_MOTOR_CONFIG_IN = BOX_ID + "/motor/config/in/"
MQTT_TOPIC_MOTOR_CONFIG_OUT = BOX_ID + "/motor/config/out/"
MQTT_TOPIC_MOTOR_COMMAND_IN = BOX_ID + "/motor/command/in/"
MQTT_TOPIC_MOTOR_COMMAND_OUT = BOX_ID + "/motor/command/out/"

client = mqtt.Client()

"""
Callback function called when the connection to the MQTT broker is established.
"""
def onConnect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT Broker at: {MQTT_BROKER_HOST}")
    else:
        print("Connection to MQTT Broker failed")

"""
Called when an MQTT message is received on the motor command topic.
Parses the message and starts or stops the motor accordingly.
"""
def onMotorCommand(client, userdata, msg):
	fields = msg.payload.decode().split(",")
	if fields[0] == "1":
		setMotorRunning(1)
	elif fields[0] == "0":
		setMotorRunning(0)

"""
Called when an MQTT message is received on the motor config topic.
The message is validated, and if validation passes, the new values are stored to the motor's config.
"""
def onMotorConfig(client, userdata, msg):
	try:
		newConfig = validateConfig(msg.payload.decode())
	except Exception as e:
		print("Invalid configuration: " + str(e))
		return
	
	global config
	config.mode = newConfig[0]
	config.continuousLevel = newConfig[1]
	config.differentialMin = newConfig[2]
	config.differentialMax = newConfig[3]
	config.differentialPeriod = newConfig[4]
	config.differentialRatio = newConfig[5]
	print("New motor config stored: \n" + str(config))

"""
Takes a string and checks if it's a correctly formatted list of comma separated values for the motor's config.
If the string and the values it contains are valid, it returns an array of those values cast into correct data types.
Otherwise an exception is thrown.
"""
def validateConfig(commaSeparatedValues):
	try:
		fields = commaSeparatedValues.split(",")
		config = [
			int(fields[0]),
			int(fields[1]),
			int(fields[2]),
			int(fields[3]),
			round(float(fields[4]), 2),
			round(float(fields[5]), 2)
		]
	except:
		raise ValueError("Missing or non-numeric config value")
	
	if config[0] != 0 and config[0] != 1:
		raise ValueError(f"Invalid mode: {config[0]}")
	elif config[1] < 1300 or config[1] > 1999:
		raise ValueError(f"Invalid continuous level: {config[0]}")
	elif config[2] < 1300 or config[2] > 1999:
		raise ValueError(f"Invalid minimum differential level: {config[0]}")
	elif config[3] < 1300 or config[3] > 1999:
		raise ValueError(f"Invalid maximum differential level: {config[0]}")
	elif config[4] <= 0.0:
		raise ValueError(f"Non-positive differential period: {config[0]}")
	elif config[5] <= 0.0 or config[5] > 1.0:
		raise ValueError(f"Invalid differential ratio: {config[0]}")
	
	return config

"""
Sets the motor active or inactive.
"""
def setMotorRunning(run):
	global status
	if run == 1 and not status.running:
		print("Motor started")
		status.running = True
	elif run == 0 and status.running:
		print("Motor stopped")
		status.running = False

"""
Stays in a loop, and while the motor is running, sends a value to the MQTT broker.
"""
def controlLoop():
	global status
	while True:
		if status.running:
			status.speed = getMotorSpeed(config.mode)
			printMotorSpeed()

			client.publish(MQTT_TOPIC_MOTOR_SPEED_OUT, str(status.speed))
			client.publish(MQTT_TOPIC_MOTOR_CONFIG_OUT, getMotorConfigMQTTString())
			client.publish(MQTT_TOPIC_MOTOR_COMMAND_OUT, getMotorStatusMQTTString())

		# The value is sent once every interval, sleep in between
		time.sleep(LOOP_INTERVAL)

"""
Selects the motor's value based on its operating mode.
"""
def getMotorSpeed(mode):
	if mode == 0:
		return getContinuousSpeed()
	elif mode == 1:
		return getDifferentialSpeed()

"""
Visualizes the motor's speed on the command line by drawing a graph, with min, max and speed values visible.
"""
def printMotorSpeed():
	global config
	global status
	TOTAL_WIDTH = 40
	
	positionPercentage = (status.speed - config.differentialMin) / (config.differentialMax - config.differentialMin)
	lowerPadding = round(TOTAL_WIDTH * positionPercentage)
	upperPadding = TOTAL_WIDTH - lowerPadding

	print(f"{config.differentialMin} |{' ' * lowerPadding}+{' ' * upperPadding}| {config.differentialMax} [{status.speed}]")

"""
Returns the motor's speed in continuous mode.
"""
def getContinuousSpeed():
	global config
	return config.continuousLevel

"""
Returns the motor's speed in differential mode.
"""
def getDifferentialSpeed():
	global config

	timeWithinPeriod = time.time() % config.differentialPeriod
	risingDuration = config.differentialPeriod * config.differentialRatio
	fallingDuration = config.differentialPeriod - risingDuration

	if timeWithinPeriod < risingDuration:
		# Rising, use 1st quarter of the unit circle
		sinValue = np.sin(np.pi * 0.5 * timeWithinPeriod / risingDuration)
	else:
		# Falling, use 3rd quarter of the unit circle
		sinValue = np.sin(np.pi + np.pi * 0.5 * (timeWithinPeriod - risingDuration) / fallingDuration) + 1.0
	
	# Scale the value from 0..1 -> differentialMin..differentialMax
	scaledValue = config.differentialMin + sinValue * (config.differentialMax - config.differentialMin)
	return int(scaledValue)

"""
Returns the motor's status as a string formatted for MQTT channel.
"""
def getMotorStatusMQTTString():
	global status
	return str(int(status.running)) + "," + str(status.speed)

"""
Returns the motor's config as a string formatted for MQTT channel.
"""
def getMotorConfigMQTTString():
	global config
	return str(int(config.mode)) + "," + str(config.continuousLevel) + "," + str(config.differentialMin) + "," + str(config.differentialMax) + "," + str(config.differentialPeriod) + "," + str(config.differentialRatio)

"""
Main function: establishes connection to the MQTT broker,
subscribes to the motor config and command topics and goes to the control loop.
"""
if __name__ == "__main__":
	client.on_connect = onConnect
	client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)

	client.subscribe([
		(MQTT_TOPIC_MOTOR_CONFIG_IN, 1),
		(MQTT_TOPIC_MOTOR_COMMAND_IN, 1)
	])
	client.message_callback_add(MQTT_TOPIC_MOTOR_CONFIG_IN, onMotorConfig)
	client.message_callback_add(MQTT_TOPIC_MOTOR_COMMAND_IN, onMotorCommand)

	client.loop_start()
	controlLoop()
