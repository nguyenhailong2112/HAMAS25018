from __future__ import annotations

import sys
import signal
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.logger_config import get_logger
from core.websocket_server import VisionHTTPServer, VisionRequestHandler
from core.vision_runtime import VisionRuntime


logger = get_logger(__name__)


def main() -> None:
    runtime = VisionRuntime()
    try:
        server = VisionHTTPServer((runtime.server_host, runtime.server_port), VisionRequestHandler, runtime)
    except OSError as exc:
        if getattr(exc, "winerror", None) == 10049 and runtime.server_host != "0.0.0.0":
            logger.warning(
                "Host %s cannot be bound on this machine, falling back to 0.0.0.0:%s",
                runtime.server_host,
                runtime.server_port,
            )
            runtime.server_host = "0.0.0.0"
            server = VisionHTTPServer((runtime.server_host, runtime.server_port), VisionRequestHandler, runtime)
        else:
            raise

    def _shutdown(*_args):
        logger.info("Shutdown requested")
        runtime.request_stop()
        try:
            server.shutdown()
        except Exception:
            logger.exception("Failed to shutdown HTTP server cleanly")

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    logger.info("Vision server listening on %s:%s", runtime.server_host, runtime.server_port)

    try:
        runtime.run_loop()
    finally:
        _shutdown()
        server.server_close()
        server_thread.join(timeout=2.0)


if __name__ == "__main__":
    main()
