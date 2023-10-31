import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
import numpy as np
import time
from dataclasses import dataclass
import pigpio

load_dotenv()
###########################
class PCA9685:
    '''
    PWM motor controller using PCA9685 boards.
    This is used for most RC Cars

    https://github.com/autorope/donkeycar

    donkeycar/donkeycar/parts/actuator.py
    '''

    def __init__(self, channel, address=0x6f, frequency=60, busnum=None, init_delay=0.1):

        self.defaultFreq = 60
        self.PWMScale = frequency / self.defaultFreq

        import Adafruit_PCA9685
        # Initialise the PCA9685 using the default address (0x40).
        if busnum is not None:
            from Adafruit_GPIO import I2C
            # replace the getBus function with our own
            def getBus():
                return busnum

            I2C.get_default_bus = getBus
        self.pwm = Adafruit_PCA9685.PCA9685(address=address)
        self.pwm.set_pwm_freq(frequency)
        self.channel = channel
        time.sleep(init_delay)  # "Tamiya TBLE-02" makes a little leap otherwise

    def setPulse(self, pulse):
        try:
            self.pwm.set_pwm(self.channel, 0, int(pulse * self.PWMScale))
        except:
            self.pwm.set_pwm(self.channel, 0, int(pulse * self.PWMScale))

    def run(self, pulse):
        self.setPulse(pulse)

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

    def setPulse(self, pulse):
        self.pgio.set_servo_pulsewidth(self.pin, pulse)

    def run(self, pulse):
        self.setPulse(pulse)
###########################

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

print("TESTING :: " + os.getenv("BOX_ID"))


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
	except ValueError as e:
		print("Invalid configuration values: " + str(e))
		return
	except Exception as e:
		print("An unexpected error occurred: " + str(e))
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
def validateConfig(commaSeparatedValues) -> list:
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
	except ValueError as e:
		raise ValueError(e)
	except Exception as e:
		raise Exception(e)
	
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

"""
Stays in a loop, and while the motor is running, sends a value to the MQTT broker.
"""
def controlLoop():
	global status
	try:
		while True:
			if status.running:
				status.speed = getMotorSpeed(config.mode)

				# The command to set the speed in the motor using the gpio
				setPWMValue(status.speed, pwm_gpio=13)
				
				printMotorSpeed()

				client.publish(MQTT_TOPIC_MOTOR_SPEED_OUT, str(status.speed))
				client.publish(MQTT_TOPIC_MOTOR_CONFIG_OUT, getMotorConfigMQTTString())
				client.publish(MQTT_TOPIC_MOTOR_COMMAND_OUT, getMotorStatusMQTTString())

			# The value is sent once every interval, sleep in between
			time.sleep(LOOP_INTERVAL)
	except KeyboardInterrupt:
		client.disconnect()
		stopPWMService(pwm_gpio=13)
	except Exception as e:
		print("An unexpected error occurred: " + str(e))
		stopPWMService(gpio=13)

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
def getContinuousSpeed() -> int:
	global config
	return config.continuousLevel

"""
Returns the motor's speed in differential mode.
"""
def getDifferentialSpeed() -> int:
	global config

	timeWithinPeriod = time.time() % config.differentialPeriod
	risingDuration = config.differentialPeriod * config.differentialRatio
	fallingDuration = config.differentialPeriod - risingDuration

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
	scaledValue = config.differentialMin + sinValue * (config.differentialMax - config.differentialMin)
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
	return str(int(config.mode)) + "," + str(config.continuousLevel) + "," + str(config.differentialMin) + "," + str(config.differentialMax) + "," + str(config.differentialPeriod) + "," + str(config.differentialRatio)

###########################
def setPWMValue(pwm_value, pwm_gpio=13):
    """
    Send a pwm value to the esc between 1000-2000

    :param pwm_gpio:
    :param pwm_value: int | str
    """
    pin = int(pwm_gpio)
    #print("Using PWM GPIO {}".format(pin))
    p = pigpio.pi()  # Init Pi's HW PWM and timers
    if not p.connected:
        exit()
    c = PiGPIO_PWM(pin, p)

    try:
        pmw = int(pwm_value)
        c.run(pmw)
    except Exception as ex:
        print("Oops, {}".format(ex))

def stopPWMService(pwm_gpio=13):
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
    print(f"Keyboard interrupt! Stopping the motor...")
###########################

"""
Main function: establishes connection to the MQTT broker,
subscribes to the motor config and command topics and goes to the control loop.
"""
if __name__ == "__main__":
	stopPWMService(pwm_gpio=13)
	
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