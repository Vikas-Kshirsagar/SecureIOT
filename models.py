from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class PacketData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Ethernet Layer
    eth_dst = db.Column(db.String(17), nullable=False)  # MAC address format: XX:XX:XX:XX:XX:XX
    eth_src = db.Column(db.String(17), nullable=False)
    eth_type = db.Column(db.String(10), nullable=False)
    
    # IP Layer
    ip_version = db.Column(db.Integer, nullable=False)
    ip_ihl = db.Column(db.Integer)
    ip_tos = db.Column(db.Integer)
    ip_len = db.Column(db.Integer)
    ip_id = db.Column(db.Integer)
    ip_flags = db.Column(db.String(10))
    ip_frag = db.Column(db.Integer)
    ip_ttl = db.Column(db.Integer)
    ip_proto = db.Column(db.String(10), nullable=False)
    ip_chksum = db.Column(db.String(10))
    src_ip = db.Column(db.String(39), nullable=False)
    dst_ip = db.Column(db.String(39), nullable=False)
    
    # Transport Layer (TCP/UDP)
    sport = db.Column(db.Integer, nullable=True)
    dport = db.Column(db.Integer, nullable=True)
    
    # TCP specific
    tcp_seq = db.Column(db.BigInteger)
    tcp_ack = db.Column(db.BigInteger)
    tcp_flags = db.Column(db.String(20))
    
    # UDP specific
    udp_len = db.Column(db.Integer)
    udp_chksum = db.Column(db.String(10))
    
    # Payload
    payload_len = db.Column(db.Integer)
    payload = db.Column(db.Text)
    
    # Human-readable data
    human_readable = db.Column(db.Text)
    
    # Device information
    device_name = db.Column(db.String(255), nullable=False, default="Unknown")
    
    # Encryption status
    is_encrypted = db.Column(db.Boolean, default=False)
    
    # SSL/TLS information (if applicable)
    tls_version = db.Column(db.String(20))

    def __repr__(self):
        return f'<PacketData {self.id}: {self.src_ip}:{self.sport} -> {self.dst_ip}:{self.dport}>'


class DeviceData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(255), nullable=False, default="Unknown")
    ip_address = db.Column(db.String(39), nullable=False)
    mac_address = db.Column(db.String(17), nullable=True)  # MAC address format: XX:XX:XX:XX:XX:XX
    device_type = db.Column(db.String(50), nullable=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<DeviceData {self.device_name}: {self.ip_address} ({self.device_type})>'