from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import PacketData, DeviceData, db
from sniffing import start_sniffing, process_packet
import threading
from datetime import datetime

app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize SQLAlchemy
db.init_app(app)

def identify_device_type(packet_info):
    # This is a basic implementation and can be expanded with more sophisticated logic
    if packet_info.get('dport') == 554 or packet_info.get('sport') == 554:
        return "CCTV"
    elif packet_info.get('dport') in [80, 443, 8008, 8009] or packet_info.get('sport') in [80, 443, 8008, 8009]:
        return "Smart TV"
    elif packet_info.get('dport') in [1935, 1936] or packet_info.get('sport') in [1935, 1936]:
        return "Mobile Phone"
    elif packet_info.get('dport') in [22, 3389] or packet_info.get('sport') in [22, 3389]:
        return "Laptop/Computer"
    else:
        return "Unknown"

def update_device_data(packet_info):
    with app.app_context():
        device_name = packet_info.get('device_name') or 'Unknown'
        ip_address = packet_info['src_ip']
        mac_address = packet_info.get('eth_src')
        device_type = identify_device_type(packet_info)

        device = DeviceData.query.filter_by(mac_address=mac_address).first()
        if device:
            device.ip_address = ip_address
            if device_name != 'Unknown':
                device.device_name = device_name
            if device.device_type == 'Unknown':
                device.device_type = device_type
            device.last_seen = datetime.utcnow()
        else:
            new_device = DeviceData(
                device_name=device_name,
                ip_address=ip_address,
                mac_address=mac_address,
                device_type=device_type
            )
            db.session.add(new_device)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error updating device data: {str(e)}")

def packet_callback(packet):
    packet_info = process_packet(packet)
    if packet_info:
        with app.app_context():
            new_packet = PacketData(**packet_info)
            db.session.add(new_packet)
            db.session.commit()
        
        src_port = packet_info.get('sport', 'N/A')
        dst_port = packet_info.get('dport', 'N/A')
        print(f"Captured packet: {packet_info['src_ip']}:{src_port} -> {packet_info['dst_ip']}:{dst_port}")
        
        update_device_data(packet_info)

def initialize_sniffer():
    sniffer_thread = threading.Thread(target=start_sniffing, args=(packet_callback,))
    sniffer_thread.daemon = True
    sniffer_thread.start()

@app.route('/')
def index():
    packets = PacketData.query.all()
    devices = DeviceData.query.all()
    return f"Captured {len(packets)} packets. Tracked {len(devices)} devices."

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created before starting the app
    
    initialize_sniffer()  # Call the function to start the sniffer
    app.run(debug=True)