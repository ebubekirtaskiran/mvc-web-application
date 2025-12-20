import os
import json
import mimetypes
import socket
import time
import argparse
import threading

from pathlib import Path
from urllib.parse import parse_qs, urlparse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

import model
import view

BASE_DIR = Path(__file__).parent
HOST = "0.0.0.0"
PORT = 8080

# === SSE clients listesi (Observer bildirimi burada broadcast eder) ===
_SSE_CLIENTS = set()          # set[BaseHTTPRequestHandler]
_SSE_LOCK = threading.Lock()

# İzlenecek klasörler
WATCH_FOLDERS = ["masaustu", "indirilenler", "resimler", "belgeler"]

# Model Observer (watchdog) instance
DIR_OBSERVER = None


def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def _sse_send(handler: BaseHTTPRequestHandler, event_name: str, data_obj: dict):
    """Tek bir SSE client'a event gönderir."""
    data = json.dumps(data_obj, ensure_ascii=False)
    msg = f"event: {event_name}\ndata: {data}\n\n"
    handler.wfile.write(msg.encode("utf-8"))
    handler.wfile.flush()


def broadcast_fs_change(payload: dict):
    """Model değişiklik bildirimi → tüm SSE client’lara gönder."""
    dead = []
    with _SSE_LOCK:
        clients = list(_SSE_CLIENTS)

    for h in clients:
        try:
            _sse_send(h, "fschange", payload)
        except Exception:
            dead.append(h)

    if dead:
        with _SSE_LOCK:
            for h in dead:
                _SSE_CLIENTS.discard(h)


def route(method: str, path: str, body_bytes: bytes):
    parsed = urlparse(path)
    p = parsed.path
    query = parse_qs(parsed.query)

    # 8080 → gateway, diğer portlar → normal tek panel
    if method == "GET" and p == "/":
        if PORT == 8080:
            html = view.render_gateway_page()
        else:
            html = view.render_main_page()
        return 200, "text/html; charset=utf-8", html.encode("utf-8")

    # (opsiyonel) tek panel yolu
    if method == "GET" and p == "/single":
        html = view.render_main_page()
        return 200, "text/html; charset=utf-8", html.encode("utf-8")

    if method == "GET" and p == "/api/list":
        path_name = query.get("path", ["masaustu"])[0]

        start_time = time.perf_counter()
        items_or_error = model.list_items(path_name)
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000.0

        item_count = len(items_or_error) if isinstance(items_or_error, list) else 0

        print("\n--- API İsteği Raporu ---")
        print(f"  Port: {PORT}")
        print(f"  Path: /api/list?path={path_name}")
        print(f"  Listelenen Öğe: {item_count} adet")
        print(f"  Süre: {duration_ms:.2f} ms")
        print("---------------------------\n")

        if isinstance(items_or_error, dict) and "error" in items_or_error:
            error_msg = json.dumps(items_or_error, ensure_ascii=False)
            return 404, "application/json; charset=utf-8", error_msg.encode("utf-8")

        json_data = json.dumps(items_or_error, ensure_ascii=False)
        return 200, "application/json; charset=utf-8", json_data.encode("utf-8")

    return 404, "text/plain; charset=utf-8", b"404 Not Found"


class MyHandler(BaseHTTPRequestHandler):
    if not mimetypes.guess_type("style.css")[0]:
        mimetypes.add_type("text/css", ".css")

    def handle_static(self, path: str):
        file_path_str = path.lstrip("/")
        safe_path = os.path.normpath(file_path_str)

        if not safe_path.startswith("static"):
            self.send_error(403, "Forbidden")
            return

        file_path = BASE_DIR / safe_path
        if file_path.is_file():
            mime_type, _ = mimetypes.guess_type(file_path)
            self.send_response(200)
            self.send_header("Content-type", mime_type or "application/octet-stream")
            self.end_headers()
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, "Static file not found")

    def handle_events(self):
        """SSE endpoint: /events"""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        # client kaydet
        with _SSE_LOCK:
            _SSE_CLIENTS.add(self)

        # İlk bağlantı mesajı (opsiyonel)
        try:
            self.wfile.write(b": connected\n\n")
            self.wfile.flush()
        except Exception:
            with _SSE_LOCK:
                _SSE_CLIENTS.discard(self)
            return

        # Bağlantıyı açık tut (threading server olduğu için sorun değil)
        try:
            while True:
                # heartbeat (bazı ortamlarda bağlantıyı canlı tutar)
                time.sleep(15)
                self.wfile.write(b": ping\n\n")
                self.wfile.flush()
        except Exception:
            with _SSE_LOCK:
                _SSE_CLIENTS.discard(self)

    def route_request(self, method: str):
        body_bytes = b""
        if method in ("POST", "PUT"):
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)

        try:
            status, ctype, body = route(method=method, path=self.path, body_bytes=body_bytes)
            self.send_response(status)
            self.send_header("Content-type", ctype)
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            print(f"Controller Hatası: {e}")
            self.send_error(500, f"Sunucu Hatası: {e}")

    def do_GET(self):
        if self.path.startswith("/static/"):
            self.handle_static(self.path)
            return

        if self.path.startswith("/events"):
            self.handle_events()
            return

        self.route_request("GET")

    def do_POST(self):
        self.route_request("POST")

    def do_DELETE(self):
        self.route_request("DELETE")


def run_server():
    global DIR_OBSERVER

    # Observer’ı başlat (Model tarafı)
    DIR_OBSERVER = model.DirectoryObserver(model.BASE_DIR, WATCH_FOLDERS)
    DIR_OBSERVER.subscribe(broadcast_fs_change)
    DIR_OBSERVER.start()

    httpd = ThreadingHTTPServer((HOST, PORT), MyHandler)

    local_ip = get_local_ip()
    print(f"\nSunucu başlatıldı. Dinleniyor: {HOST}:{PORT}")
    print(f"Bu bilgisayardan test: http://127.0.0.1:{PORT}")
    if local_ip != "127.0.0.1":
        print(f"Yerel ağdan erişim:   http://{local_ip}:{PORT}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        if DIR_OBSERVER:
            DIR_OBSERVER.stop()
        print("\nSunucu kapatıldı.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", "-p", type=int, default=8080)
    args = parser.parse_args()
    PORT = args.port
    run_server()
