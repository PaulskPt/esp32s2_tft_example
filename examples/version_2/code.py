# SPDX-FileCopyrightText: 2022 Paulus Schulinck
#
# SPDX-License-Identifier: MIT
##############################
# Script functonalities:
# Display on TFT display:
# 1) ID of the microcontroller this script is running on
# 2) Battery Voltage and charge percentage
# 3) Temperature of connected sensor
# 4) Date (yyyy-mm-dd) and time (hh:mm) from built-in RTC
# 5) Author details (from secrets.py)
# Blinks the built-in red LED and blinks the build-in NEOPIXEL
# This script contains a 'fail-safe' sensor connection:
# If the temperature sensor is disconnected this script will continue to
# try to reconnect to the sensor. If the sensor is connected again,
# this script will continue to read the temperature data from the sensor.
#
# The built-in Realtime Clock (RTC) is set at start of the script with date and time
# received through a response of a request to the Adafruit IO Time Service (AIO TS).
# Then, at intervals, currently 10 minutes, the script again receives date and time
# through a response of a request to the AIO TS.
# The script then updates the RTC.
#
# About the test_page_layout
#
# Page # 0 = Logo1
# Page # 1 = Logo2
# Page # 2 = Temperature
# Page # 3 = ID
# Page # 4 = Author
# Page # 5 = Battery
# Page # 6 = Datetime
#
#This script currently has 21 functions
#######################################
import board
import busio
import terminalio
import digitalio
import microcontroller
import sys, gc
import time
import displayio
from adafruit_display_text import bitmap_label
from adafruit_lc709203f import LC709203F
import neopixel
import adafruit_tmp117
from adafruit_displayio_layout.layouts.page_layout import PageLayout

my_debug = False
use_wifi = True
use_ping = True
use_tmp_sensor = True
use_logo = True
use_avatar = True

# Pre-definition
def tag_adjust(s):
    pass

def scan_i2c():
    pass

id = board.board_id # 'adafruit_feather_esp32s2_tft'
print(f"\nThis script is running on an \'{id}\'")

blink_cycles = 2
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)

i2c = board.I2C()

tag_width = 18

scan_i2c()

TAG = tag_adjust("global:")

bat_sensor = LC709203F(i2c)

kbd_intr = False
ssid = None
password = None
ADAFRUIT_IO_USERNAME = None
ADAFRUIT_IO_KEY = None
pool = None
requests = None
tt = None
ip = None
s_ip = None
location = None
tz_offset = None
TIME_URL = None
rtc = None
tmp117 = None
temp_update_cnt = 0
old_temp = 0.00
temp_sensor_present = None
degs_sign = '' # chr(186)  # I preferred the real degrees sign which is: chr(176)
logo1_grp = None
logo2_grp = None
ba_grp = None
dt_grp = None
ta1_grp = None
ta2_grp = None
te_grp = None
tmp117 = None
author_lst = None
t0 = None
t1 = None
t2 = None
dt = None
ba = None
ta1 = None
ta2 = None
te = None

if use_wifi:
    import wifi
    import ssl
    import ipaddress
    import socketpool
    from secrets import secrets
    import adafruit_requests
    import adafruit_ntp
    from rtc import RTC
    ssid = secrets["ssid"]
    password = secrets["password"]

rtc = RTC()

weekdays = {0:"Monday", 1:"Tuesday",2:"Wednesday",3:"Thursday",4:"Friday",5:"Saturday",6:"Sunday"}

# release any currently configured displays
#displayio.release_displays()
start_t= time.monotonic()
start_0 = start_t # remember (and don't change this value!!!)
time_received = False

TX = board.TX
RX = board.RX
uart = None
#uart = busio.UART(TX, RX, baudrate=4800, timeout=0, receiver_buffer_size=151)  # board.RX, board.TX)

# built-in display
display = board.DISPLAY

# create and show main_group
main_group = displayio.Group()
display.show(main_group)

# create the page layout
test_page_layout = PageLayout(x=0, y=0)

if use_logo:
    img_lst = ["avatar", "blinka"]  # ["paulskpt", "blinka"]   # Note: these images are 100 x ca. 100 px
    from displayio import OnDiskBitmap, TileGrid
    logo1_grp = displayio.Group()
    logo2_grp = displayio.Group()
else:
    img_lst = None
    logo1_grp = None
    logo2_grp = None

tile_grid0 = None
tile_grid1 = None
tile_grid2 = None

page_dict = { 0: 'Logo1',
    1: 'Logo2',
    2: 'Temperature',
    3: 'ID',
    4: 'Author',
    5: 'Battery',
    6: 'Datetime',
}

def tag_adjust(s):
    global tag_width
    le = len(s)
    # print(f"tag_adjust(): param s= \'{s}\', len(s)= {le}, global tag_width= {tag_width}")
    if le >= tag_width:
        s2 = s[:tag_width]
    else:
        s2 = (s + ' '*(tag_width-le))
    # print(f"tag_adjust: returning \'{s2}\'")
    return s2

def scan_i2c():
    TAG= tag_adjust("scan_i2c(): ")
    if not my_debug:
        dev_list = []
    try:
        while not i2c.try_lock():
            i2c.try_lock()
            time.sleep(0.5)
        print(TAG+f"Start scan for connected I2C devices...")
        dev_list = i2c.scan()
        if dev_list is not None:
            le = len(dev_list)
            print("{}{} I2C device{} found:".format(' '*tag_width, le, "s" if le > 1 else ""))
            for _ in range(le):
                print("{}Device {:d} at address 0x{:02x}".format(' '*tag_width, _, dev_list[_]))
        i2c.unlock()
        print("{}End of i2c scan".format(' '*tag_width))
    except Exception as exc:
        raise

def get_page_name(page_index):
    le = len(page_dict)
    # print(f"get_page_number(): param page_index = {page_index}")
    if page_index >= 0 and page_index < le:
        if page_index in page_dict.keys():
            return page_dict[page_index]
    return ''

def disp_logo(choice):
    global logo_grp1, logo_grp2, tile_grid0, tile_grid1, tile_grid2, kbd_intr
    TAG= tag_adjust("disp_logo(): ")
    logo_lst = ["Logo1", "Logo2"]

    try:
        if choice >= 1 and choice <= 2:
            test_page_layout.show_page(page_name=logo_lst[choice-1])
            if my_debug:
                print(TAG+f"going to display image file: \'{img_lst[choice-1]}\'")
                print(TAG+"showing page: \'{}\'".format(get_page_name(test_page_layout.showing_page_index)))
            time.sleep(3)
    except OSError as e:
        print(TAG+f"Error: {e}")
    #except KeyboardInterrupt:
    #    kbd_intr = True

def blink():
    for _ in range(blink_cycles):
        led.value = True
        time.sleep(0.1)
        led.value = False
        time.sleep(0.5)

def blink_NEO():
    br = 50  # was 255
    pixel.brightness = 0.3
    for _ in range(blink_cycles):
        pixel.fill((br, 0, 0))
        time.sleep(0.5)
        pixel.fill((0, br, 0))
        time.sleep(0.5)
        pixel.fill((0, 0, br))
        time.sleep(0.5)
    pixel.fill((0, 0, 0))

def wifi_is_connected():
    global ip, s_ip
    ret = False

    ip = wifi.radio.ipv4_address

    if ip:
        s_ip = str(ip)
        le_s_ip = len(s_ip)

    if s_ip is not None and len(s_ip) > 0 and s_ip != '0.0.0.0':
        ret = True
    return ret

def create_groups():
    global ba_grp, dt_grp, ta1_grp, ta2_grp, te_grp, logo1_grp, logo2_grp, tile_grid0, tile_grid1, tile_grid2, ba, dt, ta1, ta2, te, test_page_layout, img_lst
    TAG= tag_adjust("create_groups(): ")
    tmp_grp = None
    k = ''
    if use_avatar:
        ax = 156
    else:
        ax = 120
    grp_dict = {
        'ba': {'nr_items': 1, 'scale': 2, 'anchor_point': (0.5, 0.5),
            'anchored_position': (display.width // 2, display.height // 2), 'vpos_increase': 0},
        'dt':  {'nr_items': 2, 'scale': 3, 'anchor_point': (0.5, 0.5), 'anchored_position': (120, 50), 'vpos_increase': 40},
        'ta1': {'nr_items': 3, 'scale': 3, 'anchor_point': (0.5, 0.5), 'anchored_position': (120, 40), 'vpos_increase': 30},
        'ta2': {'nr_items': 3, 'scale': 3, 'anchor_point': (0.5, 0.5), 'anchored_position': (ax,  40), 'vpos_increase': 30},
        'te':  {'nr_items': 2, 'scale': 3, 'anchor_point': (0.5, 0.5), 'anchored_position': (120, 40), 'vpos_increase': 40},
    }

    for _ in range(2):
        fn = "bmp/" + img_lst[_] + ".bmp" # Or use a general image: bmp/blinka.bmp"
        logo_img = OnDiskBitmap(fn)
        if _ == 0:
            # Titegrid to use in disp_author()
            tile_grid0 = TileGrid(bitmap=logo_img, pixel_shader=logo_img.pixel_shader)
            tile_grid0.x = 0 # display.width // 2 - logo_img.width // 2
            tile_grid0.y = 20
            #logo1_grp.append(tile_grid0)

            # Tielegrid to use in disp_logo()
            tile_grid1 = TileGrid(bitmap=logo_img, pixel_shader=logo_img.pixel_shader)
            tile_grid1.x = display.width // 2 - logo_img.width // 2
            tile_grid1.y = 20
            logo1_grp.append(tile_grid1)
        elif _ == 1:
            tile_grid2 = TileGrid(bitmap=logo_img, pixel_shader=logo_img.pixel_shader)
            tile_grid2.x = display.width // 2 - logo_img.width // 2
            tile_grid2.y = 20
            logo2_grp.append(tile_grid2)
    test_page_layout.add_content(logo1_grp, "Logo1")
    test_page_layout.add_content(logo2_grp, "Logo2")

    grp_lst = []
    for k in grp_dict.keys():
        grp_lst.append(k)
    if my_debug:
        print(TAG+f"grp_lst={grp_lst}")

    le = len(grp_lst)
    if le > 0:
        for i in range(le):
            tmp_grp = displayio.Group()
            tmp = []
            nr_items = grp_dict[grp_lst[i]]['nr_items']
            sc =       grp_dict[grp_lst[i]]['scale']
            vpi =      grp_dict[grp_lst[i]]['vpos_increase']
            if my_debug:
                print(TAG+f"nr_items= {nr_items}, scale= {sc}, vpos_increase= {vpi}")
            for j in range(nr_items):
                tmp.append(bitmap_label.Label(terminalio.FONT, text='', scale=sc))
                apt = grp_dict[grp_lst[i]]['anchor_point']
                if my_debug:
                    print(TAG+f"j= {j}, anchor_point= {apt}")
                tmp[j].anchor_point = apt
                apos = (grp_dict[grp_lst[i]]['anchored_position'][0], grp_dict[grp_lst[i]]['anchored_position'][1] + (j*vpi))
                if my_debug:
                    print(TAG+f"j= {j}, anchored_position= {apos}")
                tmp[j].anchored_position = apos
                tmp_grp.append(tmp[j])
            if grp_lst[i] == 'ba':        # used by disp_bat()
                ba = tmp
                ba_grp = tmp_grp
                test_page_layout.add_content(ba_grp, "Battery")
            elif grp_lst[i] == 'dt':      # used by disp_dt()
                dt = tmp
                dt_grp = tmp_grp
                test_page_layout.add_content(dt_grp, "Datetime")
            elif grp_lst[i] == 'ta1':      #  used by disp_id()
                ta1 = tmp
                ta1_grp = tmp_grp
                test_page_layout.add_content(ta1_grp, "ID")
            elif grp_lst[i] == 'ta2':      #  used by disp_author()
                ta2 = tmp
                if use_avatar:
                    tmp_grp.append(tile_grid0)  # add the tilegrid containing the avatar.bmp
                ta2_grp = tmp_grp
                test_page_layout.add_content(ta2_grp, "Author")
            elif grp_lst[i] == 'te':      # used by disp_temp()
                te = tmp
                te_grp = tmp_grp
                test_page_layout.add_content(te_grp, "Temp_sensor")

        # add it to the group that is showing on the display
        main_group.append(test_page_layout)

def disp_bat(warn):
    global ba
    TAG= tag_adjust("disp_bat(): ")
    if warn and my_debug:
        print(TAG+"LC709203F test")
        print(TAG+"Make sure LiPoly battery is plugged into the board!")
        print(TAG+"Battery IC version:", hex(bat_sensor.ic_version))
    s1 = "Battery:\n{:.1f} Volts \n{}%"
    s2 = "Battery: {:.1f} Volts, {}% charged"
    s3 = s1.format(bat_sensor.cell_voltage, bat_sensor.cell_percent)
    s4 = s2.format(bat_sensor.cell_voltage, bat_sensor.cell_percent)
    ba[0].text = s3
    test_page_layout.show_page(page_name="Battery")
    if not my_debug:
        print(TAG+"showing page: \'{}\'".format(get_page_name(test_page_layout.showing_page_index)))
    print(TAG+s4)

def setup():
    global lcd, uart, ssid, ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY, TIME_URL, location, tz_offset, author_lst
    TAG = tag_adjust("setup(): ")
    if my_debug:
        print(TAG+"...")

    # Get our username, key and desired timezone
    ADAFRUIT_IO_USERNAME = secrets["ADAFRUIT_IO_USERNAME"]
    ADAFRUIT_IO_KEY = secrets["ADAFRUIT_IO_KEY"]
    location = secrets.get("timezone", None)

    TIME_URL = "https://io.adafruit.com/api/v2/{:s}/integrations/".format(ADAFRUIT_IO_USERNAME)
    TIME_URL += "time/strftime?x-aio-key={:s}&tz={:s}".format(ADAFRUIT_IO_KEY, location)
    TIME_URL += "&fmt=%25Y-%25m-%25d+%25H%3A%25M%3A%25S.%25L+%25j+%25u+%25z+%25Z"
    #open_socket()

    author_lst = []
    s = ''
    for _ in range(3):
        if _ == 0:
            s = secrets.get("AUTHOR1", None)
        elif _ == 1:
            s = secrets.get("AUTHOR2", None)
        elif _ == 2:
            s = secrets.get("AUTHOR3", None)
        author_lst.append(s)
    # print(TAG+f"author_lst= {author_lst}")

    # This part copied from I:/PaulskPt/Adafruit_DisplayIO_FlipClock/Examples/displayio_flipclock_ntp_test2_PaulskPt.py
    lt = secrets.get("LOCAL_TIME_FLAG", None)
    if lt is None:
        use_local_time = False
    else:
        lt2 = int(lt)
        if my_debug:
            print("lt2=", lt2)
        use_local_time = True if lt2 == 1 else False

    if use_local_time:
        location = secrets.get("timezone", None)
        if location is None:
            location = 'Not set'
            tz_offset = 0
        else:
            tz_offset0 = secrets.get("tz_offset", None)
            if tz_offset0 is None:
                tz_offset = 0
            else:
                tz_offset = int(tz_offset0)
    else:
        location = 'Etc/GMT'
        tz_offset = 0

    if wifi_is_connected():
        print(TAG+f"WiFi already connected to: \'{ssid}\'")

    create_groups()

def disp_id():
    global ta1
    TAG= tag_adjust("disp_id(): ")

    t_lst = id.split('_') # ['Adafruit', 'feather', 'esp32s2', 'tft']
    if len(t_lst) > 0:
        t_lst[2] = t_lst[2] + ' ' + t_lst[3] # join 3rd and 4th element
        t_lst2 = []
        for _ in range(len(t_lst)-1):  # create new list t_lst2, less the 4th element of t_lst
            t_lst2.append(t_lst[_])
        t_lst = []
        # print(TAG+f"t_lst2= {t_lst2}") # ['Adafruit', 'feather', 'esp32s2 tft']
        if my_debug:
            print(TAG+"ID to display: \'", end='')
        le = len(t_lst2)
        for _ in range(le):
            ta1[_].scale = 3
            t = t_lst2[_]
            ta1[_].text = t
            if my_debug:
                if _ < le-1:
                    print(t+' ', end='')
                else:
                    print(t, end='')
        test_page_layout.show_page(page_name="ID")
        #test_page_layout.showing_page_name = "ID"

        if my_debug:
            print('\'', end='\n')
        if not my_debug:
            print(TAG+"showing page: \'{}\'".format(get_page_name(test_page_layout.showing_page_index)))
    #time.sleep(5)

def disp_author():
    global ta2, author_lst
    TAG= tag_adjust("disp_author(): ")
    # Update this to change the text displayed.
    if isinstance(author_lst, list):
        le = len(author_lst)
        if le > 0:
            #print(f"t_lst= {t_lst}")
            # Update this to change the size of the text displayed. Must be a whole number.
            # print(TAG, end='')
            for _ in range(le):
                ta2[_].scale = 2
                ta2[_].text = author_lst[_]
                # print(author_lst[_]+ " ", end='')
            # print('', end='\n')
            test_page_layout.show_page(page_name="Author")
            # tile_grid1.hidden=False
            if not my_debug:
                print(TAG+"showing page: \'{}\'".format(get_page_name(test_page_layout.showing_page_index)))
        #time.sleep(5)

def open_socket():
    global pool, requests
    pool = socketpool.SocketPool(wifi.radio)
    requests = adafruit_requests.Session(pool, ssl.create_default_context())

def free_socket():
    global pool, requests
    requests._free_sockets()

def wifi_connect():
    global ip, s_ip, pool, ssid, password
    TAG = tag_adjust("wifi_connect(): ")
    print(TAG+f"\nTrying to connect to \'{ssid}\'")

    print(TAG+f"Connecting to \'{ssid}\'")
    wifi.radio.connect(ssid=ssid, password=password)
    pool = socketpool.SocketPool(wifi.radio)
    connected = False
    s2 = ''

    wifi.radio.connect(ssid=ssid, password=password)

    if wifi_is_connected():
        connected = True
        s2 = ''
    else:
        s2 = "Not"

    print(TAG+f"{s2} connected to: \'{ssid}\'")

    if my_debug:
        print(TAG+f"s_ip= \'{s_ip}\'")

    if use_ping and connected:
        if not pool:
            pool = socketpool.SocketPool(wifi.radio)
        addr_idx = 1
        addr_dict = {0:'LAN gateway', 1:'google.com'}
        info = pool.getaddrinfo(addr_dict[addr_idx], 80)
        addr = info[0][4][0]
        print(TAG+f"Resolved google address: \'{addr}\'")
        ipv4 = ipaddress.ip_address(addr)
        for _ in range(10):
            result = wifi.radio.ping(ipv4)
            if result:
                print(TAG+"Ping google.com [%s]: %.0f ms" % (addr, result*1000))
                break
            else:
                print(TAG+"Ping no response")

def get_dt_AIO():
    global time_received, TIME_URL, kbd_intr
    TAG = tag_adjust("get_dt_AIO(): ")
    dst = ''
    if my_debug:
        print(TAG+"ip=", ip)
    if not wifi_is_connected():
        wifi_connect()
    if wifi_is_connected():
        gc.collect()
        try:
            open_socket()
            time.sleep(0.5)
            response = requests.get(TIME_URL)
            if response:
                n = response.text.find("error")
                if n >= 0:
                    print(TAG+f"AIO returned an error: {response}")
                else:
                    print(" " *tag_width+"-" * 47)
                    print(TAG+"Time= ", response.text)
                    print(" "*tag_width+"-" * 47)
                    time_received = True
                    s = response.text
                    s_lst = s.split(" ")
                    #print(f"s_lst= {s_lst}")
                    n = len(s_lst)
                    if n > 0:
                        dt1 = s_lst[0]
                        tm = s_lst[1]
                        yday = s_lst[2]
                        wday = s_lst[3]
                        tz = s_lst[4]
                        dst = -1  # we don't use isdst
                        yy =int(dt1[:4])
                        mo = int(dt1[5:7])
                        dd = int(dt1[8:10])
                        #print(f"tm= {tm}")
                        hh = int(tm[:2])
                        mm = int(tm[3:5]) # +mm_corr # add the correction
                        ss = int(round(float(tm[6:8])))
                        if my_debug:
                            print(f"ss= {ss}")
                        yd = int(yday) # day of the year
                        wd = int(wday)-1 # day of the week -- strftime %u (weekday base Monday = 1), so correct because CPY datetime uses base 0
                        #sDt = "Day of the year: "+str(yd)+", "+weekdays[wd]+" "+s_lst[0]+", "+s_lst[1][:5]+" "+s_lst[4]+" "+s_lst[5]
                        sDt = "Day of the year: {}, {} {} {} {} {}".format(yd, weekdays[wd], s_lst[0], s_lst[1][:5], s_lst[4], s_lst[5])
                        if my_debug:
                            print(TAG+"sDt=", sDt)
                        """
                            NOTE: response is already closed in func get_time_fm_aio()
                            if response:
                                response.close()  # Free resources (like socket) - to be used elsewhere
                        """
                        # Set the internal RTC
                        tm2 = (yy, mo, dd, hh, mm, ss, wd, yd, dst)
                        if my_debug:
                            print(TAG+f"tm2= {tm2}")
                        tm3 = time.struct_time(tm2)
                        if my_debug:
                            print(TAG+"dt1=",dt1)
                            print(TAG+"yy ={}, mo={}, dd={}".format(yy, mm, dd))
                            print(TAG+"tm2=",tm2)
                            print(TAG+"tm3=",tm3)
                        rtc.datetime = tm3 # set the built-in RTC
                        print(TAG+"built-in rtc synchronized with Adafruit Time Service date and time")
                        if my_debug:
                            print(TAG+" Date and time splitted into:")
                            for i in range(len(s_lst)):
                                print("{}: {}".format(i, s_lst[i]))
                response.close()
                free_socket()
        except OSError as exc:
            print(TAG+"OSError occurred: {}, errno: {}".format(exc, exc.args[0]), end='\n')
        except KeyboardInterrupt:
            kbd_intr = True

def disp_dt():
    global dt
    TAG = tag_adjust("disp_dt(): ")
    """
        Get the datetime from the built-in RTC
        After being updated (synchronized) from the AIO time server;
        Note: the built-in RTC datetime gives always -1 for tm_isdst
              We determine is_dst from resp_lst[5] extracted from the AIO time server response text
    """
    ct = rtc.datetime  # read datetime from built_in RTC
    # print(TAG+f"datetime from built-in rtc= {ct}")
    # weekday (ct[6]) Correct because built-in RTC weekday index is different from the AIO weekday
    #                                                                                                              yd
    sDt = "YearDay: {}, WeekDay: {} {:4d}-{:02d}-{:02d}, {:02d}:{:02d}, timezone offset: {} Hr, is_dst: {}".format(ct[7],
    #                yy     mo     dd     hh     mm            is_dst
    weekdays[ct[6]], ct[0], ct[1], ct[2], ct[3], ct[4], tz_offset, ct[8])
    #                               yy     mo     dd
    dt0 = "{}-{:02d}-{:02d}".format(ct[0], ct[1], ct[2])
    dt[0].text = dt0
    #tm = "{:02d}:{:02d}".format(ct[4], ct[5])
    #                           hh     mm
    tm = "{:02d}:{:02d}".format(ct[3], ct[4])
    dt[1].text = tm
    test_page_layout.show_page(page_name="Datetime")
    if not my_debug:
        print(TAG+"showing page: \'{}\'".format(get_page_name(test_page_layout.showing_page_index)))
        # print(TAG+f"date time from built-in rtc: {dt0}")
    else:
        print(TAG+f"date: {dt0}, time: {tm}")
    #time.sleep(5)

"""
  If the temperature sensor has been disconnected,
  this function will try to reconnect (test if the sensor is present by now)
  If reconnected this function sets the global variable temp_sensor_present
  If failed to reconnect the function clears temp_sensor_present
"""
def sensor_connect():
    global temp_sensor_present, tmp117, t0, t1, t2, kbd_intr
    TAG= tag_adjust("sensor_connect(): ")
    t = "temperature sensor found"
    temp_sensor_present = False
    tmp117 = None
    try:
        tmp117 = adafruit_tmp117.TMP117(i2c)
    except ValueError as exc:  # ValueError occurs if the temperature sensor is not connected
        pass
    except KeyboardInterrupt:
        kbd_intr = True
        return

    if tmp117 is not None:
        temp_sensor_present = True

    if temp_sensor_present:
        print(TAG+t)
        print(TAG+f"temperature sensor connected")
        t0 = "Temperature"
        t1 = degs_sign + "C"
        t2 = 27 * "_"
    else:
        print("no " + t)
        print(TAG+f"failed to connect temperature sensor")
        t0 = None
        t1 = None
        t2 = None

def disp_temp():
    global temp_sensor_present, old_temp, temp_update_cnt, te, tmp117, t0, t1, t2, kbd_intr
    TAG= tag_adjust("disp_temp(): ")
    nr = 'no reading'
    if temp_sensor_present:
        idx = 0
        if my_debug:
            print(TAG+f"type(tmp117)= {type(tmp117)}")
        try:
            temp = tmp117.temperature
            if temp is not None:
                if (temp != old_temp):  # Only update if there is a change in temperature
                    old_temp = temp
                t_lst = []
                t_lst.append(t0[:4]+':')
                t_lst.append(" {:5.2f} ".format(temp) + t1)
                print(TAG, end='')
                for _ in range(len(t_lst)):
                    te[_].text = t_lst[_]
                    if not my_debug:
                        print(f"{t_lst[_]}", end='')
                        #print("th[{}].text = {}".format(_, th[_].text))
                if not my_debug:
                    print('', end='\n')
                test_page_layout.show_page(page_name="Temp_sensor")
                if not my_debug:
                    print(TAG+"showing page: \'{}\'".format(get_page_name(test_page_layout.showing_page_index)))
                time.sleep(2)
                temp_update_cnt += 1
                return True
            else:
                t = ""
                te[0].text = t0
                te[idx].text = nr
                test_page_layout.show_page(page_name="Temp_sensor")
        except KeyboardInterrupt:
            kbd_intr = True
            return False
        except OSError as exc:
            print(TAG+"Temperature sensor has disconnected")
            t = ""
            temp_sensor_present = False
            tmp117 = None
            te[idx].text = nr  # clean the line  (eventually: t2)
    return False

def main():
    global start_t, use_logo
    TAG = tag_adjust("main(): ")
    interval_t = 600  # 10 minutes
    print(TAG+f"Date time sync interval set to: {int(float(interval_t//60))} minutes")
    delay = 3
    setup()
    avatar = 1
    blinka = 2
    dt_shown = False
    start = True
    cnt = 0
    stop = False

    while True:
        try:
            if start and use_logo:
                disp_logo(blinka) # (avatar or blinka)
                if kbd_intr:
                    stop = True
                    break
            print('-'*89)
            curr_t = time.monotonic()
            elapsed_t = int(float(curr_t - start_t))
            print(TAG+f"elapsed_t=  {elapsed_t}")
            print(TAG+f"elapsed_t % interval_t =  {elapsed_t % interval_t}")
            disp_id()
            # First sync datetime with AIO Time Service and update the built-in RTC
            if wifi_is_connected():
                tmod = elapsed_t % interval_t
                sync_dt = True if tmod <= 20 else False
                print(TAG+f"sync_dt= {sync_dt}")
                if (sync_dt):  # leave a margin  # was: if (lapsed_t >= 20 and ...):
                    if (not dt_shown):
                        #dt_shown = True
                        start_t = curr_t
                        gc.collect()
                        time.sleep(0.1)
                        get_dt_AIO()
                        if kbd_intr:
                            stop = True
                            break
                    else:
                        dt_shown = False
            time.sleep(delay)
            disp_bat(start)
            if start:
                start = False
            blink()
            time.sleep(delay)
            if use_tmp_sensor:
                if temp_sensor_present:
                    disp_temp()
                    if kbd_intr:
                        stop = True
                        break
                    gc.collect()
                    time.sleep(delay)
                else:
                    sensor_connect()
                    gc.collect()
                disp_dt()
                time.sleep(delay)
            blink_NEO()
            time.sleep(delay)
            disp_author()
            time.sleep(delay+2)
            cnt += 1
            if cnt > 999:
                cnt = 0
            # change page by next page function. It will loop by default
            test_page_layout.next_page()
        except KeyboardInterrupt:
            stop = True
            break
    if stop:
        print("KeyboardInterrupt. Exiting...")
        if use_logo:
            disp_logo(blinka) # display blinka
        sys.exit()

if __name__ == '__main__':
    main()
