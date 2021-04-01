###############################################################################
# sender.py
# Names: Stanley Zhang, Olivier Chen
# BU IDs: U99944807, U33604671
###############################################################################

import sys
import socket
import random

SEND_BUFFER_SIZE = 1472

from util import *

def sender(receiver_ip, receiver_port, window_size):
    """TODO: Open socket and send message from sys.stdin"""
    socket.setdefaulttimeout(0.5)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # send START message
    pkt_header_start = PacketHeader(type=0, seq_num=random.randint(2,10), length = 0) 
    pkt_header_start.checksum = compute_checksum(pkt_header_start / "")
    pkt_start = pkt_header_start / ""
    s.sendto(str(pkt_start), (receiver_ip, receiver_port))

    # receive ACK for start and check seq_num (must be same) before moving on
    ack_start, address = s.recvfrom(SEND_BUFFER_SIZE)
    ack_header = PacketHeader(ack_start[:16])
    while (ack_header.seq_num != ack_header.seq_num or ack_header.type != 3):
        ack_start = s.recvfrom(SEND_BUFFER_SIZE)
        ack_header = PacketHeader(ack_start[:16])
    
    # split data into chunks of 1455 (?)
    msg = sys.stdin.read()
    msg_chunks = [msg[i:i+SEND_BUFFER_SIZE-16] for i in range(0, len(msg), SEND_BUFFER_SIZE-16)]
    
    # send chunks as DATA while adjusting seq_num appropriately (starts at 0)
    ack_count = 0
    window = [x for x in range(window_size)]
    
    # send first "window_size" number of packets
    for i in range(0,window_size,1):
        data_pkt_header = PacketHeader(type=2, seq_num=i, length=len(msg_chunks[i])) 
        data_pkt_header.checksum = compute_checksum(data_pkt_header/ msg_chunks[i])
        data_pkt = data_pkt_header / msg_chunks[i]
        s.sendto(str(data_pkt), (receiver_ip, receiver_port))

    # whenever we receive an ack we check if it is the expected ack and if so we move the sliding window fwd and send next
    while ack_count < len(msg_chunks):
        try:
            ack_data, address = s.recvfrom(SEND_BUFFER_SIZE)
            ack_header = PacketHeader(ack_data[:16])
            ack_checksum = ack_header.checksum
            ack_header.checksum = 0
            computed_checksum = compute_checksum(ack_header / "")
        except socket.timeout:
            # resend packets in window here if timeout is received
            for i in range(0,len(window),1):
                data_pkt_header = PacketHeader(type=2, seq_num=window[i], length=len(msg_chunks[window[i]])) 
                data_pkt_header.checksum = compute_checksum(data_pkt_header/ msg_chunks[window[i]])
                data_pkt = data_pkt_header / msg_chunks[window[i]]
                s.sendto(str(data_pkt), (receiver_ip, receiver_port))
        else:
            
            if ack_header.type == 3 and ack_header.length == 0 and ack_checksum == computed_checksum: # check checksum, type and length of packet
                if ack_header.seq_num == window[0]+1: # if ack has seq_num as expected
                    window.pop(0)
                    if len(window) != 0:
                        if window[len(window)-1] < len(msg_chunks)-1:   # if window has space to move forward, it does so
                            window.append(window[window_size-2]+1)
                    ack_count += 1
                    # send new window
                    for i in range(0,len(window),1):
                        data_pkt_header = PacketHeader(type=2, seq_num=window[i], length=len(msg_chunks[window[i]])) 
                        data_pkt_header.checksum = compute_checksum(data_pkt_header/ msg_chunks[window[i]])
                        data_pkt = data_pkt_header / msg_chunks[window[i]]
                        s.sendto(str(data_pkt), (receiver_ip, receiver_port))
                elif ack_header.seq_num > window[0]+1:    # if ack's seq_num is higher than expected, signifying the window should slide by more than one
                    slide_count = ack_header.seq_num - (window[0]+1)
                    while (slide_count >= 0):
                        window.pop(0)
                        if len(window) != 0:
                            if window[len(window)-1] < len(msg_chunks)-1:   # if window has space to move forward, it does so
                                window.append(window[window_size-2]+1)
                        ack_count += 1
                        slide_count -= 1
                    # send new window
                    for i in range(0,len(window),1):
                        data_pkt_header = PacketHeader(type=2, seq_num=window[i], length=len(msg_chunks[window[i]])) 
                        data_pkt_header.checksum = compute_checksum(data_pkt_header/ msg_chunks[window[i]])
                        data_pkt = data_pkt_header / msg_chunks[window[i]]
                        s.sendto(str(data_pkt), (receiver_ip, receiver_port))


    # send END message
    pkt_header_end = PacketHeader(type=1, seq_num=random.randint(2,10), length = 0) 
    pkt_header_end.checksum = compute_checksum(pkt_header_end / "")
    pkt_end = pkt_header_end / ""
    s.sendto(str(pkt_end), (receiver_ip, receiver_port))

    # receive ACK for end and check seq_num (must be same) before moving on
    ack_end, address = s.recvfrom(SEND_BUFFER_SIZE)
    ack_header = PacketHeader(ack_end[:16])
    while ack_header.seq_num != pkt_header_end.seq_num or ack_header.type != 3:
        ack_end = s.recvfrom(SEND_BUFFER_SIZE)
        ack_header = PacketHeader(ack_end[:16])



def main():
    """Parse command-line arguments and call sender function """
    if len(sys.argv) != 4:
        sys.exit("Usage: python sender.py [Receiver IP] [Receiver Port] [Window Size] < [message]")
    receiver_ip = sys.argv[1]
    receiver_port = int(sys.argv[2])
    window_size = int(sys.argv[3])
    sender(receiver_ip, receiver_port, window_size)

if __name__ == "__main__":
    main()
