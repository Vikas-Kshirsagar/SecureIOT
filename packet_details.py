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

def extract_hyperlinks(payload):
    """Extract hyperlinks from packet payload using regex."""
    # Pattern to match URLs (http/https)
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, payload)
    return urls

def analyzed_captured_packet(app, packet_info):
    """
    Analyze captured packet data and store relevant credential and hyperlink information.
    """
    if not packet_info.get('human_readable'):
        return
        
    with app.app_context():
        payload = packet_info['human_readable']
        username, password = extract_credentials_from_payload(payload)
        hyperlinks = extract_hyperlinks(payload)
        
        device_ip = packet_info.get('src_ip')
        
        try:
            # Find existing entry for this IP
            existing_entry = CollectedInfo.query.filter_by(
                device_ip=device_ip
            ).first()
            
            if existing_entry:
                # Update existing entry
                if username and password:
                    existing_entry.device_username = username
                    existing_entry.device_pass = password
                
                if hyperlinks:
                    # Append new hyperlinks to existing message
                    current_links = existing_entry.message or ''
                    new_links = '\n'.join(hyperlinks)
                    if current_links:
                        # Avoid duplicates by splitting and using set
                        existing_links = set(current_links.split('\n'))
                        all_links = existing_links.union(set(hyperlinks))
                        existing_entry.message = '\n'.join(all_links)
                    else:
                        existing_entry.message = new_links
                
                existing_entry.timestamp = datetime.utcnow()
                print(f"Updated existing entry for device: {device_ip}")
            else:
                # Create new entry
                new_entry = CollectedInfo(
                    device_ip=device_ip,
                    device_username=username,
                    device_pass=password,
                    message='\n'.join(hyperlinks) if hyperlinks else None,
                    severity='high'
                )
                db.session.add(new_entry)
                print(f"Created new entry for device: {device_ip}")
            
            db.session.commit()
            
        except Exception as e:
            print(f"Error updating/creating entry: {str(e)}")
            db.session.rollback()
            return