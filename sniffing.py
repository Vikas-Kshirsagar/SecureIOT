from scapy.all import *
import socket

def get_device_name(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return None

def is_encrypted(packet):
    if TCP in packet:
        if packet[TCP].dport == 443 or packet[TCP].sport == 443:
            return True
        if Raw in packet:
            raw_data = packet[Raw].load
            return raw_data[:1] in [b'\x16', b'\x17']
    return False

def get_tls_version(packet):
    if TCP in packet and Raw in packet:
        raw_data = packet[Raw].load
        if raw_data[:1] == b'\x16':  # TLS Handshake
            if raw_data[1:3] == b'\x03\x01':
                return "TLSv1.0"
            elif raw_data[1:3] == b'\x03\x02':
                return "TLSv1.1"
            elif raw_data[1:3] == b'\x03\x03':
                return "TLSv1.2"
            elif raw_data[1:3] == b'\x03\x04':
                return "TLSv1.3"
    return None

def process_packet(packet):
    packet_info = {}
    
    # Ethernet Layer
    if Ether in packet:
        packet_info['eth_dst'] = packet[Ether].dst
        packet_info['eth_src'] = packet[Ether].src
        packet_info['eth_type'] = hex(packet[Ether].type)
    
    # IP Layer
    if IP in packet:
        ip = packet[IP]
        packet_info.update({
            'ip_version': ip.version,
            'ip_ihl': ip.ihl,
            'ip_tos': ip.tos,
            'ip_len': ip.len,
            'ip_id': ip.id,
            'ip_flags': str(ip.flags),
            'ip_frag': ip.frag,
            'ip_ttl': ip.ttl,
            'ip_proto': ip.proto,
            'ip_chksum': hex(ip.chksum),
            'src_ip': ip.src,
            'dst_ip': ip.dst
        })
        
        # Transport Layer
        if TCP in packet:
            tcp = packet[TCP]
            packet_info.update({
                'sport': tcp.sport,
                'dport': tcp.dport,
                'tcp_seq': tcp.seq,
                'tcp_ack': tcp.ack,
                'tcp_flags': str(tcp.flags)
            })
        elif UDP in packet:
            udp = packet[UDP]
            packet_info.update({
                'sport': udp.sport,
                'dport': udp.dport,
                'udp_len': udp.len,
                'udp_chksum': hex(udp.chksum)
            })
        
        # Payload
        if Raw in packet:
            raw_data = packet[Raw].load
            packet_info['payload_len'] = len(raw_data)
            packet_info['payload'] = raw_data.hex()
            
            # Check for encryption
            packet_info['is_encrypted'] = is_encrypted(packet)
            
            if not packet_info['is_encrypted']:
                try:
                    packet_info['human_readable'] = raw_data.decode('utf-8', errors='ignore')
                except:
                    packet_info['human_readable'] = None
            
            packet_info['tls_version'] = get_tls_version(packet)
        
        # Device name
        packet_info['device_name'] = get_device_name(ip.src)
    
    return packet_info

def start_sniffing(callback):
    print("Starting packet sniffing...")
    #sniff(iface="Local Area Connection* 2", prn=callback, store=0)
    sniff(iface="Local Area Connection* 2", filter="ip and (host 192.168.137.70 or host 192.168.137.25 or host 192.168.137.57)", prn=callback, store=0)
    #sniff(iface="Local Area Connection* 2", filter="ip and host 192.168.137.84", prn=callback, store=0)