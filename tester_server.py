import http.server
import socketserver
import urllib.request
import urllib.error
import sys

PORT = 8085

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/'):
            url = f'http://127.0.0.1:8000{self.path}'
            headers = {k: v for k, v in self.headers.items() if k.lower() not in ('host', 'content-length')}
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req) as resp:
                    self.send_response(resp.status)
                    for k, v in resp.getheaders():
                        self.send_header(k, v)
                    self.end_headers()
                    self.wfile.write(resp.read())
            except urllib.error.HTTPError as e:
                self.send_response(e.code)
                for k, v in e.headers.items():
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(e.read())
            except Exception as e:
                self.send_error(502, str(e))
            return
        if self.path == '/' or self.path == '/index.html' or not self.path:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            with open('/home/user/Traveo/apps/passenger-tester/index.html', 'rb') as f:
                self.wfile.write(f.read())
            return
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith('/api/'):
            url = f'http://127.0.0.1:8000{self.path}'
            length = int(self.headers.get('content-length', 0))
            body = self.rfile.read(length) if length > 0 else None
            headers = {k: v for k, v in self.headers.items() if k.lower() not in ('host', 'content-length')}
            if 'content-type' in self.headers:
                headers['Content-Type'] = self.headers['content-type']
            req = urllib.request.Request(url, data=body, method='POST', headers=headers)
            try:
                with urllib.request.urlopen(req) as resp:
                    self.send_response(resp.status)
                    for k, v in resp.getheaders():
                        self.send_header(k, v)
                    self.end_headers()
                    self.wfile.write(resp.read())
            except urllib.error.HTTPError as e:
                self.send_response(e.code)
                for k, v in e.headers.items():
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(e.read())
            except Exception as e:
                self.send_error(502, str(e))
            return
        return super().do_POST()

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('0.0.0.0', PORT), ProxyHandler) as httpd:
    print(f"Serving Tester on 0.0.0.0:{PORT}...")
    sys.stdout.flush()
    httpd.serve_forever()
