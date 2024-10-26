from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from models import PacketData, DeviceData, PortInfo, SecurityRecommendation, db
from sniffing import start_sniffing, process_packet
from packet_details import analyzed_captured_packet
import threading
from datetime import datetime
import asyncio
from nmap_scanner import scan_device, start_scan_for_new_devices

app = Flask(__name__, static_folder='static')
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
            '''
        else:
            #device = DeviceData.query.filter_by(mac_address=mac_address).first() if mac_address else None
            device = DeviceData.query.filter_by(mac_address=mac_address).first() if mac_address else None

            if device:
                # If device exists with this MAC, update its IP address
                device.ip_address = ip_address
                if device_name != 'Unknown':
                    device.device_name = device_name
                device.last_seen = datetime.utcnow()
            else:
            '''
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
        #print(f"Captured packet: {packet_info['src_ip']}:{src_port} -> {packet_info['dst_ip']}:{dst_port}")
        
        # add asynch to analyze packet 
        analyzed_captured_packet(app, packet_info)

        ## THIS SHOULD BE UPDATED LATER 
        #update_device_data(packet_info)

        ## REMOVE THIS FOR ALL TRAFFIC
        if packet_info['src_ip'] in ['192.168.137.240', '192.168.137.57', '192.168.137.102']:
            update_device_data(packet_info)
            #print(f"Table Updated: {packet_info['src_ip']}:{src_port} -> {packet_info['dst_ip']}:{dst_port}")

def initialize_sniffer():
    sniffer_thread = threading.Thread(target=start_sniffing, args=(packet_callback,))
    sniffer_thread.daemon = True
    sniffer_thread.start()

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/devices')
def devices():
    return render_template('devices.html')

@app.route('/packets')
def packets():
    return render_template('packets.html')

@app.route('/security')
def security():
    return render_template('security.html')

# API endpoints for getting data
@app.route('/api/devices')
def get_devices():
    devices = DeviceData.query.all()
    return jsonify([{
        'id': device.id,
        'name': device.device_name,
        'ip': device.ip_address,
        'mac': device.mac_address,
        'type': device.device_type,
        'os': device.os_name,
        'last_seen': device.last_seen.isoformat() if device.last_seen else None,
        'open_ports': device.open_ports
    } for device in devices])

@app.route('/api/packets/recent')
def get_recent_packets():
    packets = PacketData.query.order_by(PacketData.timestamp.desc()).limit(100).all()
    return jsonify([{
        'id': packet.id,
        'timestamp': packet.timestamp.isoformat(),
        'src_ip': packet.src_ip,
        'dst_ip': packet.dst_ip,
        'protocol': packet.ip_proto,
        'src_port': packet.sport,
        'dst_port': packet.dport,
        'is_encrypted': packet.is_encrypted
    } for packet in packets])

@app.route('/api/security/recommendations')
def get_security_recommendations():
    recommendations = SecurityRecommendation.query.all()
    return jsonify([{
        'id': rec.id,
        'device_name': rec.device_name,
        'device_ip': rec.device_ip,
        'port': rec.port,
        'service': rec.service,
        'current_state': rec.current_state,
        'recommendation': rec.recommendation,
        'status': rec.status
    } for rec in recommendations])

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