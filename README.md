# Ventilator with Trusted Platform Module 2.0

This project consists of a ventilator prototype that communicates over Message Queuing Telemetry Transport (MQTT). The system is designed to be modular, and contains multiple components such as flow and differential pressure sensors, a brushless motor, as well as most notably the Trusted Platform Module (TPM) for ensuring secure communication between modules.

## User guide 

This is a guide for using the IoT-ventilator. In this file, you'll find instructions for building the device and getting the system running.

Note that this project depends on the Nokia Attestation Engine for setting up the Trusted Platform Module, Trust Agent and the Attestation service. You can find this at [Nokia Attestation Engine's Github](https://github.com/nokia/AttestationEngine).

## Components for the ventilator

You’re going to need atleast these components for the ventilator.

- Raspberry Pi 3 tai newer
- Raspberry Pi Display
- GPIO extender 
- Brushless motor 
- Electronic Speed Controller (ESC)
- Arduino Nano (3pcs)
- Breadboards (3pcs) connecting Arduino’s to the sensors
- Sensirion SFM3000-C200-sensor (2pcs)
- Sensirion SDP372 Differential Pressure sensor
- Micro USB power cable (2pcs, one for Raspberry Pi, one for the display)
- Power cable for the motor
- Micro USB cables for arduinos (3pcs)
- Jumper wires for sensors
- Enclosure for the components
- Mouse and keyboard for using the Raspberry Pi (optional).

## Building the ventilator
When you have these, you can build the ventilator.

1.	Connect Raspberry Pi into the display and the GPIO extender
2.	Connect the motor to the ESC and the motor’s power cable.
3.	Solder breadboards into the jumper wires.
    The pinout for the arduinos is:
    SDA = A4
    SCL = A5
    VDD = 5V
    GND = GND 
5.	Attach arduinos to the breadboards and jumper wires into sensors.
6.	Attach arduinos to the Raspberry Pi with the micro USB cables.
7.	Attach motor to the Raspberry Pi’s GPIO extender number 13 through jumper wire.
8.	Plug in the Raspberry Pi’s and the display’s power cables.
9.	Plug in the motor’s power cable.

## Installing the software

You should have Python 3.11.5 and Git installed on your Raspberry Pi. 
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

```python3 -m venv venv```

```source venv/bin/activate```

### Installing requirements

The software requires some libraries that you can install them all at once by running the command:

```pip install -r requirements.txt```

### Creating the .env file

You need this for the MQTT connection. You can set up this easily. First you should open the .env.example file.

```cat .env.example```

Now, copy everything from there and create a new file with a text editor.

```nano .env```

Paste the data from the example file into the .env file and adjust the "MQTT_BROKER_HOST" ip address to match your ventilator's MQTT broker. If you are running the MQTT broker on the Raspberry Pi, you can check your ip with ```ifconfig```. Save the file and you should be good to go.

### Starting the software

You can start the software by running the script ```startup.py```. This will startup the scripts that are needed. Note that if Attestation has not been properly set up, the script will abort the process.

```python startup.py```

### Shutting off the software

You can shut off the software simply by running the script ```stop.py```.

```python stop.py```
