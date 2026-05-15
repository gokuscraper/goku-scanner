from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


_LOCK = threading.Lock()
_DATA_PATH = Path(__file__).resolve().parent.parent / "data"
_DATA_PATH.mkdir(parents=True, exist_ok=True)
_STORE_FILE = _DATA_PATH / "devices.json"


def _load_store() -> Dict[str, Any]:
    if not _STORE_FILE.exists():
        return {}
    try:
        with _STORE_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_store(data: Dict[str, Any]) -> None:
    with _LOCK:
        with _STORE_FILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def get_note(ip: str) -> str:
    data = _load_store()
    return data.get(ip, {}).get("note", "")


def set_note(ip: str, note: str) -> None:
    data = _load_store()
    entry = data.get(ip, {})
    entry["note"] = note
    entry.setdefault("last_seen", None)
    data[ip] = entry
    _save_store(data)


def update_last_seen(ip: str, when: datetime) -> None:
    """保存为本地时区的 ISO 字符串（便于直接展示）。"""
    try:
        local_iso = when.astimezone().isoformat()
    except Exception:
        local_iso = when.isoformat()

    data = _load_store()
    entry = data.get(ip, {})
    entry["last_seen"] = local_iso
    entry.setdefault("note", "")
    data[ip] = entry
    _save_store(data)


def get_device_info(ip: str) -> Dict[str, Any]:
    data = _load_store()
    return data.get(ip, {})
