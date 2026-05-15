from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


APP_DIR = Path(__file__).resolve().parent.parent
SETTINGS_FILE = APP_DIR / "framework_settings.json"


DEFAULT_STATE: Dict[str, Any] = {
    "lang": "zh",
    "target_input": "",
    "scan_results": [],
    "selected_device": None,
    "ai_report": "",
    "ai_struct": None,
    "show_virtual_adapters": False,
    "last_result_text": "",
    "last_result_name": "",
    "env_ready": True,
}


STATE: Dict[str, Any] = dict(DEFAULT_STATE)


def load_settings() -> Dict[str, Any]:
    if not SETTINGS_FILE.exists():
        return {"target_input": ""}
    try:
        with SETTINGS_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            return data if isinstance(data, dict) else {"target_input": ""}
    except Exception:
        return {"target_input": ""}


def save_settings(target_input: str) -> None:
    data = {
        "target_input": target_input,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    with SETTINGS_FILE.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def init_state() -> Dict[str, Any]:
    settings = load_settings()
    STATE.clear()
    STATE.update(DEFAULT_STATE)
    STATE["target_input"] = settings.get("target_input", "")
    return STATE


def set_selected_device(device: dict[str, Any] | None) -> None:
    STATE["selected_device"] = device


def set_scan_results(results: list[dict[str, Any]]) -> None:
    STATE["scan_results"] = results


def set_ai_report(report: str) -> None:
    STATE["ai_report"] = report


def set_ai_struct(data: dict[str, Any] | None) -> None:
    STATE["ai_struct"] = data


def set_show_virtual_adapters(value: bool) -> None:
    STATE["show_virtual_adapters"] = bool(value)
