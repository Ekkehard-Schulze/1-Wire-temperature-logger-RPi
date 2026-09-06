1-Wire temperature logger for Linux systems
===========================================
Requires a kernel driver for 1-Wire hardware. The script creates a text file containing temperature data and timestamps. It has documented mercury arc lamp usage in a lab for two years. The Linux operating system ensures unattended, long-term, stable operation and network access to the data.


Features
--------

- Multiple temperature sensors on a single long cable

- Auto-discovery of sensors on system startup

- Mixed usage of sensor types:
  - DS18B20     ±0.5°C accuracy from -10°C to +85°C 
  - DS18S20     ±0.5°C accuracy from -10°C to +85°C (obsolete)
  - DS1822      ±2.0°C accuracy from -10°C to +85°C
  - DS28EA00 
  - MAX31850    for temperatures ranging from -200°C to +1200 °C, accuracy worse then ±2.0°C
  - DS1825  

&emsp;&emsp;&emsp;The latter two read type K thermocouples;
 all others are semiconductor thermometers.

- Linearization for type K thermocouples according ITS-90 enables measurements at temperatures below -30 °C and above +600 °C

- Preferably, the system records a data frame when called by the Linux cron daemon; otherwise, it logs temperature measurements using its own timer.

- Writes data to a TSV file with ISO 8601 timestamps. Fully compatible with Excel, Google Sheets, and Python (pandas).

- Another script provides graphical data analyzis and statistics.







Notes
-------
1. To use 1-Wire sensors with a Raspberry Pi, enable the 1-Wire bus via raspi-config. The default 
pin for 1-Wire communication is GPIO4. Connect a 4.7 kΩ pull-up 
resistor between the data line and the 3.3 V supply.

2. The 1-Wire bus can power sensors using 'external power'
(three wires) or 'parasite power' (two wires).
This script was only tested using external power.

1. To view the available command-line options run './1-Wire-temperature-logger-RPi.pyw -h'

2. Read the 'user settings' (lines 85 to 133) and modify these according to your needs.

3. The file name ending '.pyw' prevents the opening of a terminal window when running the script as a cron job. 

4. For advanced usage of 1-Wire temperature sensors with the Linux kernel driver study [Timo Furrer's w1thermsenso package](https://pypi.org/project/w1thermsensor/). This package is not used here.



Images
-------

![Sensor chan](https://github.com/Ekkehard-Schulze/1-Wire-temperature-logger-RPi/blob/main/images/Raspi_with_1-Wire_bus.jpg)

Experimental setup for monitoring mercury arc lamp usage over a two-year period. The system consists of an 8-meter 1-Wire bus cable with six DS18B20 temperature sensors connected to a Raspberry Pi 3B+. Neodymium magnets secure the sensors to the equipment
<br/><br/>
<br/><br/>
![Sensor chan](https://github.com/Ekkehard-Schulze/1-Wire-temperature-logger-RPi/blob/main/images/Raspi_with_typeK_thermocouples.jpg)

Four Type K thermocouples, connected via MAX31850 amplifiers to a Raspberry Pi 3B+, enable temperature measurements ranging from -200 °C to 1200 °C.

![Sensor chan](https://github.com/Ekkehard-Schulze/1-Wire-temperature-logger-RPi/blob/main/images/plots_and_statistics_of_time_series.py_screenshot.webp)

Screenshot of interactive data visualization using the script plots_and_statistics_of_time_series.py.