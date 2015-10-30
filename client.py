import urllib.request
import urllib.error
import sys


aenvoyer = sys.argv[1]

data = bytes(aenvoyer, 'UTF-8')
req = urllib.request.Request('http://localhost:8000', data)
#req.add_header('Content-Length', '%d' % len(data))
req.add_header('Content-Length', '%d' % len(data))
req.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0 Iceweasel/38.3.0')
req.add_header('Content-Type', 'application/octet-stream')

try:
    res = urllib.request.urlopen(req)
    print(res.read())
except (urllib.error.HTTPError, urllib.error.URLError) as e:
    print(e)
