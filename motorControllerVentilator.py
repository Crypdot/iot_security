import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
import pigpio
import numpy as np
import time
from dataclasses import dataclass
from enum import Enum

load_dotenv()

class PCA9685:
	'''
	PWM motor controller using PCA9685 boards.
	This is used for most RC Cars

	https://github.com/autorope/donkeycar

	donkeycar/donkeycar/parts/actuator.py
	'''

	def __init__(self, channel, address=0x6f, frequency=60, busnum=None, init_delay=0.1):
		self.default_freq = 60
		self.pwm_scale = frequency / self.default_freq

		import Adafruit_PCA9685
		# Initialise the PCA9685 using the default address (0x40).
		if busnum is not None:
			from Adafruit_GPIO import I2C
			# replace the get_bus function with our own
			def get_bus():
				return busnum

			I2C.get_default_bus = get_bus
		self.pwm = Adafruit_PCA9685.PCA9685(address=address)
		self.pwm.set_pwm_freq(frequency)
		self.channel = channel
		time.sleep(init_delay)  # "Tamiya TBLE-02" makes a little leap otherwise

	def set_pulse(self, pulse):
		try:
			self.pwm.set_pwm(self.channel, 0, int(pulse * self.pwm_scale))
		except:
			self.pwm.set_pwm(self.channel, 0, int(pulse * self.pwm_scale))

	def run(self, pulse):
		self.set_pulse(pulse)

class PiGPIO_PWM():
	'''
	# Use the pigpio python module and daemon to get hardware pwm controls from
	# a raspberrypi gpio pins and no additional hardware. Can serve as a replacement
	# for PCA9685.
	#
	# This class can also be used when using the Grove Base Hat. It's PWM port is just
	# connected to the raspberry pi's gpio pins (12,13)
	#
	# Install and setup:
	# sudo update && sudo apt install pigpio python3-pigpio
	# sudo systemctl start pigpiod
	#
	# Note: the range of pulses will differ from those required for PCA9685
	# and can range from 12K to 170K
	'''

	def __init__(self, pin, pgio=None, freq=75):
		import pigpio

		self.pin = pin
		self.pgio = pgio or pigpio.pi()
		self.freq = freq
		self.pgio.set_mode(self.pin, pigpio.OUTPUT)

	def __del__(self):
		self.pgio.stop()

	def set_pulse(self, pulse):
		self.pgio.set_servo_pulsewidth(self.pin, pulse)

	def run(self, pulse):
		self.set_pulse(pulse)

# Constants for the motor's operation
BOX_ID = os.getenv("BOX_ID")
LOOP_INTERVAL = float(os.getenv("MOTOR_LOOP_INTERVAL"))		# seconds
MIN_SPEED = int(os.getenv("MOTOR_MIN_SPEED"))
MAX_SPEED = int(os.getenv("MOTOR_MAX_SPEED"))
MAX_ACCELERATION = int(os.getenv("MOTOR_MAX_ACCELERATION"))	# maximum change of the motor speed in one control loop

class Mode(Enum):
	CONTINUOUS = 0
	DIFFERENTIAL = 1
	SAFE = 99

class MotorStatus:
	def __init__(self):
		self.running: bool = False
		self.speed: int = 0

class ContinuousSettings:
	def __init__(self):
		self.level: int = MIN_SPEED

class DifferentialSettings:
	def __init__(self):
		self.min: int = int(os.getenv("MOTOR_SAFE_MIN"))
		self.max: int = int(os.getenv("MOTOR_SAFE_MAX"))
		self.period: float = float(os.getenv("MOTOR_SAFE_PERIOD"))
		self.ratio: float = float(os.getenv("MOTOR_SAFE_RATIO"))

class MotorConfig:
	def __init__(self):
		self.mode: Mode = Mode(Mode.DIFFERENTIAL.value)
		self.continuous: ContinuousSettings = ContinuousSettings()
		self.differential: DifferentialSettings = DifferentialSettings()
		self.safe: DifferentialSettings = DifferentialSettings()	# same as the differential mode but with default settings

# Parameters for the motor
status = MotorStatus()
config = MotorConfig()
previousSpeed = MIN_SPEED

# Constants for the MQTT broker
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
	except ValueError as e:
		print("Invalid configuration values: " + str(e))
		return
	except Exception as e:
		print("An unexpected error occurred: " + str(e))
		return
	
	global config
	config.mode = newConfig[0]
	config.continuous.level = newConfig[1]
	config.differential.min = newConfig[2]
	config.differential.max = newConfig[3]
	config.differential.period = newConfig[4]
	config.differential.ratio = newConfig[5]
	print("New motor config stored")

"""
Takes a string and checks if it's a correctly formatted list of comma separated values for the motor's config.
If the string and the values it contains are valid, it returns an array of those values cast into correct data types.
Otherwise an exception is thrown.
"""
def validateConfig(commaSeparatedValues) -> list:
	try:
		fields = commaSeparatedValues.split(",")
		config = [
			Mode(int(fields[0])),
			int(fields[1]),
			int(fields[2]),
			int(fields[3]),
			round(float(fields[4]), 2),
			round(float(fields[5]), 2)
		]
	except ValueError as e:
		raise ValueError(e)
	except Exception as e:
		raise Exception(e)
	
	#if not (config[0] == 0 or config[0] == 1 or config[0] == 99):
		#raise ValueError(f"Invalid mode: {config[0]}")
	if config[1] < MIN_SPEED or config[1] > MAX_SPEED:
		raise ValueError(f"Invalid continuous level: {config[0]}")
	elif config[2] < MIN_SPEED or config[2] > MAX_SPEED:
		raise ValueError(f"Invalid minimum differential level: {config[0]}")
	elif config[3] < MIN_SPEED or config[3] > MAX_SPEED:
		raise ValueError(f"Invalid maximum differential level: {config[0]}")
	elif config[4] <= 0.0:
		raise ValueError(f"Non-positive differential period: {config[0]}")
	elif config[5] < 0.0 or config[5] > 1.0:
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
		stop_pwm_service(pwm_gpio=13)
"""
Stays in a loop, and while the motor is running, sends a value to the MQTT broker.
"""
def controlLoop():
	global status
	global previousSpeed
	try:
		while True:
			if status.running:
				status.speed = limitAcceleration(getMotorSpeed(config.mode), previousSpeed)
				previousSpeed = status.speed
				
				# The command to set the speed in the motor using the GPUI
				set_pwm_value(status.speed, pwm_gpio=13)
				printMotorSpeed()

				client.publish(MQTT_TOPIC_MOTOR_SPEED_OUT, str(status.speed))
				client.publish(MQTT_TOPIC_MOTOR_CONFIG_OUT, getMotorConfigMQTTString())
				client.publish(MQTT_TOPIC_MOTOR_COMMAND_OUT, getMotorStatusMQTTString())

			# The value is sent once every interval, sleep in between
			time.sleep(LOOP_INTERVAL)
	except KeyboardInterrupt:
		client.disconnect()
	except Exception as e:
		print("An unexpected error occurred: " + str(e))

"""
Limits the amount of change in the given input speed.
The returned value can differ from the input at most by MAX_ACCELERATION.
"""
def limitAcceleration(speed: int, previousSpeed: int) -> int:
	if speed > previousSpeed + MAX_ACCELERATION:
		return previousSpeed + MAX_ACCELERATION
	elif speed < previousSpeed - MAX_ACCELERATION:
		return previousSpeed - MAX_ACCELERATION
	else:
		return speed

"""
Selects the motor's speed value based on its operating mode.
"""
def getMotorSpeed(mode: Mode):
	global config
	if mode is Mode.CONTINUOUS:
		return getContinuousSpeed(config.continuous)
	elif mode is Mode.DIFFERENTIAL:
		return getDifferentialSpeed(config.differential)
	elif mode is Mode.SAFE:
		return getDifferentialSpeed(config.safe)

"""
Visualizes the motor's speed on the command line by drawing a graph, with min, max and speed values visible.
"""
def printMotorSpeed():
	global config
	global status
	TOTAL_WIDTH = 40
	
	positionPercentage = (status.speed - MIN_SPEED) / (MAX_SPEED - MIN_SPEED)
	lowerPadding = round(TOTAL_WIDTH * positionPercentage)
	upperPadding = TOTAL_WIDTH - lowerPadding

	print(f"{MIN_SPEED} |{' ' * lowerPadding}+{' ' * upperPadding}| {MAX_SPEED} [{status.speed}]")

"""
Returns the motor's speed in continuous mode.
"""
def getContinuousSpeed(settings: ContinuousSettings) -> int:
	return settings.level

"""
Returns the motor's speed in differential mode.
"""
def getDifferentialSpeed(settings: DifferentialSettings) -> int:
	timeWithinPeriod = time.time() % settings.period
	risingDuration = settings.period * settings.ratio
	fallingDuration = settings.period - risingDuration

	if timeWithinPeriod < risingDuration:
		# Rising, use 1st quarter of the unit circle
		if risingDuration == 0:
			sinValue = 0
		else:
			sinValue = np.sin(np.pi * 0.5 * timeWithinPeriod / risingDuration)
	else:
		# Falling, use 3rd quarter of the unit circle
		if fallingDuration == 0:
			sinValue = 0
		else:
			sinValue = np.sin(np.pi + np.pi * 0.5 * (timeWithinPeriod - risingDuration) / fallingDuration) + 1.0
	
	# Scale the value from 0..1 -> differentialMin..differentialMax
	scaledValue = settings.min + sinValue * (settings.max - settings.min)
	return int(scaledValue)

"""
Returns the motor's status as a string formatted for MQTT channel.
"""
def getMotorStatusMQTTString() -> str:
	global status
	return str(int(status.running)) + "," + str(status.speed)

"""
Returns the motor's config as a string formatted for MQTT channel.
"""
def getMotorConfigMQTTString() -> str:
	global config
	return str(int(config.mode.value)) + "," + str(config.continuous.level) + "," + str(config.differential.min) + "," + str(config.differential.max) + "," + str(config.differential.period) + "," + str(config.differential.ratio)

"""
Sets the current PWM value to a given value; these should be between 1300 and 1999. 
The default value for the 'pwm_gpio' is 13, as that's where the motor is attached on the board.
"""
def set_pwm_value(pwm_value, pwm_gpio=13):
	"""
	Send a pwm value to the esc between 1000-2000

	:param pwm_gpio:
	:param pwm_value: int | str
	"""
	pin = int(pwm_gpio)
	p = pigpio.pi()  # Init Pi's HW PWM and timers
	if not p.connected:
		exit()
	c = PiGPIO_PWM(pin, p)

	try:
		pmw = int(pwm_value)
		c.run(pmw)
	except Exception as ex:
		print("Oops, {}".format(ex))
"""
Stops the PWM service; stops the motor.
"""
def stop_pwm_service(pwm_gpio=13):
	print("!!!Stopping pwm service!!!")
	p = pigpio.pi()  # Init Pi's HW PWM and timers
	pin = int(pwm_gpio)

	if not p.connected:
		exit()
	c = PiGPIO_PWM(pin)

	c.run(1000)

	time.sleep(1)

	del c

	c = PiGPIO_PWM(pin)

	c.run(1000)

	print("!!!Pwm service successfully stopped!!!")

"""
Main function: establishes connection to the MQTT broker,
subscribes to the motor config and command topics and goes to the control loop.
"""
if __name__ == "__main__":
	stop_pwm_service(pwm_gpio=13)

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
