:: use windows client to download and display data

set log_file_name=1wire_temperature_log.tsv
set log_file_dir=/home/es/logged_data/1wire_logs

:: set computer=10.4.233.185 &::DNS name is: schultzepi.cyanolab.biologie.privat
set computer=schultzepi.cyanolab.biologie.privat

scp es@%computer%:%log_file_dir%/%log_file_name% .



:: plot in browser
::"C:\Users\eschulz\AppData\Roaming\Microsoft\Windows\SendTo\plotly_time_series_logs.py"  MHZ_19_CO2_log.tsv
"%AppData%\Microsoft\Windows\SendTo\plotly_time_series_logs.py"  %log_file_name%


::del %log_file_name%
::------------------