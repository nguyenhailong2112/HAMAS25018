from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any

from core.slot_contract import build_raw_slot_item, build_snapshot_payload
from core.types import ZoneConfig, ZoneState


@dataclass(frozen=True)
class CameraSlotBundle:
    camera_id: str
    camera_name: str
    zone_configs: list[ZoneConfig]


class SlotStateStore:
    def __init__(self, camera_bundles: list[CameraSlotBundle]) -> None:
        self._lock = Lock()
        self._camera_bundles = {bundle.camera_id: bundle for bundle in camera_bundles}
        self._latest: dict[str, dict[str, Any]] = {}
        self._camera_meta: dict[str, dict[str, Any]] = {}

        for bundle in camera_bundles:
            self._camera_meta[bundle.camera_id] = {
                "camera_id": bundle.camera_id,
                "camera_name": bundle.camera_name,
                "timestamp": 0.0,
                "health": "unknown",
                "detect_ms": None,
                "frame_id": None,
                "slot_count": len(bundle.zone_configs),
            }
            for zone_cfg in bundle.zone_configs:
                unknown_state = ZoneState(
                    camera_id=bundle.camera_id,
                    zone_id=zone_cfg.zone_id,
                    state="unknown",
                    score=0.0,
                    timestamp=0.0,
                    health="unknown",
                )
                key = self._slot_key(bundle.camera_id, zone_cfg.zone_id)
                self._latest[key] = {
                    "camera_id": bundle.camera_id,
                    "slot_id": zone_cfg.zone_id,
                    "nodeName": zone_cfg.node_name,
                    "state": "Unknown",
                }

    def update_camera_state(
        self,
        *,
        camera_id: str,
        camera_name: str,
        zone_configs: list[ZoneConfig],
        zone_states: list[ZoneState],
        timestamp: float,
        health: str,
        detect_ms: float | None = None,
        frame_id: int | None = None,
    ) -> None:
        with self._lock:
            self._camera_meta[camera_id] = {
                "camera_id": camera_id,
                "camera_name": camera_name,
                "timestamp": timestamp,
                "health": health,
                "detect_ms": detect_ms,
                "frame_id": frame_id,
                "slot_count": len(zone_configs),
            }
            for zone_cfg, state in zip(zone_configs, zone_states):
                key = self._slot_key(camera_id, zone_cfg.zone_id)
                self._latest[key] = build_raw_slot_item(
                    camera_id,
                    zone_cfg.zone_id,
                    state,
                    node_name=zone_cfg.node_name,
                    camera_name=camera_name,
                    detect_ms=detect_ms,
                    frame_id=frame_id,
                )

    def get_snapshot(self, timestamp: float) -> dict[str, Any]:
        with self._lock:
            items = sorted(
                [{"nodeName": item.get("nodeName", ""), "state": item.get("state", "Unknown")} for item in self._latest.values()],
                key=lambda item: str(item.get("nodeName", "")),
            )
            snapshot = build_snapshot_payload(items, timestamp)
            snapshot["camera_count"] = len(self._camera_meta)
            snapshot["online_camera_count"] = sum(1 for meta in self._camera_meta.values() if meta.get("health") == "online")
            snapshot["camera_meta"] = list(self._camera_meta.values())
            snapshot["camera_layout"] = self._build_camera_layout()
            return snapshot

    def get_raw_snapshot(self, timestamp: float) -> dict[str, Any]:
        with self._lock:
            items = sorted(
                [
                    {
                        "camera_id": item.get("camera_id"),
                        "slot_id": item.get("slot_id"),
                        "nodeName": item.get("nodeName"),
                        "state": item.get("state", "Unknown"),
                    }
                    for item in self._latest.values()
                ],
                key=lambda item: (str(item.get("camera_id", "")), str(item.get("slot_id", ""))),
            )
            snapshot = build_snapshot_payload(items, timestamp)
            snapshot["camera_count"] = len(self._camera_meta)
            snapshot["online_camera_count"] = sum(1 for meta in self._camera_meta.values() if meta.get("health") == "online")
            return snapshot

    def get_camera_snapshot(self, camera_id: str, timestamp: float) -> dict[str, Any]:
        with self._lock:
            items = [
                payload
                for key, payload in self._latest.items()
                if key.startswith(f"{camera_id}:")
            ]
            items.sort(key=lambda item: str(item.get("nodeName", "")))
            snapshot = build_snapshot_payload(items, timestamp)
            snapshot["camera"] = self._camera_meta.get(camera_id, {"camera_id": camera_id})
            return snapshot

    def _build_camera_layout(self) -> list[dict[str, Any]]:
        layout: list[dict[str, Any]] = []
        for camera_id, bundle in self._camera_bundles.items():
            slots = []
            for zone_cfg in bundle.zone_configs:
                item = self._latest.get(self._slot_key(camera_id, zone_cfg.zone_id))
                if item is None:
                    item = {
                        "camera_id": camera_id,
                        "slot_id": zone_cfg.zone_id,
                        "nodeName": zone_cfg.node_name,
                        "state": "Unknown",
                    }
                slots.append(dict(item))
            layout.append(
                {
                    "camera_id": camera_id,
                    "camera_name": bundle.camera_name,
                    "slots": sorted(slots, key=lambda item: str(item.get("nodeName", ""))),
                }
            )
        return layout

    def get_slot(self, camera_id: str, slot_id: str, timestamp: float) -> dict[str, Any] | None:
        with self._lock:
            item = self._latest.get(self._slot_key(camera_id, slot_id))
            return dict(item) if item is not None else None

    def get_node(self, node_name: str) -> dict[str, Any] | None:
        normalized = str(node_name).strip()
        if not normalized:
            return None
        with self._lock:
            for item in self._latest.values():
                if str(item.get("nodeName", "")).strip() == normalized:
                    return dict(item)
        return None

    @staticmethod
    def _slot_key(camera_id: str, slot_id: str) -> str:
        return f"{camera_id}:{slot_id}"
