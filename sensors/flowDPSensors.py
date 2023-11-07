import serial
import sys
import time
import os
import argparse
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv()

# Parameters for the MQTT broker
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT"))
MQTT_TOPIC_SENSOR_FLOW_OUT = os.getenv("MQTT_TOPIC_SENSOR_INFLOW_OUT")
MQTT_TOPIC_SENSOR_DP_OUT = os.getenv("MQTT_TOPIC_SENSOR_DP_OUT")
MQTT_TOPIC_SENSOR_TEMP_OUT =os.getenv("MQTT_TOPIC_SENSOR_TEMP_OUT")
SAMPLE_RATE = float(os.getenv("MQTT_SENSOR_SAMPLERATE"))

# These likely should be parameters given when the program is run. Otherwise maybe assume a default value?
#boxID = os.getenv("BOX_ID")
#sensorID = "diffPressure01"

parser = argparse.ArgumentParser(description="A script to be run for the sensors. This code is configured to be able to run the flowrate sensors and differential pressure sensors. Use as indicated.")
parser.add_argument("-si", type=str, required=True, help="The sensor's ID. The channel this sensor posts on will depend on this name. Name this based on the sensor; fe: 'flowrateSensor01'")
parser.add_argument("-bi", type=str, required=True, help="The box's ID. The channel this sensor posts on will depend on this name. Name this based on the box; fe: 'box01'")
parser.add_argument("-cp", type=str, required=True, help="The USB port. Check which port this sensor is attached to, so that it knows where to get the right data from; fe: '/dev/ttyUSB0'. Note that it may be 'ACM0' as well. Check using 'dmesg -w' before use.")
#parser.add_argument("-i", type=int, default=1, help="Something very helpful regarding integers, for sure.")

"""
Configures the sensor to run as indicated by the arguments given.

TODO :: Possibly adding an additional argument to toggle between flow- and DP-modes, so that the user can simply indicate the type of sensor on runtime?
"""
def setup():
   global boxID, sensorID, flowChannel, dpChannel, sensorSerialPort
   
   args = parser.parse_args()
   boxID = args.bi
   sensorID = args.si
   sensorPort = args.cp
   flowChannel = boxID+"/"+sensorID+MQTT_TOPIC_SENSOR_FLOW_OUT
   dpChannel = boxID+"/"+sensorID

   """
   Configures the serial port to listen to the arduino. 
   NOTE :: This *should* be "USB0", but it may be "USB1" or "ACM0"; check the port. On Windows, "COM" ports are also possible.
   """
   print("\nConfiguring Serial Ports")
   sensorSerialPort = sensorPort

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
      
      if len(data) >= 2:
         pressure = str(data[0]).strip()
         temp = str(data[1]).strip()
         
         print(f"Publishing '{pressure}' to '{dpChannel}'")
         client.publish(dpChannel+"pressure", pressure)
         print(f"Publishing '{temp}' to '{tempChannel}'")
         client.publish(tempChannel, temp)
   except Exception as error:
      print(f"Something went wrong :: {error}")

# Run starts here

setup()

print("Ventilator Test Code") 

print("Flow rate in SLM (standard litre per minute)\n"+
"Differential pressure in Pascals,  1atm = 101Pa. 1cmH20 = 98 Pa, typical CPAP range 4-20\n"+
"Temperature in Celcius\n")

client = mqtt.Client()
client.on_connect = onConnect
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=60, bind_address="")
client.loop_start()


print("Connecting to sensor")
sensor = serial.Serial(sensorSerialPort,115200,timeout=1)
print(f"Serial connected \nPort :: {sensorSerialPort}, sensor :: {sensor}")

# Give it a few seconds to set itself up. No-wait results in consistent failures, as does a single second. 
time.sleep(2)

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