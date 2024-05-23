from socket import *
import os
import sys
import struct
import time
import select

ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY = 0
ICMP_DEST_UNREACH = 3

def checksum(str_):
    # Calculate the checksum of the packet
    str_ = bytearray(str_)
    csum = 0
    countTo = (len(str_) // 2) * 2

    for count in range(0, countTo, 2):
        thisVal = str_[count+1] * 256 + str_[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff

    if countTo < len(str_):
        csum = csum + str_[-1]
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout
    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []:  # Timeout
            return "Request timed out."

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        icmpHeader = recPacket[20:28]
        icmpType, code, mychecksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)

        # Parse the ICMP response error codes
        if icmpType == 3:  # This is an ICMP error message
            if code == 0:
                return "Destination Network Unreachable"
            elif code == 1:
                return "Destination Host Unreachable"
        elif icmpType == 0 and packetID == ID:  # This is an ICMP echo reply
            bytesInDouble = struct.calcsize("d")
            timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
            return timeReceived - timeSent

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "Request timed out."


def sendOnePing(mySocket, destAddr, ID):
    # Create the ICMP header
    myChecksum = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    myChecksum = checksum(header + data)

    if sys.platform == 'darwin':
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    mySocket.sendto(packet, (destAddr, 1))

def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")
    mySocket = socket(AF_INET, SOCK_DGRAM, icmp)
    myID = os.getpid() & 0xFFFF
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return delay

def ping(host, timeout=1):
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    print("")

    totalSentPackets = 0
    totalReceivedPackets = 0
    totalRTT = 0
    minRTT = float('inf')
    maxRTT = 0

    for i in range(10):  # Send 10 pings
        delay = doOnePing(dest, timeout)
        totalSentPackets += 1
        if isinstance(delay, float):
            totalReceivedPackets += 1
            totalRTT += delay
            minRTT = min(minRTT, delay)
            maxRTT = max(maxRTT, delay)
            print(f"RTT: {delay:.6f} seconds")
        else:
            print(delay)  # Print error message

    # Calculate packet loss rate
    packetLossRate = ((totalSentPackets - totalReceivedPackets) / totalSentPackets) * 100

    # Calculate average RTT
    avgRTT = totalRTT / totalReceivedPackets if totalReceivedPackets > 0 else 0

    print("\nPing statistics for " + dest + ":")
    print(f"Packets: Sent = {totalSentPackets}, Received = {totalReceivedPackets}, Lost = {totalSentPackets - totalReceivedPackets} ({packetLossRate:.2f}% loss)")
    print(f"Approximate round trip times in milli-seconds: Minimum = {minRTT*1000:.2f}ms, Maximum = {maxRTT*1000:.2f}ms, Average = {avgRTT*1000:.2f}ms")

print("Ping to Canada")
ping("23.56.229.33")  

print('-----------------------')
print("Ping to China")
ping("www.china.org.cn") 

print('-----------------------')
print("Ping to Australia")
ping("223.252.19.130") 

print('-----------------------')
print("Ping to Europe")
ping("172.67.73.142")  

print('-----------------------')
print("Ping to localhost")
ping("localhost")
