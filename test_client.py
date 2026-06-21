Access-Control-Allow-Origin: *
HTTP/1.0 200 OK
Server: SimpleHTTP/0.6 Python/3.11.15
Date: Sun, 21 Jun 2026 05:06:00 GMT
Content-type: text/x-python
Content-Length: 429
Last-Modified: Sun, 21 Jun 2026 03:19:12 GMT

import urllib.request
import sys

print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")

try:
    r = urllib.request.urlopen('http://127.0.0.1:8765/', timeout=5)
    print(f"Status: {r.status}")
    data = r.read()
    print(f"Length: {len(data)}")
    print(f"Content:\n{data[:400].decode('utf-8', errors='replace')}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
