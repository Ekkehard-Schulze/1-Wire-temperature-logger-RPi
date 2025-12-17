#!/usr/bin/env python3

# pylint: disable=trailing-whitespace
# pylint: disable=line-too-long
# pylint: disable=invalid-name
# pylint: disable=too-many-lines
# pylint: disable=too-many-public-methods
# pylint: disable=import-error
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=consider-using-f-string
# pylint: disable=import-outside-toplevel
# pylint: disable=unspecified-encoding

# flake8 --ignore=F541,E501 "plots_and_statistics_of_time_series.py"

r'''

Plotly based interactive inspection of time series data

Check user settings below to control which tasks are executed by this script.

Implemented tasks are:
-----------------------
DO_interactive_browser_plot

SAVE_interactive_html_plot

SAVE_statistics_file

WRITE_timeline_png

WRITE_LOG_data_as_EXCEL_file

WRITE_LOG_data_as_open_doc_ods_file

accepted ISO8601 formtats versions are:

2025-12-02T15:25:00
2025-12-02T15:25:00+01:00
2025-12-02T15:25:00Z

'''

import re
import os
import sys
import datetime
import pathlib
import platform
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ----------- task control: select tasks to be done using True, use False unselect taskto have task not done -------

DO_interactive_browser_plot = True
SAVE_interactive_html_plot = True
SAVE_statistics_file = True
WRITE_timeline_png = False
WRITE_LOG_data_as_EXCEL_file = True
WRITE_LOG_data_as_open_doc_ods_file = True  # failed on large data sets

# ----------------- content definitions ------------------------
CHAR_CODING = "utf8"

OUTPUT_DIR_for_script = "output_files_of_py_script"  # you may set this to ""

STATS_file_separator = "\t"

parse_for_bad_lines = True
parse_for_bad_datelines = True

#allsensor_options = ['TMP1', 'TMP2', 'TMP3', 'TMP4']  # replaced by accept all, but Logger-id, Date_time, VBatt

BAT_voltage_field_name = 'Vbatt'

Date_time_field_name = "Date_time"

LOGGER_ID_field_name = "Logger-id"

default_separator = "\t"

ISO_DATE_TIME_format = "%Y-%m-%dT%H:%M:%S"

ISO_DATE_TIME_format_re = r'\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d'

default_title = "TSV log data"

# -----------------end of  content definitions ------------------------

SECONDS_PER_HOURS = 60 * 60  # 3600 führt zu Rundungsfehlern, obwohl beide integer sind!

no_sensor_list =[Date_time_field_name, BAT_voltage_field_name, LOGGER_ID_field_name]

if SAVE_interactive_html_plot:
    import plotly.offline


def add_prefix_to_file_stem(ppath, stem_prefixl):
    '''inserts a prefix into a path at the beginning of the file name'''
    return(
        #str(pathlib.Path(ppath).parent)
        #+ os.sep
        stem_prefixl
        + str(pathlib.Path(ppath).stem)
        + str(pathlib.Path(ppath).suffix)
    )


def add_prefix_to_file_stem_and_swap_extension(ppath, stem_prefixl, new_extension):
    '''inserts a prefix into a path at the beginning of the file name'''
    return(
        #str(pathlib.Path(ppath).parent)
        #+ os.sep
        stem_prefixl
        + str(pathlib.Path(ppath).stem)
        + new_extension
    )


def bad_date_and_repeated_header_masker(linesl):
    '''masks badlyformatted iso dates. Used for my circuit-python logger'''
    date_pattern_c = re.compile(ISO_DATE_TIME_format_re)
    skiplinesl = []
    toplines = True
    check_datetime = Date_time_field_name in linesl[0]  # bool
    for ln, l in enumerate(linesl):
        if l.startswith('#'):  # comment found, redundant with pandas df load comment =
            skiplinesl.append(ln)
        elif LOGGER_ID_field_name in l:
            if toplines:
                if ln > 0:
                    skiplinesl.append(ln - 1)  # leave last of multiple top header lines. This is required for re-starts in case the restart was done due to an observed sensor count failure (LED blinks)
            else:
                skiplinesl.append(ln)
        else:
            toplines = False  # first values found
            if check_datetime and parse_for_bad_datelines:
                if not re.search(date_pattern_c, l):
                    skiplinesl.append(ln)
    return skiplinesl


def main():

    print("initializing...")

    # -------------------- file picker ------------------------
    if (len(sys.argv) < 2 or len(sys.argv) > 2):  # 2 is for one parameter , 1 means no argument given, 2 means one argument given
        from tkinter import Tk
        from tkinter.filedialog import askopenfilename
        Tk().withdraw()                      # we don't want a full GUI, so keep the root window from appearing
        logger_tsv_file = askopenfilename(initialdir=os.getcwd(), title="Select temperature logger .tsv file. Use -h for help in console mode.", filetypes=(("tsv files", "*.tsv"), ("csv files", "*.csv"), ("all files", "*.*")))  # show an "Open" dialog box and return the path to the selected file
        if logger_tsv_file == "":
            sys.exit()  # Abort has been pressed
        # logger_tsv_file = logger_tsv_file.split('/')[-1]
        if platform.system() == 'Windows':
            logger_tsv_file = logger_tsv_file.replace("/", os.sep)

    else:
        if sys.argv[1] == '-h' or sys.argv[1] == '--help':
            print(__doc__)
            sys.exit()
        else:
            logger_tsv_file = sys.argv[1]

    # -------------------- read data  ----------------------------

    # ----------------- find bad line numbers, such as repeated headers from logger re-starts
    print("loading...")
    skiplines = []

    with open(logger_tsv_file, encoding='utf-8-sig', errors="ignore") as f:
        lines = f.readlines()

    skiplines = bad_date_and_repeated_header_masker(lines)

    df = pd.read_csv(logger_tsv_file, encoding=CHAR_CODING, sep=None, comment='#', engine='python', skiprows=skiplines, on_bad_lines="skip")

    accepted_sensors = []
    for field_name in df.columns:
        if field_name not in no_sensor_list and not "Unnamed" in field_name: # Unnamed is pandas name for empty column
            accepted_sensors.append(field_name)

    if Date_time_field_name not in df.columns:
        print('Datum stamp "' + Date_time_field_name + '" is missing in tsv-data')
        print(df)
        sys.exit()

    df[Date_time_field_name] = pd.to_datetime(df[Date_time_field_name])

    # ------- generate output dir ----------------------
    output_dir_path = str(pathlib.Path(logger_tsv_file).parent)
    if output_dir_path:
        output_dir_path += os.sep
    output_dir_with_path = output_dir_path + OUTPUT_DIR_for_script
    if output_dir_with_path and not os.path.exists(output_dir_with_path):
        os.makedirs(output_dir_with_path)    
    if output_dir_with_path:
        output_dir_with_path = output_dir_with_path + os.sep        

    # --------- data we need later --------------------
    last_datetime_str = str(df[Date_time_field_name].iloc[-1]).replace(":", "_")
    starttime = df[Date_time_field_name].iloc[0]
    endtime = df[Date_time_field_name].iloc[-1]
    log_duration = endtime - starttime
    my_title = df['logger-id'][1] if 'logger-id' in df.columns else default_title        
    
    # --------------- working on data -----------------------------------


    if SAVE_statistics_file:
        print("Writing statistics file...")
        prefix = last_datetime_str + "_statistics_"
        sfile_name_xlsx = output_dir_with_path + add_prefix_to_file_stem_and_swap_extension(logger_tsv_file, prefix, ".xlsx") 
        sfile_name_tsv = output_dir_with_path + add_prefix_to_file_stem_and_swap_extension(logger_tsv_file, prefix, ".tsv")                
        df_stats = df.describe()
        try:
            df_stats = df_stats.drop(Date_time_field_name, axis=1)
        except:
            pass
        df_stats['duration'] = log_duration
        try:
            df_stats.to_csv(sfile_name_tsv, index=True, sep=STATS_file_separator)
        except PermissionError:
            print('Failed to open statistics file.\nClose other application (e.g. Excel) blocking ' + sfile_name_tsv + '\n')
            input('Press Enter to quit.')
            sys.exit()         
        try:
            df_stats.rename(columns={'duration': 'duration [d]'}, inplace=True)
            df_stats.to_excel(sfile_name_xlsx, index=True)
        except PermissionError:
            print('Failed to open statistics file.\nClose other application (e.g. Excel) blocking ' + sfile_name_xlsx + '\n')
            input('Press Enter to quit.')
            sys.exit()        
        
        #write_statistics_file(df, sfile_name, accepted_sensors)

    if DO_interactive_browser_plot or SAVE_interactive_html_plot or WRITE_timeline_png:

        # ---------------------- plot battery voltage -----------------------------------------

        if BAT_voltage_field_name in df.columns:

            print(f"plotting {BAT_voltage_field_name}...")

            fig_bat = go.Figure(go.Scatter(x=df[Date_time_field_name], y=df[BAT_voltage_field_name], name=BAT_voltage_field_name))

            fig_bat.update_layout(title=my_title + ": Battery Voltage [mV]    (full: 4200, empty: 3600)", plot_bgcolor='rgb(230, 230,230)', showlegend=True)

            # fig_bat.show()

        # -----------plot temperature data violin plot.

        try:   # just in case something happens, we would still get the timeline plot
            print("plotting violin plot...")

            n = 0
            for sensor in accepted_sensors:
                if sensor in df.columns:
                    n += 1
            fig_violine = make_subplots(rows=1, cols=n)

            c = 0
            for sensor in accepted_sensors:

                if sensor in df.columns:
                    c += 1
                    fig_violine.append_trace(
                        go.Violin(
                            y=df[sensor],
                            name=sensor,
                            box_visible=True,
                            # line_color="black",
                            meanline_visible=True,
                        ), row=1, col=c
                    )  # plot second to last trace

            # fig_violine.update_layout(title='temperature logged',plot_bgcolor='rgb(230, 230,230)', showlegend=True)
            # fig_violine.update_layout(title=df[LOGGER_ID_field_name][1],plot_bgcolor='rgb(230, 230,230)', showlegend=True)

            # fig_violine.show()

        except:
            print('Violin plot failed')
            raise

        # -------------------- plot temperature data timeline plot ----------------------------

        print("plotting timeline...")
        # Create figure with secondary y-axis

        fig_time = make_subplots(specs=[[{"secondary_y": True}]])
        for sensor in accepted_sensors:
            # find and plot first track
            if sensor in df.columns:
                # fig_time.add_trace(go.Scatter(x = df[Date_time_field_name], y = df[sensor], name=sensor, hovertemplate="%{x|%d %b %Y, %H:%M:%S} %{y}"), secondary_y=False)
                fig_time.add_trace(go.Scatter(x=df[Date_time_field_name], y=df[sensor], name=sensor, hovertemplate="%{x|%d %b %Y, %H:%M} %{y}"), secondary_y=False)

        fig_time.update_layout(title=my_title, plot_bgcolor='rgb(230, 230,230)', showlegend=True)

        # ----------- all fig calculated, now generate output ----------------
        if SAVE_interactive_html_plot:
            print("Writing timeline plot to interactive html...")
            last_datetime = str(df[Date_time_field_name].iloc[-1]).replace(":", "_")
            stem_prefix = last_datetime + "_interactive_plot_"
            #f_html_name = str(pathlib.Path(logger_tsv_file).parent) + os.sep + stem_prefix + str(pathlib.Path(logger_tsv_file).stem) + ".html"
            f_html_name = output_dir_with_path + add_prefix_to_file_stem_and_swap_extension(logger_tsv_file, stem_prefix, ".html")                    
            plotly.offline.plot(fig_time, filename=f_html_name, auto_open=False)

        if DO_interactive_browser_plot:
            if BAT_voltage_field_name in df.columns:
                fig_bat.show()
            fig_violine.show()
            fig_time.show()
            
        if WRITE_timeline_png:
            print("Writing png...")
            last_datetime = str(df[Date_time_field_name].iloc[-1]).replace(":", "_")
            #stem_prefix = last_datetime + "_"
            #png_name = str(pathlib.Path(logger_tsv_file).parent) + os.sep + stem_prefix + str(pathlib.Path(logger_tsv_file).stem) + ".png"
            png_name = output_dir_with_path + add_prefix_to_file_stem_and_swap_extension(logger_tsv_file, last_datetime_str + "_", ".png")                    
            width_l=2880
            height_l=1620
            my_ytick_font_size = 33                                  # my default is 20 for sparse plots, use 16 for very many plots
            my_xtick_font_size = 33                                   # my default is 20 for sparse plots, use 16 for very many plots
            # my_yaxes_title_font_size = 20           
            fig_time.update_layout(xaxis=dict(tickfont = dict(size=my_xtick_font_size)), yaxis=dict(tickfont = dict(size=my_ytick_font_size)) )            
            fig_time.update_layout(width=width_l, height=height_l)
            #fig_time.update_layout(font=dict(family='Times New Roman',size=20,title=dict(font=dict(family='Ariel', size=33))))            
            fig_time.update_traces(marker={'size': 15})
            fig_time.update_layout(title_font_size=33)            
            fig_time.update_layout(legend_font_size=33)
            fig_time.update_yaxes(automargin=True, title_standoff = 33)            
            fig_time.write_image(png_name)             

    if WRITE_LOG_data_as_EXCEL_file or WRITE_LOG_data_as_open_doc_ods_file:
        if df[Date_time_field_name].dt.tz is not None:
            df[Date_time_field_name] = df[Date_time_field_name].dt.tz_localize(None)  # remove timezone info for Excel      

    if WRITE_LOG_data_as_EXCEL_file:
        print("Writing log data to EXCEL file...")        
        efile_name = output_dir_with_path + add_prefix_to_file_stem_and_swap_extension(logger_tsv_file, last_datetime_str + "_", ".xlsx")        
        df.to_excel(efile_name, index=False)
   
    if WRITE_LOG_data_as_open_doc_ods_file:
        print("Writing log data to open document file...")        
        efile_name = output_dir_with_path + add_prefix_to_file_stem_and_swap_extension(logger_tsv_file, last_datetime_str + "_", ".ods")        
        df.to_excel(efile_name, index=False)


if __name__ == '__main__':
    main()
