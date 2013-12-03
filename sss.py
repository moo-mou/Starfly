# Simple server for SSS
import uuid

BLK_SIZE = 1024

def captureScreen():
    import subprocess
    filename = uuid.uuid4()
    retcode = subprocess.call(["screencapture", "/tmp/"+str(filename)])

    if retcode == 0:
        return "/tmp/" + str(filename)
    else:
        return None

def convert_to_bytes(no):
    result = bytearray()
    result.append(no & 0xff)
    for i in range(3):
        no = no >> 8
        result.append(no & 0xff)
    return result

def mainServer():
    import socket, sys, os
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("localhost", 9999))
    s.listen(1)

    while True:
        conn, addr = s.accept()

        print "Connection received:", conn, addr

        filepath = captureScreen()
        filesize = os.path.getsize(filepath)

        conn.send(convert_to_bytes(filesize))
        print "Filesize:", filesize

        sent = 0
        with open(filepath, 'rb') as f:
            packet = f.read(BLK_SIZE)
            sent += len(packet)
            while packet: 
                conn.send(packet)
                packet = f.read(BLK_SIZE)
                sent += len(packet)
            print "finished sending:", sent

mainServer()
