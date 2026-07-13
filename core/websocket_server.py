from __future__ import annotations

import base64
import hashlib
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from core.logger_config import get_logger


logger = get_logger(__name__)


MONITOR_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HAMAS25018 Vision Monitor</title>
  <style>
    :root { color-scheme: light; --bg:#f6f7f2; --ink:#20231f; --muted:#697066; --line:#d7dbd2; --ok:#147a45; --full:#b44420; --unknown:#7b6a11; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: "Segoe UI", Tahoma, sans-serif; background:var(--bg); color:var(--ink); }
    header { display:flex; align-items:flex-end; justify-content:space-between; gap:16px; padding:20px 24px; border-bottom:1px solid var(--line); background:#fff; }
    h1 { margin:0; font-size:22px; font-weight:650; }
    .meta { color:var(--muted); font-size:13px; text-align:right; }
    main { padding:20px 24px; }
    .summary { display:grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap:12px; margin-bottom:18px; }
    .tile { background:#fff; border:1px solid var(--line); border-radius:8px; padding:14px; }
    .tile strong { display:block; font-size:24px; margin-top:4px; }
    .grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:14px; }
    .camera { background:#fff; border:1px solid var(--line); border-radius:8px; overflow:hidden; }
    .camera h2 { margin:0; padding:12px 14px 4px; font-size:16px; }
    .cam-meta { padding:0 14px 12px; color:var(--muted); font-size:12px; border-bottom:1px solid var(--line); }
    .slots { display:grid; grid-template-columns: repeat(auto-fill, minmax(88px, 1fr)); gap:8px; padding:12px; }
    .slot { min-height:74px; border:1px solid var(--line); border-radius:8px; padding:10px; background:#fafbf8; }
    .slot b { display:block; font-size:15px; margin-bottom:8px; }
    .state { display:inline-block; font-size:12px; padding:4px 7px; border-radius:999px; color:#fff; }
    .empty { background:var(--ok); }
    .full { background:var(--full); }
    .unknown { background:var(--unknown); }
    @media (max-width:720px) { header { display:block; } .meta { text-align:left; margin-top:8px; } .summary { grid-template-columns: repeat(2, 1fr); } }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>HAMAS25018 Vision Monitor</h1>
      <div class="meta" id="endpoint"></div>
    </div>
    <div class="meta">
      <div id="status">Connecting...</div>
      <div id="timestamp">-</div>
    </div>
  </header>
  <main>
    <section class="summary">
      <div class="tile">Total slots<strong id="total">0</strong></div>
      <div class="tile">Empty<strong id="empty">0</strong></div>
      <div class="tile">Car Full<strong id="full">0</strong></div>
      <div class="tile">Unknown<strong id="unknown">0</strong></div>
    </section>
    <section class="grid" id="grid"></section>
  </main>
  <script>
    const grid = document.getElementById("grid");
    const statusEl = document.getElementById("status");
    const tsEl = document.getElementById("timestamp");
    const endpoint = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/slot-states`;
    document.getElementById("endpoint").textContent = endpoint;
    let cameraNames = new Map();

    function cls(state) {
      if (state === "Empty") return "empty";
      if (state === "Car Full") return "full";
      return "unknown";
    }

    function render(payload) {
      const slots = payload.slots || [];
      const counts = { Empty: 0, "Car Full": 0, Unknown: 0 };
      slots.forEach(s => counts[s.state] = (counts[s.state] || 0) + 1);
      document.getElementById("total").textContent = slots.length;
      document.getElementById("empty").textContent = counts.Empty || 0;
      document.getElementById("full").textContent = counts["Car Full"] || 0;
      document.getElementById("unknown").textContent = counts.Unknown || 0;
      tsEl.textContent = payload.timestamp || "-";

      const groups = new Map();
      slots.forEach(slot => {
        const key = String(slot.camera_id);
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key).push(slot);
      });
      grid.innerHTML = "";
      [...groups.entries()].sort().forEach(([cameraId, layout]) => {
        const cameraName = cameraNames.get(cameraId) || cameraId;
        const card = document.createElement("article");
        card.className = "camera";
        card.innerHTML = `<h2>${cameraName}</h2><div class="cam-meta">camera_id: ${cameraId}</div><div class="slots"></div>`;
        const slotsEl = card.querySelector(".slots");
        layout.forEach(slot => {
          const el = document.createElement("div");
          el.className = "slot";
          el.innerHTML = `<b>${slot.slot_id}</b><span class="state ${cls(slot.state)}">${slot.state}</span>`;
          slotsEl.appendChild(el);
        });
        grid.appendChild(card);
      });
    }

    function loadCameraNames() {
      fetch("/api/v1/cameras")
        .then(resp => resp.json())
        .then(payload => {
          cameraNames = new Map((payload.cameras || []).map(cam => [String(cam.camera_id), cam.camera_name || cam.camera_id]));
        })
        .catch(() => {});
    }

    function connect() {
      const ws = new WebSocket(endpoint);
      ws.onopen = () => { statusEl.textContent = "Connected"; };
      ws.onmessage = event => render(JSON.parse(event.data));
      ws.onclose = () => { statusEl.textContent = "Disconnected, retrying..."; setTimeout(connect, 1500); };
      ws.onerror = () => { statusEl.textContent = "Connection error"; ws.close(); };
    }
    loadCameraNames();
    connect();
  </script>
</body>
</html>
"""


def _accept_key(sec_websocket_key: str) -> str:
    magic = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    sha1 = hashlib.sha1((sec_websocket_key + magic).encode("utf-8")).digest()
    return base64.b64encode(sha1).decode("ascii")


class VisionRequestHandler(BaseHTTPRequestHandler):
    server_version = "HAMAS25018Vision/1.0"

    def do_GET(self) -> None:  # noqa: N802
        if not self._client_allowed():
            self._write_error(HTTPStatus.FORBIDDEN, "client_ip_not_allowed", "Client IP is not in Vision Server allowlist.")
            return
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._handle_health()
            return
        if parsed.path == "/api/v1/server-info":
            self._handle_server_info()
            return
        if parsed.path in {"/", "/monitor"}:
            self._handle_monitor()
            return
        if parsed.path == "/api/v1/slots":
            self._handle_slots()
            return
        if parsed.path == "/api/v1/slot-state":
            self._handle_slot_state(parsed)
            return
        if parsed.path == "/api/v1/cameras":
            self._handle_cameras()
            return
        if parsed.path == "/api/v1/events":
            self._handle_events()
            return
        if parsed.path == "/api/v1/logs":
            self._handle_logs()
            return
        if parsed.path == "/ws/slot-states" and self.headers.get("Upgrade", "").lower() == "websocket":
            self._handle_websocket()
            return
        if parsed.path == "/ws/events" and self.headers.get("Upgrade", "").lower() == "websocket":
            self._handle_events_websocket()
            return
        self._write_error(HTTPStatus.NOT_FOUND, "not_found", "Endpoint not found.")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        logger.info("%s - %s", self.address_string(), format % args)

    def _client_allowed(self) -> bool:
        client_ip = self.client_address[0]
        return self.server.runtime.is_client_allowed(client_ip)

    def _handle_health(self) -> None:
        snapshot = self.server.runtime.build_health_payload()
        self._write_json(snapshot)

    def _handle_server_info(self) -> None:
        payload = self.server.runtime.server_info_payload()
        self._write_json(payload)

    def _handle_monitor(self) -> None:
        body = MONITOR_HTML.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_slots(self) -> None:
        snapshot = self.server.runtime.snapshot()
        self._write_json(snapshot)

    def _handle_slot_state(self, parsed) -> None:
        from urllib.parse import parse_qs

        query = parse_qs(parsed.query, keep_blank_values=True)
        slot_id = str(query.get("slot_id", [""])[0]).strip()
        if not slot_id:
            self._write_error(HTTPStatus.BAD_REQUEST, "missing_slot_id", "Query parameter slot_id is required.")
            return
        payload = self.server.runtime.slot_state_payload(slot_id)
        if payload is None:
            self._write_error(HTTPStatus.NOT_FOUND, "slot_not_found", f"Slot not found: slot_id={slot_id}")
            return
        self._write_json(payload)

    def _handle_cameras(self) -> None:
        payload = self.server.runtime.cameras_payload()
        self._write_json(payload)

    def _handle_events(self) -> None:
        limit = self._read_limit_default(50)
        payload = self.server.runtime.recent_events_payload(limit=limit)
        self._write_json(payload)

    def _handle_logs(self) -> None:
        limit = self._read_limit_default(100)
        payload = self.server.runtime.recent_logs_payload(limit=limit)
        self._write_json(payload)

    def _handle_websocket(self) -> None:
        key = self.headers.get("Sec-WebSocket-Key")
        if not key:
            self._write_error(HTTPStatus.BAD_REQUEST, "missing_websocket_key", "Missing Sec-WebSocket-Key.")
            return
        accept = _accept_key(key)
        self.send_response(HTTPStatus.SWITCHING_PROTOCOLS)
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept)
        self.end_headers()

        conn = self.connection
        conn.settimeout(1.0)
        self.server.runtime.register_ws_client(conn)
        try:
            self.server.runtime.send_current_public_snapshot_to_client(conn)
            self.server.runtime.hold_ws_connection(conn)
        finally:
            self.server.runtime.unregister_ws_client(conn)

    def _handle_events_websocket(self) -> None:
        key = self.headers.get("Sec-WebSocket-Key")
        if not key:
            self._write_error(HTTPStatus.BAD_REQUEST, "missing_websocket_key", "Missing Sec-WebSocket-Key.")
            return
        accept = _accept_key(key)
        self.send_response(HTTPStatus.SWITCHING_PROTOCOLS)
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept)
        self.end_headers()

        conn = self.connection
        conn.settimeout(1.0)
        self.server.runtime.register_event_ws_client(conn)
        try:
            self.server.runtime.send_recent_events_to_client(conn)
            self.server.runtime.hold_ws_connection(conn)
        finally:
            self.server.runtime.unregister_event_ws_client(conn)

    def _write_json(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _write_error(self, status: HTTPStatus, code: str, message: str) -> None:
        payload = {
            "error": {
                "code": code,
                "message": message,
                "client_ip": self.client_address[0],
            }
        }
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_limit_default(self, default: int) -> int:
        from urllib.parse import parse_qs

        query = parse_qs(urlparse(self.path).query, keep_blank_values=True)
        raw = query.get("limit", [str(default)])[0]
        try:
            return max(1, min(int(raw), 300))
        except (TypeError, ValueError):
            return default


class VisionHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address, RequestHandlerClass, runtime):
        super().__init__(server_address, RequestHandlerClass)
        self.runtime = runtime
