import sys
import urllib.parse
import http.server, socketserver, socket
import threading, time
import queue

#Variables globales
MAX_LENGTH = 4096
HTTP_PORT = 8000
SSHSERVER_PORT = 7777
SSHClient_IsConnected = None
dataQueue = queue.Queue()
CLOSE_SOCKET_MESSAGE = 'TO_CLOSE'
OPEN_SOCKET_MESSAGE = 'TO_OPEN'
EMPTY_MESSAGE = 'BLANK'
TRY_CONNECTION_MESSAGE = 'TRY_CONNECTION'
ASK_COMMAND_MESSAGE = 'WAITING_FOR_COMMAND'

class MethodHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self,ssh_socket,*args):
        self.SSHclientSocket=ssh_socket
        http.server.BaseHTTPRequestHandler.__init__(self,*args)
        print("init!") #DEBUG

    # A GET will only be echoed
    def do_GET(self):
        parsedParams = urllib.parse.urlparse(self.path)
        queryParsed = urllib.parse.parse_qs(parsedParams.query)
        try:
            length = int(self.headers['Content-Length'])
        except TypeError:
            self.returnResponse("411 - Length Required", "text/html")
            return
        data_received = self.rfile.read(length)
        if(data_received[0:3] == "test"):
            self.returnResponse("Test, OK.".encode())
        self.returnResponse(self.rfile.read(length).decode('utf-8'), "text/html")

    def do_POST(self):
        global SSHClient_IsConnected
        # Parse query data & params to find out what was passed
        try:
            length = int(self.headers['Content-Length'])
        except TypeError:
            self.returnResponse("411 - Length Required", "text/html")
            return
        #Reading the POST content
        post_data = self.rfile.read(length)
        print("#######################################")    #DEBUG
        print("Header \n" + str(self.headers))              #DEBUG
        print("Sent : " + post_data.decode('utf-8'))        #DEBUG
        print("#######################################")    #DEBUG

        if(SSHClient_IsConnected):
            if(post_data == ASK_COMMAND_MESSAGE):
                if(dataQueue.empty() == False):
                    self.returnResponse("202 ".encode() + dataQueue.get())
            else:
                self.SSHclientSocket.send(post_data)
        else:
            self.returnResponse(EMPTY_MESSAGE.encode())
        return

    def returnResponse(self, response, type="application/octet-stream"):
        self.send_response(200)
        self.send_header("Content-type", type)
        self.end_headers()
        self.wfile.write(response)
        return

    #Used for testing
    def returnEchoPOSTresponse(self, post_data):
        self.returnResponse(("200 - You did a POST ! You sent me : " + post_data.decode('utf-8')), "text/html")
        return

def HTTPserverLoop(httpd,run_event):
    print("HTTPserverLoop Started.")
    while(run_event.is_set()):
        httpd.serve_forever()

def SSHclientlistenerLoop(socketToSSHClient,run_event):
    print("SSHclientlistenerLoop Started.")
    global SSHClient_IsConnected
    global dataQueue

    while(run_event.is_set()):
        if(SSHClient_IsConnected == False):
            try:
                print("Waiting for ssh client connexion...")
                (SSHclientSocket, address) = socketToSSHClient.accept()
            except OSError as problem:
                print(str(problem))
                SSHClient_IsConnected = False
            print('SSHClient_IsConnected with ' + address[0] + ':' + str(address[1]))
            SSHClient_IsConnected = True
        else:
            sshdata = SSHclientSocket.recv(1024)
            dataQueue.put(sshdata)
            print("SSH client received :" + sshdata.decode())       #DEBUG

def handleRequestsUsing(ssh_socket):
    return lambda *args: MethodHandler(ssh_socket, *args)

if __name__ == '__main__':
    httpd = None
    run_event = threading.Event()
    run_event.set()
    #SSHClient_IsConnected
    SSHClient_IsConnected = False
    SSHclientSocket = None
    #SSH Socket server creation
    socketToSSHClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        socketToSSHClient.bind(('', SSHSERVER_PORT))
    except socket.error as e:
        print("Error : " + str(e))
    #Tells to only listens to 1 client
    socketToSSHClient.listen(1)

    #Creating the the HTTP daemon
    try:
        handler = handleRequestsUsing(SSHclientSocket)
        httpd = http.server.HTTPServer(("", HTTP_PORT), handler)
        httpd.SSHClient_IsConnected = SSHClient_IsConnected
        httpd.SSHclientSocket = SSHclientSocket
    except OSError as problem:
        print("Error when creating the http daemon :" + str(problem))
        sys.exit()

    print("Tunnel server started, use <Ctrl-C> to stop")
    print("The web server will handle requests at port : " + str(HTTP_PORT))
    print("The SSH local server will listen to port :" + str(SSHSERVER_PORT))
    SSHlistenerThread = threading.Thread(target=SSHclientlistenerLoop, args=(socketToSSHClient, run_event))
    HTTPserverThread = threading.Thread(target=HTTPserverLoop, args=(httpd,run_event))

    try:
        SSHlistenerThread.start()
        HTTPserverThread.start()
        while 1:
            time.sleep(.1)
    #Proper closing by handling a Ctrl-C (Doesn't really work well but whatever)
    except KeyboardInterrupt:
        print("<Ctrl-C> Received, ending program.")
        run_event.clear()
        httpd.shutdown()
        SSHlistenerThread.join()
        HTTPserverThread.join()
        if(httpd is not None):
            httpd.shutdown()
        if(socketToSSHClient is not None):
            if(SSHClient_IsConnected == False):
                '''closingSocket = socket.socket()
                closingSocket.connect(("localhost",SSHSERVER_PORT))
                closingSocket.send("dummy".encode())
                '''
                socketToSSHClient.close()
        if( SSHclientSocket is not None):
            SSHclientSocket.close()
        sys.exit()
