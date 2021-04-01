###############################################################################
# receiver.py
# Names: Stanley Zhang, Olivier Chen
# BU IDs: U99944807, U33604671
###############################################################################

import sys
import socket

SEND_BUFFER_SIZE = 1472

from util import *

def receiver(receiver_port, window_size):
    """TODO: Listen on socket and print received message to sys.stdout"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('127.0.0.1', receiver_port))
    isConnected = False
    while True:
        # waiting for START packet
        while isConnected == False:
            pkt, address = s.recvfrom(SEND_BUFFER_SIZE)
            pkt_header = PacketHeader(pkt[:16])
            msg = pkt[16:16+pkt_header.length]
            pkt_checksum = pkt_header.checksum
            pkt_header.checksum = 0
            computed_checksum = compute_checksum(pkt_header / msg)
            if pkt_checksum != computed_checksum:
                print "checksums not match"
            else:
                # check if packet is START and send ack if so
                ack_start_header = PacketHeader(type=3, seq_num=pkt_header.seq_num, length = 0)
                ack_start_header.checksum = compute_checksum(ack_start_header / "")
                ack_start = ack_start_header / ""
                s.sendto(str(ack_start), address)
                isConnected = True
        
        N = 0
        buffer = ["" for i in range(window_size)]

        # after receiving START, data will be received until END is received
        while isConnected == True:
            pkt, address = s.recvfrom(SEND_BUFFER_SIZE)
            pkt_header = PacketHeader(pkt[:16])
            msg = pkt[16:16+pkt_header.length]
            pkt_checksum = pkt_header.checksum
            pkt_header.checksum = 0
            computed_checksum = compute_checksum(pkt_header / msg)
            if pkt_checksum != computed_checksum:
                print "checksums not match"
            else:
                # check if packet is END and send ack if so
                if (pkt_header.type == 1) and (pkt_header.length == 0):
                    ack_end_header = PacketHeader(type=3, seq_num=pkt_header.seq_num, length = 0)
                    ack_end_header.checksum = compute_checksum(ack_end_header / "")
                    ack_end = ack_end_header / ""
                    s.sendto(str(ack_end), address)
                    isConnected = False
                # if not END, the packet is DATA
                else:
                    # case 1: DATA packet's seq_num is not equal to expected_seq_num (N), send back ack with seq_num N
                    if N != pkt_header.seq_num:
                        # if seq_num is less than N+window_size but greater than N:
                        if pkt_header.seq_num < N + window_size and pkt_header.seq_num > N:
                            ack_header = PacketHeader(type=3, seq_num=pkt_header.seq_num, length = 0)     
                            ack_header.checksum = compute_checksum(ack_header / "")
                            ack = ack_header / ""
                            s.sendto(str(ack), address)
                            window_position = pkt_header.seq_num - N
                            if buffer[window_position]  == "":    # if seq_num isn't in buffer already (no duplicates)
                                buffer[window_position] = pkt
                                               
                    # case 2: DATA packet's seq_num IS equal to N
                    else:
                       
                        buffer[0] = pkt
                        M = N
                        while buffer[0] != "":
                            print buffer[0][16:16+len(buffer[0])]
                            buffer.pop(0)
                            buffer.append("")
                            M += 1
                        N = M
                        ack_header = PacketHeader(type=3, seq_num=pkt_header.seq_num, length = 0)     
                        ack_header.checksum = compute_checksum(ack_header / "")
                        ack = ack_header / ""
                        s.sendto(str(ack), address)
                        
def main():
    """Parse command-line argument and call receiver function """
    if len(sys.argv) != 3:
        sys.exit("Usage: python receiver.py [Receiver Port] [Window Size]")
    receiver_port = int(sys.argv[1])
    window_size = int(sys.argv[2])
    receiver(receiver_port, window_size)

if __name__ == "__main__":
    main()
