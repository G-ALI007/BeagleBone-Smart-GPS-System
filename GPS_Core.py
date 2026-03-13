import subprocess
import serial
import time
from datetime import datetime, timedelta

subprocess.call(['config-pin', 'p9_24', 'uart'])
subprocess.call(['config-pin', 'p9_26', 'uart'])

ser = serial.Serial(port="/dev/ttyO1", baudrate=9600, timeout=1)
time.sleep(1)

# GPS initialization with AT commands
ser.write(b'AT+CGPSPWR=1\r')  # Power on GPS
time.sleep(0.5)
ser.write(b'AT+CGPSRST=0\r')  # Hot start
time.sleep(1)
ser.write(b'AT+CGPSOUT=255\r')  # Enable all NMEA output
time.sleep(0.5)

print("Waiting for GPS fix...")

# Initialize variables
date_str = ""
satellites_used = "0"
satellites_in_view = "0"

# Set your local UTC offset (e.g., +3 for Saudi Arabia)
UTC_OFFSET_HOURS = 3

try:
    while True:
        line = ser.readline().decode('ascii', errors='ignore').strip()

        if line.startswith("$GPRMC"):
            # Extract date from RMC sentence
            fields = line.split(',')
            if len(fields) > 9 and fields[9]:
                raw_date = fields[9]  # Format: ddmmyy
                day = raw_date[:2]
                month = raw_date[2:4]
                year = "20" + raw_date[4:]
                date_str = f"{year}-{month}-{day}"

        elif line.startswith("$GPGSV"):
            # Extract total number of satellites in view
            fields = line.split(',')
            if len(fields) > 3:
                satellites_in_view = fields[3]

        elif line.startswith("$GPGGA"):
            # Extract coordinates, fix status, satellites used, and altitude
            fields = line.split(',')
            if len(fields) > 9:
                utc_time = fields[1]  # Format: hhmmss.ss
                lat = fields[2]
                lat_dir = fields[3]
                lon = fields[4]
                lon_dir = fields[5]
                fix = fields[6]
                satellites_used = fields[7]
                altitude = fields[9]

                if lat and lon and utc_time:
                    # Convert latitude and longitude from NMEA to decimal degrees
                    lat_deg = float(lat[:2])
                    lat_min = float(lat[2:])
                    lon_deg = float(lon[:3])
                    lon_min = float(lon[3:])
                    lat_dd = lat_deg + (lat_min / 60.0)
                    lon_dd = lon_deg + (lon_min / 60.0)
                    if lat_dir == 'S':
                        lat_dd = -lat_dd
                    if lon_dir == 'W':
                        lon_dd = -lon_dd

                    # Convert UTC time to local time using fixed offset
                    if len(utc_time) >= 6 and date_str:
                        hour = int(utc_time[0:2])
                        minute = int(utc_time[2:4])
                        second = int(utc_time[4:6])
                        dt_utc = datetime.strptime(
                            f"{date_str} {hour}:{minute}:{second}", "%Y-%m-%d %H:%M:%S")
                        dt_local = dt_utc + timedelta(hours=UTC_OFFSET_HOURS)
                        local_time_str = dt_local.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        local_time_str = "Waiting for time"

                    fix_status = "Valid fix" if fix != '0' else "No fix"

                    # Print parsed GPS data
                    print(f"Local Time: {local_time_str}, Latitude: {lat_dd:.6f}, Longitude: {lon_dd:.6f}, "
                          f"Used Satellites: {satellites_used}, In View: {satellites_in_view}, "
                          f"Altitude: {altitude} m, Fix: {fix_status}")
        time.sleep(1)
except KeyboardInterrupt:
    print("\nTerminating program and closing serial port.")
    ser.close()
