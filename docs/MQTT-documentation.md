<!--
    I added what I remembered, and from referencing my own notes thus far. 
    If you want to add to this, or adjust, by all means. I've probably forgotten some things. 
    This is likely subject to change as the project continues and we discover things we've missed/overthought.

    - Alex 

-->

# MQTT topics
Generally speaking, the plan is to have the following hierarchy. This is subject to change.
- `{boxID}/{sensorID}/{dataType}/out`
    - `boxID` is used to identify a specific ventilator-system, which presumably contains the motor and some sensors.
    - `sensorID` is used to identify a specific sensor; `temperature_sensor01`, for example.
    - `dataType` is used to identify the type of data received from a sensor. Each data type gets its own channel. 
        - For example, a temperature sensor will output both temperature and humidity readings on their own channels.
    - `in` is used as the general input channel; ie, if we want to tell the motor to do something, it would go in the `in` -channel.
    - `out` is used as the general data output channel.

## Examples
A few quick examples to get the general idea.

### Sensor channels
- `box01/diffPressure01/pressure/out/`
    - This will give the pressure readings from `diffPressure01`, inside `box01`.
        - The reading will be given in Pascals. 
- `box02/diffPressure02/pressure/out/`
    - This will give the current pressure readings from `diffPressure02`, inside `box02`
- `box01/diffPressure01/temperature/out/`
    - This will give the temperature readings from `diffPressure01`, inside `box01`.
        - The reading will be given in Celsius.
- `box01/inflow01/inflowRate/out/`
    - This will give the flow rate from the inflow sensor named `inflow01`, inside `box01`.
    - The flowrate reading will be given in standard litre per minute (SLM).
- `box01/outflow01/outflowRate/out/`
    - This will give the flow rate from the outflow sensor named `outflow01`, inside `box01`.

## Motor channels
- `box01/motor/config/in`
	- Controller sends configurations to the Motor Controller using this channel.
		- data: "`MODE`,`CONTINUOUS_LEVEL`,`MIN`,`MAX`,`PERIOD`,`RATIO`"
			- `MODE`: `0` for Continuous, `1` for Differential. Integer.
            - `CONTINUOUS_LEVEL`: `1300`-`1999`. Integer.
            - `MIN`: `1300`-`1999`; For the differential mode. Integer
            - `MAX`: `1300`-`1999`; For the differential mode. Integer.
            - `PERIOD`: `float`; The duration in seconds per cycle. Float.
            - `RATIO`: `0.0`-`1.0`; The point at which the level reaches its maximum, percentage of the period. Float.
- `box01/motor/config/out`
    - Largely the same as the previous. Data remains in the same format as well. Currently, the idea is that the Motor Controller will broadcast its current configuration in case other components need to know what it's current operating conditions are. <!--This was one I'm not sure we wanted to keep(?)-->
- `box01/motor/command/in`
	- Controller sends to Motor Controller.
		- data: "`0`/`1`"
            - `0` being "stop" and `1` meaning "start".
- `box01/motor/speed/in`
	- Motor controller sends this to the motor
        - data: "`1300`-`1999`"
            - This represents the speed at which the motor ought to be running.
- `box01/motor/speed/out`
	- Motor Controller broadcasts the current speed at which the motor is running.
        - data: "`1300`-`1999`". 
	- Display subscribes to this to display the current speed on a graph.

# Considerations
If the motor is currently in, say, Continuous Pressure Mode, and we send it new Differential Pressure Mode configurations, we have elected to *not* change the operating mode immediately. There will have to be a separate command to switch modes. This will be achieved by the Controller sending out the following string, for example, to the `box01/motor/config/in` -channel:

- "1,,1400,1800,8,0.8"
    - Meaning, switch to Differential Pressure Mode, with `1400` as the `MIN`, `1800` as the `MAX`, `8` as the `PERIOD`, and `0.8` as the `RATIO`.
- When only changing the configuration, we will leave the `MODE` as a blank value. The Motor Controller will parse out the relevant information from the string published to the relevant channel.
- ",,1400,1800,8,0.8"
    - This would change the configuration the same, without changing the operating mode. 

## Questions
### motor/config/in
Query as to how useful it is to simply leave a value blank in the string. Would it be better to instead have `-1` as the value flagged as something to ignore? It may be more immediately human-readable to have a clear indicator of something being "ignorable" than a simple missing space.