import nmap
from datetime import datetime, timedelta
import asyncio
from models import db, DeviceData, PortInfo, SecurityRecommendation

nmap_path = [r"C:\Program Files (x86)\Nmap\nmap.exe",]
nm = nmap.PortScanner(nmap_search_path=nmap_path)

async def encryption_recommendation_engine(app, ip_address):
    with app.app_context():
        device = DeviceData.query.filter_by(ip_address=ip_address).first()
        if not device:
            print(f"No device found with IP: {ip_address}")
            return

        for port_info in device.ports:
            # Check if a recommendation already exists
            existing_recommendation = SecurityRecommendation.query.filter_by(
                device_ip=ip_address,
                port=port_info.port_number
            ).first()

            if existing_recommendation:
                # Update existing recommendation
                update_recommendation(existing_recommendation, device, port_info)
            else:
                # Create new recommendation
                new_recommendation = create_recommendation(device, port_info)
                db.session.add(new_recommendation)

        db.session.commit()

def update_recommendation(recommendation, device, port_info):
    recommendation.device_name = device.device_name
    recommendation.status = port_info.state
    recommendation.service = port_info.service
    update_recommendation_details(recommendation, port_info)

def create_recommendation(device, port_info):
    recommendation = SecurityRecommendation(
        device_name=device.device_name,
        device_ip=device.ip_address,
        port=port_info.port_number,
        status=port_info.state,
        service=port_info.service
    )
    update_recommendation_details(recommendation, port_info)
    return recommendation

def update_recommendation_details(recommendation, port_info):
    # Determine if encryption is needed and what type
    if port_info.service in ['http', 'ftp', 'telnet']:
        recommendation.encryption_needed = True
        recommendation.certificate_required = True
        recommendation.current_encryption = 'None'
        recommendation.current_state = f'Unencrypted {port_info.service.upper()}'
        recommendation.recommendation = f'Install SSL certificate and switch to {port_info.service.upper()}S'
    elif port_info.service in ['https', 'ftps', 'ssh']:
        recommendation.encryption_needed = True
        recommendation.certificate_required = True
        # check if the current TLS is set properly and certs are installed for port 443 and others
        recommendation.current_encryption = 'SSL/TLS'
        recommendation.current_state = f'Encrypted {port_info.service.upper()}'
        recommendation.recommendation = 'Ensure SSL/TLS certificate is up to date'
    else:
        recommendation.encryption_needed = False
        recommendation.certificate_required = False
        recommendation.current_encryption = 'Unknown'
        recommendation.current_state = f'Unknown service on port {port_info.port_number}'
        recommendation.recommendation = 'Investigate service and determine if encryption is needed'

    recommendation.action_taken = 'Pending'
    recommendation.status = 'Under Investigation'

def determine_device_type(product):
    common_devices = {
        "camera":0,
        "TV":0,
        "speaker":0,
        "printer":0,
        "Lamp":0,
        "iOS":0,
        "windows":0
    }

    if product:
        port_info_words = product.split()
        for word in port_info_words:
            for device in common_devices:
                if device.lower() in word.lower():  # Case-insensitive match
                    common_devices[device] += 1
            
            if word.lower() in ['cam', 'dashcam', 'webcam']:
                common_devices["camera"] += 1

            if word.lower() in ['FireTV']:
                common_devices["TV"] += 1


    max_device = max(common_devices, key=common_devices.get)

    if common_devices[max_device] > 0:
        return max_device
    else:
        return "Unknown"
            
async def scan_device(app, ip_address):
    print(f"Starting Nmap scan for {ip_address}...")
    try:
        #scan_data = nm.scan(hosts=ip_address, arguments='-n -Pn -sS -p 80,443 -T5 -v -A')
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
            port_lt=[]
            # Update device_type and product
            if 'tcp' in host_info:
                
                for port, port_info in host_info['tcp'].items():
                    if port not in port_lt:
                        port_lt.append(port)

                for port, port_info in host_info['tcp'].items():
                    if 'product' in port_info and port_info['product']:
                        device.product = port_info['product']
                        device.device_type = determine_device_type(port_info['product'])
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
            if len(port_lt)!=0:    
                device.open_ports=port_lt[:]
            db.session.commit()
        print(f"Nmap scan completed for {ip_address}")
        print("########################################################################################################################################")
        await encryption_recommendation_engine(app, ip_address)
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