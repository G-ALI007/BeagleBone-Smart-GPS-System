import subprocess
import serial
import time
from datetime import datetime, timedelta
from math import radians, degrees, sin, cos, sqrt, atan2

subprocess.call(['config-pin', 'p9_24', 'uart'])
subprocess.call(['config-pin', 'p9_26', 'uart'])

ser = serial.Serial(port="/dev/ttyO1", baudrate=9600, timeout=1)
time.sleep(1)

# GPS initialization
ser.write(b'AT+CGPSPWR=1\r')
time.sleep(0.5)
ser.write(b'AT+CGPSRST=0\r')
time.sleep(1)
ser.write(b'AT+CGPSOUT=255\r')
time.sleep(0.5)

print("Waiting for GPS fix...")

UTC_OFFSET_HOURS = 3

target_lat = float(input("Enter target latitude: "))
target_lon = float(input("Enter target longitude: "))


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1_r, lon1_r = radians(lat1), radians(lon1)
    lat2_r, lon2_r = radians(lat2), radians(lon2)
    dlat, dlon = lat2_r - lat1_r, lon2_r - lon1_r
    a = sin(dlat/2)**2 + cos(lat1_r) * cos(lat2_r) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1_r = radians(lat1)
    lat2_r = radians(lat2)
    dlon_r = radians(lon2 - lon1)
    x = sin(dlon_r) * cos(lat2_r)
    y = cos(lat1_r) * sin(lat2_r) - sin(lat1_r) * cos(lat2_r) * cos(dlon_r)
    bearing = (degrees(atan2(x, y)) + 360) % 360
    return bearing


def bearing_to_direction(bearing):
    directions = ["N", "NE", "E", "SE",
                  "S", "SW", "W", "NW"]
    idx = int((bearing + 22.5) % 360 // 45)
    return directions[idx]


date_str = ""
satellites_used = "0"
satellites_in_view = "0"

try:
    while True:
        line = ser.readline().decode('ascii', errors='ignore').strip()

        if line.startswith("$GPRMC"):
            fields = line.split(',')
            if len(fields) > 9 and fields[9]:
                raw_date = fields[9]
                day, month, year = raw_date[:2], raw_date[2:4], "20" + \
                    raw_date[4:]
                date_str = f"{year}-{month}-{day}"

        elif line.startswith("$GPGSV"):
            fields = line.split(',')
            if len(fields) > 3:
                satellites_in_view = fields[3]

        elif line.startswith("$GPGGA"):
            fields = line.split(',')
            if len(fields) > 9:
                utc_time = fields[1]
                lat, lat_dir = fields[2], fields[3]
                lon, lon_dir = fields[4], fields[5]
                fix = fields[6]
                satellites_used = fields[7]
                altitude = fields[9]

                if lat and lon and utc_time:
                    lat_dd = float(lat[:2]) + float(lat[2:]) / 60.0
                    lon_dd = float(lon[:3]) + float(lon[3:]) / 60.0
                    if lat_dir == 'S':
                        lat_dd = -lat_dd
                    if lon_dir == 'W':
                        lon_dd = -lon_dd

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

                    distance_km = haversine(
                        lat_dd, lon_dd, target_lat, target_lon)
                    distance_m = distance_km * 1000

                    bearing_deg = calculate_bearing(
                        lat_dd, lon_dd, target_lat, target_lon)
                    direction_str = bearing_to_direction(bearing_deg)
                    print(f"Local Time: {local_time_str}, Latitude: {lat_dd:.6f}, Longitude: {lon_dd:.6f}, "
                          f"Used Satellites: {satellites_used}, In View: {satellites_in_view}, "
                          f"Altitude: {altitude} m, Fix: {fix_status}, "
                          f"Distance: {distance_m:.1f} m, Direction: {direction_str} ({bearing_deg:.1f})")
        time.sleep(1)
except KeyboardInterrupt:
    print("\nTerminating program and closing serial port.")
    ser.close()
