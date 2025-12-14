1wire-temperature logger for Linux systems
------------------------------------------

This Python script uses the Linux kernel driver for 

1-Wire sensor readings. It recorded mercury short arc lamp 

usage in a lab for years. The 1-Wire bus enables multiple 

temperature sensors on a single long cable. 

Type K thermocouples were used with the MAX31850 Adafruit 1727 

interface, measuring -200°C to 1260°C. 

The kernel auto-discovers 1-Wire temperature sensors at startup.

Various sensors can be used on the same bus. This script logs 

data from all 1Wire temperature sensors. The kernel supports 1-Wire 

sensors DS18S22, DS18B20, MAX31850, DS1825, and DS28EA00. 

This script logs periodic temperature measurements or, alternatively,

records a single data frame, suitable for a crontab job.

Prefer the latter for very long recordings with larger

time intervals.


Use this crontab line to trigger a data frame recording every 15 minutes: 

*/15  * * * *    /home/user_name/bin/1wire-temperature-logger-RPi.pyw -q    >/dev/null 2>>/dev/null


The 1-Wire bus can power sensors using 'external power'

(three wires) or 'parasite power' (two wires).

This code was only tested using external power.

To use with a Raspberry Pi, activate the 1-Wire bus via raspi-config 

or by editing /boot/config.txt.

The default Raspberry Pi GPIO pin for 1-Wire communication is

GPIO4 (physical pin 7), but you can use other pins by 

specifying a different gpio pin in /boot/config.txt.

Moreover, you'll need a pull-up resistor (typically 4.7kΩ) between the 

data line and 3.3V, connect the sensor's GND to Pi's GND, and VDD to 3.3V.


<!-- your 

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

comment -->