from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if "/download/" in self.path:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(bytes("OK", "utf-8"))
            url_parts = self.path.split("/download/")
            url = url_parts[1]
            self.app.intent_url = url
        else:
            self.send_response(404)
            self.end_headers()

class WebApiServer():
    def __init__(self):
        self.server = HTTPServer(("0.0.0.0", 8686), RequestHandler)
        self.server.RequestHandlerClass.app = self
        self.intent_url = ""
        self.server_thread = Thread(target=self.server.serve_forever, name="webapi_server")
        self.server_thread.start()