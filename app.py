from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from models import PacketData, DeviceData, PortInfo, SecurityRecommendation, db, User, Notification, CollectedInfo
from sniffing import start_sniffing, process_packet
from packet_details import analyzed_captured_packet
from check_firmware import check_latest_firmware
import threading
from datetime import datetime
import asyncio
from nmap_scanner import scan_device, start_scan_for_new_devices
from faker import Faker
from random import randint
import json

app = Flask(__name__, static_folder='static')
app.config.from_object('config.Config')

db.init_app(app)

def create_fake_users(total):
    fake = Faker()
    for i in range(total):
        user = User(
            username=fake.user_name(),
            age=randint(18, 100),
            email=fake.email(),
            phone=fake.phone_number(),
            address=fake.address()
        )
        db.session.add(user)
    db.session.commit()
    print(f'Created {total} fake users and added them to the database')

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
        if packet_info['src_ip'] in ['192.168.137.118', '192.168.137.100']:
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

@app.route('/users')
def users():
    return render_template('users.html')

@app.route('/api/users')
def get_users():
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'age': user.age,
        'phone': user.phone,
        'address': user.address,
        'created_at': user.created_at.isoformat() if user.created_at else None
    } for user in users])

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

@app.route('/api/device/<ip>/security')
def get_device_security(ip):
    recommendations = SecurityRecommendation.query.filter_by(device_ip=ip).all()
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

@app.route('/api/notifications')
def get_notifications():
    notifications = Notification.query.filter_by(is_read=False).order_by(Notification.created_at.desc()).all()
    return jsonify([{
        'id': n.id,
        'device_name': n.device_name,
        'device_ip': n.device_ip,
        'message': n.message,
        'created_at': n.created_at.isoformat()
    } for n in notifications])

@app.route('/api/notifications/<int:id>', methods=['POST'])
def mark_notification_read(id):
    notification = Notification.query.get(id)
    if notification:
        notification.is_read = True
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/traffic-stats')
def traffic_stats():
    # Safely count encrypted and unencrypted traffic
    encrypted_traffic = PacketData.query.filter_by(is_encrypted=True).count() or 0
    unencrypted_traffic = PacketData.query.filter_by(is_encrypted=False).count() or 0

    # Initialize device type dictionary with default zero values
    device_types = {}
    for device in DeviceData.query.all():
        device_type = device.device_type or "Unknown"  # Handle cases where device.type is None
        device_types[device_type] = device_types.get(device_type, 0) + 1

    # Prepare the response, ensuring no 'NoneType' is present
    return jsonify({
        'encrypted': encrypted_traffic,
        'unencrypted': unencrypted_traffic,
        'device_types': device_types
    })

@app.route('/information/<ip>')
def device_information(ip):
    return render_template('information.html')

@app.route('/api/device-info/<ip>')
def get_device_info(ip):
    info = CollectedInfo.query.filter_by(device_ip=ip).first()
    if info:
        return jsonify({
            'device_ip': info.device_ip,
            'username': info.device_username,
            'password': info.device_pass,
            'links': info.message
        })
    return jsonify({
        'device_ip': ip,
        'username': None,
        'password': None,
        'links': None
    })

@app.route('/api/device-hosts/<ip>')
def get_device_hosts(ip):
    # Get all unique connections to/from this IP
    packets = PacketData.query.filter(
        (PacketData.src_ip == ip) | (PacketData.dst_ip == ip)
    ).distinct(PacketData.src_ip, PacketData.dst_ip).all()
    
    # Create a set to store unique host IPs
    host_ips = set()
    for packet in packets:
        if packet.src_ip == ip:
            host_ips.add(packet.dst_ip)
        else:
            host_ips.add(packet.src_ip)
    
    # Get device information for each host
    hosts = []
    for host_ip in host_ips:
        device = PacketData.query.filter_by(src_ip=host_ip).first()
        host_info = {
            'ip': host_ip,
            'name': device.device_name if device else None,
            'last_seen': device.timestamp.isoformat() if device and device.timestamp else None
        }
        hosts.append(host_info)
    
    return jsonify(hosts)

@app.route('/check_firmware_update/<ip>', methods=['GET'])
def firmware_update_check(ip):
    try:
        # Query the database for the device name using the IP address
        device = DeviceData.query.filter_by(ip_address=ip).first()
        if not device:
            return jsonify({
                'status': 'error',
                'message': 'Device not found'
            }), 404
            
        result = check_latest_firmware(device.product, device.os_name)
        if result:
            return jsonify({
                'status': 'success',
                'data': result
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No firmware information available'
            }), 404
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
        

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
        create_fake_users(10)
    
    initialize_sniffer()  # Call the function to start the sniffer
    
    # Start the asynchronous nmap scanning task
    async_thread = threading.Thread(target=run_async_tasks)
    async_thread.daemon = True
    async_thread.start()
    
    app.run(debug=True)