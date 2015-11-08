import sys
import urllib.parse
import http.server, socketserver, socket
import threading, time
import queue
import base64
#Default Values
EMPTY_MESSAGE = b'BLANK'
ASK_COMMAND_MESSAGE = b'WAITING_FOR_COMMAND'
EMPREINTE_SERVER = 'SERVER4269'
EMPREINTE_CLIENT = "CLIENT4269"
MAX_LENGTH = 2048
HTTP_PORT = 8000
SSHSERVER_PORT = 7777
REFRESH_RATE = 0.01
SSHClient_IsConnected = None
dataToSSHQueue = queue.Queue()
dataFromSSHQueue = queue.Queue()

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

class MethodHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self,*args):
        http.server.BaseHTTPRequestHandler.__init__(self,*args)
        #DEBUG print("Initialisation du handler")

    # A GET will only be echoed
    def do_GET(self):
        parsedParams = urllib.parse.urlparse(self.path)
        queryParsed = urllib.parse.parse_qs(parsedParams.query)
        try:
            length = int(self.headers['Content-Length'])
        except TypeError:
            self.returnTypeErrorResponse("Length Required".encode())
            return
        message = self.rfile.read(length)
        message = encrypt(EMPREINTE_SERVER+message.decode()).encode()
        self.returnOKResponse(message, "text/html")

    def do_POST(self):
        #global SSHClient_IsConnected
        # Parse query data & params to find out what was passed
        try:
            length = int(self.headers['Content-Length'])
        except TypeError:
            self.returnTypeErrorResponse("Length Required")
            return
        #Reading the POST content
        post_data = self.rfile.read(length)
        post_data = decrypt(post_data.decode())
        #print("Header :")
        #print("#######################################")    #DEBUG
        #print(str(self.headers))              #DEBUG
        #print("#######################################")    #DEBUG
        #print("Received from POST: |" + str(post_data) + "|")    #DEBUG
        message = ''
        if(SSHClient_IsConnected):
            if(not(post_data.startswith(EMPREINTE_CLIENT))):
                self.returnTypeErrorResponse("Bad Request")
                return
            else :
                post_data = post_data.replace(EMPREINTE_CLIENT,'')
                post_data = post_data.encode()
            if(post_data == ASK_COMMAND_MESSAGE):
                print("### Received an ASK_COMMAND_MESSAGE ###") #DEBUG
            else:
                dataToSSHQueue.put(post_data)

            if(dataFromSSHQueue.empty() == False):
                message = dataFromSSHQueue.get()
            else:
                print("Nothing to send, asking for a command.") #DEBUG
                message = ASK_COMMAND_MESSAGE
        else:
            message = EMPTY_MESSAGE
        message = encrypt(EMPREINTE_SERVER + message.decode()).encode()
        self.returnOKResponse(message)
        return

    def returnTypeErrorResponse(self, response):
        self.send_response(411)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", len(response))
        self.end_headers()
        self.wfile.write(response)
        return

    def returnOKResponse(self, response, type="application/octet-stream"):
        self.send_response(200)
        self.send_header("Content-type", type)
        self.send_header("Content-Length", len(response))
        self.end_headers()
        self.wfile.write(response)
        return

    #Used for testing
    def returnEchoPOSTresponse(self, post_data):
        self.returnOKResponse(("You did a POST ! You sent me : " + post_data.decode()), "text/html")
        return

def HTTPserverLoop(httpd,run_event):
    print("HTTPserverLoop Started.")
    httpd.serve_forever()

def ClearQueue(queueToClear):
    while(queueToClear.empty()==False):
        nall = queueToClear.get()

def SSHclientlistenerLoop(socketToSSHClient,run_event):
    print("SSHclientlistenerLoop Started.")
    global SSHClient_IsConnected
    global dataQueue
    SSHclientThreadsEvent = threading.Event()

    while(run_event.is_set()):
        time.sleep(REFRESH_RATE * 30)
        if(SSHClient_IsConnected == False):
            try:
                print("Waiting for ssh client connexion...")
                (SSHclientSocket, address) = socketToSSHClient.accept()
            except OSError as problem:
                print("Error at" + str(problem))
                SSHClient_IsConnected = False
            print('SSHClient_IsConnected with ' + address[0] + ':' + str(address[1]))
            SSHClient_IsConnected = True
            SSHclientThreadsEvent.set()
            ClearQueue(dataToSSHQueue)
            ClearQueue(dataFromSSHQueue)
            ToSSHThread = threading.Thread(target=DataToSSHclientLoop, args=(SSHclientSocket, SSHclientThreadsEvent))
            FromSSHThread = threading.Thread(target=DataFromSSHclientLoop, args=(SSHclientSocket, SSHclientThreadsEvent))
            ToSSHThread.start()
            FromSSHThread.start()

    if(run_event.is_set() == False):
        SSHclientThreadsEvent.clear()

def DataToSSHclientLoop(SSHclientSocket, SSHclientThreadsEvent):
    while(SSHclientThreadsEvent.is_set()):
        time.sleep(REFRESH_RATE)
        if(SSHClient_IsConnected == True):
            if(dataToSSHQueue.empty() == False):
                data = dataToSSHQueue.get()
                data = data.decode()
                data = data.encode('ISO-8859-1')
                SSHclientSocket.send(data)

def DataFromSSHclientLoop(SSHclientSocket, SSHclientThreadsEvent):
    global SSHClient_IsConnected
    while(SSHclientThreadsEvent.is_set()):
        time.sleep(REFRESH_RATE)
        if(SSHClient_IsConnected == True):
            sshdata = SSHclientSocket.recv(MAX_LENGTH).decode('ISO-8859-1')
            sshdata = sshdata.encode()
            print('type SSH : ' + str(type(sshdata)))
            if(sshdata == b''):
                print("Socket connection broken")
                SSHClient_IsConnected = False
                SSHclientThreadsEvent.clear()
            else:
                dataFromSSHQueue.put(sshdata)
                print("SSH client received : |" + str(sshdata) + '|')       #DEBUG

if __name__ == '__main__':
    #Processing the arguments
    if(len(sys.argv) > 1):
        try:
            REFRESH_RATE = 0.01 * int(sys.argv[1])
        except ValueError as error:
            print("Problem with the first argument : " + str(error))
            print("Default value for REFRESH_RATE set to {}".format(REFRESH_RATE))
        if(len(sys.argv) > 2):
            HTTP_PORT=int(sys.argv[2])
            if(len(sys.argv) > 3):
                try:
                    SSHSERVER_PORT=int(sys.argv[3])
                except ValueError as error:
                    print("Problem with the second argument : " + str(error))
                    print("Default value for SSHSERVER_PORT set to {}".format(7777))
                    SSHSERVER_PORT = 7777
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
        httpd = http.server.HTTPServer(("", HTTP_PORT), MethodHandler)
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
        while(run_event.is_set()):
            time.sleep(.2)
    #Proper closing by handling a Ctrl-C (Doesn't really work well but whatever)
    except KeyboardInterrupt:
        print("<Ctrl-C> Received, ending program.")
        run_event.clear()
        httpd.shutdown()
        if(httpd is not None):
            httpd.shutdown()
        if(socketToSSHClient is not None):
            if(SSHClient_IsConnected == False):
                closingSocket = socket.socket()
                closingSocket.connect(("localhost",SSHSERVER_PORT))
                closingSocket.send(b'')
                socketToSSHClient.close()
        if( SSHclientSocket is not None):
            SSHclientSocket.close()
        SSHlistenerThread.join(.2)
        HTTPserverThread.join(.2)
        sys.exit()
