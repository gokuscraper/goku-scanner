from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Optional

APP_DIR = Path(__file__).resolve().parent.parent
KEY_FILE = APP_DIR / ".zhipu_api_key"
GROQ_KEY_FILE = APP_DIR / ".groq_api_key"


def _is_windows() -> bool:
    return os.name == "nt"


if _is_windows():
    import ctypes
    from ctypes import wintypes

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


    def _encrypt_windows(data: bytes) -> bytes:
        blob_in = DATA_BLOB()
        blob_in.cbData = len(data)
        blob_in.pbData = ctypes.cast(ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_ubyte))
        blob_out = DATA_BLOB()
        if crypt32.CryptProtectData(ctypes.byref(blob_in), None, None, None, None, 0x01, ctypes.byref(blob_out)):
            try:
                buffer = ctypes.cast(blob_out.pbData, ctypes.POINTER(ctypes.c_ubyte * blob_out.cbData)).contents
                return bytes(buffer)
            finally:
                if blob_out.pbData:
                    kernel32.LocalFree(blob_out.pbData)
        raise ctypes.WinError()


    def _decrypt_windows(data: bytes) -> bytes:
        blob_in = DATA_BLOB()
        blob_in.cbData = len(data)
        blob_in.pbData = ctypes.cast(ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_ubyte))
        blob_out = DATA_BLOB()
        if crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0x01, ctypes.byref(blob_out)):
            try:
                buffer = ctypes.cast(blob_out.pbData, ctypes.POINTER(ctypes.c_ubyte * blob_out.cbData)).contents
                return bytes(buffer)
            finally:
                if blob_out.pbData:
                    kernel32.LocalFree(blob_out.pbData)
        raise ctypes.WinError()


def _save_key_file(path: Path, api_key: str) -> bool:
    try:
        if not api_key:
            return False
        data = api_key.encode("utf-8")
        if _is_windows():
            enc = _encrypt_windows(data)
        else:
            enc = base64.b64encode(data)
        path.write_text(base64.b64encode(enc).decode("ascii"), encoding="utf-8")
        try:
            os.chmod(path, 0o600)
        except Exception:
            pass
        return True
    except Exception:
        return False


def _load_key_file(path: Path) -> Optional[str]:
    try:
        if not path.exists():
            return None
        raw = path.read_text(encoding="utf-8")
        enc = base64.b64decode(raw)
        if _is_windows():
            dec = _decrypt_windows(enc)
        else:
            dec = base64.b64decode(enc)
        return dec.decode("utf-8")
    except Exception:
        return None


def save_api_key(api_key: str) -> bool:
    """保存智谱 API Key 到本地文件（Windows 使用 DPAPI 加密）。"""
    return _save_key_file(KEY_FILE, api_key)


def load_api_key() -> Optional[str]:
    """从本地读取并解密智谱 API Key，失败返回 None。"""
    return _load_key_file(KEY_FILE)


def save_groq_api_key(api_key: str) -> bool:
    """保存 Groq API Key 到本地文件（Windows 使用 DPAPI 加密）。"""
    return _save_key_file(GROQ_KEY_FILE, api_key)


def load_groq_api_key() -> Optional[str]:
    """从本地读取并解密 Groq API Key，失败返回 None。"""
    return _load_key_file(GROQ_KEY_FILE)
