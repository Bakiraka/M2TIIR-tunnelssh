import urllib.request
import urllib.error
import sys


aenvoyer = sys.argv[1]

data = bytes(aenvoyer, 'UTF-8')
req = urllib.request.Request('http://localhost:8888', data)
#req.add_header('Content-Length', '%d' % len(data))
req.add_header('Content-Length', '%d' % len(data))
req.add_header('Content-Type', 'application/octet-stream')

try:
    res = urllib.request.urlopen(req)
    print(res.read())
except (urllib.error.HTTPError, urllib.error.URLError) as e:
    print(e)
