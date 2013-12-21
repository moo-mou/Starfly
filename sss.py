# Simple server for SSS
import sys, os, tempfile, subprocess, socket

BLK_SIZE = 1024

if sys.platform == "darwin": # mac
    CMD = ["screencapture", '-x']
elif sys.platform.find("win") >= 0: # window
    CMD = [os.getcwd() + "/win32/bin/Minicap.exe", 
        "-capturedesktop", "-closeapp", "-exit", "-save"]
else:
    print "Sorry, only OS X and Windows are supported."
    exit()

def captureScreen():
    f = tempfile.NamedTemporaryFile(delete = False)
    cmd = CMD[:] + [f.name]
    retcode = subprocess.call(cmd)

    if retcode == 0:
        return f.name
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
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 9999))
    s.listen(1)

    while True:
        conn, addr = s.accept()
        print "Connection received:", conn, addr

        filepath = captureScreen()
        filesize = os.path.getsize(filepath)

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
