import socket
import sys
import urllib.request, urllib.error, urllib.parse
import http.client
import threading, time
import queue
import base64

#Default and global values
EMPTY_MESSAGE = b'BLANK'
ASK_COMMAND_MESSAGE = b'WAITING_FOR_COMMAND'
PORT_SSHD = 22
MAX_LENGTH = 2048
ADDRESS_SSHD = "localhost"
ADDRESS_SERVER = "localhost"
PORT_SERVER = 8000
REFRESH_RATE = 0.01

def encrypt(message) :
    message = message [::-1]
    cipher = base64.b64encode(message.encode()).decode()
    cipher = cipher [1:] + cipher [0]
    return cipher [::-1]
    
def decrypt(message) :
    todecipher = message [::-1]
    todecipher = todecipher [len(message) - 1] + todecipher [0 : len(message) - 1]
    todecipher = todecipher.encode()
    return str(base64.b64decode(todecipher).decode()) [::-1]

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
        time.sleep(REFRESH_RATE * 10)
        if(queueIn.empty() == False):
            if(tmp == None):
                tmp = queueIn.get().decode()
                tmp = tmp.encode('ISO-8859-1')
                SSHserverSocket.send(tmp)
            tmp = None

def DataFromSSHserverLoop(SSHserverSocket,queueOut,run_event):
    toReceive = None
    while(run_event.is_set()):
        time.sleep(REFRESH_RATE * 10)
        toReceive = SSHserverSocket.recv(MAX_LENGTH)
        toReceive = toReceive.decode('ISO-8859-1')
        toReceive = toReceive.encode()
        
        if(toReceive != None):
            queueOut.put(toReceive)
        toReceive = None

if __name__== '__main__':
    #Processing the arguments
    if(len(sys.argv) > 1):
        try:
            REFRESH_RATE = 0.01 * int(sys.argv[1])
        except ValueError as error:
            print("Problem with the first argument : " + str(error))
            print("Default value for REFRESH_RATE set to {}".format(REFRESH_RATE))
        if(len(sys.argv) > 2):
            ADDRESS_SERVER = sys.argv[2]
            if(len(sys.argv) > 3):
                try:
                    PORT_SERVER=int(sys.argv[3])
                except ValueError as error:
                    print("Problem with the third argument : " + str(error))
                    print("Default value for HTTP PORT set to 8000")
                    PORT_SERVER = 8000

    content = b''
    toSend = encrypt(ASK_COMMAND_MESSAGE.decode()).encode()
    #Thread synchronisation element
    run_event = threading.Event()
    run_event.set()

    q = queue.Queue()
    qo = queue.Queue()
    threadSSH = threading.Thread(target=threadCommunicationSSH, args=(q,qo,run_event))
    threadSSH.start()

    while(run_event.is_set()):
        try:
            time.sleep(REFRESH_RATE)
            req = urllib.request.Request('http://'+ADDRESS_SERVER+':'+str(PORT_SERVER), toSend)
            req.add_header('Content-Length', len(toSend))
            req.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0 Iceweasel/38.3.0')
            req.add_header('Content-Type', 'application/octet-stream')

            #DEBUG print("Openning : " + req.get_full_url())
            if((toSend != ASK_COMMAND_MESSAGE) and (toSend != EMPTY_MESSAGE) and content != b''): #DEBUG
                print("Sending to HTTP server : |" + str(toSend) + '|') #DEBUG
            try:
                res = urllib.request.urlopen(req)
                content = res.read()
                content = decrypt(content.decode()).encode()
                #DEBUG print("Content from HTTP server: |" + str(content) + '|')

                if((content != ASK_COMMAND_MESSAGE) and (content != EMPTY_MESSAGE)):
                    if(content == b''):
                        #TODO DO SOMETHING ?
                        print("## Content is blank ! ##")
                    else:
                        #DEBUG print("Puting content into queue.")
                        q.put(content)

            except http.client.BadStatusLine as error:
                print("BadStatusLine Error : " + str(error))
            except (urllib.error.HTTPError, urllib.error.URLError) as error:
                print("Urllib error : " + str(error))
                continue
            except ConnectionResetError as error:
                '''
                Là on a eu une interruption de connection de la part du serveur
                On indique au serveur SSH qu'on arrête (pas sûr à 100% que ça marche)
                '''
                print("Connection reset by peer, closing now.")
                q.put(b'')
                run_event.clear()

            if(qo.empty()):
                toSend = ASK_COMMAND_MESSAGE
            else:
                toSend = qo.get()
            toSend = encrypt(toSend.decode()).encode()

        except KeyboardInterrupt:
            print("<Ctrl-C> Received, ending program.")
            run_event.clear()

    threadSSH.join(0.1)
    sys.exit()
