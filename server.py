import sys
import urllib.parse
import logging, cgi
import http.server, socketserver, socket

#Variables globales
MAX_LENGTH = 4096
HTTP_PORT = 8888
SSHSERVER_PORT = 7777
SSHClient_connected = None
clientsocket = None
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
        global clientsocket
        global SSHClient_connected
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
        if(SSHClient_connected):
            clientsocket.send(post_data)
            sshdata = clientsocket.recv(1024)
            print("SSH client received :" + sshdata.decode())
            self.returnEchoPOSTresponse(sshdata)
        else:
            self.returnEchoPOSTresponse(post_data)
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

if __name__ == '__main__':
    MAX_LENGTH = 4096
    HTTP_PORT = 8888
    SSHSERVER_PORT = 7777
    SSHClient_connected = False
    socketToSSHClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketToSSHClient.bind(("localhost", SSHSERVER_PORT))
    #only listens to 1 client
    socketToSSHClient.listen(1)

    try:
        httpd = socketserver.TCPServer(("", HTTP_PORT), MethodHandler)
    except OSError as problem:
        print("Error ! " + str(problem))
        sys.exit()

    print("Starting the tunnel server, use <Ctrl-C> to stop")
    try:
        while(True):
            try:
                if(SSHClient_connected == False):
                    print("Waiting for ssh client connexion...")
                    (clientsocket, address) = socketToSSHClient.accept()
                    print('SSHClient_connected with ' + address[0] + ':' + str(address[1]))
                    SSHClient_connected == True
                else:
                    print("Web server, handling request at port " + str(HTTP_PORT)) #DEBUG
                    httpd.handle_request()
            except OSError as problem:
                print(str(problem))
                SSHClient_connected = False

    except KeyboardInterrupt:
        print("<Ctrl-C> Received, ending program.")
        httpd.server_close()
        socketToSSHClient.close()
        clientsocket.close()
        sys.exit()
