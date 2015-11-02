import socket
import sys
import urllib.request, urllib.error, urllib.parse
import http.client
import threading, time
import queue

#Default and global values
EMPTY_MESSAGE = b'BLANK'
ASK_COMMAND_MESSAGE = b'WAITING_FOR_COMMAND'
PORT_SSHD = 22
MAX_LENGTH = 2048
ADDRESS_SSHD = "localhost"
ADDRESS_SERVER = "localhost"
PORT_SERVER = 8000

def threadCommunicationSSH(queueIn, queueOut, run_event):
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
        time.sleep(.5)

def DataToSSHserverLoop(SSHserverSocket,queueIn,run_event):
    tmp = None
    while(run_event.is_set()):
        time.sleep(0.1)
        if(queueIn.empty() == False):
            if(tmp == None):
                tmp = queueIn.get()
                SSHserverSocket.send(tmp)
            tmp = None

def DataFromSSHserverLoop(SSHserverSocket,queueOut,run_event):
    toReceive = None
    while(run_event.is_set()):
        time.sleep(0.1)
        toReceive = SSHserverSocket.recv(MAX_LENGTH)
        if(toReceive != None):
            queueOut.put(toReceive)
        toReceive = None

if __name__== '__main__':
    #Processing the arguments
    if(len(sys.argv) > 1):
        ADDRESS_SERVER = sys.argv[1]
        if(len(sys.argv) > 2):
            try:
                PORT_SERVER=int(sys.argv[2])
            except ValueError as error:
                print("Problem with the second argument : " + str(error))
                print("Default value for HTTP PORT set to 8000")
                PORT_SERVER = 8000

    content = b''
    toSend = ASK_COMMAND_MESSAGE
    #Thread synchronisation element
    run_event = threading.Event()
    run_event.set()

    q = queue.Queue()
    qo = queue.Queue()
    threadSSH = threading.Thread(target=threadCommunicationSSH, args=(q,qo,run_event))
    threadSSH.start()

    while(run_event.is_set()):
        try:
            time.sleep(0.5) ############## DEBUG
            req = urllib.request.Request('http://'+ADDRESS_SERVER+':'+str(PORT_SERVER), toSend)
            req.add_header('Content-Length', len(toSend))
            req.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0 Iceweasel/38.3.0')
            req.add_header('Content-Type', 'application/octet-stream')
            try :
                print("Openning : " + req.get_full_url())
                print("Sending to HTTP server : |" + str(toSend) + '|')
                try:
                    res = urllib.request.urlopen(req)
                    content = res.read()
                    print("Content from HTTP server: |" + str(content) + '|')

                    if((content != ASK_COMMAND_MESSAGE) and (content != EMPTY_MESSAGE)):
                        if(content == b''):
                            #TODO DO SOMETHING ?
                            print("## Content is blank ! ##")
                        else:
                            print("Puting content into queue.")
                            q.put(content)

                except http.client.BadStatusLine as e:
                    print("BadStatusLine Error : " + str(e))
            except (urllib.error.HTTPError, urllib.error.URLError) as e :
                print("Urllib error : " + str(e))
                continue

            if(qo.empty()):
                toSend = ASK_COMMAND_MESSAGE
            else:
                toSend = qo.get()

        except KeyboardInterrupt:
            print("<Ctrl-C> Received, ending program.")
            run_event.clear()

    threadSSH.join(2.0)
    sys.exit()
