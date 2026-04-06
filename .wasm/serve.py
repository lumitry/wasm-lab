import http.server

class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        super().end_headers()

if __name__ == '__main__':
    print("Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...")
    http.server.ThreadingHTTPServer(('', 8000), H).serve_forever()