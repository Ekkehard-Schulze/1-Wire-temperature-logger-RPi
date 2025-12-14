1wire-temperature logger for Linux systems
------------------------------------------

This python script uses the Linux kernel driver 

for sensor readings of 1-Wire bus.

The 1-Wire bus allows many temperature sensors on

a single bus cable with many meter long connections.

This script was run in a lab  environment for years 

using a RaspberryPi 4 as a crontab job. The sensor 

chain used carried 6 DS18B20 sensors on a 8 meter long 

cable and monitored the usage of mercury short arc lamp.
 
Moreover, four type K thermocouples were tested using the

MAX31850 based Adafruit #1727 interface.



The sensors are auto-discovered by the kernel

during startup and all read out by this script.

Different types of sensors can be used together

on the same bus. This script logs data from all attached

1Wire temperature sensors. The sensors supported by the

Linux kernal are DS18S22", DS18B20, DS18B20, MAX31850,
DS1825, and DS28EA00.

The 1-Wire bus can power sensors using 'external power'

(three wires) or 'parasite power' (two wires).

This code was only tested using external power.




This script can iterate unlimited periodic measurements.

Alternatively, it can be used for a single dataframe reading

triggered by the crontab deamon. The latter is recomended

for indefinite measurements with larger time intervals.

crontab entry used to trigger a single data logging event every 15 minutes:
# -----------------------------------------------
# quarter-hourly logging of all 1-Wire temperature sensors
*/15  * * * *    /home/user_name/bin/1wire-temperature-logger-RPi.pyw -q    >/dev/null 2>>/dev/null


The default Raspberry Pi GPIO pin for 1-Wire communication is

GPIO4 (physical pin 7), but you can use other pins by enabling

the interface in /boot/config.txt and specifying a gpiopin.

You'll need a pull-up resistor (typically 4.7kΩ) between the data line and 3.3V,

connecting the sensor's DQ to GPIO4, GND to Pi's GND, and VDD to 3.3V.




Images
-------

![Sensor before and after coating with epoxy resin](https://github.com/Ekkehard-Schulze/precision-temperature-logger/blob/main/hardware_sensor_breakout_boards/TMP117-WSON-package-Sensor-PCBs/populated%20TMP117%20sensor%20breakout%20PCB.jpg)

Board with TMP117A sensor before and after coating with epoxy resin

![Sensor before and after coating with epoxy resin](https://github.com/Ekkehard-Schulze/precision-temperature-logger/blob/main/hardware_sensor_breakout_boards/TMP117-WSON-package-Sensor-PCBs/Sensor_with_wires_and_plug.jpg)

Sensor board with polytetrafluoroethylene isolated wires and plug

![Sensor before and after coating with epoxy resin](https://github.com/Ekkehard-Schulze/precision-temperature-logger/blob/main/hardware_sensor_breakout_boards/TMP117-WSON-package-Sensor-PCBs/Logger_with_Sensor.jpg)

Logger with sensor attached

![Sensor before and after coating with epoxy resin](https://github.com/Ekkehard-Schulze/precision-temperature-logger/blob/main/hardware_sensor_breakout_boards/TMP117_in_CyA.JPG)

TMP117A sensor soldered to wires and coated with cyanoacrylate after years of lab use. 

Avoid outdoor use of cyanoacrylate polymer (CyA) coated sensors; UV light deteriorates CyA.