from __future__ import annotations

import json
import ipaddress
import socket
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.camera_reader import CameraReader
from core.config import (
    load_camera_configs,
    load_ingest_config,
    load_json_dict,
    load_rule_config,
    load_zone_configs,
    validate_camera_configs,
    validate_ingest_config,
    validate_rule_config,
)
from core.file_utils import append_jsonl_rotating, write_json_atomic
from core.frame_store import FrameStore
from core.logger_config import get_logger
from core.path_utils import PROJECT_ROOT, ensure_exists, resolve_project_path
from core.slot_contract import build_snapshot_payload
from core.slot_state_store import CameraSlotBundle, SlotStateStore
from core.types import Detection, DetectionResult
from core.video_file_reader import VideoFileReader
from core.zone_reasoner import ZoneReasoner
from core.state_tracker import StateTracker
from core.detector import YoloDetector


logger = get_logger(__name__)


@dataclass
class CameraRuntime:
    camera_id: str
    camera_name: str
    camera_type: str
    source_type: str
    source_path: str
    model_path: str
    zone_config_path: str
    infer_every_n_frames: int
    frame_store: FrameStore
    reader: CameraReader | VideoFileReader
    zone_configs: list
    reasoner: ZoneReasoner
    tracker: StateTracker
    detector: YoloDetector
    last_infer_ts: float = 0.0
    last_inferred_frame_id: int = -1
    last_result: dict[str, Any] | None = None
    last_preview_ts: float = 0.0
    last_debug_ts: float = 0.0
    last_detect_ms: float = 0.0

    def get_latest_frame(self):
        return self.frame_store.get_latest(self.camera_id)

    def get_health(self) -> str:
        try:
            return self.reader.get_health()
        except Exception:
            return "unknown"


class VisionRuntime:
    def __init__(self, project_root: Path = PROJECT_ROOT) -> None:
        self.project_root = project_root
        self.camera_config_path = self.project_root / "configs" / "cameras.json"
        self.rule_config_path = self.project_root / "configs" / "rules.json"
        self.ingest_config_path = self.project_root / "configs" / "ingest.json"
        self.runtime_config_path = self.project_root / "configs" / "runtime.json"
        self.history_dir = self.project_root / "outputs" / "history"
        self.runtime_dir = self.project_root / "outputs" / "runtime"
        self.slot_snapshot_path = self.runtime_dir / "slot_states_latest.json"
        self._start_ts = time.time()

        self.camera_configs = [cfg for cfg in load_camera_configs(self.camera_config_path) if cfg.enabled]
        self.rule_cfg = load_rule_config(self.rule_config_path)
        self.ingest_cfg = load_ingest_config(self.ingest_config_path)
        self.runtime_cfg = load_json_dict(self.runtime_config_path)
        validate_camera_configs(self.camera_configs)
        validate_rule_config(self.rule_cfg)
        validate_ingest_config(self.ingest_cfg)

        self.export_interval_sec = max(0.1, float(self.runtime_cfg.get("export_interval_ms", 500)) / 1000.0)
        self.debug_export_interval_sec = 1.0 / max(1.0, float(self.runtime_cfg.get("debug_export_fps", 2.0)))
        self.websocket_push_interval_sec = 1.0 / max(0.5, float(self.runtime_cfg.get("websocket_push_fps", 3.0)))
        self.preview_width = int(self.runtime_cfg.get("preview_width", 960))
        self.preview_height = int(self.runtime_cfg.get("preview_height", 540))
        self.schedule_sleep_sec = max(0.001, float(self.runtime_cfg.get("schedule_sleep_ms", 5)) / 1000.0)
        server_cfg = self.runtime_cfg.get("server", {})
        self.server_host = str(server_cfg.get("host", "192.168.1.64"))
        self.server_port = int(server_cfg.get("port", 2112))
        self.websocket_path = str(server_cfg.get("websocket_path", "/ws/slot-states"))
        raw_allowlist = server_cfg.get("ip_allowlist", [])
        self.ip_allowlist_entries = [str(item).strip() for item in raw_allowlist if str(item).strip()] if isinstance(raw_allowlist, list) else []
        self.ip_allowlist_networks = self._parse_ip_allowlist(self.ip_allowlist_entries)

        self.camera_runtimes: list[CameraRuntime] = []
        self.state_store = SlotStateStore([])
        self._ws_client_lock = threading.Lock()
        self._ws_clients: set[Any] = set()
        self._stop_event = threading.Event()
        self._runtime_lock = threading.Lock()
        self._last_export_ts = 0.0
        self._last_ws_broadcast_ts = 0.0
        self._log_state_path = self.history_dir / "slot_state_changes.jsonl"
        self._build_camera_runtimes()

    def _build_camera_runtimes(self) -> None:
        bundles: list[CameraSlotBundle] = []
        for camera_cfg in self.camera_configs:
            zone_config_path = camera_cfg.zone_config or ""
            if not zone_config_path:
                raise ValueError(f"{camera_cfg.camera_id}: zone_config is required")
            zone_configs = [zone for zone in load_zone_configs(zone_config_path) if zone.enabled]
            reasoner = ZoneReasoner(zone_configs, self.rule_cfg)
            tracker = StateTracker(self.rule_cfg)
            detector = YoloDetector(
                camera_cfg.model_path,
                self.rule_cfg.conf_threshold,
                img_size=self.rule_cfg.img_size,
                batch_size=self.rule_cfg.batch_size,
                batch_timeout_ms=self.rule_cfg.batch_timeout_ms,
                max_pending_requests=self.rule_cfg.max_pending_requests,
            )
            frame_store = FrameStore()
            reader = self._build_reader(camera_cfg.camera_id, camera_cfg.source_type, camera_cfg.source_path, frame_store)
            runtime = CameraRuntime(
                camera_id=camera_cfg.camera_id,
                camera_name=camera_cfg.name,
                camera_type=camera_cfg.camera_type,
                source_type=camera_cfg.source_type,
                source_path=camera_cfg.source_path,
                model_path=camera_cfg.model_path,
                zone_config_path=zone_config_path,
                infer_every_n_frames=max(1, int(camera_cfg.infer_every_n_frames)),
                frame_store=frame_store,
                reader=reader,
                zone_configs=zone_configs,
                reasoner=reasoner,
                tracker=tracker,
                detector=detector,
            )
            self.camera_runtimes.append(runtime)
            bundles.append(CameraSlotBundle(camera_id=camera_cfg.camera_id, camera_name=camera_cfg.name, zone_configs=zone_configs))

        self.state_store = SlotStateStore(bundles)

    def _build_reader(self, camera_id: str, source_type: str, source_path: str, frame_store: FrameStore):
        decode_fps = float(self.ingest_cfg.reader_output_fps)
        if source_type in {"rtsp", "live"}:
            reader = CameraReader(
                camera_id,
                source_path,
                frame_store,
                expected_fps=decode_fps,
                ingest_config=self.ingest_cfg,
            )
        else:
            source = str(ensure_exists(resolve_project_path(source_path), "Video source"))
            reader = VideoFileReader(camera_id, source, frame_store, target_fps=decode_fps)
        reader.start()
        return reader

    def start(self) -> None:
        self._stop_event.clear()
        for runtime in self.camera_runtimes:
            logger.info("Started camera runtime: %s", runtime.camera_id)

    def stop(self) -> None:
        self._stop_event.set()
        for runtime in self.camera_runtimes:
            try:
                runtime.reader.stop()
            except Exception:
                logger.exception("Failed to stop reader for %s", runtime.camera_id)

    def should_stop(self) -> bool:
        return self._stop_event.is_set()

    def request_stop(self) -> None:
        self._stop_event.set()

    def run_loop(self) -> None:
        self.start()
        try:
            while not self.should_stop():
                now_ts = time.time()
                current_snapshot = self.snapshot(now_ts)
                updated_any = False
                for runtime in self._select_due_runtimes(now_ts):
                    updated_any |= self._process_camera(runtime, now_ts)

                if updated_any or (now_ts - self._last_export_ts) >= self.export_interval_sec:
                    current_snapshot = self.snapshot(now_ts)
                    self._export_snapshot(current_snapshot)
                    self._last_export_ts = now_ts

                if (now_ts - self._last_ws_broadcast_ts) >= self.websocket_push_interval_sec:
                    self._last_ws_broadcast_ts = now_ts
                    self.broadcast(current_snapshot)

                time.sleep(self.schedule_sleep_sec)
        finally:
            self.stop()

    def _select_due_runtimes(self, now_ts: float) -> list[CameraRuntime]:
        due: list[tuple[float, CameraRuntime]] = []
        for runtime in self.camera_runtimes:
            live_frame = runtime.get_latest_frame()
            if live_frame is None or live_frame.frame_id == runtime.last_inferred_frame_id:
                continue
            target_interval = 1.0 / max(0.1, float(self.ingest_cfg.reader_output_fps) / max(1, runtime.infer_every_n_frames))
            if (now_ts - runtime.last_infer_ts) < target_interval * 0.6:
                continue
            score = (now_ts - runtime.last_infer_ts) / target_interval
            if runtime.get_health() != "online":
                score *= 0.2
            due.append((score, runtime))
        due.sort(key=lambda item: item[0], reverse=True)
        return [runtime for _, runtime in due[: max(1, int(self.rule_cfg.batch_size))]]

    def _process_camera(self, runtime: CameraRuntime, now_ts: float) -> bool:
        live_frame = runtime.get_latest_frame()
        if live_frame is None:
            return False

        t0 = time.perf_counter()
        try:
            result = runtime.detector.infer(live_frame.frame, runtime.camera_id, live_frame.frame_id, live_frame.timestamp)
        except Exception:
            logger.exception("Inference failed for %s frame_id=%s", runtime.camera_id, live_frame.frame_id)
            result = None
        detect_ms = (time.perf_counter() - t0) * 1000.0
        if result is None:
            result = DetectionResult(
                camera_id=runtime.camera_id,
                frame_id=live_frame.frame_id,
                timestamp=live_frame.timestamp,
                detections=[],
            )

        observations = runtime.reasoner.observe(result, live_frame.frame.shape)
        changed_states = runtime.tracker.update_observations(observations)
        current_states = runtime.tracker.get_current_states(runtime.camera_id, live_frame.timestamp)
        runtime.last_infer_ts = live_frame.timestamp
        runtime.last_inferred_frame_id = live_frame.frame_id
        runtime.last_detect_ms = detect_ms
        runtime.last_result = {
            "camera_id": runtime.camera_id,
            "camera_name": runtime.camera_name,
            "frame_id": live_frame.frame_id,
            "timestamp": live_frame.timestamp,
            "detections": [self._serialize_detection(det) for det in result.detections],
        }

        self.state_store.update_camera_state(
            camera_id=runtime.camera_id,
            camera_name=runtime.camera_name,
            zone_configs=runtime.zone_configs,
            zone_states=current_states,
            timestamp=live_frame.timestamp,
            health=runtime.get_health(),
            detect_ms=detect_ms,
            frame_id=live_frame.frame_id,
        )

        # State changes are persisted as a light append-only audit trail for future review.
        if changed_states:
            for state in changed_states:
                append_jsonl_rotating(
                    self._log_state_path,
                    {
                        "camera_id": state.camera_id,
                        "zone_id": state.zone_id,
                        "state": state.state,
                        "score": round(float(state.score), 4),
                        "timestamp": state.timestamp,
                    },
                    max_bytes=10 * 1024 * 1024,
                    backup_count=7,
                )
        return True

    @staticmethod
    def _serialize_detection(det: Detection) -> dict[str, Any]:
        return {
            "class_name": det.class_name,
            "confidence": round(float(det.confidence), 4),
            "bbox_xyxy": list(det.bbox_xyxy),
        }

    def snapshot(self, timestamp: float | None = None) -> dict[str, Any]:
        return self.state_store.get_snapshot(timestamp or time.time())

    def cameras_payload(self) -> dict[str, Any]:
        payload = {
            "timestamp": build_snapshot_payload([], time.time())["timestamp"],
            "cameras": [],
        }
        for runtime in self.camera_runtimes:
            payload["cameras"].append(
                {
                    "camera_id": runtime.camera_id,
                    "camera_name": runtime.camera_name,
                    "health": runtime.get_health(),
                    "slot_count": len(runtime.zone_configs),
                    "last_frame_id": runtime.last_inferred_frame_id,
                    "last_infer_at": runtime.last_infer_ts,
                }
            )
        return payload

    def build_health_payload(self) -> dict[str, Any]:
        snapshot = self.snapshot()
        return {
            "status": "online" if not self.should_stop() else "stopping",
            "timestamp": snapshot["timestamp"],
            "uptime_sec": round(time.time() - self._start_ts, 3),
            "camera_count": snapshot.get("camera_count", 0),
            "online_camera_count": snapshot.get("online_camera_count", 0),
            "total_slots": snapshot.get("total_slots", 0),
            "unknown_slots": sum(1 for item in snapshot.get("slots", []) if item.get("state") == "Unknown"),
        }

    def server_info_payload(self) -> dict[str, Any]:
        return {
            "service": "HAMAS25018 Vision Server",
            "role": "Occupancy Sensor Server",
            "timestamp": build_snapshot_payload([], time.time())["timestamp"],
            "listen": {
                "host": self.server_host,
                "port": self.server_port,
            },
            "endpoints": {
                "health": "/health",
                "server_info": "/api/v1/server-info",
                "slots_snapshot": "/api/v1/slots",
                "cameras": "/api/v1/cameras",
                "websocket_slots": self.websocket_path,
                "monitor": "/monitor",
            },
            "slot_contract": {
                "states": ["Empty", "Occupied", "Unknown"],
                "required_fields": ["camera_id", "slot_id", "state"],
                "unknown_rule": "Unknown must not be treated as Empty.",
            },
            "runtime": {
                "camera_count": len(self.camera_runtimes),
                "websocket_push_fps": round(1.0 / self.websocket_push_interval_sec, 3),
                "snapshot_export_interval_sec": self.export_interval_sec,
            },
            "security": {
                "ip_allowlist_enabled": bool(self.ip_allowlist_entries),
                "ip_allowlist": self.ip_allowlist_entries,
            },
        }

    def is_client_allowed(self, client_ip: str) -> bool:
        if not self.ip_allowlist_networks:
            return True
        try:
            address = ipaddress.ip_address(client_ip)
        except ValueError:
            return False
        return any(address in network for network in self.ip_allowlist_networks)

    @staticmethod
    def _parse_ip_allowlist(entries: list[str]) -> list[ipaddress._BaseNetwork]:
        networks = []
        for entry in entries:
            try:
                if "/" in entry:
                    networks.append(ipaddress.ip_network(entry, strict=False))
                else:
                    networks.append(ipaddress.ip_network(f"{entry}/32", strict=False))
            except ValueError as exc:
                raise ValueError(f"Invalid server.ip_allowlist entry: {entry}") from exc
        return networks

    def _export_snapshot(self, snapshot: dict[str, Any]) -> None:
        write_json_atomic(self.slot_snapshot_path, snapshot, indent=None)

    def register_ws_client(self, conn) -> None:
        with self._ws_client_lock:
            self._ws_clients.add(conn)

    def unregister_ws_client(self, conn) -> None:
        with self._ws_client_lock:
            self._ws_clients.discard(conn)

    def broadcast(self, snapshot: dict[str, Any]) -> None:
        message = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        frame = self._encode_ws_text(message)
        dead = []
        with self._ws_client_lock:
            clients = list(self._ws_clients)
        for conn in clients:
            try:
                conn.sendall(frame)
            except OSError:
                dead.append(conn)
        for conn in dead:
            self.unregister_ws_client(conn)
            try:
                conn.close()
            except OSError:
                pass

    def send_current_snapshot_to_client(self, conn) -> None:
        snapshot = self.snapshot()
        frame = self._encode_ws_text(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        conn.sendall(frame)

    def hold_ws_connection(self, conn) -> None:
        while not self.should_stop():
            try:
                data = conn.recv(2)
                if not data:
                    break
            except socket.timeout:  # type: ignore[name-defined]
                continue
            except OSError:
                break

    @staticmethod
    def _encode_ws_text(message: bytes) -> bytes:
        length = len(message)
        header = bytearray([0x81])
        if length < 126:
            header.append(length)
        elif length < 65536:
            header.append(126)
            header.extend(length.to_bytes(2, "big"))
        else:
            header.append(127)
            header.extend(length.to_bytes(8, "big"))
        return bytes(header) + message
