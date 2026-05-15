from __future__ import annotations

import ctypes
import html
import ipaddress
import os
import re
import socket
import subprocess
import time
from datetime import datetime
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import Any, Callable

from core.mac_vendor import get_vendor_from_mac
from core.device_classifier import classify_device
from core.device_store import update_last_seen, get_note, get_device_info


PING_TIMEOUT_MS = 250
SCAN_PORTS = (135, 80, 62078, 8008, 8009, 5555, 1900)


@dataclass(slots=True)
class DeviceRecord:
    ip: str
    mac: str = "-"
    vendor: str = "未知"
    device_type: str = "未知设备"
    device_name: str = ""
    evidence: str = ""
    confidence: float = 0.3
    response_ms: float | None = None
    hostname: str = ""
    web_title: str = ""
    open_ports: list[int] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["open_ports"] = self.open_ports or []
        return data


def detect_local_network() -> str:
    """尽量推断一个可扫的本地网段，失败时回退到常见私网段。"""
    try:
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)
        if host_ip.startswith("127."):
            raise OSError("loopback ip")
        network = ipaddress.ip_network(f"{host_ip}/24", strict=False)
        return str(network)
    except Exception:
        return "192.168.1.0/24"


def _ping_host(ip: str) -> float | None:
    args = ["ping", "-n", "1", "-w", str(PING_TIMEOUT_MS), ip]
    try:
        started_at = time.perf_counter()
        
        # Windows下隐藏CMD窗口
        creation_flags = 0
        if os.name == 'nt':
            creation_flags = subprocess.CREATE_NO_WINDOW
        
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=2,
            creationflags=creation_flags,  # 隐藏窗口
        )
        if completed.returncode != 0:
            return None
        return round((time.perf_counter() - started_at) * 1000, 2)
    except Exception:
        return None


def ping_stats(ip: str, count: int = 4, timeout_ms: int = 1000) -> dict:
    """对单个主机执行多次 ping，返回丢包与延迟统计（跨平台）。"""
    if os.name == "nt":
        # Windows
        args = ["ping", "-n", str(count), "-w", str(timeout_ms), ip]
    else:
        # Linux/macOS: -c count, -W timeout (seconds) or -W (ms on some platforms)
        args = ["ping", "-c", str(count), "-W", str(int(timeout_ms / 1000)), ip]

    try:
        # Windows下隐藏CMD窗口
        creation_flags = 0
        if os.name == 'nt':
            creation_flags = subprocess.CREATE_NO_WINDOW
        
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=(count * (timeout_ms / 1000.0) + 5),
            creationflags=creation_flags,  # 隐藏窗口
        )
        out = completed.stdout or completed.stderr or ""
        # 解析丢包
        sent = received = lost = 0
        loss_pct = None
        min_rtt = avg_rtt = max_rtt = None
        if os.name == "nt":
            m = re.search(r"Packets: Sent = (\d+), Received = (\d+), Lost = (\d+)", out)
            if m:
                sent = int(m.group(1)); received = int(m.group(2)); lost = int(m.group(3))
                loss_pct = round(lost / sent * 100.0, 2) if sent else None
            m2 = re.search(r"Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms", out)
            if m2:
                min_rtt = float(m2.group(1)); max_rtt = float(m2.group(2)); avg_rtt = float(m2.group(3))
            # 回退：尝试从原始输出中提取所有延迟值进行统计
            if completed.returncode == 0 and received == 0:
                # 从输出中提取所有 "time=XXms" 或 "XXms" 格式的延迟
                all_times = re.findall(r"time[=<](\d+)ms|(\d+)\s*ms", out)
                if all_times:
                    times = [float(t[0] or t[1]) for t in all_times]
                    received = len(times)
                    sent = count
                    lost = sent - received
                    loss_pct = round(lost / sent * 100.0, 2)
                    min_rtt = min(times)
                    max_rtt = max(times)
                    avg_rtt = sum(times) / len(times)
                else:
                    # 真的没有任何响应
                    sent = count
                    received = 0
                    lost = count
                    loss_pct = 100.0
        else:
            m = re.search(r"(\d+) packets transmitted, (\d+) received, .* (\d+)% packet loss", out)
            if m:
                sent = int(m.group(1)); received = int(m.group(2)); loss_pct = float(m.group(3)); lost = sent - received
            m2 = re.search(r"min/avg/max(?:/mdev)? = ([0-9\.]+)/([0-9\.]+)/([0-9\.]+)", out)
            if m2:
                min_rtt = float(m2.group(1)); avg_rtt = float(m2.group(2)); max_rtt = float(m2.group(3))

        return {
            "ip": ip,
            "sent": sent,
            "received": received,
            "lost": lost,
            "loss_pct": loss_pct,
            "min_ms": min_rtt,
            "avg_ms": avg_rtt,
            "max_ms": max_rtt,
            "raw": out,
        }
    except Exception:
        return {"ip": ip, "sent": count, "received": 0, "lost": count, "loss_pct": 100.0}


def stream_ping(ip: str, count: int = 30, timeout_ms: int = 1000):
    """实时产生每次 ping 的结果字典，适用于前端流式显示。

    在 Windows 上使用 `ping -n count`，在类 Unix 上使用 `ping -c count`。
    逐行读取子进程 stdout 并解析回复行，yield 单次回复的解析字典。
    最后会 yield 一个汇总结果字典，key 为 'summary'.
    """
    if os.name == "nt":
        args = ["ping", "-n", str(count), "-w", str(timeout_ms), ip]
    else:
        args = ["ping", "-c", str(count), "-W", str(int(timeout_ms / 1000)), ip]

    try:
        # Windows下隐藏CMD窗口
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
            encoding="utf-8",
            errors="ignore",
            creationflags=creation_flags,  # 隐藏窗口
        )
    except Exception:
        # 返回空的汇总
        yield {"ip": ip, "sent": count, "received": 0, "lost": count, "loss_pct": 100.0}
        return

    sent = 0
    received = 0
    rtts: list[float] = []

    # 逐行读取并解析
    try:
        assert proc.stdout is not None
        for raw_line in proc.stdout:
            line = raw_line.strip()
            if not line:
                continue

            # 尝试解析单次响应（Windows 和 Linux 常见模式）
            # Windows: "Reply from 8.8.8.8: bytes=32 time=44ms TTL=111"
            m_win = re.search(r"time[=<]\s*(\d+)(?:ms)?", line)
            m_unix = re.search(r"time[=]\s*([0-9\.]+)\s*ms", line)
            if "Reply from" in line or "bytes=" in line or m_win or m_unix:
                sent += 1
                rtt = None
                if m_unix:
                    try:
                        rtt = float(m_unix.group(1))
                    except Exception:
                        rtt = None
                elif m_win:
                    try:
                        rtt = float(m_win.group(1))
                    except Exception:
                        rtt = None

                if rtt is not None:
                    received += 1
                    rtts.append(rtt)

                yield {"type": "reply", "line": line, "rtt": rtt, "sent": sent, "received": received}

        # 等待进程结束
        proc.wait(timeout=1)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass

    # 汇总
    lost = sent - received
    loss_pct = round(lost / sent * 100.0, 2) if sent else 100.0
    summary = {
        "type": "summary",
        "ip": ip,
        "sent": sent,
        "received": received,
        "lost": lost,
        "loss_pct": loss_pct,
        "min_ms": round(min(rtts), 2) if rtts else None,
        "avg_ms": round(sum(rtts) / len(rtts), 2) if rtts else None,
        "max_ms": round(max(rtts), 2) if rtts else None,
    }
    yield summary


def batch_ping(ips: list[str], count: int = 1, timeout_ms: int = 250, max_workers: int = 64) -> dict[str, dict]:
    """并行对多个 IP 进行 ping，返回每个 IP 的统计结果字典。"""
    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(ping_stats, ip, count, timeout_ms): ip for ip in ips}
        for fut in as_completed(futures):
            ip = futures[fut]
            try:
                results[ip] = fut.result()
            except Exception:
                results[ip] = {"ip": ip, "sent": count, "received": 0, "lost": count, "loss_pct": 100.0}
    return results


def _get_mac_from_arp(ip: str) -> str:
    try:
        # Windows下隐藏CMD窗口
        creation_flags = 0
        if os.name == 'nt':
            creation_flags = subprocess.CREATE_NO_WINDOW
        
        completed = subprocess.run(
            ["arp", "-a"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=2,
            creationflags=creation_flags,  # 隐藏窗口
        )
        # Windows 的 arp 输出通常有前导空格，MAC 常见格式为 xx-xx-xx-xx-xx-xx
        pattern = re.compile(rf"^\s*{re.escape(ip)}\s+([0-9a-fA-F:-]{{17}})\s+", re.MULTILINE)
        match = pattern.search(completed.stdout)
        if match:
            return match.group(1).replace("-", ":").lower()
    except Exception:
        return "-"
    return "-"


def _fetch_web_title(ip: str) -> str:
    """带严格超时的Web标题抓取，避免卡住"""
    import concurrent.futures
    
    def do_fetch():
        try:
            request = urllib.request.Request(
                f"http://{ip}/",
                headers={"User-Agent": "Mozilla/5.0"},
                method="GET",
            )
            with urllib.request.urlopen(request, timeout=1.5) as response:
                content_type = response.headers.get_content_type()
                if content_type not in ("text/html", "application/xhtml+xml", "application/xml", "text/plain"):
                    return ""
                raw = response.read(16384)
                charset = response.headers.get_content_charset() or "utf-8"
                text = raw.decode(charset, errors="ignore")
                match = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
                if not match:
                    return ""
                title = html.unescape(" ".join(match.group(1).split())).strip()
                return title
        except Exception:
            return ""
    
    # 设置2秒总超时（包括连接+读取）
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(do_fetch)
        try:
            return future.result(timeout=2)
        except concurrent.futures.TimeoutError:
            return ""


def _resolve_netbios_name(ip: str) -> str:
    if os.name != "nt":
        return ""

    import concurrent.futures
    
    def do_nbtstat():
        try:
            # Windows下隐藏CMD窗口
            creation_flags = subprocess.CREATE_NO_WINDOW
            
            completed = subprocess.run(
                ["nbtstat", "-A", ip],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=2,
                creationflags=creation_flags,  # 隐藏窗口
            )
            output = completed.stdout or ""
            # 放宽匹配以兼容不同编码/字符的 NetBIOS 名称（取首个出现的 <00> 或 <20> UNIQUE 名称）
            patterns = (
                re.compile(r"^\s*(\S{1,15})\s+<00>\s+UNIQUE", re.IGNORECASE | re.MULTILINE),
                re.compile(r"^\s*(\S{1,15})\s+<20>\s+UNIQUE", re.IGNORECASE | re.MULTILINE),
            )
            for pattern in patterns:
                match = pattern.search(output)
                if match:
                    name = match.group(1).strip()
                    # 尝试去除不可见或控制字符
                    name = re.sub(r"[\x00-\x1f\x7f]+", "", name)
                    return name
        except Exception:
            return ""
        return ""
    
    # 设置2秒总超时（减少等待时间）
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(do_nbtstat)
        try:
            return future.result(timeout=2)  # 从3秒减少到2秒
        except concurrent.futures.TimeoutError:
            return ""


def _get_mac_via_sendarp_windows(ip: str) -> str:
    """Windows 下优先用 SendARP 获取 MAC，稳定性通常高于解析 arp 文本。"""
    if os.name != "nt":
        return "-"

    try:
        ws2_32 = ctypes.windll.ws2_32
        iphlpapi = ctypes.windll.iphlpapi

        inet_addr = ws2_32.inet_addr
        inet_addr.argtypes = [ctypes.c_char_p]
        inet_addr.restype = ctypes.c_ulong

        send_arp = iphlpapi.SendARP
        send_arp.argtypes = [
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_ulong),
        ]
        send_arp.restype = ctypes.c_ulong

        dest_ip = inet_addr(ip.encode("ascii"))
        if dest_ip in (0xFFFFFFFF, 0):
            return "-"

        mac_buffer = (ctypes.c_ubyte * 6)()
        mac_len = ctypes.c_ulong(ctypes.sizeof(mac_buffer))

        result = send_arp(dest_ip, 0, ctypes.byref(mac_buffer), ctypes.byref(mac_len))
        if result != 0 or mac_len.value <= 0:
            return "-"

        mac_bytes = bytes(mac_buffer[: mac_len.value])
        if len(mac_bytes) < 6:
            return "-"

        return ":".join(f"{b:02x}" for b in mac_bytes[:6])
    except Exception:
        return "-"


def _get_mac(ip: str) -> str:
    mac = _get_mac_via_sendarp_windows(ip)
    if mac != "-":
        return mac
    return _get_mac_from_arp(ip)


def _probe_ports(ip: str) -> list[int]:
    open_ports: list[int] = []
    for port in SCAN_PORTS:
        try:
            with socket.create_connection((ip, port), timeout=0.2):
                open_ports.append(port)
        except Exception:
            continue
    return open_ports


def _resolve_hostname(ip: str) -> str:
    """快速DNS查询，1秒超时"""
    if os.name == 'nt':
        import concurrent.futures
        def do_resolve():
            try:
                hostname, *_ = socket.gethostbyaddr(ip)
                return hostname
            except Exception:
                return ""
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(do_resolve)
            try:
                return future.result(timeout=1)  # 减少到1秒
            except concurrent.futures.TimeoutError:
                return ""
    else:
        import signal
        class TimeoutError(Exception):
            pass
        
        def handler(signum, frame):
            raise TimeoutError("DNS query timeout")
        
        old_handler = signal.signal(signal.SIGALRM, handler)
        signal.alarm(1)
        try:
            hostname, *_ = socket.gethostbyaddr(ip)
            return hostname
        except TimeoutError:
            return ""
        except Exception:
            return ""
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)


def scan_lan(
    cidr: str,
    max_workers: int = 32,  # 降低并发数到32，避免系统资源竞争
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[dict[str, Any]]:
    """轻量扫描指定网段，返回可直接给界面展示的字典列表。"""
    network = ipaddress.ip_network(cidr, strict=False)
    hosts = [str(host) for host in network.hosts()]
    results: list[dict[str, Any]] = []
    total = len(hosts)
    completed = 0

    def scan_one(ip: str) -> dict[str, Any] | None:
        # 先用更可靠的单次 ping 判断在线（依赖返回码，而非语言/地区化的文本解析）
        response_ms = _ping_host(ip)
        if response_ms is None:
            return None
        
        open_ports = _probe_ports(ip)
        hostname = ""  # 暂时禁DNS解析，太慢了
        # hostname = _resolve_hostname(ip)
        mac = _get_mac(ip)
        web_title = _fetch_web_title(ip) if 80 in open_ports else ""
        netbios_name = ""
        # 暂时禁用NetBIOS查询，太慢了
        # if 135 in open_ports:
        #     netbios_name = _resolve_netbios_name(ip)
        
        # 若反向 DNS 没有主机名，回退使用 NetBIOS 名称（如果存在）
        if not hostname and netbios_name:
            hostname = netbios_name
        # 优先用 MAC 前缀识别厂商，如果是本机则标记为 "本机"
        if hostname and hostname == socket.gethostname():
            vendor = "本机"
        else:
            vendor = get_vendor_from_mac(mac)
        classification = classify_device(
            mac=mac,
            vendor=vendor,
            open_ports=open_ports,
            hostname=hostname,
            web_title=web_title,
            netbios_name=netbios_name,
        )
        record = DeviceRecord(
            ip=ip,
            mac=mac,
            vendor=vendor,
            device_type=classification.get("device_type", "未知设备"),
            device_name=classification.get("device_name", ""),
            evidence=classification.get("evidence", ""),
            confidence=float(classification.get("confidence", 0.3)),
            response_ms=response_ms,
            hostname=hostname,
            web_title=web_title,
            open_ports=open_ports,
        )
        # 更新最后在线时间并附加用户备注
        try:
            # 保存本地带时区的时间，避免显示成固定的 8 小时差（UTC vs 本地）
            update_last_seen(ip, datetime.now().astimezone())
        except Exception:
            pass

        out = record.to_dict()
        info = get_note(ip)
        out["note"] = info or ""
        out["online"] = True
        out["last_seen"] = get_device_info(ip).get("last_seen")
        
        return out

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        import time as _time
        scan_start = _time.time()
        futures = [executor.submit(scan_one, ip) for ip in hosts]
        for future in as_completed(futures):
            record = future.result()
            if record:
                results.append(record)
            completed += 1
            if progress_callback:
                try:
                    progress_callback(completed, total)
                except Exception:
                    pass
        
        scan_elapsed = _time.time() - scan_start
        print(f"[INFO] 扫描完成：共{total}个IP，发现{len(results)}个设备，耗时{scan_elapsed:.2f}秒")

    results.sort(key=lambda item: item["ip"])
    return results
