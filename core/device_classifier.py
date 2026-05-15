from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from typing import Any

try:
    from core.ai_engine import build_asset_report
except Exception:
    build_asset_report = None

MOBILE_VENDOR_HINTS = (
    "xiaomi",
    "redmi",
    "mi ",
    "huawei",
    "honor",
    "oppo",
    "vivo",
    "realme",
    "oneplus",
    "samsung",
    "sony",
    "motorola",
    "google",
    "pixel",
    "nokia",
    "meizu",
    "lenovo",
    "asus",
    "zte",
    "nubia",
    "tcl",
    "poco",
    "apple",
)

ROUTER_KEYWORDS = (
    "router",
    "gateway",
    "login",
    "admin",
    "tp-link",
    "tplink",
    "huawei",
    "d-link",
    "dlink",
    "xiaomi",
    "miwifi",
    "netgear",
    "mercusys",
    "tenda",
    "fast",
    "phicomm",
    "ruijie",
    "hikvision",
    "dahua",
    "uniview",
    "nvr",
    "ipc",
    "camera",
    "摄像头",
    "路由",
)

WEB_TITLE_SUFFIX_RE = re.compile(r"\s*(?:[-|—–]\s*)?(?:login|admin|management|web|登录|管理|管理页面|登录页面)$", re.IGNORECASE)


@dataclass(slots=True)
class DeviceClassification:
    device_type: str = "未知设备"
    device_name: str = ""
    evidence: str = ""
    confidence: float = 0.3

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["confidence"] = round(float(self.confidence), 2)
        return data


def _clean_title(title: str) -> str:
    cleaned = " ".join((title or "").split()).strip()
    if not cleaned:
        return ""
    cleaned = WEB_TITLE_SUFFIX_RE.sub("", cleaned).strip(" -|—–\t")
    return cleaned


def _looks_like_router_title(title: str) -> bool:
    lowered = title.lower()
    return any(keyword in lowered for keyword in ROUTER_KEYWORDS)


def _looks_like_mobile_vendor(vendor: str) -> bool:
    lowered = vendor.lower()
    return any(keyword in lowered for keyword in MOBILE_VENDOR_HINTS)


def classify_device(
    *,
    mac: str,
    vendor: str,
    open_ports: list[int] | None,
    hostname: str = "",
    web_title: str = "",
    netbios_name: str = "",
) -> dict[str, Any]:
    ports = set(open_ports or [])
    vendor_text = vendor or "未知"
    hostname_text = (hostname or "").strip()
    netbios_text = (netbios_name or "").strip()
    title_text = _clean_title(web_title)

    if 135 in ports:
        device_name = netbios_text or hostname_text or title_text or "Windows 设备"
        evidence = ["135 端口开放（RPC/SMB）"]
        if netbios_text:
            evidence.append(f"NetBIOS：{netbios_text}")
        elif hostname_text:
            evidence.append(f"主机名：{hostname_text}")
        return DeviceClassification(
            device_type="Windows 设备",
            device_name=device_name,
            evidence="；".join(evidence),
            confidence=0.96,
        ).to_dict()

    if 62078 in ports:
        device_name = title_text or hostname_text or "Apple 移动终端"
        evidence = ["62078 端口开放（Apple 生态强特征）"]
        if vendor_text != "未知":
            evidence.append(f"MAC 厂商：{vendor_text}")
        return DeviceClassification(
            device_type="Apple 移动终端",
            device_name=device_name,
            evidence="；".join(evidence),
            confidence=0.97,
        ).to_dict()

    if 8008 in ports:
        device_name = title_text or hostname_text or vendor_text or "Android/投屏终端"
        evidence = ["8008 端口开放（Google Cast / 投屏强特征）"]
        if vendor_text != "未知":
            evidence.append(f"MAC 厂商：{vendor_text}")
        return DeviceClassification(
            device_type="Android/投屏终端",
            device_name=device_name,
            evidence="；".join(evidence),
            confidence=0.92,
        ).to_dict()

    if title_text:
        if _looks_like_router_title(title_text):
            device_type = "路由器/摄像头"
            confidence = 0.88
        else:
            device_type = "Web 管理设备"
            confidence = 0.76
        evidence = ["80 端口开放（Web 界面）", f"标题：{title_text}"]
        if vendor_text != "未知":
            evidence.append(f"MAC 厂商：{vendor_text}")
        return DeviceClassification(
            device_type=device_type,
            device_name=title_text,
            evidence="；".join(evidence),
            confidence=confidence,
        ).to_dict()

    # 关键厂商直接映射（中等置信度）
    if vendor_text != "未知":
        vendor_lower = vendor_text.lower()
        # 安卓系厂商
        android_vendors = ("xiaomi", "redmi", "huawei", "honor", "oppo", "vivo", "realme", "oneplus", "samsung", "zte", "tcl", "poco")
        if any(kw in vendor_lower for kw in android_vendors):
            return DeviceClassification(
                device_type="安卓移动终端",
                device_name=hostname_text or vendor_text,
                evidence=f"MAC 厂商：{vendor_text}",
                confidence=0.72,
            ).to_dict()

    # 启发式规则：无端口但厂商未知且有 MAC = 可能是被动发现的移动设备
    if not ports and mac != "-" and vendor_text == "未知":
        return DeviceClassification(
            device_type="未知移动设备(疑似)",
            device_name=hostname_text or "未命名设备",
            evidence="无特征端口；MAC 前缀未在数据库找到；可能是手机或 IoT 设备（需手动诊断）",
            confidence=0.48,
        ).to_dict()

    if vendor_text != "未知" and _looks_like_mobile_vendor(vendor_text):
        return DeviceClassification(
            device_type="安卓移动终端(疑似)",
            device_name=hostname_text or vendor_text,
            evidence=f"MAC 厂商：{vendor_text}",
            confidence=0.64,
        ).to_dict()

    if vendor_text != "未知":
        return DeviceClassification(
            device_type="厂商设备",
            device_name=hostname_text or vendor_text,
            evidence=f"MAC 厂商：{vendor_text}",
            confidence=0.52,
        ).to_dict()
    # 基础启发式未给出高置信度结果，返回默认分类。
    base = DeviceClassification(
        device_type="未知设备",
        device_name=hostname_text or mac or "未知",
        evidence="信息不足，未命中高置信度规则",
        confidence=0.3,
    ).to_dict()

    # 若置信度较低且有可用的 AI 接口，则尝试调用 AI 进行补充推断（异步调用者可忽略）
    try:
        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        zhipu_key = os.getenv("ZHIPU_API_KEY", "").strip()
        if build_asset_report and float(base.get("confidence", 0)) < 0.7 and (groq_key or zhipu_key):
            # 构建最小设备信息，交给 AI 进一步推测
            device = {
                "ip": "",
                "mac": mac,
                "vendor": vendor_text,
                "device_type": base.get("device_type", "未知设备"),
                "device_name": base.get("device_name", ""),
                "evidence": base.get("evidence", ""),
                "confidence": base.get("confidence", 0.3),
                "hostname": hostname_text,
                "open_ports": list(ports),
                "web_title": title_text,
            }
            try:
                if groq_key:
                    text = build_asset_report(device, groq_key, provider="groq")
                else:
                    text = build_asset_report(device, zhipu_key, provider="zhipu")
                if text and "{" in text:
                    # 尝试从 AI 文本中提取 JSON 结构化区域
                    idx = text.find("结构化数据(JSON)：")
                    json_text = None
                    if idx != -1:
                        start = text.find("{", idx)
                    else:
                        start = text.rfind("{")
                    if start != -1:
                        # 找到匹配的右括号
                        depth = 0
                        end = -1
                        for i in range(start, len(text)):
                            if text[i] == "{":
                                depth += 1
                            elif text[i] == "}":
                                depth -= 1
                                if depth == 0:
                                    end = i + 1
                                    break
                        if end != -1:
                            candidate = text[start:end]
                            try:
                                parsed = json.loads(candidate)
                                json_text = parsed
                            except Exception:
                                json_text = None
                    if isinstance(json_text, dict):
                        # 使用 AI 的结构化字段补强结果
                        ai_name = json_text.get("device_name") or json_text.get("name")
                        ai_purpose = json_text.get("purpose")
                        ai_risks = json_text.get("risk_tips")
                        ai_conf = json_text.get("confidence")
                        if ai_name:
                            base["device_name"] = ai_name
                        if ai_conf is not None:
                            try:
                                ai_conf_f = float(ai_conf)
                                base["confidence"] = round(max(float(base.get("confidence", 0)), ai_conf_f), 2)
                            except Exception:
                                pass
                        # 将 AI 推断加入 evidence
                        extras = []
                        if ai_purpose:
                            extras.append(f"用途（AI 推测）：{ai_purpose}")
                        if ai_risks:
                            if isinstance(ai_risks, (list, tuple)):
                                extras.append("风险提示（AI）：" + ";".join(str(x) for x in ai_risks))
                            else:
                                extras.append(f"风险提示（AI）：{ai_risks}")
                        if extras:
                            base["evidence"] = (base.get("evidence", "") + "；" + "；".join(extras)).strip("；")
            except Exception:
                pass
    except Exception:
        pass

    return base
