# iot_security
Our project github for our innovation project. 

## User guide

This is a guide for using the IoT-ventilator. In this file, we’re telling you how to build the device and get the system running.

## Components for the ventilator

You’re going to need atleast these components for the ventilator.

- Raspberry Pi 3 tai newer
- Raspberry Pi Display
- GPIO extender 
- Brushless motor 
- Electronic Speed Controller [ESC]
- Arduino Nano (3pcs)
- Breadboards (3pcs) connecting Arduino’s to the sensors
- Sensirion SFM3000-C200-sensor (2pcs)
- Sensirion SDP372 Differential Pressure sensor
- Micro USB power cable (2pcs, one for Raspi, one for the display)
- Power cable for the motor
- Micro USB cables for arduinos
- jumper wires for sensors
- Enclosure for the components, our ventilator was in a hard plastic box.
- Mouse and keyboard for using the RasPi (optional)

## Building the ventilator
When you have these, you can build the ventilator.

1.	Connect Raspi into the display and the GPIO extender
2.	Connect the motor to the ESC and the motor’s power cable.
3.	Solder breadboards into the jumper wires
4.	Attach arduinos to the breadboards and jumper wires into sensors.
5.	Attach arduinos to the RasPi with the micro USB cables.
6.	Attach motor to the Raspi’s GPIO extender number 13 through jumper wire.
7.	Plug in the RasPi’s and the display’s power cables.
8.	Plug in the motor’s power cable.

## Installing the software

You should have Python 3.11.5 and Git installed on your Raspi. 
Here is everything you need to do to get the software running.

### Clone the repo

```git clone https://github.com/Crypdot/iot_security.git```

```cd iot_security```

### Install Mosquitto

All the data is going to move through the MQTT service.

```sudo apt-get update```

```sudo apt-get install mosquitto```

```sudo systemctl start mosquitto```

If you want Mosquitto to start automatically every time you boot the device: ```sudo systemctl enable mosquitto```

### Setup and activate virtual environment

Using venv makes it possible to setup the software easily.

```python 3 -m venv venv```

```source venv/bin/activate```

### Installing requirements

The software requires some libraries, that you can install them all at once with this.

```pip install -r requirements.txt```

### Creating the .env file

You need this for the MQTT connection. You can set up this easily. First you should open the .env.example file.

```cat .env.example```

Now, copy everything from there and create a new file with a text editor.

```nano .env```

Paste the data from the example file into the .env file and adjust the "MQTT_BROKER_HOST" ip address to match your ventilator's MQTT broker. You can check your broker's ip with ```ifconfig```. Save the file and you should be good to go.

### Starting the software

You can start the software by running the script ```startup.py```. This will startup the scripts that are needed.

```python startup.py```

### Shutting off the software

You can shut off the software simply by running the script ```stop.py```.

```python stop.py```

```python stop.py```
