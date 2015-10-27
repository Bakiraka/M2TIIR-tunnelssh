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
sock = socket.socket()
content = ''
toSend = bytes(ASK_COMMAND_MESSAGE, 'UTF-8')
data = toSend
while True :
    data = toSend
    req = urllib.request.Request('http://'+ADDRESS_SERVER+':'+PORT_SERVER, data)
    req.add_header('Content-Length', len(data))
    req.add_header('Content-Type', 'application/octet-stream')
    try :
        res = urllib.request.urlopen(req)
        content = res.read()
    except (urllib.error.HTTPError, urllib.error.URLError) as e :
        continue
    if closed == True :
        closed = False
        sock.connect((ADDRESS_SSHD,PORT_SSHD))
        sock.setblocking(False)
    # si le message demande qu'on close la socket, on le fait, et on redemande la connection au serveur
    if str(content) == CLOSE_SOCKET_MESSAGE :
        sock.close()
        closed = True
    # si le message n'est pas un message d'attente, on envoie la commande ssh, puis on recoit les données qu'on envoie
    if str(content) != EMPTY_MESSAGE :
        sock.send(content)
    try :
        toSend = sock.recv(MAX_LENGTH)
        print(toSend)
    except (BlockingIOError) as e :
        toSend = bytes(ASK_COMMAND_MESSAGE, 'UTF-8')
