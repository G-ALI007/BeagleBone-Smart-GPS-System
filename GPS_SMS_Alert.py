import serial
import time
from datetime import datetime, timedelta
import subprocess

# ------------ Configuration ------------
GPS_PORT = "/dev/ttyO1"      # GPS and SIM808 are on same port in this case
GPS_BAUDRATE = 9600
SIM_BAUDRATE = 115200
SERIAL_TIMEOUT = 2
UTC_OFFSET_HOURS = 3

# Initialize UART pins for BeagleBone Black (optional if already configured)
subprocess.call(['config-pin', 'p9_24', 'uart'])
subprocess.call(['config-pin', 'p9_26', 'uart'])

# Open serial port
ser = serial.Serial(GPS_PORT, baudrate=SIM_BAUDRATE, timeout=SERIAL_TIMEOUT)


def wait_for_prompt(prompt, timeout=5):
    start_time = time.time()
    buffer = ""
    while time.time() - start_time < timeout:
        if ser.in_waiting:
            buffer += ser.read(ser.in_waiting).decode(errors='ignore')
            if prompt in buffer:
                return True
        time.sleep(0.1)
    return False


def unlock_sim_if_needed():
    ser.write(b'AT+CPIN?\r')
    time.sleep(0.5)
    response = ser.read(100).decode(errors='ignore')
    print("[SIM Status]:", response.strip())
    if "SIM PIN" in response:
        pin = input("SIM requires PIN. Enter PIN code: ").strip()
        ser.write(f'AT+CPIN="{pin}"\r'.encode())
        time.sleep(2)
        print(ser.read(100).decode(errors='ignore'))


def initialize_gps():
    ser.write(b'AT+CGPSPWR=1\r')  # Power on GPS
    time.sleep(0.5)
    ser.write(b'AT+CGPSRST=0\r')  # Hot start
    time.sleep(1)
    ser.write(b'AT+CGPSOUT=255\r')  # Enable all NMEA output
    time.sleep(0.5)


def get_gps_coordinates():
    print("Waiting for GPS fix...")
    date_str = ""
    while True:
        line = ser.readline().decode('ascii', errors='ignore').strip()
        if line.startswith("$GPRMC"):
            fields = line.split(',')
            if len(fields) > 9 and fields[9]:
                raw_date = fields[9]
                day, month, year = raw_date[:2], raw_date[2:4], "20" + \
                    raw_date[4:]
                date_str = f"{year}-{month}-{day}"

        elif line.startswith("$GPGGA"):
            fields = line.split(',')
            if len(fields) > 9:
                utc_time = fields[1]
                lat = fields[2]
                lat_dir = fields[3]
                lon = fields[4]
                lon_dir = fields[5]
                fix = fields[6]
                if fix == '0':
                    continue  # No fix yet

                if lat and lon:
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

                    if len(utc_time) >= 6 and date_str:
                        hour = int(utc_time[0:2])
                        minute = int(utc_time[2:4])
                        second = int(utc_time[4:6])
                        dt_utc = datetime.strptime(
                            f"{date_str} {hour}:{minute}:{second}",
                            "%Y-%m-%d %H:%M:%S"
                        )
                        dt_local = dt_utc + timedelta(hours=UTC_OFFSET_HOURS)
                        local_time_str = dt_local.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        local_time_str = "Unknown Time"

                    return f"Time: {local_time_str}, Lat: {lat_dd:.6f}, Lon: {lon_dd:.6f}"
        time.sleep(0.5)


#               ✅ الخطأ #1 و #2: تصحيح المسافات البادئة
def send_sms(phone_number, message):
    try:
        print("[*] Initializing modem...")
        ser.write(b'AT\r')
        time.sleep(0.5)
        print(ser.read(100).decode(errors='ignore'))

        unlock_sim_if_needed()

        ser.write(b'AT+CMGF=1\r')  # Text mode
        time.sleep(0.5)
        print("[Text mode]:", ser.read(100).decode(errors='ignore'))

        command = f'AT+CMGS="{phone_number}"\r'
        ser.write(command.encode())

        if wait_for_prompt(">"):
            print("[*] Sending SMS...")
            ser.write(message.encode() + b"\x1A")  # Ctrl+Z
            time.sleep(5)
            response = ser.read(500).decode(errors='ignore')
            print("[Modem Response]:", response.strip())
            if "+CMGS:" in response:
                print("[✔️] SMS sent successfully.")
            else:
                print("[✖️] Failed to send SMS.")
        else:
            print("[!] Prompt '>' not received.")
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        ser.close()
        print("[*] Serial connection closed.")


# -------- Main --------
#               ✅ الخطأ #3: تصحيح الشرط الرئيسي
if __name__ == "__main__":
    number = input("Enter phone number (e.g., +9639xxxxxxxx): ").strip()
    initialize_gps()
    gps_message = get_gps_coordinates()
    print("[GPS]:", gps_message)
    send_sms(number, f"Hi, my location is: {gps_message}")
