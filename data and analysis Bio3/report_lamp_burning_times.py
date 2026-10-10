#!/usr/bin/env python3
# pylint: disable=trailing-whitespace
# pylint: disable=line-too-long
# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes
r'''  
HBO lamp on version, see 10 HBO specific lines in main()

Plotly time series data with ISO date format, e. g. HBO lamp Lux data or temperatures

This code can be used as a generic template for plotly time series plots.

Lines with wrongly formatted ISO dates are optionally removed by parser

Header coded time zone for fixed-time zone RTC, such as clk_UTC, clk_CET, clk_CEST
are optionally presented in legally valid local time.

Data may contain comments. Multiple header lines are not allowed.

https://plot.ly/python/time-series/

'''


import sys
import pandas as pd
from pathlib import Path
import time
import re
import datetime 
from dateutil import tz
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

convert_RTC_to_legal_local_time = True # True is not robust, fails on datetime formatting errors
parse_for_bad_datelines = False # my Circuit-python throwed a few bad dates before midnight. This search takes time!

                            # interactive plot legend comes in this order:
allsensor_options_default = ['TMP1','TMP2','TMP3','TMP4',
                             'ADT1','ADT2','ADT3','ADT4',       
                             'MLX','Mlx_temp', 'Mlx_ir_temp', 'BME_temp', 'DS3231_temp',
                             'BME_humidity',
                             'CO2',
                             'BME_pressure',
                             'Dum1',
                             'Lux', 
                             'BME_air',
                             'FrbW','delta_1hr', 'deltaT',                           # Freiburg Uni Wetter web scraper
                             'SZX12_R', 'ImagerZ1', 'M165FC', 'Lumar', 'Axioplan2', 'SZX12_L', # 1wire chain  lab optical room  
                             'Freiburg', 'Goslar', 'Holzminden', 'Goettingen',  # Umlaute in Plotly Namen nicht hinbekommen
                             ] + ["DS"+str(x) for x in range(0,256)]                 # add 256 options for fingerprinted DS18B20 Sensors
                             
do_not_use = ['BME_temp']                             
                             
#separate_y_scale_sensors =  ['BME_pressure', 'BME_humidity'] 
separate_y_scale_sensors =  ['BME_pressure','CO2'] 
                             
Date_time_field_name = "Date_time"

default_separator = "\t" 

default_title = "TSV log data"

clock_mode_prefix = "clk_"  # used to optionally read clock time zone UTC, CET, CEST from a speceal header

SECONDS_PER_HOURS = 60 * 60  # 3600 führt zu Rundungsfehlern, obwohl beide integer sind!


# name, value for ON
series_names = [
    ["SZX12_R", 28],
    ["SZX12_L", 28],
    ["ImagerZ1", 35],
    ["Axioplan2", 35],
    ["M165FC", 27.8],
    ["Lumar", 35],
]

ON_VAL = 1
OFF_VAL = 0



def bad_date_and_repeated_header_masker(logger_tsv_filel):
    '''masks badlyformatted iso dates. Used for my circuit-python logger'''
    date_pattern_c = re.compile(r'\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d')
    skiplinesl =[]
    toplines=True
    with open(logger_tsv_filel, encoding='utf-8-sig', errors="ignore") as f:
        lines = f.readlines()
    check_datetime = True if Date_time_field_name in lines[0] else False
    for ln,l in enumerate(lines):
        if l.startswith('#'):  # comment found, redundant with pandas df load comment =
            skiplinesl.append(ln)
        elif "logger-id" in l: 
                if toplines:
                    if ln>0: 
                        skiplinesl.append(ln-1) # leave last of multiple top header lines. This is required for re-starts in case the restart was done due to an observed sensor count failure (LED blinks)
                else:
                    skiplinesl.append(ln)
        else:
            toplines = False # first values found
            if check_datetime and parse_for_bad_datelines:
                if not re.search(date_pattern_c, l):
                    skiplinesl.append(ln)      
    return skiplinesl



def get_UTC_offset_of_logger_clock(logger_clock_time_zonel):
    ''' determines UTC offset_hours of logger clock from time zone '''
    if logger_clock_time_zonel == "UTC":
        offset_hours = 0
    elif  logger_clock_time_zonel == "CET":
        offset_hours = 1
    elif  logger_clock_time_zonel == "CEST":
        offset_hours = 2
    else:
        print("Time zone correction for "+logger_clock_time_zonel+" not implemented yet.")
        sys.exit(1)
    return offset_hours




def convert_fixed_clock_tz_to_legal_local(dfl):
    '''Attention: this is very sensitive for time formatting errors. Fails if pandas and plotly alone would have worked'''
    logger_clock_time_zone = None
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()    
    for label in dfl.columns:  # search time zone information in header
        if label.startswith(clock_mode_prefix):
            logger_clock_time_zone = label.split("_")[1] 
    if logger_clock_time_zone:
        offset_seconds = get_UTC_offset_of_logger_clock(logger_clock_time_zone) * SECONDS_PER_HOURS
    else:
        return # nothing to do, no timezone indicated
    dfl["Date_time"] = dfl[
        "Date_time"
    ].apply(  # change times series "unix-datetime" (in unix-seconds format, but with RTC either set to UTC, CET, CST) 
              # in dataframe to the actual 'now' = runtime legally valid local time. This is not writte to file.
              # strategy: calculate UTC seconds from RTC data by subtracting offset, then get real legal local time from UTC
        lambda lutime: (
            datetime.datetime.fromtimestamp(datetime.datetime.strptime(lutime, "%Y-%m-%d %H:%M:%S").timestamp()
               - offset_seconds
            ).replace(tzinfo=from_zone).astimezone(to_zone) 
        ).strftime(
            "%Y-%m-%d %H:%M:%S"   # plotly recignizes a time series plot automatically from the iso date format !
        )  # in meinem script plotly_temperature_logs.py war die explizite Zuordnung zu UTC-und Konversion zu TZ-local nicht notwendig, keine Ahnung warum dieselben Befehle hier nicht automatisch nach lokal konvertieren
    )
    return


def main():

    print("initializing...")

    allsensor_options = [x for x in allsensor_options_default if x not in do_not_use]

    #-------------------- file picker ------------------------
    if (len(sys.argv) < 2  or  len(sys.argv) > 2): # 2 is for one parameter , 1 means no argument given, 2 means one argument given
        from tkinter import Tk
        from tkinter.filedialog import askopenfilename
        Tk().withdraw()                      # we don't want a full GUI, so keep the root window from appearing
        logger_tsv_file  = askopenfilename(initialdir=os.getcwd(), title = "Select temperature logger .tsv file. Use -h for help in console mode.",filetypes = (("tsv files","*.tsv"),("csv files","*.csv"),("all files","*.*"))) # show an "Open" dialog box and return the path to the selected file
        if logger_tsv_file  == "":
            sys.exit() # Abort has been pressed
    else:
        if sys.argv[1] == '-h' or sys.argv[1] == '--help':
            print(__doc__)
            sys.exit()
        else:
            logger_tsv_file = sys.argv[1]

    #-------------------- read data and convert unix date   ----------------------------
    #  ----------------- find bad line numbers, such as repeated headers from logger re-starts
    print("loading...")
    skiplines = []


    skiplines = bad_date_and_repeated_header_masker(logger_tsv_file)
    
    df = pd.read_csv(logger_tsv_file, encoding='ansi', sep=None, comment='#', engine='python', skiprows=skiplines,  on_bad_lines="skip" )  

   
    
    if not Date_time_field_name in df.columns:
        print('Datum stamp "'+Date_time_field_name+'" is missing in tsv-data')
        print(df)
        sys.exit()

    
    if convert_RTC_to_legal_local_time:
        convert_fixed_clock_tz_to_legal_local(df)

    my_title = df['logger-id'][1] if 'logger-id' in df.columns else default_title        


    #--------- filter for HBO lamp on to normalized mock values, OFF to zero ----------
    for s in series_names:  # binarisation
        df[s[0]] = df[s[0]].apply(lambda x: ON_VAL if x > s[1] else OFF_VAL)

    # conversion to datetime
    df['Date_time'] = pd.to_datetime(df['Date_time'], format='%Y-%m-%d %H:%M:%S') # 2024-05-31 16:45:01

    print()
    for s in series_names:  # binarisation
        sum = df[s[0]].sum()/4
        print(f'{s[0]}: {sum}')


if __name__ == '__main__':
    main()





       