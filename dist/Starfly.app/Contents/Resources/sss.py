# Simple server for SSS
import sys, os, tempfile, subprocess, socket, struct, time
import shutil
from multiprocessing import Process, Lock, Value, freeze_support

BLK_SIZE = 1024

CMD_PING = 1
CMD_CALIBRATE = 2
CMD_SNAP = 3

WINDOW_SIZE = 5

globalCaptureInst = None
globalCapturedScreens = [tempfile.NamedTemporaryFile(delete = False, suffix=".jpeg").name for x in range(5)]

class CaptureProcess(Process):
    def __init__(self, captureCmd, latency, sharedFiles, lock, extStart, extEnd):
        super(CaptureProcess, self).__init__()

        self.captureCmd = captureCmd[:]
        self.latency = latency
        self.globalScreens = sharedFiles[:]
        self.lock = lock
        self.extStart = extStart
        self.extEnd = extEnd

        self.window = [0, 0]
        self.windowInd = 0

    def captureScreen(self, captureCmd):
        start, end = self.window

        if start == end: # special case - starting condition
            f = self.globalScreens[start]
            self.extStart.value = start
        else:
            f = self.globalScreens[end]
            self.extStart.value = end

        cmd = captureCmd[:] + [f]
        retcode = subprocess.call(cmd)

        if retcode == 0: # Success
            self.window[1] = (end + 1) % len(self.globalScreens)
            if start == self.window[1]:
                self.window[0] = (start + 1) % len(self.globalScreens)
                self.extStart.value = self.window[0]
            return f
        else:
            return None

    def run(self):
        while True:
            time.sleep(self.latency / 1000000000.0)

            self.lock.acquire()
            filepath = self.captureScreen(self.captureCmd)
            self.lock.release()

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

def mainServer(captureCmd):
    print "Server Process Started"
	
    fileAccessLock = Lock()
    startInd = Value('i', 0)
    endInd = Value('i', 0)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 9999))
    s.listen(1)
    print "Binded to socket 9999"
	
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

            global globalCaptureInst, globalCapturedScreens
            if not globalCaptureInst:
                globalCaptureInst = CaptureProcess(captureCmd,
                        latency,
                        globalCapturedScreens,
                        fileAccessLock,
                        startInd,
                        endInd)
                globalCaptureInst.start()
                print "Started Process"
            continue

        elif cmd == CMD_SNAP:

            fileAccessLock.acquire()

            srcFile = globalCapturedScreens[startInd.value]
            dstFile = tempfile.NamedTemporaryFile(delete = False, suffix=".jpeg").name
            shutil.copyfile(srcFile, dstFile)

            fileAccessLock.release()

            filepath = dstFile
            filesize = os.path.getsize(dstFile)

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
                os.remove(filepath)
            os.remove(filepath)

# Initialization Code
if __name__ == "__main__":
    freeze_support()
    if sys.platform == "darwin": # mac
        captureCmd = ["screencapture", '-x']
    elif sys.platform.find("win") >= 0: # window
        captureCmd = [os.path.join(os.getcwd(),'win32', 'MiniCap.exe'),
            "-capturedesktop", "-closeapp", "-exit", "-save"]
        print captureCmd
    else:
        print "Sorry, only OS X and Windows are supported."
        exit()

    mainServer(captureCmd)