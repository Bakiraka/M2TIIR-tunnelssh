PORT = 4269
SIZE = 256
ADDRESS = "localhost"
import socket
sock = socket.socket()
sock.connect(ADDRESS, PORT)
while True :
    data = bytes("test data", 'UTF-8')
    req = urllib.request.Request('http://localhost:8888', data)
    req.add_header('Content-Length', '%d' % len(data))
    req.add_header('Content-Type', 'application/octet-stream')
    res = urllib.request.urlopen(req)
    content = res.read()
    socket.send(content)
    
    
