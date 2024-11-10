# check_firmware.py
import requests
from bs4 import BeautifulSoup
import re

def check_latest_firmware(device_name, os_name):
    if 'D-Link' in device_name or 'D-Link' in os_name:
        print("D-link found.......")
        url = "http://support.dlink.com.au/Download/download.aspx?product=DCS-932L&type=Firmware"
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            firmware_pattern = re.compile(r'dcs932lb1.*?v[\d.]+\.bin', re.IGNORECASE)
            for link in soup.find_all('a', href=True):
                match = firmware_pattern.search(link['href'] + link.text)
                if match:
                    return match.group(0)  # Return the matched firmware version
            return "No new firmware version found."
        except requests.exceptions.RequestException as e:
            return f"Error checking firmware update: {e}"
        
    if 'Foscam' in device_name or 'Foscam' in os_name:
        print("Foscam found.......")
        url = "https://www.foscam.eu/attachments/FI8918W_Firmware"
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            firmware_pattern = re.compile(r'FI8918W Firmware\s*[\d.]+', re.IGNORECASE)
            for link in soup.find_all('a', href=True):
                match = firmware_pattern.search(link['href'] + link.text)
                if match:
                    return match.group(0)  # Return the matched firmware version
            return "No new firmware version found."
        except requests.exceptions.RequestException as e:
            return f"Error checking firmware update: {e}"
    else:
        return "Device not supported for firmware check."