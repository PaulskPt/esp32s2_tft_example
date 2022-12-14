Introduction
============

This repo contains two examples to show how one could program the Adafruit ESP32-S2-TFT-Feather (prod nr: 5300).

These examples use the Adafruit_DisplayIO library. 

Example Version_1:
------------------

This script creates four Groups: 

- ba_grp for the battery;
- dt_grp for the date and time;
- ta_grp for the pr_id() and pr_author() functions;
- te_grp for the temperature.

The script uses global label objects: ba, dt, ta and te. 
These label objects will be used to actualize the label.text attribute from within the functions:
pr_id(), pr_author(), pr_bat() and get_time()

Displays on TFT display:

- ID of the microcontroller this script is running on
- Battery Voltage and charge percentage
- Temperature of connected sensor
- Date (yyyy-mm-dd) and time (hh:mm) from built-in RTC
- Details of the author

The built-in Realtime Clock (RTC) is set at start of the script with date and time received through a response of a request to the Adafruit IO Time Service (AIO TS).
Then, at intervals, currently 10 minutes, the script again receives date and time through a response of a request to the AIO TS. 
The script then updates the RTC.

The script also Blinks the normal internal (red) LED as well as the built-in NEOPIXEL.

Both example scripts contains a 'fail-safe' sensor connection:
If the temperature sensor is disconnected this script will continue to
try to reconnect to the sensor. If the sensor is connected again,
this script will continue to read the temperature data from the sensor.

Example Version_2:
------------------
This example adds .bmp images using the adafruit_imageload module. 
There are a few more groups in this script:

- logo1_grp and logo2_grp;
- ba_grp for the battery;
- dt_grp for the date and time;
- ta1_grp for the disp_id()
- ta2_grp for disp_author() functions;
- te_grp for the temperature.

Some function names have been changed. E.g.: 'pr_id' --> 'disp_id'.
At the start of this script blinka.bmp is shown. The blinka.bmp is also displayed at leaving the script
upon Ctrl+C (Keyboard interrupt).
An avatar.bmp image is shown in function disp_author(), depending on the value of the global boolean flag 'use_avatar'.
The .bmp files are in the folder /bmp.
In this script the way the pages are being displayed differs from the method used in exampe 'version_1'

Hardware requirements
=====================

- `Adafruit ESP32-S2-TFT-Feather <https://www.adafruit.com/product/5300>`
- `Adafruit TMP117 temperature sensor. <https://www.adafruit.com/product/4821>`
- `Adafruit Litium Ion Polymer Battery - 3.7v 500mAh. <https://www.adafruit.com/product/1578>` (not needed if you power from another source)
- a breadboard;
- a USB-A to USB-C cable;

Dependencies
=============
This example depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_

The script uses the following modules that are not in the CircuitPython core:

* dafruit_display_text
* adafruit_displayio_layout
* adafruit_imageload
* adafruit_register
* adafruit_lc709203f
* adafruit_ntp
* adafruit_requests
* adafruit_tmp117
* neopixel

The needed modules one can get by downloading the .zip file of ones choice at 
  '<https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/tag/20221101>'


You need also to personalize the values in the file secrets.py:

- WiFi SSID;
- WiFi Password;
- AIO Username;
- AIO Key;
- time zone (string, e.g.: 'America/New_York';
- tz_offset in seconds. e.g.: New York is UTC - 4 hours = 4 x 3600 = 14400 seconds.
  For New York the tz_offset value has to be a negative value: -14400;
- DEBUG_FLAG: '0' if you don't want debug output to the REPL. '1' if you want debug output to REPL;
- LOCAL_TIME_FLAG: '1' if you want the time to be your local time (zone). '0' if you want the UTC time displayed;
- AUTHOR1 ... AUTHOR3. For personal details e.g.:
  AUTHOR1 '(c) 2022 John';
  AUTHOR2 'Doe';
  AUTHOR3 'Github: @JDoe'.

Don't change the names of the 'Keys' in secrets.py, e.g. 'ADAFRUIT_IO_KEY'.

Automatic WiFi connection:
--------------------------
I added the .env file. In this file one needs to fill in ones 'WiFi SSID' and 'WiFi Password'
(the same as one puts in file secrets.py). When the file .env is present, CircuitPython
will automatically establish WiFi connection to the WiFi Access Point defined in .env .
When a WiFi connection has been established, the circuitpython status_bar will show an IP-address.
  

Documentation
=============
The documentation can be found in the subfolder 'docs' of this repo.
In this folder I added a REPL_output.txt file.
In the folder 'images' I put a screenshot of the VSCode Outline of this example script.
Added also a short video of the ESP32-S2-TFT-Feather and the TMP117 while this example script was running.

For a manual of the Adafruit ESP32-S2-TFT-Feather see: '<https://cdn-learn.adafruit.com/downloads/pdf/adafruit-esp32-s2-tft-feather.pdf>'


