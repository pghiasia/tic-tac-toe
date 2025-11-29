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
        # Try to find blacklist.txt in the same directory as the script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        blacklist_file = os.path.join(script_dir, blacklist_path)
        
        # If not found, try current directory
        if not os.path.exists(blacklist_file):
            blacklist_file = blacklist_path
        
        with open(blacklist_file, 'r') as f:
            content = f.read().strip()
            # Split by comma and strip whitespace
            keywords = [kw.strip() for kw in content.split(',') if kw.strip()]
            return keywords
    except FileNotFoundError:
        print(f"Warning: Could not find {blacklist_path}. Using empty blacklist.")
        return []
    except Exception as e:
        print(f"Warning: Error reading blacklist: {e}. Using empty blacklist.")
        return []

def l2_handler(message, middlebox_port, iface_name, blocked_keywords):
    eth_frame = Ether(message)
    if eth_frame.haslayer(UDP) and eth_frame[UDP].dport == middlebox_port\
            and eth_frame[IP].ttl == 64:
        print(f"Received a UDP packet with destination port {middlebox_port}")
        
        # Extract payload
        if not eth_frame.haslayer(Raw):
            print("Packet has no payload, forwarding...")
            return
        
        payload = eth_frame[Raw].load
        payload_str = payload.decode("utf-8", errors='ignore')
        
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
            return
        
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
