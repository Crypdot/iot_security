import serial
import time
import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
import time

load_dotenv()

# Parameters for the MQTT broker
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT"))
MQTT_TOPIC_SENSOR_FLOW_OUT = os.getenv("MQTT_TOPIC_SENSOR_INFLOW_OUT")
MQTT_TOPIC_SENSOR_DP_OUT = os.getenv("MQTT_TOPIC_SENSOR_DP_OUT")
MQTT_TOPIC_SENSOR_TEMP_OUT =os.getenv("MQTT_TOPIC_SENSOR_TEMP_OUT")
SAMPLE_RATE = float(os.getenv("MQTT_SENSOR_SAMPLERATE"))

# These likely should be parameters given when the program is run. Otherwise maybe assume a default value?
boxID = os.getenv("BOX_ID")
sensorID = "diffPressure01"

flowChannel = boxID+"/"+sensorID+MQTT_TOPIC_SENSOR_FLOW_OUT
dpChannel = boxID+"/"+sensorID

# Process Messages
def onConnect(client, metadata, flags, rc):
	print(f"Using MQTT broker at {MQTT_BROKER_HOST} at {str(MQTT_BROKER_PORT)}")

def onDisconnect(client, metadata, flags, rc):
	print("MQTT Disconnected :: Reconnecting")
	try:
		client.reconnect()
	except Exception as error:
		print(f"Something went wrong :: {error}")

def publishError(message):
	client.publish(f"ERROR :: {message}")

def publishFlow(client, channel, value):
   try:
      dataString = value.decode("UTF-8").strip()
      dataString = dataString[0:-1]  
      if "Error" in dataString:
         print(f"Data contains an error. Ignoring it. {dataString}")    
      else:
         print(f"Publishing '{dataString}' to '{channel}'")
         client.publish(channel, dataString)
   except Exception as error:
      print(f"Something went wrong :: {error}")

def publishDP(client, channel, value):
   dpChannel = channel+MQTT_TOPIC_SENSOR_DP_OUT
   tempChannel = channel+MQTT_TOPIC_SENSOR_TEMP_OUT

   try:
      data = value.decode("UTF-8").split(",")
      pressure = str(data[0]).strip()
      temp = str(data[1]).strip()
      
      print(f"Publishing '{pressure}' to '{dpChannel}'")
      client.publish(dpChannel+"pressure", pressure)
      print(f"Publishing '{temp}' to '{tempChannel}'")
      client.publish(tempChannel, temp)
   except Exception as error:
      print(f"Something went wrong :: {error}")


print("Ventilator Test Code") 

print("Flow rate in SLM (standard litre per minute)\n"+
"Differential pressure in Pascals,  1atm = 101Pa. 1cmH20 = 98 Pa, typical CPAP range 4-20\n"+
"Temperature in Celcius\n")

print(f"Using MQTT broker at {MQTT_BROKER_HOST} at {str(MQTT_BROKER_PORT)}")

client = mqtt.Client()
client.on_connect = onConnect
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=60, bind_address="")
client.loop_start()

"""
Configures the serial port to listen to the arduino. 
This *should* be "USB0", but it may be "USB1" or "ACM0"; check the port. On Windows, "COM" ports are also possible.

TODO :: Should this be a parameter given to the program on run?
"""
print("\nConfiguring Serial Ports")
sensorSerialPort = "/dev/ttyUSB0"

print("Connecting to sensor")
sensor = serial.Serial(sensorSerialPort,115200,timeout=1)
print(f"Serial connected \nPort :: {sensorSerialPort}, sensor :: {sensor}")

# Give it a few seconds to set itself up. No-wait results in consistent failures, as does a single second. 
time.sleep(5)

sensor.flushInput()
sensor.flushOutput()

"""
#print("Inflow")
#sensor.write("s".encode())
#sensorSerialNumber = sensor.readline(24)
#print(f"Flow sensor :: {sensorSerialNumber}")

#sensor.write("e".encode())
#sensorSerialNumber = sensor.readline(24)
#print(f"DP sensor :: {sensorSerialNumber}")

sensor.flushInput()
sensor.flushOutput()
"""


"""
Flow rate into continuous mode, then DP into continuous mode.
1 is for setting the flow sensor, 3 is for the differential pressure sensor

NOTE :: Currently this needs to be toggled between reading the flow- and differential pressure sensors separately.
"""
print("Setting the sensors into continuous mode")
#sensor.write("1".encode())
sensor.write("3".encode())

print("Running . . . ")

sensor.flushInput()
sensor.flushOutput()
try: 
   while True:
      #Requests the Flow sensor's data
      #sensor.write("f".encode())
      #publishFlow(client,flowChannel,sensor.readline())
      #sensor.flushInput()
      #sensor.flushOutput()

      # Requests the DP sensor's data
      sensor.write("d".encode())
      publishDP(client,dpChannel,sensor.readline())

      sensor.flushInput()
      sensor.flushOutput()
      time.sleep(SAMPLE_RATE)
except KeyboardInterrupt:
   client.disconnect()
except Exception as error:
   print(f"Something went wrong :: {error}")

print("Shutting down")

sensor.flushInput()
sensor.flushOutput()