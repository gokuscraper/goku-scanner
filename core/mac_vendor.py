"""MAC 厂商识别封装."""
from __future__ import annotations

from functools import lru_cache

from mac_vendor_lookup import InvalidMacError, MacLookup, VendorNotFoundError


@lru_cache(maxsize=1)
def _get_lookup() -> MacLookup:
    lookup = MacLookup()
    try:
        # 禁用自动更新，直接使用本地缓存（避免网络请求卡住）
        # lookup.update_vendors()
        lookup.load_vendors()
    except Exception:
        # 降级：使用内置缓存或离线数据库
        try:
            lookup.load_vendors()
        except Exception:
            pass
    return lookup


def get_vendor_from_mac(mac: str) -> str:
    """根据 MAC 地址查询厂商名称，未知时返回“未知”。"""
    if not mac or mac == "-":
        return "未知"

    try:
        return _get_lookup().lookup(mac)
    except (InvalidMacError, VendorNotFoundError):
        return "未知"
    except Exception:
        return "未知"


def reload_vendor_db() -> None:
    """清空缓存并重新加载厂商库。"""
    _get_lookup.cache_clear()
