#!/usr/bin/env python3 

import socket as sock
import logging as log
import argparse
import os

from scapy.all import *

class RawSocketListener():
    MAX_RECV_SIZE = 1024
    def __init__(self, handler, middlebox_port, iface_name, blocked_keywords):
        self.handler = handler
        self.middlebox_port = middlebox_port
        self.iface_name = iface_name
        self.blocked_keywords = blocked_keywords
        self.listener = sock.socket(sock.AF_PACKET, sock.SOCK_RAW, sock.ntohs(0x0003))

    def listen_forever(self):
        print(f"Listening on middlebox port {self.middlebox_port}")
        print(f"Blocked keywords: {self.blocked_keywords}")
        while True:
            try:
                message = self.listener.recv(self.MAX_RECV_SIZE)
            except KeyboardInterrupt:
                print("Shutting down!")
                return None

            self.handler(message, self.middlebox_port, self.iface_name, self.blocked_keywords)

def load_blacklist(blacklist_path="blacklist.txt"):
    """
    Load blocked keywords from blacklist.txt file.
    Returns a list of keywords to block.
    """
    try:
        # Try absolute path first (for VM environment)
        if os.path.exists(blacklist_path):
            file_path = blacklist_path
        else:
            # Try to find blacklist.txt in the same directory as the script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(script_dir, blacklist_path)
            
            # If not found, try current directory
            if not os.path.exists(file_path):
                file_path = blacklist_path
        
        if not os.path.exists(file_path):
            print(f"ERROR: Could not find blacklist file at {file_path}")
            print(f"Current directory: {os.getcwd()}")
            print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
            return []
        
        print(f"Loading blacklist from: {file_path}")
        with open(file_path, 'r') as f:
            content = f.read().strip()
            # Split by comma and strip whitespace
            keywords = [kw.strip() for kw in content.split(',') if kw.strip()]
            print(f"Loaded {len(keywords)} keywords: {keywords}")
            return keywords
    except FileNotFoundError:
        print(f"ERROR: Could not find {blacklist_path}. No packets will be blocked!")
        return []
    except Exception as e:
        print(f"ERROR: Error reading blacklist: {e}. No packets will be blocked!")
        import traceback
        traceback.print_exc()
        return []

def l2_handler(message, middlebox_port, iface_name, blocked_keywords):
    eth_frame = Ether(message)
    # Check if it's a UDP packet with the correct destination port
    # Remove TTL check as it may vary depending on network path
    if eth_frame.haslayer(UDP) and eth_frame.haslayer(IP):
        if eth_frame[UDP].dport == middlebox_port:
            print(f"Received a UDP packet with destination port {middlebox_port}")
            print(f"Packet from {eth_frame[IP].src}:{eth_frame[UDP].sport} to {eth_frame[IP].dst}:{eth_frame[UDP].dport}")
            print(f"TTL: {eth_frame[IP].ttl}")
            
            # Extract payload
            if not eth_frame.haslayer(Raw):
                print("Packet has no payload, forwarding...")
                # Forward packet even without payload
                eth_frame[IP].ttl -= 1
                eth_frame[IP].chksum = None
                eth_frame[UDP].chksum = None
                eth_frame[IP].len = None
                eth_frame[UDP].len = None
                eth_frame = Ether(bytes(eth_frame))
                sendp(eth_frame, iface=iface_name)
                return
            
            payload = eth_frame[Raw].load
            payload_str = payload.decode("utf-8", errors='ignore')
            print(f"Payload: {payload_str}")
            print(f"Blocked keywords: {blocked_keywords}")
            
            # Check if payload contains any blocked keywords
            should_block = False
            matched_keyword = None
            for keyword in blocked_keywords:
                if keyword.lower() in payload_str.lower():
                    should_block = True
                    matched_keyword = keyword
                    break
            
            if should_block:
                print(f"BLOCKED: Packet contains blocked keyword '{matched_keyword}'. Dropping packet.")
                return  # Drop the packet, don't forward
            
            # Packet is safe, forward it without modification
            print(f"Packet is safe. Forwarding to destination: "
                  f"{eth_frame[IP].dst}:{eth_frame[UDP].dport}")
            eth_frame[IP].ttl -= 1
            eth_frame[IP].chksum = None
            eth_frame[UDP].chksum = None
            eth_frame[IP].len = None
            eth_frame[UDP].len = None
            eth_frame = Ether(bytes(eth_frame))
            eth_frame.show2()
            sendp(eth_frame, iface=iface_name)

def main():
    parser = argparse.ArgumentParser(
            description="Read UDP packets sent to the middlebox port, check "
                        "for blocked keywords, and forward safe packets to the "
                        "destination specified in their IP header.")
    parser.add_argument("middlebox_port", metavar="middlebox_port", type=int,
            help="The UDP port that the middlebox will listen on, "
                 "should be the same as the port that the UDP server is listening on.")
    parser.add_argument("iface_name", metavar="iface_name",
            help="The name of the interface on the middlebox host. For example,"
                 " if you are using h3 as the middlebox host then the name of the"
                 " interface should be h3-eth0.")
    parser.add_argument("--blacklist", metavar="blacklist_file", type=str,
            default="blacklist.txt",
            help="Path to the blacklist file (default: blacklist.txt)")
    args = parser.parse_args()
    
    # Load blocked keywords from blacklist file
    blocked_keywords = load_blacklist(args.blacklist)
    
    the_server = RawSocketListener(l2_handler, args.middlebox_port, args.iface_name, blocked_keywords)
    the_server.listen_forever()


if __name__ == "__main__":
    main()
