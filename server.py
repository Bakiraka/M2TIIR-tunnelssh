import sys
import urllib.parse
import logging, cgi
import http.server, socketserver, socket
import threading

#Variables globales
MAX_LENGTH = 4096
HTTP_PORT = 8888
SSHSERVER_PORT = 7777
SSHClient_IsConnected = None
SSHclientSocket = None
CLOSE_SOCKET_MESSAGE = 'TO_CLOSE'
OPEN_SOCKET_MESSAGE = 'TO_OPEN'
EMPTY_MESSAGE = 'BLANK'
TRY_CONNECTION_MESSAGE = 'TRY_CONNECTION'
ASK_COMMAND_MESSAGE = 'WAITING_FOR_COMMAND'

class MethodHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, req, client_addr, server):
        http.server.BaseHTTPRequestHandler.__init__(self,req,client_addr,server)

    # A GET will only be echoed
    def do_GET(self):
        parsedParams = urllib.parse.urlparse(self.path)
        queryParsed = urllib.parse.parse_qs(parsedParams.query)
        try:
            length = int(self.headers['Content-Length'])
        except TypeError:
            self.returnResponse("411 - Length Required", "text/html")
            return
        self.returnResponse(self.rfile.read(length).decode('utf-8'), "text/html")

    def do_POST(self):
        global SSHclientSocket
        global SSHClient_IsConnected
        # Parse query data & params to find out what was passed
        try:
            length = int(self.headers['Content-Length'])
        except TypeError:
            self.returnResponse("411 - Length Required", "text/html")
            return
        #Reading the POST content
        post_data = self.rfile.read(length)
        print("#######################################")
        print("Header \n" + str(self.headers))
        print("Sent : " + post_data.decode('utf-8'))
        if(SSHClient_IsConnected):
            SSHclientSocket.send(post_data)
            sshdata = SSHclientSocket.recv(1024)
            print("SSH client received :" + sshdata.decode())
            self.returnResponse(sshdata)
        else:
            self.returnResponse(EMPTY_MESSAGE.encode())
        return

    def returnResponse(self, response, type="application/octet-stream"):
        self.send_response(200)
        self.send_header("Content-type", type)
        self.end_headers()
        self.wfile.write(bytes(response,'utf-8'))
        return

    #Used for testing
    def returnEchoPOSTresponse(self, post_data):
        self.returnResponse(("200 - You did a POST ! You sent me : " + post_data.decode('utf-8')), "text/html")
        return

def HTTPserverLoop(httpd):
    while(True):
        httpd.handle_request()

def SSHclientlistenerLoop(socketToSSHClient, ):
    while(True):
        if(SSHClient_IsConnected == False):
            try:
                print("Waiting for ssh client connexion...")
                (SSHclientSocket, address) = socketToSSHClient.accept()
            except OSError as problem:
                print(str(problem))
                SSHClient_IsConnected = False
            print('SSHClient_IsConnected with ' + address[0] + ':' + str(address[1]))
            SSHClient_IsConnected = True


if __name__ == '__main__':
    #SSHClient_IsConnected
    SSHClient_IsConnected = False
    socketToSSHClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        socketToSSHClient.bind(("localhost", SSHSERVER_PORT))
    except error:
        print("Error : " + str(e))
    #only listens to 1 client
    socketToSSHClient.listen(1)

    #Creating the the HTTP daemon
    try:
        httpd = socketserver.TCPServer(("", HTTP_PORT), MethodHandler)
    except OSError as problem:
        print("Error ! " + str(problem))
        sys.exit()

    print("Tunnel server started, use <Ctrl-C> to stop")
    print("The web server will handle requests at port : " + str(HTTP_PORT))
    print("The SSH local server will listen to port :" + str(SSHSERVER_PORT))
    SSHlistenerThread = threading.Thread(target=SSHclientlistenerLoop, args=(socketToSSHClient,))
    HTTPserverThread = threading.Thread(target=HTTPserverLoop)

    try:

    except KeyboardInterrupt:
        print("<Ctrl-C> Received, ending program.")
        httpd.server_close()
        socketToSSHClient.close()
        if( SSHclientSocket is not None):
            SSHclientSocket.close()
        sys.exit()
