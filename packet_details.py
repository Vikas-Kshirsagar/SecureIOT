from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models import db, PacketData, CollectedInfo
import base64
import re

def extract_credentials_from_payload(payload):
    """
    Extract base64 encoded credentials from packet payload.
    Returns tuple of (username, password) or (None, None) if not found.
    """
    auth_match = re.search(r'Authorization: Basic (\S+)', payload)
    if not auth_match:
        return None, None
        
    base64_value = auth_match.group(1)
    decoded_value = base64.b64decode(base64_value).decode('utf-8')
    print("base64_value --> ", decoded_value)

    # Extract password from payload
    username, password = re.split(':', decoded_value)
    return username, password

def analyzed_captured_packet(app, packet_info):
    """
    Analyze captured packet data and store relevant credential information.
    """
    if not packet_info.get('human_readable'):
        return
        
    with app.app_context():
        payload = packet_info['human_readable']
        username, password = extract_credentials_from_payload(payload)
        if username or password:
            new_packet = CollectedInfo(
            device_ip = packet_info.get('src_ip'),
            device_username=username,
            device_pass=password,
            severity='high',
            )
            try:
                db.session.add(new_packet)
                db.session.commit()
                print(f"Credentials recovered for device: {packet_info['src_ip']}")
            except Exception as e:
                print(f"Error creating notification: {str(e)}")
                db.session.rollback()
                return