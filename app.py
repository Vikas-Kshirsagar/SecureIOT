from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import PacketData, db
from sniffing import start_sniffing, process_packet
import threading
from scapy.all import *

app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize SQLAlchemy
db.init_app(app)

def packet_callback(packet):
    packet_info = process_packet(packet)
    if packet_info:
        with app.app_context():
            new_packet = PacketData(
                src_ip=packet_info["src_ip"],
                dest_ip=packet_info["dest_ip"],
                protocol=str(packet_info["protocol"]),
                port=packet_info["port"],
                packet_data=str(packet_info["packet_data"])
            )
            db.session.add(new_packet)
            db.session.commit()
        
        print(f"Device Name: {packet_info['device_name']}")
        print(f"IP: {packet_info['src_ip']}")
        print(f"dst: {packet_info['dest_ip']}")
        print(f"proto: {packet_info['protocol']}")
        print(f"sport: {packet_info['port']}")
        print(hexdump(packet_info['packet_data']))

def initialize_sniffer():
    sniffer_thread = threading.Thread(target=start_sniffing, args=(packet_callback,))
    sniffer_thread.daemon = True
    sniffer_thread.start()

@app.route('/')
def index():
    packets = PacketData.query.all()
    return f"Captured {len(packets)} packets."

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created before starting the app
    
    initialize_sniffer()  # Call the function to start the sniffer
    app.run(debug=True)