from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from core.types import ZoneState


@dataclass(frozen=True)
class SlotConfigView:
    camera_id: str
    zone_id: str
    name: str


def format_timestamp(ts: float | None) -> str | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).astimezone().isoformat(timespec="milliseconds")


def state_to_public_label(state: str) -> str:
    normalized = (state or "").strip().lower()
    if normalized == "occupied":
        return "Car Full"
    if normalized == "empty":
        return "Empty"
    return "Unknown"

def build_public_slot_item(
    camera_id: str,
    slot_id: str,
    state: ZoneState,
    *,
    camera_name: str | None = None,
    detect_ms: float | None = None,
    frame_id: int | None = None,
) -> dict[str, Any]:
    return {
        "camera_id": camera_id,
        "slot_id": slot_id,
        "state": state_to_public_label(state.state),
    }


def build_raw_slot_item(
    camera_id: str,
    slot_id: str,
    state: ZoneState,
    *,
    camera_name: str | None = None,
    detect_ms: float | None = None,
    frame_id: int | None = None,
) -> dict[str, Any]:
    return {
        "camera_id": camera_id,
        "slot_id": slot_id,
        "state": state_to_public_label(state.state),
    }


def build_snapshot_payload(items: list[dict[str, Any]], timestamp: float) -> dict[str, Any]:
    return {
        "timestamp": format_timestamp(timestamp),
        "total_slots": len(items),
        "slots": items,
    }
