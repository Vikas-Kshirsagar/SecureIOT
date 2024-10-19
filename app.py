from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import PacketData, DeviceData, PortInfo, db
from sniffing import start_sniffing, process_packet
import threading
from datetime import datetime
import asyncio
from nmap_scanner import scan_device, start_scan_for_new_devices

app = Flask(__name__)
app.config.from_object('config.Config')

db.init_app(app)

def update_device_data(packet_info):
    with app.app_context():
        device_name = packet_info.get('device_name') or 'Unknown'
        ip_address = packet_info['src_ip']
        mac_address = packet_info.get('eth_src')

        device = DeviceData.query.filter_by(ip_address=ip_address).first()
        if device:
            if device_name != 'Unknown':
                device.device_name = device_name
            if mac_address:
                device.mac_address = mac_address
            device.last_seen = datetime.utcnow()
        else:
            device = DeviceData.query.filter_by(mac_address=mac_address).first() if mac_address else None

            if device:
                # If device exists with this MAC, update its IP address
                device.ip_address = ip_address
                if device_name != 'Unknown':
                    device.device_name = device_name
                device.last_seen = datetime.utcnow()
            else:
                # If no device with this IP or MAC exists, create a new entry
                new_device = DeviceData(
                    device_name=device_name,
                    ip_address=ip_address,
                    mac_address=mac_address,
                )
                db.session.add(new_device)
                device = new_device
        
        try:
            db.session.commit()
            if not device:  # If it's a new device, trigger a scan
                asyncio.run_coroutine_threadsafe(scan_device(app, ip_address), asyncio.get_event_loop())
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

def run_async_tasks():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def run_with_context():
        await asyncio.sleep(30)
        await start_scan_for_new_devices(app)
    
    loop.create_task(run_with_context())
    loop.run_forever()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created before starting the app
    
    initialize_sniffer()  # Call the function to start the sniffer
    
    # Start the asynchronous nmap scanning task
    async_thread = threading.Thread(target=run_async_tasks)
    async_thread.daemon = True
    async_thread.start()
    
    app.run(debug=True)