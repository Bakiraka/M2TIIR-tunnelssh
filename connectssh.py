PORT_SSHD = 4269
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
sock = socket.socket()
content = ''
data = ''
while True :
    data = bytes(data, 'UTF-8')
    req = urllib.request.Request('http://'+ADDRESS_SERVER+':'+PORT_SERVER, data)
    req.add_header('Content-Length', len(data))
    req.add_header('Content-Type', 'application/octet-stream')
    res = urllib.request.urlopen(req)
    content = res.read()
    # si le message qu'on recoit demande de commencer la com ssh, on le fait, et on attend des commandes
    if str(content) == OPEN_SOCKET_MESSAGE :
        sock.connect(ADDRESS_SSHD, PORT_SSHD)
        closed = False
        data = ASK_COMMAND_MESSAGE
    # si le message demande qu'on close la socket, on le fait, et on redemande la connection au serveur
    if str(content) == CLOSE_SOCKET_MESSAGE :
        sock.close()
        closed = True
        data = TRY_CONNECTION_MESSAGE
    # si le message n'est pas un message d'attente, on envoie la commande ssh, puis on recoit les données qu'on envoie
    if closed == False and str(content) != EMPTY_MESSAGE :
        socket.send(content)
        toSend = socket.receive(MAX_LENGTH)
        data = bytes(toSend, 'UTF-8')
    # sinon on envoit une demande de commande
    else :
        data = ASK_COMMAND_MESSAGE
    
