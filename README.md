1-Wire temperature logger for Linux systems
-------------------------------------------

This Python script uses the Linux kernel driver for 

1-Wire sensor readings. The 1-Wire bus enables multiple 

temperature sensors on a single long cable. 

The Linux kernel auto-discovers 1-Wire temperature sensors at startup.

Different types of sensors can be connected to the same bus. This script logs 

data from all connected sensors. The kernel supports 1-Wire sensor types 

DS18S20, DS1822, DS18B20, MAX31850, DS1825, and DS28EA00. 

This script either logs temperature measurements with its own timer,

or, alternatively, records a single data frame, suitable for periodic calls

by the cron deamon.

For example, this crontab line invokes a data frame recording every 15 minutes: 

*/15  * * * *    /home/user_name/bin/1-Wire-temperature-logger-RPi.pyw -q    >/dev/null 2>>/dev/null

The 1-Wire bus can power sensors using 'external power'

(three wires) or 'parasite power' (two wires).

This script was only tested using external power.

To use 1-Wire sensors with a Raspberry Pi, activate the 1-Wire bus 

via raspi-config. The default Raspberry Pi GPIO pin for 

1-Wire communication is GPIO4.

You need a 4.7kΩ resistor between the data line and 3.3 volt. 

Moreover, connect the sensor's GND to Pi's GND, and VDD to 3.3 volt.


Notes
-------

1.) To see the (few) command line options use './1-Wire-temperature-logger-RPi.pyw -h'

2.) Read the 'user settings' (lines 87 to 130) and modify these according to your needs.

3.) The file name extension '.pyw' prevents the opening of a terminal window in case

you invoke the script as a cron job.





Images
-------

![Sensor chan](https://github.com/Ekkehard-Schulze/1wire-temperature-logger-RPi/blob/main/images/Raspi_with_1Wire_bus.jpg)

An eight-meter long 1-Wire bus cable with six DS18B20 sensors connected to a RaspberryPi3B+

was used to document mercury arc lamp usage in a lab for two years without ever rebooting the Raspberry Pi.

![Sensor chan](https://github.com/Ekkehard-Schulze/1wire-temperature-logger-RPi/blob/main/images/Raspi_with_typeK_thermocouples.jpg)

Four type K thermocouples connected via 1-Wire bus to a RaspberryPi3B+ using MAX31850 amplifiers

allow to measure temperatures ranging from -200°C to 1200°C with the MAX31850 interface.
