"""网卡信息收集和选择."""
from __future__ import annotations

import ipaddress
import socket
import subprocess
import os
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class NetworkInterface:
    name: str
    ip: str
    netmask: str
    mac: str
    gateway: str = ""
    is_up: bool = True

    @property
    def network_cidr(self) -> str:
        """根据 IP 和 netmask 计算网络 CIDR."""
        try:
            net = ipaddress.ip_network(f"{self.ip}/{self.netmask}", strict=False)
            return str(net)
        except Exception:
            return ""

    @property
    def is_connected(self) -> bool:
        """判断是否处于连接状态：启用且有网关."""
        return self.is_up and bool(self.gateway and self.gateway != "0.0.0.0")

    def display_text(self) -> str:
        """返回用于下拉框显示的文本."""
        cidr = self.network_cidr or "无"
        gw_text = self.gateway or "未检测"
        status = "✓ 已连接" if self.is_connected else "✗ 未连接"
        return f"{self.name} | {self.ip}/{self.netmask.split('.')[-1]} | GW:{gw_text} | {status}"

    def detail_text(self) -> str:
        """返回详细文本展示（用于 UI 列表）."""
        cidr = self.network_cidr or "无"
        gw_text = self.gateway or "未检测"
        status = "✓ 已启用" if self.is_up else "✗ 已禁用"
        connected = "✓ 已联网" if self.is_connected else "✗ 未联网"
        return f"**{self.name}**  |  IP: {self.ip}  |  子网: {cidr}  |  网关: {gw_text}  |  状态: {status} {connected}"


def get_network_interfaces_windows() -> list[NetworkInterface]:
    """Windows 下用 PowerShell 获取每个适配器信息（含各接口的网关和描述），并过滤虚拟网卡。"""
    interfaces: list[NetworkInterface] = []
    try:
        ps_script = """
$adapters = Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object -Property Name, MacAddress, InterfaceIndex, InterfaceDescription
foreach ($adapter in $adapters) {
    $ipconfig = Get-NetIPConfiguration -InterfaceIndex $adapter.InterfaceIndex -ErrorAction SilentlyContinue
    if ($ipconfig -and $ipconfig.IPv4Address) {
        $ip = $ipconfig.IPv4Address.IPAddress
        $prefix = $ipconfig.IPv4Address.PrefixLength
        $gateway = $ipconfig.IPv4DefaultGateway.NextHop
        $mac = $adapter.MacAddress.Replace('-', ':').ToLower()
        $desc = $adapter.InterfaceDescription
        $displayName = if ([string]::IsNullOrEmpty($desc)) { $adapter.Name } else { $desc }

        # 计算子网掩码
        $netmask = ""
        if ($prefix -eq 32) { $netmask = "255.255.255.255" }
        elseif ($prefix -eq 31) { $netmask = "255.255.255.254" }
        elseif ($prefix -eq 30) { $netmask = "255.255.255.252" }
        elseif ($prefix -eq 29) { $netmask = "255.255.255.248" }
        elseif ($prefix -eq 28) { $netmask = "255.255.255.240" }
        elseif ($prefix -eq 27) { $netmask = "255.255.255.224" }
        elseif ($prefix -eq 26) { $netmask = "255.255.255.192" }
        elseif ($prefix -eq 25) { $netmask = "255.255.255.128" }
        elseif ($prefix -eq 24) { $netmask = "255.255.255.0" }
        elseif ($prefix -eq 23) { $netmask = "255.255.254.0" }
        elseif ($prefix -eq 22) { $netmask = "255.255.252.0" }
        elseif ($prefix -eq 21) { $netmask = "255.255.248.0" }
        elseif ($prefix -eq 20) { $netmask = "255.255.240.0" }
        elseif ($prefix -eq 19) { $netmask = "255.255.224.0" }
        elseif ($prefix -eq 18) { $netmask = "255.255.192.0" }
        elseif ($prefix -eq 17) { $netmask = "255.255.128.0" }
        elseif ($prefix -eq 16) { $netmask = "255.255.0.0" }

        if ($ip -and $netmask) {
            Write-Host "$displayName|$ip|$netmask|$mac|$gateway"
        }
    }
}
"""

        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,  # Windows下隐藏窗口
        )

        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                parts = line.split("|")
                if len(parts) >= 4:
                    name = parts[0].strip()
                    ip = parts[1].strip()
                    netmask = parts[2].strip()
                    mac = parts[3].strip()
                    gateway = parts[4].strip() if len(parts) > 4 else ""

                    # 过滤回环与无效 IP
                    if not ip or ip.startswith("127."):
                        continue

                    # 不在此处过滤虚拟适配器，UI 层决定是否隐藏或标注

                    iface = NetworkInterface(
                        name=name,
                        ip=ip,
                        netmask=netmask,
                        mac=mac or "-",
                        gateway=gateway or "",
                        is_up=True,
                    )
                    interfaces.append(iface)
            except Exception:
                continue
    except Exception:
        return []

    return interfaces


def get_network_interfaces_linux() -> list[NetworkInterface]:
    """Linux 下用 ip 命令获取网卡信息."""
    interfaces = []
    try:
        result = subprocess.run(
            ["ip", "addr", "show"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,  # Windows下隐藏窗口
        )
        output = result.stdout
        lines = output.split("\n")

        current_name = None
        current_mac = None
        for line in lines:
            # 提取网卡名称和 MAC
            if line and line[0].isdigit():
                parts = line.split(":")
                if len(parts) >= 2:
                    current_name = parts[1].strip()
                    if "link/ether" in line:
                        mac_part = line.split("link/ether")[1].split()[0]
                        current_mac = mac_part.lower()
            # 提取 IP 和子网掩码
            elif current_name and "inet " in line:
                parts = line.strip().split()
                if len(parts) >= 2:
                    cidr = parts[1]
                    try:
                        net = ipaddress.ip_network(cidr, strict=False)
                        ip = str(net.network_address)
                        netmask = str(net.netmask)
                        iface = NetworkInterface(
                            name=current_name,
                            ip=ip,
                            netmask=netmask,
                            mac=current_mac or "-",
                            is_up=True,
                        )
                        if ip != "127.0.0.1":
                            interfaces.append(iface)
                    except Exception:
                        pass

        return interfaces
    except Exception:
        return []


def get_network_interfaces() -> list[NetworkInterface]:
    """跨平台获取网卡信息."""
    import os

    if os.name == "nt":
        return get_network_interfaces_windows()
    else:
        return get_network_interfaces_linux()


def filter_active_interfaces(interfaces: list[NetworkInterface]) -> list[NetworkInterface]:
    """过滤并优先排序：物理网卡优先，排除虚拟/代理适配器，确保推荐真实物理网段。"""
    # reuse exported helpers if available
    try:
        _is_virtual_interface = is_virtual_interface  # type: ignore[name-defined]
        _is_physical_interface = is_physical_interface  # type: ignore[name-defined]
    except Exception:
        # fallback local definitions
        def _is_virtual_interface(name: str) -> bool:
            virtual_keywords = (
                "vmware",
                "virtualbox",
                "vethernet",
                "hyper-v",
                "docker",
                "clash",
                "mihomo",
                "tun",
                "tap",
                "vmnet",
            )
            lower = name.lower()
            return any(kw in lower for kw in virtual_keywords)

        def _is_physical_interface(name: str) -> bool:
            physical_keywords = (
                "ethernet",
                "realtek",
                "intel",
                "broadcom",
                "atheros",
                "mediatek",
                "qualcomm",
                "marvell",
                "network adapter",
                "以太网",
                "无线",
                "wlan",
                "wifi",
            )
            lower = name.lower()
            if any(kw in lower for kw in ("vmware", "virtualbox", "clash", "meta", "vethernet")):
                return False
            return any(kw in lower for kw in physical_keywords)

    active = [iface for iface in interfaces if iface.is_up and iface.ip and iface.network_cidr and not _is_virtual_interface(iface.name)]

    def priority_key(iface: NetworkInterface) -> tuple:
        return (-int(_is_physical_interface(iface.name)), -int(bool(iface.gateway)), iface.name)

    return sorted(active, key=priority_key)


def is_virtual_interface(name: str) -> bool:
    """导出：判断是否为虚拟接口（UI 可用来标注）。"""
    virtual_keywords = (
        "vmware",
        "virtualbox",
        "vethernet",
        "hyper-v",
        "docker",
        "clash",
        "mihomo",
        "tun",
        "tap",
        "vmnet",
    )
    lower = name.lower()
    return any(kw in lower for kw in virtual_keywords)


def is_physical_interface(name: str) -> bool:
    """导出：判断是否为物理接口。"""
    physical_keywords = (
        "ethernet",
        "realtek",
        "intel",
        "broadcom",
        "atheros",
        "mediatek",
        "qualcomm",
        "marvell",
        "network adapter",
        "以太网",
        "无线",
        "wlan",
        "wifi",
    )
    lower = name.lower()
    if any(kw in lower for kw in ("vmware", "virtualbox", "clash", "meta", "vethernet")):
        return False
    return any(kw in lower for kw in physical_keywords)
