import sys
import urllib.parse
import logging, cgi
import http.server, socketserver

######### application/octet-stream


class MethodHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self,req,client_addr,server):
        http.server.SimpleHTTPRequestHandler.__init__(self,req,client_addr,server)
        '''
    def do_GET(self):
        # Parse query data & params to find out what was passed
        parsedParams = urllib.parse.urlparse(self.path)
        queryParsed = urllib.parse.parse_qs(parsedParams.query)

        # request is either for a file to be served up or our test
        if parsedParams.path == "/ssh":
            self.processMySSHRequest(queryParsed)
        else:
            # Default to serve up a local file
            http.server.SimpleHTTPRequestHandler.do_GET(self);


    def processMySSHRequest(self, query):
        DUMMY_RESPONSE = "TEST"
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-length", len(DUMMY_RESPONSE))
        self.end_headers()
        self.wfile.write(bytes(DUMMY_RESPONSE, 'UTF-8'))
        return
        '''

    def do_POST(self):
        '''# Parse the form data posted
        length = int(self.headers.getheader('content-length'))
        data = self.rfile.read(length)
        print("##########################")
        print(line)
        print("##########################")'''

        length = int(self.headers['Content-Length'])
        post_data = urllib.parse.parse_qs(self.rfile.read(length).decode('utf-8'))
        # You now have a dictionary of the post data
        print("Sent : " + str(post_data))

        # Begin the response
        self.send_response(200)
        self.send_header("Content-type", "application/octet-stream")
        self.end_headers()
        self.wfile.write(bytes("Hello ! You did a POST !",'utf-8'))
    #    self.wfile.write(bytes("You sent me : " + post_data,'utf-8'))
        return

if __name__ == '__main__':
    PORT = 8888
    try:
        httpd = socketserver.TCPServer(("", PORT), MethodHandler)
    except OSError as bleme:
        print("Error ! " + str(bleme))
        sys.exit()

    print("Starting server at port " + str(PORT) + ", use <Ctrl-C> to stop")
    httpd.serve_forever()
