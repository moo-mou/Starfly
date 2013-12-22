# Simple server for SSS
import sys, os, tempfile, subprocess, socket, struct, time
from threading import Thread

BLK_SIZE = 1024

CMD_PING = 1
CMD_CALIBRATE = 2
CMD_SNAP = 3

globalThreadInst = None
globalCapturedScreens = [(None, None) for x in range(1)]

def captureScreen():
    f = tempfile.NamedTemporaryFile(delete = False)
    cmd = CMD[:] + [f.name]
    retcode = subprocess.call(cmd)

    if retcode == 0:
        return f.name
    else:
        return None

def timedCapture(latency):
    print "Thread started with latency:", latency
    while True:
        time.sleep(latency / 1000000000.0)

        filepath = captureScreen()
        filesize = os.path.getsize(filepath)

        ringInd = len(globalCapturedScreens) % len(globalCapturedScreens)
        existingFile, _ = globalCapturedScreens[ringInd]

        if existingFile:
            os.remove(existingFile)

        print "KACHING"
        globalCapturedScreens[ringInd] = (filepath, filesize)

if sys.platform == "darwin": # mac
    CMD = ["screencapture", '-x']
elif sys.platform.find("win") >= 0: # window
    CMD = [os.getcwd() + "/win32/bin/Minicap.exe",
        "-capturedesktop", "-closeapp", "-exit", "-save"]
else:
    print "Sorry, only OS X and Windows are supported."
    exit()

def convert_to_bytes(no):
    result = bytearray()
    result.append(no & 0xff)
    for i in range(3):
        no = no >> 8
        result.append(no & 0xff)
    return result

def receiveXByte(x, conn):
    data, dataSize = "", 0
    offset = 0
    while dataSize < x:
        buf = conn.recv(BLK_SIZE)
        dataSize += len(buf)
        data += buf

    # Decode 8 bytes as a big endian long
    intValue = struct.unpack('>Q', data)[0]
    return intValue

def mainServer():
    global globalThreadInst, globalCapturedScreens
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 9999))
    s.listen(1)

    while True:
        conn, addr = s.accept()
        print "Connection received:", conn, addr

        cmd, data = "", ""
        while len(data) <= 0:
            # reads 1 byte
            data = conn.recv(BLK_SIZE)
            if (data):
                cmd = ord(data)

        print "Received Command:", cmd

        if not cmd:
            conn.close()
            continue
        elif cmd == CMD_PING:
            conn.send(convert_to_bytes(CMD_PING))
            conn.close()
            continue
        elif cmd == CMD_CALIBRATE:
            conn.send(convert_to_bytes(CMD_PING))
            latency = receiveXByte(4, conn)
            print "Latency (ns): ", latency
            conn.close()

            if not globalThreadInst:
                globalThreadInst = Thread(target = timedCapture, args = (latency,))
                globalThreadInst.run()
                print "Started thread"

            continue
        elif cmd == CMD_SNAP:
            # Always get the 1st for now
            filepath, filesize = globalCapturedScreens[0]

            try:
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
            except socket.error, e:
                print "Pipe error:", socket.error

mainServer()
