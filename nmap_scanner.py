import nmap
from datetime import datetime, timedelta
import asyncio
from models import db, DeviceData, PortInfo

nmap_path = [r"C:\Program Files (x86)\Nmap\nmap.exe",]
nm = nmap.PortScanner(nmap_search_path=nmap_path)

def determine_device_type(port_info):
    common_ports = {
        80: "Web Server",
        443: "Web Server (HTTPS)",
        554: "IP Camera/Webcam (RTSP)",
        8080: "Web Server/Proxy",
        8554: "IP Camera/Webcam (RTSP)",
        9100: "Printer",
        21: "FTP Server",
        22: "SSH Server",
        23: "Telnet Server",
        25: "SMTP Server",
        53: "DNS Server",
        3306: "MySQL Database",
        3389: "Remote Desktop"
    }
    
    for port, info in port_info.items():
        if int(port) in common_ports:
            return common_ports[int(port)]
    
    return "Unknown"

async def scan_device(app, ip_address):
    print(f"Starting Nmap scan for {ip_address}...")
    try:
        #scan_data = nm.scan(hosts=ip_address, arguments='-n -Pn -sS -p 80,443 -v -A')
        scan_data = nm.scan(hosts=ip_address, arguments='-n -Pn -sS -pT:0-65535 -T5 -v -A')

        if ip_address not in nm.all_hosts():
            raise ValueError(f"No scan results found for {ip_address}. Host might be down or unreachable.")

        host_info = nm[ip_address]
        print("########################################################################################################################################")
        print("########################################################################################################################################")
        print("########################################################################################################################################")
        print("########################################################################################################################################")
        print("########################################################################################################################################")
        print("########################################################################################################################################")
        print("########################################################################################################################################")

        print("host_info", host_info)
        

        with app.app_context():
            device = DeviceData.query.filter_by(ip_address=ip_address).first()
            if not device:
                device = DeviceData(ip_address=ip_address)
                db.session.add(device)

            device.mac_address = host_info['addresses'].get('mac', 'Unknown')
            
            os_info = host_info.get('osmatch', [])
            if os_info:
                device.os_name = os_info[0]['name']
                device.os_accuracy = int(os_info[0]['accuracy'])

            uptime = host_info.get('uptime', {})
            if uptime:
                device.uptime = uptime.get('lastboot', 'Unknown')

            device.tcp_sequence_difficulty = scan_data['scan'][ip_address].get('tcpsequence', {}).get('difficulty', 'Unknown')

            # Update device_type and product
            if 'tcp' in host_info:
                device.device_type = determine_device_type(host_info['tcp'])
                for port, port_info in host_info['tcp'].items():
                    if 'product' in port_info:
                        device.product = port_info['product']
                        break  # Use the first product found

                for port, port_info in host_info['tcp'].items():
                    port_obj = PortInfo.query.filter_by(device_id=device.id, port_number=port, protocol='tcp').first()
                    if not port_obj:
                        port_obj = PortInfo(device_id=device.id, port_number=port, protocol='tcp')
                        db.session.add(port_obj)

                    port_obj.state = port_info['state']
                    port_obj.service = port_info.get('name', 'Unknown')
                    port_obj.version = port_info.get('version', 'Unknown')
                    port_obj.product = port_info.get('product', 'Unknown')
                    port_obj.extra_info = port_info.get('extrainfo', '')

            device.last_scanned = datetime.utcnow()
            db.session.commit()
        print(f"Nmap scan completed for {ip_address}")
        print("########################################################################################################################################")

    except Exception as e:
        print(f"Error scanning {ip_address}: {str(e)}")

async def start_scan_for_new_devices(app):
    while True:
        print("########################################################################################################################################")
        with app.app_context():
            session = db.session()
            try:
                unscanned_devices = session.query(DeviceData).filter(
                    (DeviceData.os_name.is_(None) & DeviceData.uptime.is_(None)) |
                    (DeviceData.last_scanned.is_(None)) | 
                    (DeviceData.last_scanned < datetime.utcnow() - timedelta(hours=1))
                ).all()
                for device in unscanned_devices:
                    device = session.merge(device)
                    await scan_device(app, device.ip_address)
                
                session.commit()
            except Exception as e:
                print(f"Error in start_scan_for_new_devices: {str(e)}")
                session.rollback()
            finally:
                session.close()
        
        await asyncio.sleep(30)  # Wait for 5 minutes before checking for new devices again