import sys
import urllib.parse
import logging, cgi
import http.server, socketserver, socket

class MethodHandler(http.server.BaseHTTPRequestHandler):
    CLOSE_SOCKET_MESSAGE = 'TO_CLOSE'
    OPEN_SOCKET_MESSAGE = 'TO_OPEN'
    EMPTY_MESSAGE = 'BLANK'
    TRY_CONNECTION_MESSAGE = 'TRY_CONNECTION'
    ASK_COMMAND_MESSAGE = 'WAITING_FOR_COMMAND'

    def __init__(self, req, client_addr, server):
        http.server.BaseHTTPRequestHandler.__init__(self,req,client_addr,server)

    def do_POST(self):
        # Parse query data & params to find out what was passed
        parsedParams = urllib.parse.urlparse(self.path)
        queryParsed = urllib.parse.parse_qs(parsedParams.query)
        self.processMySSHRequest(queryParsed)

    def processMySSHRequest(self, query):
        length = int(self.headers['Content-Length'])
        #Reading the POST content
        post_data = self.rfile.read(length).decode('utf-8')
        self.returnEchoPOSTresponse(post_data)
        return
        #DEBUG print("Sent : " + str(post_data))

    #    if(post_data == TRY_CONNECTION_MESSAGE):
            #test si le client SSH
    #        pass

    def returnResponse(self, response):
        self.send_response(200)
        self.send_header("Content-type", "application/octet-stream")
        self.end_headers()
        self.wfile.write(bytes(response,'utf-8'))
        return

    #Used for testing
    def returnEchoPOSTresponse(self, post_data):
        self.returnResponse("Hello ! You did a POST ! \nYou sent me : " + post_data)
        return

if __name__ == '__main__':
    MAX_LENGTH = 4096
    HTTP_PORT = 8888
    SSHSERVER_PORT = 7777
    connected = False
    socketToSSHClient = socket.socket()
    socketToSSHClient.setblocking(0)
#    socketToSSHClient.settimeout(None)
    socketToSSHClient.bind(("localhost", 7777))
    socketToSSHClient.listen(1)

    #while(True):
    #while(connected == False):
    try:
        (clientsocket, address) = socketToSSHClient.accept()
        connected == True
    except OSError as bleme:
#                print("Not connected")
        print(str(bleme))
        connected = False
    print("DEBUG X")

    try:
        httpd = socketserver.TCPServer(("", HTTP_PORT), MethodHandler)
    except OSError as bleme:
        print("Error ! " + str(bleme))
        sys.exit()
    httpd.handle_request()
    httpd.server_close()

'''
    #print("Starting server at port " + str(HTTP_PORT) + ", use <Ctrl-C> to stop")
    try:
        httpd = socketserver.TCPServer(("", HTTP_PORT), MethodHandler)
        httpd.serve_forever()
    except OSError as bleme:
        print("Error ! " + str(bleme))
        sys.exit()
'''
