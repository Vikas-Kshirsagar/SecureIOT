from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class PacketData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    src_ip = db.Column(db.String(64))
    dest_ip = db.Column(db.String(64))
    protocol = db.Column(db.String(16))
    port = db.Column(db.Integer)
    packet_data = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, src_ip, dest_ip, protocol, port, packet_data):
        self.src_ip = src_ip
        self.dest_ip = dest_ip
        self.protocol = protocol
        self.port = port
        self.packet_data = packet_data
