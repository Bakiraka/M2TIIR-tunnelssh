import socket
import sys
import urllib.request, urllib.error, urllib.parse
import http.client
import threading, time
import queue

#Default and global values
EMPTY_MESSAGE = 'BLANK'
ASK_COMMAND_MESSAGE = 'WAITING_FOR_COMMAND'
PORT_SSHD = 22
MAX_LENGTH = 2048
ADDRESS_SSHD = "localhost"
ADDRESS_SERVER = "localhost"
PORT_SERVER = "7777"

def threadSSH(queueIn, queueOut, run_event):
    sock = socket.socket()
    try:
        sock.connect((ADDRESS_SSHD,PORT_SSHD))
        #sock.setblocking(False)
    except ConnectionRefusedError as e:
        print("Connection error : " + str(e))
        print("Exiting...")
        run_event.clear()

    ToSSHThread = threading.Thread(target=DataToSSHserverLoop, args=(sock,queueIn,run_event))
    FromSSHThread = threading.Thread(target=DataFromSSHserverLoop, args=(sock,queueOut,run_event))
    ToSSHThread.start()
    FromSSHThread.start()
    while(run_event.is_set()):
        time.sleep(.2)

def DataToSSHserverLoop(SSHserverSocket,queueIn,run_event):
    tmp = None
    while(run_event.is_set()):
        if not(queueIn.empty()):
            if (tmp != None):
                tmp = queueIn.get()
                SSHserverSocket.send(tmp)
            tmp = None

def DataFromSSHserverLoop(SSHserverSocket,queueOut,run_event):
    toReceive = None
    while(run_event.is_set()):
        toReceive = SSHserverSocket.recv(MAX_LENGTH)
        if(toReceive != None):
            queueOut.put(toReceive)
        toReceive = None

if __name__== '__main__':
    #Processing the arguments
    if(len(sys.argv) > 1):
        ADDRESS_SERVER = sys.argv[1]
        if(len(sys.argv) > 2):
            PORT_SERVER=sys.argv[2]

    content = ''
    #Thread synchronisation element
    run_event = threading.Event()
    run_event.set()

    q = queue.Queue()
    qo = queue.Queue()
    processSSH = threading.Thread(target=threadSSH, args=(q,qo,run_event))
    processSSH.start()
    toSend = bytes(ASK_COMMAND_MESSAGE, 'UTF-8')

    while(run_event.is_set()):
        try:
            time.sleep(2) ############## DEBUG
            data = toSend
            print("Sending : |" + data.decode() + '|')
            req = urllib.request.Request('http://'+ADDRESS_SERVER+':'+PORT_SERVER, data)
            req.add_header('Content-Length', len(data))
            req.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0 Iceweasel/38.3.0')
            req.add_header('Content-Type', 'application/octet-stream')
            try :
                print("Openning : " + req.get_full_url())
                try:
                    res = urllib.request.urlopen(req)
                    content = res.read()
                    print("Received : |" + content.decode() + '|')
                except http.client.BadStatusLine as e:
                    print("BadStatusLine Error : " + str(e))
            except (urllib.error.HTTPError, urllib.error.URLError) as e :
                print("urllib error : " + str(e))
                continue

            if str(content.decode()) != EMPTY_MESSAGE :
                q.put(content)

            if qo.empty() :
                toSend = ASK_COMMAND_MESSAGE.encode()
            else:
                toSend = qo.get()

        except KeyboardInterrupt:
            print("<Ctrl-C> Received, ending program.")
            run_event.clear()
            time.sleep(1)
            processSSH.join()
            sys.exit()
