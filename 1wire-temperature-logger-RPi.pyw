#!/usr/bin/env python3
# pylint: disable=line-too-long
# pylint: disable=invalid-name

# flake8 --ignore=F541,E501 "1wire-temperature-logger-RPi.pyw"

'''
   1wire-temperature-logger-RPi.pyw uses

   the Linux kernel driver for sensor readings

   of 1-Wire bus temperature sensors.

   It was tested and productively used in a lab

   environment for years with RaspberryPi 3 and

   RaspberryPi 4. The sensors tested were

   DS18B20 (6 pieces) and MAX31850 (4 pieces, with type

   K thermocouples).

   The 1-Wire bus alows many temperature sensors on

   a single bus with many meter long cable connections.

   The sensors are auto-discovered by the kernel

   during startup and all read out by this script.

   Different types of sensors can be used together

   on the same bus.

   This script logs data from all attached

   1Wire temperature sensors to a .tsv file.

   The 1-Wire bus can power sensors using 'external power'

   (three wires) or 'parasite power' (two wires).

   This code was only tested using the external power.




  This script can iterate unlimited periodic measurements.

  Alternatively, it can be used for a single dataframe reading

  triggered by the crontab deamon. The latter is recomendet

  for indefinite measurements with larger time intervals.


# crontab entry used to trigger a single data logging event every 15 minutes:
# -------------------
# Min hour day month weekday
# quarter-hourly logging of a data frame
*/15  * * * *    /home/user_name/bin/1wire-temperature-logger-RPi.pyw -q    >/dev/null 2>>/dev/null


   The default Raspberry Pi GPIO pin for 1-Wire communication is

   GPIO4 (physical pin 7), but you can use other pins by enabling

   the interface in /boot/config.txt and specifying a gpiopin.

   You'll need a pull-up resistor (typically 4.7kΩ) between the data line and 3.3V,

   connecting the sensor's DQ to GPIO4, GND to Pi's GND, and VDD to 3.3V.

'''

import os
import sys
import time
import glob
import traceback
import argparse
from datetime import datetime, timezone

# ---------------------- user settings --------------------------

sensor_name_translation = {  # used in a past project to generate explicit column names
    # 'DS159': "SZX12_R",    # given here as an example
    # 'DS198': "ImagerZ1",   # replace these names with your own names and un-comment
    # 'DS111': "M165FC",     # your edited lines
    # 'DS74':  "Lumar",
    # 'DS206': "Axioplan2",
    # 'DS140': "SZX12_L",
}

USE_UTC_time = True  # otherwise local time  (with or without UTC offset indication) is used
USE_LOCAL_time_with_UTC_offset = False # otherwise UTC time or local time without ISO8601 offset is used

log_every_n_seconds = 15  # default value, may get changed by command line argument

LOGGER_NAME = '1wire_logger_1'

write_log_data_to_file = True  # may get changed by command line argument

LOG_FILE_NAME = '1wire-temperatures.tsv'  # if empty name comes from first sensor object

LOGGER_DATA_DIR = '~/1wire_logs'  # relative to user home
# LOGGER_DATA_DIR = r'/home/your_user_name/logged_data/1wire_logs'  # use absolute path for crontab jobs !!!
# LOGGER_DATA_DIR = './1wire_logs'  # relative to present dir


USE_SHORT_SENSOR_NAMES = True  # short format is like DS133, long is indicating the sensor type like DS18B20_159

VERBOSE = True  # print data to stdout

LOG_EXCEPTIONS_TO_FILE = False  # attention: if set to True, you get no backtraces on the terminal, just the written file
                                # intended for crontab jobs and for long unsupervised runs
SEPARATOR = '\t'

LOG_EXCEPTIONS_FILE_NAME = 'expeptions_log.txt'

MAX_LOG_SIZE = None             # set if you want to limit the log file size
# MAX_LOG_SIZE = 100_000_000  # bytes

MAX_READ_ATTEMPTS = 30  # per sensor

LOGGER_ID_field_name = "Logger-id"

DATE_TIME_field_name = "Date_time"

ENCODING = "utf-8"

# ---------------------- end of user default settings --------------------------


class one_wire_temperature():
    ''' ----------- sensor 1wire specific code for logger  ------------
    stores list of responding 1Wire temperature sensors.
    Retrieves sensor names and measurements of all sensors at once.

    8 meter 3wire lab cable logging sequence of 7Q-TEK18B20 is e. g. #1-6: DS159, DS198, DS111, DS74, DS206, DS140

    Kernel driver doc: https://docs.kernel.org/w1/slaves/w1_therm.html
    interesting: Maxim MAX31850 thermoelement interface is supported in addition to silicon based sensors
    '''

    FAMILY_CODES = {

        "10": "DS18S20",
        "22": "DS1822",
        "28": "DS18B20",
        "3b": "MAX31850",  # could also be "DS1825", both are for type-K thermocouples
        "42": "DS28EA00",
    }

    def __init__(self):
        self.LOGGER_NAME = "1wire_logger"
        self.base_dir = '/sys/bus/w1/devices/'
        self.device_folder_list = []  # this list stores the sensors found
        for family_code in one_wire_temperature.FAMILY_CODES:
            self.device_folder_list += glob.glob(self.base_dir + family_code + '*')

    def generate_name(self, device_folderl):
        '''Uses 8-bit sum of hex-ID  to generate sensor names, NOT crc8. Saves the purpose as well
        Be aware that in rare cases can poduce collisions (two sensors with same name).
        This code is not warning for collisions, watch yourself.
        '''
        hex_id = device_folderl.split(os.sep)[-1].replace('-', '')
        family_code = device_folderl.split(os.sep)[-1][0:2]
        bbb = bytearray.fromhex(hex_id)
        if USE_SHORT_SENSOR_NAMES and family_code != "3b":
            sensor_name = "DS" + str(sum(bbb) % 256)
        elif  USE_SHORT_SENSOR_NAMES and family_code == "3b":
            sensor_name = "MAX" + str(sum(bbb) % 256)
        else:
            sensor_name = one_wire_temperature.FAMILY_CODES[family_code] + '_' + str(sum(bbb) % 256)
        return (
            sensor_name_translation[sensor_name]
            if sensor_name in sensor_name_translation
            else sensor_name
        )

    def thermoelement_type_K_linearization(self, temp):
        ''' physical linearization table for type K thermocouples based on ITS-90 standards
        required for measurement <-20°C and >+140°C
        Works by looking up the next lower 10°C value and then doing interpolation
        of the correction in the interval to the next higher 10°C step.
        '''
        K_linearization_lookup_table = (
            (-210, -63.79),
            (-200, -57.28),
            (-190, -51.18),
            (-180, -45.54),
            (-170, -40.29),
            (-160, -35.45),
            (-150, -30.97),
            (-140, -26.88),
            (-130, -23.13),
            (-120, -19.75),
            (-110, -16.68),
            (-100, -13.90),
            (-90, -11.43),
            (-80, -9.26),
            (-70, -7.32),
            (-60, -5.66),
            (-50, -4.23),
            (-40, -3.01),
            (-30, -1.99),
            (-20, -1.15),
            (-10, -0.50),
            (0, 0.00),
            (10, 0.38),
            (20, 0.67),
            (30, 0.85),
            (40, 0.95),
            (50, 0.99),
            (60, 0.98),
            (70, 0.93),
            (80, 0.85),
            (90, 0.80),
            (100, 0.77),
            (110, 0.76),
            (120, 0.80),
            (130, 0.92),
            (140, 1.06),
            (150, 1.29),
            (160, 1.55),
            (170, 1.84),
            (180, 2.17),
            (190, 2.51),
            (200, 2.84),
            (210, 3.12),
            (220, 3.41),
            (230, 3.65),
            (240, 3.86),
            (250, 4.02),
            (260, 4.14),
            (270, 4.20),
            (280, 4.25),
            (290, 4.24),
            (300, 4.21),
            (310, 4.16),
            (320, 4.08),
            (330, 3.98),
            (340, 3.87),
            (350, 3.72),
            (360, 3.55),
            (370, 3.37),
            (380, 3.17),
            (390, 2.97),
            (400, 2.75),
            (410, 2.50),
            (420, 2.25),
            (430, 1.98),
            (440, 1.71),
            (450, 1.41),
            (460, 1.11),
            (470, 0.82),
            (480, 0.50),
            (490, 0.18),
            (500, -0.15),
            (510, -0.49),
            (520, -0.81),
            (530, -1.16),
            (540, -1.48),
            (550, -1.80),
            (560, -2.14),
            (570, -2.46),
            (580, -2.78),
            (590, -3.08),
            (600, -3.38),
            (610, -3.67),
            (620, -3.97),
            (630, -4.24),
            (640, -4.49),
            (650, -4.74),
            (660, -4.96),
            (670, -5.19),
            (680, -5.36),
            (690, -5.56),
            (700, -5.71),
            (710, -5.86),
            (720, -5.97),
            (730, -6.07),
            (740, -6.15),
            (750, -6.20),
            (760, -6.26),
            (770, -6.26),
            (780, -6.24),
            (790, -6.23),
            (800, -6.16),
            (810, -6.09),
            (820, -5.98),
            (830, -5.86),
            (840, -5.72),
            (850, -5.53),
            (860, -5.35),
            (870, -5.11),
            (880, -4.87),
            (890, -4.59),
            (900, -4.30),
            (910, -3.97),
            (920, -3.64),
            (930, -3.28),
            (940, -2.87),
            (950, -2.47),
            (960, -2.01),
            (970, -1.53),
            (980, -1.05),
            (990, -0.53),
            (1000, 0.01),
            (1010, 0.58),
            (1020, 1.17),
            (1030, 1.79),
            (1040, 2.44),
            (1050, 3.11),
            (1060, 3.82),
            (1070, 4.54),
            (1080, 5.30),
            (1090, 6.09),
            (1100, 6.90),
            (1110, 7.75),
            (1120, 8.62),
            (1130, 9.53),
            (1140, 10.46),
            (1150, 11.43),
            (1160, 12.44),
            (1170, 13.47),
            (1180, 14.54),
            (1190, 15.65),
            (1200, 16.79),
            (1210, 17.97),
            (1220, 19.18),
            (1230, 20.43),
            (1240, 21.72),
            (1250, 23.04),
            (1260, 24.41),
            (1270, 25.81),
            (1280, 27.25),
            (1290, 28.73),
            (1300, 30.25),
            (1310, 31.80),
            (1320, 33.40),
            (1330, 35.03),
            (1340, 36.70),
            (1350, 38.40),
            (1360, 40.13),
            (1370, 41.90),
            (2000, 41.90),
        )

        i = 0
        while temp >= K_linearization_lookup_table[i][0]:
            i += 1
        i -= 1
        interval_for_interpolation = K_linearization_lookup_table[i + 1][1] - K_linearization_lookup_table[i][1]
        Fraction = (temp - K_linearization_lookup_table[i][0]) / (K_linearization_lookup_table[i + 1][0] - (K_linearization_lookup_table[i][0]))
        temp_linearized = temp + (Fraction * interval_for_interpolation) + K_linearization_lookup_table[i][1]

        return temp_linearized

    def _read_temp_raw(self, device_folderl):
        '''access and read device dir'''
        device_file = device_folderl + os.sep + 'w1_slave'
        with open(device_file, 'r', encoding=ENCODING) as f:
            lines = f.readlines()
        return lines

    def get_sensor_headers(self):
        '''get the name sequence of sensors covered by this object. Used for tsv/csv header'''
        header = ''
        for dd in self.device_folder_list:
            header += SEPARATOR + self.generate_name(dd)
        return header

    def get_measurement_str(self):
        '''get string of all sensors registered in this class.
        Write "ND" if reading fails'''
        out_str = ''
        for device_folder in self.device_folder_list:
            temp_c = "ND"
            lines = self._read_temp_raw(device_folder)
            counts = MAX_READ_ATTEMPTS
            while lines[0].strip()[-3:] != 'YES' and counts > 0:
                counts -= 1
                time.sleep(0.2)
                lines = self._read_temp_raw(device_folder)
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp_string = lines[1][equals_pos + 2:]
                temp_c = float(temp_string) / 1000.0
                if device_folder.split(os.sep)[-1][0:2] == "3b":  # Type K thermocouple
                    temp_c = self.thermoelement_type_K_linearization(temp_c)
            out_str += f'{SEPARATOR}{temp_c:.2f}'
        return out_str


def truncate_log_top(log_file_namel):
    '''Delete 10% top part of log data in order to limit file size.
    This prunes oldest data.'''
    if 0 < MAX_LOG_SIZE < os.stat(log_file_namel).st_size:
        with open(log_file_namel, encoding=ENCODING) as f:
            num_lines = len(f.readlines())
        n_lines_to_delete = int(0.1 * num_lines)
        print('lines deleted', n_lines_to_delete)
        bak_file_name = log_file_namel[:-4] + '.bak'
        if os.path.isfile(bak_file_name):
            os.remove(bak_file_name)
        os.rename(log_file_namel, bak_file_name)
        with open(bak_file_name, 'r', encoding=ENCODING) as oldfile, open(log_file_namel, 'w', encoding=ENCODING) as newfile:
            for n, l in enumerate(oldfile):
                if n == 0 or n > n_lines_to_delete:  # keep header, trucate top n data lines
                    newfile.write(l)
        os.remove(bak_file_name)


# --------- main  ----------------------------

# ------------ init  -------------------------------

parser = argparse.ArgumentParser(
    description="Ekkehard's 1wire temperature logger for RaspberryPi/Linux",
    epilog="Use -q for crontab jobs", formatter_class=argparse.RawTextHelpFormatter)  # init object

# ---------- define arguments
parser.add_argument('-s', '--log_every_n_seconds', default=str(log_every_n_seconds), help='Log every second')  # string
parser.add_argument("-nf", "--do_not_write_log_file", default=False, help="write no logfile", action="store_true")  # boolean argparse
parser.add_argument("-q", "--log_once", default=False, help="quits after single log", action="store_true")  # boolean argparse
# --------------  collect arguments
args = parser.parse_args()

# ------- store arguments
log_every_n_seconds = int(args.log_every_n_seconds, 0)
write_log_data_to_file = not args.do_not_write_log_file

# -------------------  log dir and exceptions file  ------------------------

LOGGER_DATA_DIR = os.path.expanduser(LOGGER_DATA_DIR) if "~" in LOGGER_DATA_DIR else LOGGER_DATA_DIR

if LOGGER_DATA_DIR != '' and write_log_data_to_file:
    os.makedirs(LOGGER_DATA_DIR, exist_ok=True)

if (not os.path.isfile(LOGGER_DATA_DIR + os.sep + LOG_EXCEPTIONS_FILE_NAME)) and LOG_EXCEPTIONS_TO_FILE:
    with open(LOGGER_DATA_DIR + os.sep + LOG_EXCEPTIONS_FILE_NAME, "a", encoding=ENCODING) as except_log_file:
        pass


try:  # -------- outer error handler loop -------------------

    # ----------------- init sensor objects if sensor presence is detected -----------------------------
    my_sensors = []  # list of sensor objects. Only sensors responding on init are listed here.

    my_sensors.append(one_wire_temperature())

    # --------------- collect all sensor names from sensor objects -------------------------------

    # sens_header = ''.join([SEPARATOR + sensor.get_sensor_headers()  for sensor in my_sensors])

    sens_header = ''.join([sensor.get_sensor_headers() for sensor in my_sensors])   # concat for multiple
                                                                                    # heterogeneous sensor objects
    if VERBOSE or write_log_data_to_file:
        print('\nSensor(s) ' + sens_header.replace(SEPARATOR, ' '))

    # ------------------- init log file  ------------------------

    if not os.path.isfile(LOGGER_DATA_DIR + os.sep + LOG_FILE_NAME) and write_log_data_to_file:     # test for file presence to assure a single header line
        with open(LOGGER_DATA_DIR + os.sep + LOG_FILE_NAME, "a", encoding=ENCODING) as log_file:    # use append mode to prevent deleting data. Append makes a new file if none exists.
            log_file.write(
                LOGGER_ID_field_name + SEPARATOR
                + DATE_TIME_field_name
                + sens_header + "\n"
            )
    # test if found log file header matches detected sensors
    elif write_log_data_to_file and os.path.isfile(LOGGER_DATA_DIR + os.sep + LOG_FILE_NAME):
        with open(LOGGER_DATA_DIR + os.sep + LOG_FILE_NAME, "r", encoding=ENCODING) as log_file:
            file_head_line = log_file.readline()
        if file_head_line != LOGGER_ID_field_name + SEPARATOR + DATE_TIME_field_name + sens_header + "\n":
            raise Exception('File header not matching sensors detected')

    # ----------------- init logger ----------------------------------
    starttime = time.monotonic()
    last_monotonic_log_time = time.monotonic() - log_every_n_seconds

    # -------------- startup message file logging --------------------------
    if write_log_data_to_file:
        print('\nData logging to ' + LOGGER_DATA_DIR + os.sep + LOG_FILE_NAME + ' in progess....')
    print('Terminate with Strg+C')

    # ------------------- main loop ------------------------------------

    while True:
        now_monotonic_time = time.monotonic()
        if now_monotonic_time - last_monotonic_log_time >= log_every_n_seconds:
            last_monotonic_log_time = now_monotonic_time

            if USE_UTC_time:
                date_str = datetime.strftime(datetime.now(timezone.utc), "%Y-%m-%dT%H:%M:%SZ")
            elif USE_LOCAL_time_with_UTC_offset:
                date_str = str(datetime.now().astimezone().replace(microsecond=0).isoformat())
            else:
                date_str = str(datetime.now().replace(microsecond=0).isoformat())  # local time

            sensor_measurements = ''.join([sensor.get_measurement_str() for sensor in my_sensors])

            logline = (
                LOGGER_NAME + SEPARATOR
                + date_str
                + sensor_measurements
            )

            if VERBOSE:
                print(logline)
            if write_log_data_to_file:
                with open(LOGGER_DATA_DIR + os.sep + LOG_FILE_NAME, "a", encoding=ENCODING) as log_file:
                    log_file.write(logline + "\n")
                if MAX_LOG_SIZE:
                    truncate_log_top(LOGGER_DATA_DIR + os.sep + LOG_FILE_NAME)

            if args.log_once:
                sys.exit(0)

            remaining_time = log_every_n_seconds - (time.monotonic() - last_monotonic_log_time)
            time.sleep(max(remaining_time, 0))  # smallest allowed number is 0

    # -------------------- end main loop --------------------------

except KeyboardInterrupt:
    sys.exit('')

except Exception as e:
    if LOG_EXCEPTIONS_TO_FILE:
        with open(LOGGER_DATA_DIR + os.sep + LOG_EXCEPTIONS_FILE_NAME, "a", encoding=ENCODING) as except_log_file:
            except_log_file.write('\n' + str(e) + ' in line ' + str(e.__traceback__.tb_lineno) + '\n')
            except_log_file.write('-' * 70 + '\n')
            except_log_file.write(traceback.format_exc())
        if str(e) == 'File header not matching sensors detected':
            raise
    else:
        raise
