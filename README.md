# BeagleBone Smart GPS & SMS Navigation System 🛰️📱

This project is a comprehensive GPS solution developed for **BeagleBone Black/Green**. It provides a full suite of location-based services, from raw NMEA data parsing to advanced navigation math and remote SMS reporting using SIM808/GSM modules.

## 🌟 Project Components

The system is divided into three main functional modules:

1.  **Core Tracking:** Real-time extraction of decimal coordinates, altitude, and synchronized local time from satellite data.
2.  **Smart Navigation:** Implementation of the **Haversine Formula** to calculate the distance (meters) and bearing (compass direction) to any target destination.
3.  **SMS Integration:** A remote reporting system that sends current location, time, and status to a mobile phone via AT commands.

## 🛠️ Hardware Setup
- **Microcontroller:** BeagleBone Black / Green.
- **GPS/GSM Module:** SIM808 or equivalent (connected via UART).
- **BeagleBone Pins:**
  - **TX:** `P9_24` (UART1_TXD)
  - **RX:** `P9_26` (UART1_RXD)
- **Baud Rates:** 9600 (GPS) / 115200 (Modem).

## 🚀 Installation & Usage

### Prerequisites
Install the required Python library:
```bash
pip install pyserial
Running the Modules
For basic tracking: python GPS_Core.py

For navigation to a target: python GPS_Navigation.py

For sending location via SMS: python GPS_SMS_Alert.py

⚙️ Features & Logic
Local Time Sync: Automatically adjusts UTC satellite time to your local timezone (e.g., UTC+3).

Automatic Pin Muxing: Uses config-pin to ensure UART is ready on boot.

Fail-safe SMS: Includes a SIM PIN check and prompt detection (>) for reliable messaging.

Navigation Accuracy: Uses spherical trigonometry for precise azimuth (Bearing) calculations.

📜 License
Open-source under MIT License. Feel free to contribute!
