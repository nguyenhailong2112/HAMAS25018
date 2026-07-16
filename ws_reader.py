import threading
import websocket
import json

HOST = "192.168.53.111:8088"

URLS = [
    f"ws://{HOST}/ws/slot-states",
]


def on_message(ws, message):
    print(f"\n[{ws.url}]")

    try:
        data = json.loads(message)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        print(message)


def on_error(ws, error):
    print(f"[{ws.url}] ERROR: {error}")


def on_close(ws, close_status_code, close_msg):
    print(f"[{ws.url}] Closed ({close_status_code}) {close_msg}")


def on_open(ws):
    print(f"[{ws.url}] Connected")


def start_ws(url):
    ws = websocket.WebSocketApp(
        url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    ws.run_forever()


if __name__ == "__main__":
    threads = []

    for url in URLS:
        t = threading.Thread(target=start_ws, args=(url,), daemon=True)
        t.start()
        threads.append(t)

    print("Listening WebSocket... Press Ctrl+C to exit.")

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Exiting...")