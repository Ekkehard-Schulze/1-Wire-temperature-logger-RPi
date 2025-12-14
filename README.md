1wire-temperature logger for Linux systems
------------------------------------------

This Python script uses the Linux kernel driver for 

1-Wire sensor readings. The 1-Wire bus enables multiple 

temperature sensors on a single long cable. 

This script tracked mercury arc lamp usage in a lab for years 

using DS18B20 sensors. Moreover, type K thermocouples were used 

with the MAX31850 Adafruit 1727 interface, for measuring temperatures 

ranging from -200°C to 1260°C. 

The Linux kernel auto-discovers 1-Wire temperature sensors at startup.

Different types of sensors can be used on the same bus. This script logs 

data from all 1Wire temperature sensors. The kernel supports 1-Wire 

sensors DS18S20, DS1822, DS18B20, MAX31850, DS1825, and DS28EA00. 

This script either logs periodic temperature measurements or, 

alternatively, records a single data frame, suitable for a crontab job.

Prefer the latter for very long recordings with larger

time intervals.

For example, use this crontab line to trigger a data frame recording every 15 minutes: 

*/15  * * * *    /home/user_name/bin/1wire-temperature-logger-RPi.pyw -q    >/dev/null 2>>/dev/null

The 1-Wire bus can power sensors using 'external power'

(three wires) or 'parasite power' (two wires).

This script was only tested using external power.

To use with a Raspberry Pi, activate the 1-Wire bus via raspi-config 

or by editing /boot/config.txt.

The default Raspberry Pi GPIO pin for 1-Wire communication is

GPIO4 (physical pin 7), but you can use other pins by 

specifying a different gpio pin in /boot/config.txt.

Moreover, you'll need a pull-up resistor (typically 4.7kΩ) between the 

data line and 3.3V, connect the sensor's GND to Pi's GND, and VDD to 3.3V.



Images
-------


![Sensor chan](https://github.com/Ekkehard-Schulze/1wire-temperature-logger-RPi/blob/main/images/Raspi_with_1Wire_bus.jpg)

8 meter long 1-wire bus cable with six DS18B20 sensors connected to a RaspberryPi3B+

![Sensor chan](https://github.com/Ekkehard-Schulze/1wire-temperature-logger-RPi/blob/main/images/Raspi_with_typeK_thermocouples.jpg)

Four type K thermocouples connected to a RaspberryPi3B+ via 1-Wire bus using MAX31850 amplifiers
