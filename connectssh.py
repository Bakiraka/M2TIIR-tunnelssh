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
MAX_LENGTH = 4096
ADDRESS_SSHD = "localhost"
ADDRESS_SERVER = "localhost"
PORT_SERVER = "7777"

def threadSSH(queueIn, queueOut, run_event):
    toReceive = None
    tmp = None
    sock = socket.socket()
    try:
        sock.connect((ADDRESS_SSHD,PORT_SSHD))
        sock.setblocking(False)
    except ConnectionRefusedError as e:
        print("Connection error : " + str(e))
        print("Exiting...")
        run_event.clear()

    while(run_event.is_set()):
        time.sleep(0.1)
        if not(queueIn.empty()) or tmp != None :
            if (tmp != None) :
                tmp = queueIn.get()
            sock.send(tmp)
            tmp = None

        try :
            toReceive = sock.recv(MAX_LENGTH)
        except BlockingIOError as e :
            print ("Blocking Error :" + str(e))
            toReceive = None
        if toReceive != None:
            queueOut.put(toReceive)


if __name__== '__main__':
    #Processing the arguments
    if(len(sys.argv) > 1):
        ADDRESS_SERVER = sys.argv[1]
        if(len(sys.argv) > 2):
            PORT_SERVER=sys.argv[2]

    content = ''
    #Thread Synchronisation element
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
            req = urllib.request.Request('http://'+ADDRESS_SERVER+':'+PORT_SERVER, data)
            req.add_header('Content-Length', len(data))
            req.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0 Iceweasel/38.3.0')
            req.add_header('Content-Type', 'application/octet-stream')
            try :
                print("openning : " + req.get_full_url())
                try:
                    res = urllib.request.urlopen(req)
                    content = res.read().decode('UTF-8')
                    print("Received : " + content)
                except http.client.BadStatusLine as e:
                    print("Error : " + str(e))
                #content = res.read().decode('UTF-8')
            except (urllib.error.HTTPError, urllib.error.URLError) as e :
                continue
            if str(content) != EMPTY_MESSAGE :
                q.put(content)
            if qo.empty() :
                toSend = ASK_COMMAND_MESSAGE.encode()
            else :
                toSend = qo.get()

        except KeyboardInterrupt:
            print("<Ctrl-C> Received, ending program.")
            processSSH.terminate()
            sys.exit()
