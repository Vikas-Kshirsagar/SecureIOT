from scapy.all import *
import socket

def is_encrypted(packet):
    if TCP in packet:
        if packet[TCP].dport == 443 or packet[TCP].sport == 443:
            if Raw in packet:
                raw_data = packet[Raw].load
                return raw_data[:1] in [b'\x16', b'\x17']
            return True
    return Raw not in packet

def get_device_name_from_ip(ip):
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except (socket.herror, Exception):
        return None

def process_packet(packet):
    """
    Process each packet captured by Scapy.
    Returns a dictionary with packet information if the packet is not encrypted.
    """
    if not is_encrypted(packet):
        if IP in packet:
            device_name = get_device_name_from_ip(packet[IP].src)
            return {
                "device_name": device_name,
                "src_ip": packet[IP].src,
                "dest_ip": packet[IP].dst,
                "protocol": packet[IP].proto,
                "port": packet[TCP].sport if TCP in packet else None,
                "packet_data": bytes(packet)
            }
    return None

def start_sniffing(callback):
    print("Starting packet sniffing...")
    sniff(iface="Local Area Connection* 2", filter="ip and host 192.168.137.50", prn=callback, store=0)