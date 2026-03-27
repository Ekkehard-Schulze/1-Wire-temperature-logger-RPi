1-Wire temperature logger for Linux systems
===========================================
This script documented mercury arc lamp usage in a laboratory on a Raspberry Pi for two years autonomously. The Linux system ensured continuous network access to the data.


Features
--------

- Multiple temperature sensors on a single long cable

- Auto-discovery of sensors on startup

- Mixed usage of sensor types:
  - DS18B20     ±0.5°C accuracy from -10°C to +85°C 
  - DS18S20     ±0.5°C accuracy from -10°C to +85°C (obsolete)
  - DS1822      ±2.0°C accuracy from -10°C to +85°C
  - DS28EA00 
  - MAX31850    ±2°C for temperatures -200°C to +1200 °C
  - DS1825  

&emsp;&emsp;&emsp;The latter two read type K thermocouples,
whereas all others are semiconductor sensors.

- Linearization for type K thermocouples according ITS-90 enables measurements at temperatures below -30 °C and above +600 °C

- Writes data to tab separated value table with 
ISO 8601 formatted date and time. This is compatible with python's pandas 
and plotly packages as well as with spreadsheet processing. 

- Logs temperature measurements with its own timer,
or, alternatively, records a single data frame when called 
by the Linux cron deamon. This example crontab line invokes a data frame recording every 15 minutes: 

&emsp;&emsp;*/15  * * * *    /home/user_name/bin/1-Wire-temperature-logger-RPi.pyw -q    >/dev/null 2>>/dev/null

- Another script provides graphical data analyzis and statistics.







Notes
-------
1. To use 1-Wire sensors with a Raspberry Pi, activate the 1-Wire bus 
via raspi-config. The default Raspberry Pi GPIO pin for 
1-Wire communication is GPIO4. Add a 4.7kΩ resistor 
between the data line and 3.3 volt. 

2. The 1-Wire bus can power sensors using 'external power'
(three wires) or 'parasite power' (two wires).
This script was only tested using external power.

1. To see the command line options use './1-Wire-temperature-logger-RPi.pyw -h'

2. Read the 'user settings' (lines 85 to 133) and modify these according to your needs.

3. The file name extension '.pyw' prevents the opening of a terminal window when running the script as a cron job. 

4. For advanced usage of 1Wire temperature sensors with the Linux kernel driver study [Timo Furrer's w1thermsenso package](https://pypi.org/project/w1thermsensor/). This package is not used here.



Images
-------

![Sensor chan](https://github.com/Ekkehard-Schulze/1wire-temperature-logger-RPi/blob/main/images/Raspi_with_1Wire_bus.jpg)

An eight-meter long 1-Wire bus cable with six DS18B20 sensors connected to a RaspberryPi3B+

was used to document mercury arc lamp usage in a lab for two years.

![Sensor chan](https://github.com/Ekkehard-Schulze/1wire-temperature-logger-RPi/blob/main/images/Raspi_with_typeK_thermocouples.jpg)

Four type K thermocouples connected via 1-Wire bus to a RaspberryPi3B+ using MAX31850 amplifiers

allow to measure temperatures ranging from -200°C to 1200°C.

![Sensor chan](https://github.com/Ekkehard-Schulze/1wire-temperature-logger-RPi/blob/main/images/plots_and_statistics_of_time_series.py_screenshot.webp)

Screenshot of data visualizing from the script plots_and_statistics_of_time_series.py.