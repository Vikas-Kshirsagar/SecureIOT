import nmap
from datetime import datetime, timedelta
import asyncio
from models import db, DeviceData, PortInfo, SecurityRecommendation
import ssl
import socket
from datetime import datetime

nmap_path = [r"C:\Program Files (x86)\Nmap\nmap.exe",]
nm = nmap.PortScanner(nmap_search_path=nmap_path)

def check_tls_certificate(host, port):
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        with socket.create_connection((host, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=None) as ssock:
                cert = ssock.getpeercert()

                if cert:
                    not_after = cert['notAfter']
                    not_after = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')

                    current_date = datetime.utcnow()
                    if current_date > not_after:
                        return "Certificate has expired!"
                    elif (not_after - current_date) < timedelta(days=30):
                        return f"Certificate will expire soon! Valid until {not_after}."
                    else:
                        return f"Certificate is valid until {not_after}."
                else:
                    return "Port is open, but no certificate installed."
    except ssl.SSLError as e:
        if "certificate verify failed" in str(e):
            return "Certificate verification failed: self-signed certificate or untrusted CA."
        elif "wrong version number" in str(e):
            return "SSL/TLS handshake failed: Protocol version mismatch."
        elif "no peer certificate" in str(e):
            return "No SSL/TLS certificate found on the server."
        else:
            return f"SSL error: {str(e)}"
    except ConnectionRefusedError:
        return f"Connection to {host}:{port} refused!"
    except socket.timeout:
        return f"Connection to {host}:{port} timed out."
    except Exception as e:
        return f"Error: {str(e)}"

def check_port_and_tls(host, port):
    try:
        with socket.create_connection((host, port), timeout=5):
            print(f"Port {port} is open, checking TLS certificate...")
            return check_tls_certificate(host, port)
    except ConnectionRefusedError:
        return f"Port {port} is closed on {host}."
    except socket.timeout:
        return f"Connection to {host}:{port} timed out."
    except Exception as e:
        return f"Error: {str(e)}"

async def encryption_recommendation_engine(app, ip_address):
    print(f"Starting encryption recommendation engine for IP: {ip_address}")
    
    with app.app_context():
        # Check if device exists
        device = DeviceData.query.filter_by(ip_address=ip_address).first()
        if not device:
            print(f"No device found with IP: {ip_address}")
            return

        # Check if port info exists for the device
        port_info_exists = PortInfo.query.filter_by(device_id=device.id).first()
        if not port_info_exists:
            print(f"No port information available for device {ip_address}. Skipping recommendation engine.")
            return

        # Get all ports for the device
        device_ports = PortInfo.query.filter_by(device_id=device.id).all()
        
        # Check if ports need updating based on last scan
        needs_update = False
        for port in device_ports:
            if (not port.last_scanned) or (device.last_scanned and port.last_scanned < device.last_scanned):
                needs_update = True
                break

        if not needs_update:
            print(f"Port information is up to date for device {ip_address}")
            return

        print(f"Updating recommendations for device {device.device_name} ({ip_address})")

        for port_info in device_ports:
            # Check if a recommendation already exists
            existing_recommendation = SecurityRecommendation.query.filter_by(
                device_ip=ip_address,
                port=port_info.port_number
            ).first()

            if existing_recommendation:
                update_recommendation(existing_recommendation, device, port_info)
            else:
                new_recommendation = create_recommendation(device, port_info)
                db.session.add(new_recommendation)

        try:
            db.session.commit()
            print(f"Successfully updated recommendations for {ip_address}")
        except Exception as e:
            print(f"Error committing recommendations: {str(e)}")
            db.session.rollback()

def update_recommendation(recommendation, device, port_info):
    recommendation.device_name = device.device_name
    recommendation.status = port_info.state
    recommendation.service = port_info.service
    update_recommendation_details(recommendation, port_info, device)

def create_recommendation(device, port_info):
    recommendation = SecurityRecommendation(
        device_name=device.device_name,
        device_ip=device.ip_address,
        port=port_info.port_number,
        status=port_info.state,
        service=port_info.service
    )
    update_recommendation_details(recommendation, port_info, device)
    return recommendation

def update_recommendation_details(recommendation, port_info, device):
    if port_info.service in ['http', 'ftp', 'telnet']:
        recommendation.encryption_needed = True
        recommendation.certificate_required = True
        recommendation.current_encryption = 'None'
        recommendation.current_state = f'Unencrypted {port_info.service.upper()}'
        
        secure_service = {
            'http': 'HTTPS',
            'ftp': 'FTPS',
            'telnet': 'SSH'
        }.get(port_info.service, f'{port_info.service.upper()}S')
        
        recommendation.recommendation = f'Install SSL/TLS certificate and switch to {secure_service}'
        
    elif port_info.service in ['https', 'ftps', 'ssh']:
        recommendation.encryption_needed = True
        recommendation.certificate_required = True
        recommendation.current_encryption = 'SSL/TLS'
        
        # Check TLS configuration
        tls_status = check_port_and_tls(device.ip_address, port_info.port_number)
        recommendation.current_state = tls_status
        
        # Set recommendations based on TLS status
        if "expired" in tls_status.lower():
            recommendation.recommendation = "URGENT: Replace expired SSL/TLS certificate"
        elif "will expire soon" in tls_status.lower():
            recommendation.recommendation = "Plan to renew SSL/TLS certificate before expiration"
        elif "verification failed" in tls_status.lower():
            recommendation.recommendation = "Replace self-signed certificate with one from a trusted CA"
        elif "handshake failed" in tls_status.lower():
            recommendation.recommendation = "Check and update SSL/TLS configuration"
        elif "no certificate" in tls_status.lower():
            recommendation.recommendation = "Install valid SSL/TLS certificate"
        elif "valid until" in tls_status.lower():
            recommendation.recommendation = "Certificate is properly configured"
        else:
            recommendation.recommendation = "Investigate SSL/TLS configuration"
            
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
            product_value=None
            # Update device_type and product
            if 'tcp' in host_info:
                
                for port, port_info in host_info['tcp'].items():
                    if port not in port_lt:
                        port_lt.append(port)

                for port, port_info in host_info['tcp'].items():
                    if 'product' in port_info and port_info['product']:
                        product_value = port_info['product']
                        device.product = product_value
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
                    port_obj.last_scanned = datetime.utcnow()

            device.last_scanned = datetime.utcnow()

            if not product_value:
                os_info = host_info.get('osmatch', [])
                if os_info and os_info[0]['osclass']:
                    os_class_details = os_info[0]['osclass']
                    if os_class_details[0]['type']:
                        device.device_name = os_class_details[0]['type']
                        device.device_type = os_class_details[0]['type']

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