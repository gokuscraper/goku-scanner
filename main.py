from __future__ import annotations

import asyncio
import ipaddress
import os
import platform
import socket
from collections import Counter
from datetime import datetime
from typing import Any

from nicegui import ui

from core.ai_engine import DEFAULT_AI_PROVIDER, DEFAULT_MODEL, GROQ_DEFAULT_MODEL, ZHIPU_DEFAULT_MODEL, build_asset_report, build_global_network_prompt, stream_global_network_report, fetch_remote_model_list
from core.app_state import STATE, init_state, save_settings, set_ai_report, set_scan_results
from core.secure_store import load_api_key, load_groq_api_key, save_api_key, save_groq_api_key
from core.network_engine import detect_local_network, scan_lan
from core.network_interface import (
    NetworkInterface,
    filter_active_interfaces,
    get_network_interfaces,
    is_virtual_interface,
)


APP_TITLE = "悟空局域网侦探"
DEFAULT_CIDR = "192.168.1.0/24"

init_state()

ui.add_head_html(
    """
    <style>
    :root {
      --brand: #2563eb;
      --ink: #111827;
      --muted: #6b7280;
      --line: #e5e7eb;
      --soft: #f8fafc;
      --ok: #059669;
      --warn: #d97706;
    }
    body {
      margin: 0;
      background: #f3f4f6;
      color: var(--ink);
      font-family: Inter, "Microsoft YaHei", "PingFang SC", Arial, sans-serif;
      letter-spacing: 0;
      overflow: hidden; /* 防止body出现滚动条 */
    }
    .q-page { min-height: 100vh; }
    .app-shell {
      height: 100vh;
      max-height: 100vh;
      background: #ffffff;
      display: grid;
      grid-template-columns: 292px minmax(0, 1fr);
      overflow: hidden;
    }
    .sidebar {
      background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
      border-right: 1px solid var(--line);
      overflow-y: auto; /* 只允许垂直滚动 */
      overflow-x: hidden; /* 禁止水平滚动 */
      padding: 22px 26px;
    }
    .main {
      overflow-y: auto; /* 只允许垂直滚动 */
      overflow-x: hidden; /* 禁止水平滚动 */
      padding: 28px 34px 32px;
      background:
        linear-gradient(180deg, rgba(255,255,255,.95), rgba(255,255,255,.88)),
        radial-gradient(circle at 72% 46%, rgba(37,99,235,.08), transparent 34%);
    }
    .brand-icon {
      /* width: 32px; */
      /* height: 32px; */
      /* border-radius: 9px; */
      display: grid;
      place-items: center;
      /* background: var(--brand); */
      /* color: white; */
      /* box-shadow: 0 8px 18px rgba(37,99,235,.22); */
    }
    .title { font-size: 18px; font-weight: 750; line-height: 1.2; }
    .caption { color: var(--muted); font-size: 12px; }
    .info-card {
      border: 1px solid var(--line);
      background: #ffffff;
      border-radius: 8px;
      box-shadow: 0 10px 30px rgba(15,23,42,.04);
    }
    .blue-panel {
      background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 55%, #0f766e 100%);
      color: white;
      border-radius: 6px;
      padding: 16px 18px;
      box-shadow: 0 16px 34px rgba(37,99,235,.24);
    }
    .kv-row {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 10px 0;
      border-bottom: 1px solid #eef2f7;
      font-size: 12px;
    }
    .kv-row:last-child { border-bottom: 0; }
    .kv-row span:first-child { color: #64748b; }
    .kv-row span:last-child { color: #1f2937; font-weight: 650; text-align: right; }
    .toolbar {
      display: grid;
      grid-template-columns: minmax(260px, 1fr) auto auto auto;
      gap: 14px;
      align-items: center;
      margin-bottom: 24px;
    }
    .mode-chip {
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 9px 13px;
      font-size: 13px;
      color: #374151;
      background: white;
    }
    .mode-chip.active {
      background: #111827;
      color: white;
      border-color: #111827;
    }
    .metric {
      min-height: 96px;
      border-left: 1px solid #edf2f7;
      padding: 4px 28px;
    }
    .metric-value { font-size: 28px; font-weight: 800; line-height: 1; }
    .metric-label { color: var(--muted); font-size: 12px; margin-top: 8px; }
    .network-option {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      cursor: pointer;
      background: #ffffff;
      transition: border .15s, box-shadow .15s, background .15s;
    }
    .network-option.active {
      border-color: #2563eb;
      background: #f8fbff;
      box-shadow: inset 3px 0 0 #2563eb;
    }
    .topology {
      width: 100%;
      min-height: 330px;
      border-top: 1px solid #eef2f7;
      position: relative;
      overflow: hidden;
    }
    .device-table .q-table__top, .device-table thead tr:first-child th {
      background: #f8fafc;
    }
    .q-btn { border-radius: 7px; text-transform: none; }
    .q-field--outlined .q-field__control { border-radius: 7px; }
    @media (max-width: 900px) {
      .app-shell { grid-template-columns: 1fr; height: auto; max-height: none; }
      .sidebar { border-right: 0; border-bottom: 1px solid var(--line); }
      .toolbar { grid-template-columns: 1fr; }
      .main { padding: 22px 18px 28px; }
    }
    </style>
    """,
    shared=True,
)


def _safe_network(cidr: str) -> ipaddress.IPv4Network | ipaddress.IPv6Network:
    return ipaddress.ip_network(cidr, strict=False)


def _host_count(cidr: str) -> int:
    try:
        return _safe_network(cidr).num_addresses - 2
    except Exception:
        return 0


def _range_text(cidr: str) -> str:
    try:
        hosts = list(_safe_network(cidr).hosts())
        if not hosts:
            return "-"
        return f"{hosts[0]} - {hosts[-1]}"
    except Exception:
        return "-"


def _time_text(value: str | None) -> str:
    if not value:
        return "-"
    try:
        return datetime.fromisoformat(value).strftime("%H:%M:%S")
    except Exception:
        return value


def _device_name(device: dict[str, Any]) -> str:
    return (
        device.get("device_name")
        or device.get("hostname")
        or device.get("vendor")
        or "未知设备"
    )


def _guess_gateway(iface: NetworkInterface | None, cidr: str) -> str:
    if iface and iface.gateway:
        return iface.gateway
    try:
        return str(next(_safe_network(cidr).hosts()))
    except Exception:
        return "-"


def _device_icon(device: dict[str, Any]) -> str:
    # 包含更多字段以便根据厂商与设备类型判断图标
    device_type_text = str(device.get('device_type', '')).lower()
    text = f"{device_type_text} {_device_name(device)} {device.get('open_ports', '')} {device.get('vendor', '')}".lower()
    if "router" in text or "网关" in text or "gateway" in text:
        return "router"

    # 未知移动设备应显示移动设备图标，而不是电脑
    if "未知移动" in device_type_text or "移动" in device_type_text or "mobile" in device_type_text:
        # 若厂商指向 Apple 使用 iPhone 图标，否则使用通用手机图标
        if "apple" in text or "iphone" in text:
            return "phone_iphone"
        return "smartphone"

    # 优先根据厂商判断手机类型（iPhone / Android）
    if "apple" in text or "iphone" in text:
        return "phone_iphone"
    android_keywords = ("phone", "mobile", "手机", "xiaomi", "redmi", "huawei", "honor", "oppo", "vivo", "realme", "oneplus", "samsung", "sony", "motorola", "google", "pixel", "nokia", "meizu", "lenovo", "asus", "zte", "nubia", "tcl", "poco")
    if any(k in text for k in android_keywords):
        return "smartphone_android"
    if "printer" in text or "打印" in text:
        return "print"
    if "camera" in text or "摄像" in text:
        return "photo_camera"
    if "web" in text or "80" in text:
        return "language"
    # 若设备类型模糊为未知设备，使用通用设备图标而非电脑图标
    if "未知设备" in device_type_text or device_type_text.strip().startswith("未知"):
        return "devices_other"
    return "computer"


def _latency_average(results: list[dict[str, Any]]) -> float:
    values = [
        float(item["response_ms"])
        for item in results
        if isinstance(item.get("response_ms"), (int, float))
    ]
    return round(sum(values) / len(values), 1) if values else 0.0


def _services_count(results: list[dict[str, Any]]) -> int:
    return sum(len(item.get("open_ports") or []) for item in results)


def _risk_count(results: list[dict[str, Any]]) -> int:
    risky_ports = {23, 135, 445, 5555, 8008, 8009}
    return sum(1 for item in results if risky_ports.intersection(item.get("open_ports") or []))


class LanScopeApp:
    def __init__(self) -> None:
        # 延迟初始化网卡信息，避免阻塞UI加载
        self.interfaces = []
        self.active_interfaces = []
        self.selected_iface = None
        # 是否显示被隐藏的虚拟/代理适配器（从全局状态读取/写入）
        if "show_virtual_adapters" not in STATE:
            STATE["show_virtual_adapters"] = False
        default_target = STATE.get("target_input") or DEFAULT_CIDR
        self.target_input = None
        self.search_input = None
        self.scan_button = None
        self.ai_deep_button = None
        self.status_label = None
        self.progress_bar = None
        self.progress_label = None
        self.progress_timer = None
        self.overview_area = None
        self.topology_area = None
        self.table_area = None
        self.sidebar_area = None
        self.ai_area = None
        self.selected_device: dict[str, Any] | None = STATE.get("selected_device")
        STATE["target_input"] = default_target

    def _default_interface(self) -> NetworkInterface | None:
        if not self.active_interfaces:
            return None
        connected = [item for item in self.active_interfaces if item.is_connected]
        return connected[0] if connected else self.active_interfaces[0]

    def init_network_interfaces(self) -> None:
        """在UI加载完成后初始化网卡信息"""
        try:
            self.interfaces = get_network_interfaces()
            self.active_interfaces = filter_active_interfaces(self.interfaces)
            self.selected_iface = self._default_interface()
            # 更新默认目标网段
            if not STATE.get("target_input"):
                STATE["target_input"] = self.selected_iface.network_cidr if self.selected_iface else DEFAULT_CIDR
            if self.target_input and self.selected_iface:
                self.target_input.value = STATE["target_input"]
        except Exception as e:
            print(f"初始化网卡信息失败: {e}")
            # 即使失败也使用默认值
            if not STATE.get("target_input"):
                STATE["target_input"] = DEFAULT_CIDR

    def build(self) -> None:
        with ui.element("div").classes("app-shell"):
            with ui.element("aside").classes("sidebar"):
                self.sidebar_area = ui.column().classes("w-full gap-5")
                self.render_sidebar()
            with ui.element("main").classes("main"):
                self.render_main()
        
        # UI加载完成后，延迟初始化网卡信息
        ui.timer(0.1, self._delayed_init, once=True)
    
    def _delayed_init(self) -> None:
        """延迟初始化，在UI渲染完成后执行"""
        self.init_network_interfaces()
        # 刷新侧边栏和主界面
        self.render_sidebar()
        self.refresh_dashboard()

    def render_sidebar(self) -> None:
        assert self.sidebar_area is not None
        self.sidebar_area.clear()
        with self.sidebar_area:
            with ui.row().classes("items-center gap-3"):
                with ui.element("div").classes("brand-icon"):
                    ui.image('logo.svg').classes('w-12 h-auto')
                with ui.column().classes("gap-0"):
                    ui.label(APP_TITLE).classes("title")
                    ui.label("本地网络拓扑").classes("caption")

            self.render_network_summary()
            self.render_interface_picker()

    def render_network_summary(self) -> None:
        cidr = STATE.get("target_input") or DEFAULT_CIDR
        gateway = _guess_gateway(self.selected_iface, cidr)
        local_ip = self.selected_iface.ip if self.selected_iface else "-"
        with ui.element("div").classes("blue-panel w-full"):
            self._panel_row("子网掩码", self.selected_iface.netmask if self.selected_iface else "-")
            self._panel_row("网关地址", gateway)
            self._panel_row("主机数", str(_host_count(cidr)))

        with ui.element("div").classes("w-full"):
            self._kv("主机名", socket.gethostname())
            self._kv("MAC 地址", self.selected_iface.mac if self.selected_iface else "-")
            self._kv("DNS", gateway)
            self._kv("子网段", cidr)
            self._kv("可用范围", _range_text(cidr))
            self._kv("系统", f"{platform.system()} {platform.release()}")
            self._kv("用户", os.getenv("USERNAME") or os.getenv("USER") or "-")

    def _panel_row(self, label: str, value: str) -> None:
        with ui.row().classes("justify-between items-center w-full text-xs py-1"):
            ui.label(label).classes("opacity-80")
            ui.label(value).classes("font-bold")

    def _kv(self, label: str, value: str) -> None:
        ui.html(f'<div class="kv-row"><span>{label}</span><span>{value}</span></div>')

    def render_interface_picker(self) -> None:
        with ui.column().classes("w-full gap-3"):
            with ui.row().classes("items-center justify-between w-full"):
                ui.label("网卡选择").classes("font-bold text-base")
                if self.active_interfaces:
                    ui.label(f"{len(self.active_interfaces)} 个").classes("caption")
                else:
                    ui.label("加载中...").classes("caption")
            
            # 如果网卡信息还未加载完成，显示加载提示
            if not self.interfaces and not self.active_interfaces:
                with ui.row().classes("items-center gap-2"):
                    ui.spinner(size="sm")
                    ui.label("正在检测网卡...").classes("caption")
                return
            
            if not self.active_interfaces:
                ui.label("未检测到活跃网卡").classes("caption")
                return
            # 根据用户是否选择展示虚拟适配器来过滤列表
            show_virtual = bool(STATE.get("show_virtual_adapters", False))
            interfaces_to_show = (
                self.interfaces if show_virtual else [item for item in self.active_interfaces if not is_virtual_interface(item.name)]
            )
            for iface in interfaces_to_show:
                active = iface == self.selected_iface
                with ui.element("div").classes(f"network-option {'active' if active else ''} w-full").on(
                    "click", lambda _event, item=iface: self.select_interface(item)
                ):
                    with ui.row().classes("items-start gap-3 no-wrap"):
                        ui.icon("wifi" if "wi" in iface.name.lower() else "hub").classes(
                            "text-blue-600 mt-1"
                        )
                        with ui.column().classes("gap-0 min-w-0"):
                            with ui.row().classes("items-center gap-2"):
                                ui.label(iface.name).classes("font-medium text-sm")
                                if iface.is_connected:
                                    ui.badge("活跃", color="green")
                            ui.label(iface.network_cidr).classes("caption")

            # 显示可切换的隐藏适配器提示，用户可点击展开/收起
            virtual_count = len([item for item in self.interfaces if is_virtual_interface(item.name)])
            if virtual_count:
                if show_virtual:
                    ui.button(f"收起 {virtual_count} 个虚拟/代理适配器", on_click=lambda: self._toggle_virtual()).props("flat small")
                else:
                    ui.button(f"已隐藏 {virtual_count} 个虚拟/代理适配器（点击显示）", on_click=lambda: self._toggle_virtual()).props("flat small")

    def select_interface(self, iface: NetworkInterface) -> None:
        self.selected_iface = iface
        STATE["target_input"] = iface.network_cidr or detect_local_network()
        if self.target_input:
            self.target_input.value = STATE["target_input"]
        self.render_sidebar()
        self.refresh_dashboard()

    def render_main(self) -> None:
        self.render_toolbar()
        self.overview_area = ui.column().classes("w-full gap-5")
        self.topology_area = ui.column().classes("w-full")
        self.table_area = ui.column().classes("w-full")
        self.ai_area = ui.column().classes("w-full")
        self.refresh_dashboard()

    def render_toolbar(self) -> None:
        with ui.element("div").classes("toolbar"):
            self.search_input = ui.input(
                placeholder="搜索 IP / 主机名 / MAC / 厂商",
                on_change=lambda _event: self.refresh_table(),
            ).props("outlined dense clearable").classes("w-full")
            
            # 中间按钮组
            with ui.row().classes('items-center gap-2'):
                ui.button('设备列表', on_click=self.scroll_to_table).classes('mode-chip h-10')
                ui.button('拓扑', on_click=self.scroll_to_topology).classes('mode-chip active h-10')
                ai_analyze_btn = ui.button("AI 分析", icon="auto_awesome", on_click=self.scroll_to_ai).props("outline")
                ai_analyze_btn.classes('h-10')
            
            # 右侧交流群
            with ui.column().classes('items-center gap-1'):
                ui.image('gzh.jpg').classes('w-24 h-auto rounded shadow-sm cursor-pointer').on('click', lambda: ui.notify('扫码加入交流群', type='info'))
                ui.label('交流群').classes('text-xs text-gray-600')

        # 初始化扫描模式
        STATE.setdefault("scan_mode", "standard")  # standard 或 ai_deep
        
        with ui.row().classes("items-center gap-4 mb-5"):
            self.scan_button = ui.button("开始扫描", icon="play_arrow", on_click=self.start_scan).props("unelevated")
            self.scan_button.classes('h-10')
            
            # 标准模式按钮 - 默认激活
            self.std_mode_btn = ui.button("标准", icon="my_location", on_click=lambda: self.set_scan_mode("standard"))
            self.std_mode_btn.classes('mode-chip active h-10')
            
            # AI深度模式按钮 - 默认半透明
            self.ai_deep_btn_element = ui.element('button').classes('h-10 px-6 rounded-lg text-white font-bold shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer border-0')
            self.ai_deep_btn_element.style('background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); opacity: 0.5;')
            with self.ai_deep_btn_element:
                with ui.row().classes('items-center gap-2'):
                    ui.icon('radar')
                    ui.label('AI 深度模式')
            self.ai_deep_btn_element.on('click', lambda: self.set_scan_mode("ai_deep"))
            
            self.target_input = ui.input(
                value=STATE.get("target_input") or DEFAULT_CIDR,
                placeholder="192.168.1.0/24",
                on_change=self.update_target,
            ).props("outlined dense").classes("w-56")
            ui.label(f"{_host_count(STATE.get('target_input') or DEFAULT_CIDR)} 主机").classes("caption")
            self.status_label = ui.label("准备就绪").classes("caption text-green-700")

        with ui.row().classes("items-center gap-3 mb-2"):
            self.progress_bar = ui.linear_progress(value=0).classes("w-56")
            self.progress_label = ui.label("").classes("caption")
            self.progress_bar.set_visibility(False)
            self.progress_label.set_visibility(False)

    def update_target(self, event: Any) -> None:
        STATE["target_input"] = str(event.value or "").strip() or DEFAULT_CIDR
        save_settings(STATE["target_input"])
        self.render_sidebar()
        self.refresh_dashboard()

    def set_scan_mode(self, mode: str) -> None:
        """设置扫描模式"""
        STATE["scan_mode"] = mode
        
        if mode == "standard":
            # 标准模式：激活标准按钮，AI深度模式变灰
            self.std_mode_btn.classes('active')
            self.std_mode_btn.style('opacity: 1;')
            self.ai_deep_btn_element.style('opacity: 0.5;')
            ui.notify("已切换到标准模式", type="info")
        else:
            # AI深度模式：取消标准按钮激活并半透明，AI深度模式高亮
            self.std_mode_btn.classes(remove='active')
            self.std_mode_btn.style('opacity: 0.5;')
            self.ai_deep_btn_element.style('opacity: 1;')
            ui.notify("已切换到 AI 深度模式 - 将进行全网拓扑分析", type="info")
    
    async def start_scan(self) -> None:
        cidr = str(self.target_input.value if self.target_input else STATE.get("target_input")).strip()
        try:
            _safe_network(cidr)
        except Exception:
            ui.notify("网段格式不正确，请输入类似 192.168.1.0/24", type="negative")
            return

        save_settings(cidr)
        STATE["target_input"] = cidr
        STATE["scan_progress"] = 0
        STATE["scan_total"] = 0
        STATE["scan_in_progress"] = True
        if self.scan_button:
            self.scan_button.disable()
        if self.status_label:
            self.status_label.text = "正在扫描..."
        if self.progress_bar and self.progress_label:
            self.progress_bar.value = 0
            self.progress_bar.set_visibility(True)
            self.progress_label.text = "0%"
            self.progress_label.set_visibility(True)
        if self.progress_timer:
            try:
                self.progress_timer.cancel()
            except Exception:
                pass
        self.progress_timer = ui.timer(0.3, self._refresh_progress)
        ui.notify(f"开始扫描 {cidr}", type="info")
        started = datetime.now()
        try:
            def _progress(done: int, total: int) -> None:
                STATE["scan_progress"] = done
                STATE["scan_total"] = total

            results = await asyncio.to_thread(scan_lan, cidr, progress_callback=_progress)
        except Exception as exc:
            ui.notify(f"扫描失败：{exc}", type="negative")
            results = []
        elapsed = (datetime.now() - started).total_seconds()
        set_scan_results(results)
        self.selected_device = results[0] if results else None
        STATE["selected_device"] = self.selected_device
        
        # 检查是否为AI深度模式
        scan_mode = STATE.get("scan_mode", "standard")
        
        if scan_mode == "ai_deep" and results:
            # AI深度模式：扫描完成后自动调用AI分析
            if self.status_label:
                self.status_label.text = f"AI深度模式 · 发现 {len(results)} 台设备 · 正在生成全局报告..."
            
            # 获取API配置
            provider = STATE.get("ai_provider", DEFAULT_AI_PROVIDER)
            api_key = load_groq_api_key() if provider == "groq" else load_api_key()
            if not api_key:
                api_key = os.getenv("GROQ_API_KEY") if provider == "groq" else os.getenv("ZHIPU_API_KEY")
            
            if api_key:
                model = STATE.get(f"ai_model_{provider}", GROQ_DEFAULT_MODEL if provider == "groq" else ZHIPU_DEFAULT_MODEL)
                
                try:
                    ui.notify("正在生成《悟空局域网全局全景情报报告》...", type="info")
                    
                    # 调用AI生成全局报告
                    report_text = ""
                    for chunk in stream_global_network_report(results, api_key, model, provider=provider):
                        report_text += chunk
                    
                    # 只显示弹窗，不保存到STATE（避免显示在AI分析区域）
                    self.show_global_report_dialog(report_text)
                    
                    if self.status_label:
                        self.status_label.text = f"AI深度模式 · 发现 {len(results)} 台设备 · {elapsed:.1f}s"
                    ui.notify("✅ 《悟空局域网全局全景情报报告》已生成！", type="positive")
                except Exception as e:
                    ui.notify(f"AI 分析失败：{str(e)[:200]}", type="negative")
                    if self.status_label:
                        self.status_label.text = f"AI深度模式 · 发现 {len(results)} 台设备 · {elapsed:.1f}s"
            else:
                ui.notify(f"请先在 AI 分析区域配置 {provider} API Key", type="warning")
                if self.status_label:
                    self.status_label.text = f"AI深度模式 · 发现 {len(results)} 台设备 · {elapsed:.1f}s"
        else:
            # 标准模式
            if self.status_label:
                self.status_label.text = f"标准 · 发现 {len(results)} 台设备 · {elapsed:.1f}s"
        if self.scan_button:
            self.scan_button.enable()
        STATE["scan_in_progress"] = False
        if self.progress_timer:
            try:
                self.progress_timer.cancel()
            except Exception:
                pass
        if self.progress_bar and self.progress_label:
            self.progress_bar.set_visibility(False)
            self.progress_label.set_visibility(False)
        self.render_sidebar()
        self.refresh_dashboard()
    
    def show_global_report_dialog(self, report_content: str) -> None:
        """显示全局报告弹窗"""
        with ui.dialog() as dialog, ui.card().classes('w-[800px] max-w-[90vw]'):
            # 标题栏
            with ui.row().classes('items-center justify-between w-full mb-4'):
                ui.label('《悟空局域网全局全景情报报告》').classes('text-xl font-bold text-purple-700')
                ui.button(icon='close', on_click=dialog.close).props('flat round dense')
            
            # 报告内容（可滚动）
            with ui.element('div').classes('overflow-y-auto max-h-[60vh]'):
                ui.markdown(report_content).classes('w-full')
            
            # 操作按钮
            with ui.row().classes('gap-3 mt-4 justify-end'):
                async def copy_report():
                    if report_content:
                        ui.run_javascript(f"navigator.clipboard.writeText({repr(report_content)})")
                        ui.notify("已复制到剪贴板", type="positive")
                    else:
                        ui.notify("暂无报告内容", type="warning")
                
                def download_report():
                    if not report_content:
                        ui.notify("暂无报告内容", type="warning")
                        return
                    
                    import os
                    from datetime import datetime
                    
                    # 创建downloads文件夹（如果不存在）
                    download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
                    if not os.path.exists(download_dir):
                        os.makedirs(download_dir)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"悟空雷达_全局情报报告_{timestamp}.md"
                    filepath = os.path.join(download_dir, filename)
                    
                    # 写入文件
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(report_content)
                    
                    ui.notify(f"报告已保存: downloads/{filename}", type="positive")
                
                ui.button("复制报告", icon="content_copy", on_click=copy_report).props("outline")
                download_btn = ui.button("下载报告", icon="download", on_click=download_report).props("unelevated")
                download_btn.classes('bg-purple-700 text-white hover:bg-purple-800')
                ui.button("关闭", icon="close", on_click=dialog.close).props("flat")
        
        dialog.open()

    def _refresh_progress(self) -> None:
        if not self.progress_bar or not self.progress_label:
            return
        if not STATE.get("scan_in_progress"):
            return
        total = int(STATE.get("scan_total") or 0)
        done = int(STATE.get("scan_progress") or 0)
        value = (done / total) if total else 0
        self.progress_bar.value = max(0, min(1, value))
        pct = int(value * 100) if total else 0
        self.progress_label.text = f"{pct}% ({done}/{total})"

    def refresh_dashboard(self) -> None:
        self.refresh_overview()
        self.refresh_topology()
        self.refresh_table()
        self.refresh_ai()

    def refresh_overview(self) -> None:
        assert self.overview_area is not None
        results = STATE.get("scan_results", [])
        cidr = STATE.get("target_input") or DEFAULT_CIDR
        self.overview_area.clear()
        with self.overview_area:
            with ui.element("div").classes("info-card w-full p-6"):
                with ui.row().classes("items-start justify-between w-full gap-6"):
                    with ui.column().classes("gap-2"):
                        ui.label("扫描概览").classes("font-bold text-lg")
                        ui.label(f"{cidr} · 网关 {_guess_gateway(self.selected_iface, cidr)} · {_time_text(datetime.now().isoformat())}").classes("caption")
                        ui.label(
                            f"随机 MAC / 热点地址设备 {self._unknown_count(results)}    本机 {self._local_count(results)}"
                        ).classes("text-xs text-gray-600")
                        ui.label(
                            f"带 Web 管理界面的设备 {self._web_count(results)}    路由器 / 网关 {self._gateway_count(results)}    移动设备 {self._mobile_count(results)}"
                        ).classes("text-xs text-gray-600")
                    self._metric("device_hub", "发现设备", f"{len(results)}", f"在线 {len(results)}")
                    self._metric("dns", "服务指纹", f"{_services_count(results)}", f"{self._service_devices(results)} 台设备")
                    self._metric("monitor_heart", "平均延迟", f"{_latency_average(results)} ms", "标准模式")
                    self._metric("warning", "待确认", f"{_risk_count(results)}", "状态完整")

    def _metric(self, icon: str, label: str, value: str, sub: str) -> None:
        with ui.row().classes("metric items-center gap-4"):
            ui.icon(icon).classes("text-blue-600 text-2xl")
            with ui.column().classes("gap-0"):
                ui.label(label).classes("metric-label")
                ui.label(value).classes("metric-value")
                ui.label(sub).classes("caption")

    def refresh_topology(self) -> None:
        assert self.topology_area is not None
        self.topology_area.clear()
        results = STATE.get("scan_results", [])
        cidr = STATE.get("target_input") or DEFAULT_CIDR
        with self.topology_area:
            ui.html('<div id="topology-section"></div>')
            with ui.element("div").classes("info-card w-full p-0"):
                with ui.row().classes("items-center gap-3 px-5 pt-4"):
                    ui.label("拓扑").classes("font-bold")
                    ui.label(f"{len(results)} 个节点").classes("caption")
                    ui.label(f"在线 {len(results)}").classes("caption")
                    ui.label(f"服务 {_services_count(results)}").classes("caption")
                ui.html(self._topology_html(results, _guess_gateway(self.selected_iface, cidr))).classes("topology")

    def _topology_html(self, results: list[dict[str, Any]], gateway: str) -> str:
        nodes = results[:8]
        if not nodes:
            return """
            <div style="height:330px;display:grid;place-items:center;color:#64748b;font-size:13px">
              点击“开始扫描”后会在这里生成拓扑图
            </div>
            """

        width = 920
        height = 330
        center_x = width / 2
        center_y = 50
        positions = []
        count = max(len(nodes), 1)
        for index, device in enumerate(nodes):
            x = 120 + index * ((width - 240) / max(count - 1, 1))
            y = 190 + (index % 3) * 34
            positions.append((device, x, y))

        lines = "\n".join(
            f'<path d="M {center_x:.0f} {center_y + 42:.0f} C {center_x:.0f} 130, {x:.0f} 120, {x:.0f} {y - 18:.0f}" '
            f'stroke="{"#1f4e79" if index == 1 else "#d8dee8"}" stroke-width="{2 if index == 1 else 1}" fill="none"/>'
            for index, (_device, x, y) in enumerate(positions)
        )
        cards = "\n".join(self._node_html(device, x, y) for device, x, y in positions)
        return f"""
        <svg viewBox="0 0 {width} {height}" width="100%" height="330" preserveAspectRatio="xMidYMid meet">
          <defs>
            <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="8" stdDeviation="8" flood-color="#0f172a" flood-opacity=".08"/>
            </filter>
          </defs>
          {lines}
          <g filter="url(#shadow)">
            <rect x="{center_x - 78:.0f}" y="20" width="156" height="62" rx="7" fill="#fff" stroke="#e5e7eb"/>
            <text x="{center_x - 58:.0f}" y="43" font-size="12" font-weight="700" fill="#111827">{gateway}</text>
            <text x="{center_x + 34:.0f}" y="43" font-size="11" fill="#d97706">网关</text>
            <circle cx="{center_x - 57:.0f}" cy="63" r="3" fill="#10b981"/>
            <text x="{center_x - 49:.0f}" y="67" font-size="10" fill="#64748b">在线   1750 ms   源房</text>
          </g>
          {cards}
        </svg>
        """

    def _node_html(self, device: dict[str, Any], x: float, y: float) -> str:
        ip = device.get("ip", "-")
        name = _device_name(device)[:14]
        latency = device.get("response_ms", "-")
        icon = _device_icon(device)
        return f"""
        <g filter="url(#shadow)">
          <rect x="{x - 58:.0f}" y="{y - 30:.0f}" width="116" height="58" rx="7" fill="#fff" stroke="#e8edf4"/>
          <text x="{x - 35:.0f}" y="{y - 10:.0f}" font-size="11" font-weight="700" fill="#111827">{ip}</text>
          <text x="{x - 35:.0f}" y="{y + 6:.0f}" font-size="10" fill="#64748b">{name}</text>
          <circle cx="{x - 34:.0f}" cy="{y + 18:.0f}" r="3" fill="#10b981"/>
          <text x="{x - 26:.0f}" y="{y + 21:.0f}" font-size="9" fill="#64748b">在线   {latency} ms</text>
          <text x="{x - 50:.0f}" y="{y + 3:.0f}" font-family="Material Icons" font-size="16" fill="#2563eb">{icon}</text>
        </g>
        """

    def refresh_table(self) -> None:
        assert self.table_area is not None
        self.table_area.clear()
        results = self._filtered_results()
        with self.table_area:
            ui.html('<div id="table-section"></div>')
            with ui.element("div").classes("info-card w-full p-4 mt-5"):
                with ui.row().classes('items-center justify-between w-full mb-3'):
                    ui.label("设备列表").classes("font-bold")
                    
                    # 导出CSV按钮
                    def export_csv():
                        if not results:
                            ui.notify("暂无数据可导出", type="warning")
                            return
                        
                        import csv
                        import os
                        from datetime import datetime
                        
                        # 创建downloads文件夹（如果不存在）
                        download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
                        if not os.path.exists(download_dir):
                            os.makedirs(download_dir)
                        
                        # 生成文件名
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"悟空雷达_设备列表_{timestamp}.csv"
                        filepath = os.path.join(download_dir, filename)
                        
                        # 写入CSV文件
                        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                            writer = csv.writer(f)
                            
                            # 写入表头
                            writer.writerow(["IP地址", "设备名称", "设备类型", "MAC地址", "厂商", "开放端口", "延迟(ms)", "在线状态"])
                            
                            # 写入数据
                            for item in results:
                                ports = ", ".join(str(p) for p in item.get("open_ports", [])) if item.get("open_ports") else "无"
                                writer.writerow([
                                    item.get("ip", "-"),
                                    _device_name(item),
                                    item.get("device_type", "未知设备"),
                                    item.get("mac", "-"),
                                    item.get("vendor", "-"),
                                    ports,
                                    item.get("response_ms", "-"),
                                    "在线" if item.get("online") else "离线"  # 修正：使用online字段
                                ])
                        
                        ui.notify(f"已导出 {len(results)} 条记录到: downloads/{filename}", type="positive")
                    
                    ui.button("导出CSV", icon="download", on_click=export_csv).props("outline small")
                if not results:
                    ui.label("暂无匹配设备").classes("caption")
                    return
                rows = [
                    {
                        "ip": item.get("ip", "-"),
                        "name": _device_name(item),
                        "type": item.get("device_type", "未知设备"),
                        "mac": item.get("mac", "-"),
                        "vendor": item.get("vendor", "未知"),
                        "ports": ", ".join(str(port) for port in (item.get("open_ports") or [])) or "-",
                        "latency": item.get("response_ms", "-"),
                    }
                    for item in results
                ]
                table = ui.table(
                    columns=[
                        {"name": "ip", "label": "IP", "field": "ip", "align": "left", "sortable": True},
                        {"name": "type", "label": "类型", "field": "type", "align": "left"},
                        {"name": "vendor", "label": "厂商", "field": "vendor", "align": "left"},
                        {"name": "name", "label": "名称", "field": "name", "align": "left"},
                        {"name": "mac", "label": "MAC", "field": "mac", "align": "left"},
                        {"name": "ports", "label": "开放端口", "field": "ports", "align": "left"},
                        {"name": "latency", "label": "延迟(ms)", "field": "latency", "align": "right"},
                    ],
                    rows=rows,
                    row_key="ip",
                    pagination=10,
                ).classes("device-table w-full")
                table.on("rowClick", lambda event: self.select_device_by_ip(event.args[1].get("ip")))

    def select_device_by_ip(self, ip: str) -> None:
        for item in STATE.get("scan_results", []):
            if item.get("ip") == ip:
                self.selected_device = item
                STATE["selected_device"] = item
                ui.notify(f"已选中 {ip}", type="positive")
                self.refresh_ai()
                break

    def refresh_ai(self) -> None:
        assert self.ai_area is not None
        self.ai_area.clear()
        selected = self.selected_device
        with self.ai_area:
            with ui.element("div").classes("info-card w-full p-4 mt-5"):
                with ui.row().classes("items-center justify-between w-full"):
                    ui.label("AI 分析").classes("font-bold")
                    
                if not selected:
                    ui.label("先在列表里选中设备，或完成一次扫描。").classes("caption")
                    return
                ui.label(f"{selected.get('ip')} · {_device_name(selected)}").classes("text-sm text-gray-700 mb-2")
                
                # API Provider 选择
                provider_select = ui.select(
                    options={"groq": "Groq", "zhipu": "智谱 AI"},
                    value=STATE.get("ai_provider", DEFAULT_AI_PROVIDER),
                    label="AI 服务商"
                ).props("outlined dense").classes("w-full max-w-lg")
                
                # API Key 输入（根据选择的 provider 动态显示）
                groq_key_input = ui.input(
                    "Groq API Key",
                    password=True,
                    password_toggle_button=True,
                    value=(load_groq_api_key() or os.getenv("GROQ_API_KEY", "")),
                ).props("outlined dense").classes("w-full max-w-lg")
                
                zhipu_key_input = ui.input(
                    "智谱 API Key",
                    password=True,
                    password_toggle_button=True,
                    value=(load_api_key() or os.getenv("ZHIPU_API_KEY", "")),
                ).props("outlined dense").classes("w-full max-w-lg")
                
                # 模型选择
                model_options = {
                    "groq": [
                        GROQ_DEFAULT_MODEL,
                        "meta-llama/llama-4-maverick-17b-128e-instruct",
                        "meta-llama/llama-3.3-70b-versatile",
                        "mixtral-8x7b-32768",
                        "gemma2-9b-it",
                    ],
                    "zhipu": [
                        ZHIPU_DEFAULT_MODEL,
                        "glm-4-plus",
                        "glm-4-air",
                        "glm-4-flash",
                    ]
                }
                
                # 存储从 API 获取的模型列表（按提供商区分）
                fetched_models_cache = {}
                
                current_provider = STATE.get("ai_provider", DEFAULT_AI_PROVIDER)
                default_model = STATE.get(f"ai_model_{current_provider}", 
                                         GROQ_DEFAULT_MODEL if current_provider == "groq" else ZHIPU_DEFAULT_MODEL)
                
                model_select = ui.select(
                    options={m: m for m in model_options.get(current_provider, [])},
                    value=default_model,
                    label="模型"
                ).props("outlined dense").classes("w-full max-w-lg")
                
                # 获取可用模型列表按钮
                model_list_box = ui.column().classes("w-full max-w-lg mt-2")
                
                async def fetch_models() -> None:
                    provider = str(provider_select.value or DEFAULT_AI_PROVIDER)
                    key_input = groq_key_input if provider == "groq" else zhipu_key_input
                    api_key = str(key_input.value or "").strip()
                    if not api_key:
                        ui.notify("请先填写 API Key", type="warning")
                        return
                    
                    # 显示加载提示
                    model_list_box.clear()
                    with model_list_box:
                        ui.label("正在获取模型列表...").classes("caption")
                    
                    try:
                        models = await asyncio.to_thread(fetch_remote_model_list, api_key, provider)
                        
                        # 保存到缓存
                        fetched_models_cache[provider] = models
                        
                        # 更新模型选择框，直接替换选项
                        new_options = {m: m for m in models}
                        model_select.options.clear()
                        model_select.options.update(new_options)
                        
                        # 如果当前选中的模型不在新列表中，切换到默认模型
                        if models and model_select.value not in models:
                            # 优先使用已保存的模型，否则使用默认模型
                            saved_model = STATE.get(f"ai_model_{provider}")
                            if saved_model and saved_model in models:
                                model_select.value = saved_model
                            else:
                                model_select.value = GROQ_DEFAULT_MODEL if provider == "groq" else ZHIPU_DEFAULT_MODEL
                        
                        # 强制刷新UI
                        model_select.update()
                        
                        # 清空提示区域
                        model_list_box.clear()
                        ui.notify(f"成功获取 {len(models)} 个可用模型，已更新到模型选择框", type="positive")
                    except Exception as e:
                        model_list_box.clear()
                        with model_list_box:
                            ui.label(f"获取失败: {str(e)[:200]}").classes("text-red-600 text-xs")
                        ui.notify(f"获取模型列表失败: {e}", type="negative")
                
                with ui.row().classes("gap-2 w-full max-w-lg"):
                    ui.button("获取可用模型", icon="refresh", on_click=fetch_models).props("flat small")
                
                # 报告输出区域
                report = ui.markdown(STATE.get("ai_report") or "等待生成分析报告。").classes("w-full")

                async def run_ai() -> None:
                    provider = str(provider_select.value or DEFAULT_AI_PROVIDER)
                    key_input = groq_key_input if provider == "groq" else zhipu_key_input
                    api_key = str(key_input.value or "").strip()
                    if not api_key:
                        ui.notify("请先填写 API Key", type="warning")
                        return
                    
                    model = str(model_select.value or "").strip()
                    if not model:
                        ui.notify("请选择模型", type="warning")
                        return
                    
                    # 保存设置
                    STATE["ai_provider"] = provider
                    STATE[f"ai_model_{provider}"] = model
                    try:
                        if provider == "groq":
                            save_groq_api_key(api_key)
                        else:
                            save_api_key(api_key)
                    except Exception:
                        pass
                    
                    report.content = "正在生成..."
                    text = await asyncio.to_thread(build_asset_report, selected, api_key, model, provider=provider)
                    set_ai_report(text)
                    report.content = text

                ui.button("生成 AI 画像", icon="auto_awesome", on_click=run_ai).props("unelevated")
                
                # 控制 API Key 显示的逻辑
                def update_key_visibility():
                    provider = str(provider_select.value or DEFAULT_AI_PROVIDER)
                    groq_key_input.set_visibility(provider == "groq")
                    zhipu_key_input.set_visibility(provider == "zhipu")
                    
                    # 优先使用从 API 获取的模型列表，否则使用硬编码的默认列表
                    if provider in fetched_models_cache and fetched_models_cache[provider]:
                        new_models = fetched_models_cache[provider]
                    else:
                        new_models = model_options.get(provider, [])
                    
                    model_select.options = {m: m for m in new_models}
                    if new_models:
                        saved_model = STATE.get(f"ai_model_{provider}")
                        if saved_model and saved_model in new_models:
                            model_select.value = saved_model
                        else:
                            model_select.value = new_models[0]
                
                provider_select.on("update:model-value", lambda e: update_key_visibility())
                update_key_visibility()  # 初始化显示

    def _filtered_results(self) -> list[dict[str, Any]]:
        results = STATE.get("scan_results", [])
        query = str(self.search_input.value or "").strip().lower() if self.search_input else ""
        if not query:
            return results
        return [
            item
            for item in results
            if query
            in " ".join(
                str(item.get(key, ""))
                for key in ("ip", "mac", "vendor", "device_type", "device_name", "hostname")
            ).lower()
        ]

    def scroll_to_ai(self) -> None:
        ui.run_javascript("document.querySelector('.main').scrollTo({top: document.querySelector('.main').scrollHeight, behavior: 'smooth'})")

    def scroll_to_table(self) -> None:
        js = (
            "(function(){"
            "const main=document.querySelector('.main');"
            "const el=document.getElementById('table-section');"
            "if(!main||!el) return;"
            "const mainRect=main.getBoundingClientRect();"
            "const elRect=el.getBoundingClientRect();"
            "const offset=elRect.top-mainRect.top+main.scrollTop-16;"
            "main.scrollTo({top: offset, behavior:'smooth'});"
            "})()"
        )
        ui.run_javascript(js)

    def scroll_to_topology(self) -> None:
        js = (
            "(function(){"
            "const main=document.querySelector('.main');"
            "const el=document.getElementById('topology-section');"
            "if(!main||!el) return;"
            "const mainRect=main.getBoundingClientRect();"
            "const elRect=el.getBoundingClientRect();"
            "const offset=elRect.top-mainRect.top+main.scrollTop-16;"
            "main.scrollTo({top: offset, behavior:'smooth'});"
            "})()"
        )
        ui.run_javascript(js)

    def _unknown_count(self, results: list[dict[str, Any]]) -> int:
        return sum(1 for item in results if item.get("mac") in ("", "-") or item.get("vendor") in ("", "未知"))

    def _local_count(self, results: list[dict[str, Any]]) -> int:
        host = socket.gethostname().lower()
        return sum(1 for item in results if str(item.get("hostname", "")).lower() == host)

    def _web_count(self, results: list[dict[str, Any]]) -> int:
        return sum(1 for item in results if 80 in (item.get("open_ports") or []))

    def _gateway_count(self, results: list[dict[str, Any]]) -> int:
        return sum(1 for item in results if "网关" in str(item.get("device_type", "")) or "router" in str(item.get("device_type", "")).lower())

    def _mobile_count(self, results: list[dict[str, Any]]) -> int:
        text = " ".join(str(item.get("device_type", "")) for item in results).lower()
        return text.count("手机") + text.count("mobile") + text.count("phone")

    def _service_devices(self, results: list[dict[str, Any]]) -> int:
        return sum(1 for item in results if item.get("open_ports"))

    def _toggle_virtual(self) -> None:
        # 切换全局状态并刷新侧栏与表格
        current = bool(STATE.get("show_virtual_adapters", False))
        STATE["show_virtual_adapters"] = not current
        self.render_sidebar()
        self.refresh_dashboard()


@ui.page("/")
def index() -> None:
    ui.page_title(APP_TITLE)
    LanScopeApp().build()


def run_home() -> None:
    # 启用原生窗口（pywebview）
    import webview
    import os
    import sys
    
    # 先启动NiceGUI服务
    import threading
    import time
    
    def start_nicegui():
        ui.run(
            title=APP_TITLE,
            host="127.0.0.1",
            port=8080,
            reload=False,
            show=False,  # 不让NiceGUI自动打开
            native=False,
            favicon="logo.svg",
        )
    
    try:
        # 在后台线程启动NiceGUI
        thread = threading.Thread(target=start_nicegui, daemon=True)
        thread.start()
        
        # 等待服务启动
        time.sleep(2)
        
        # 创建pywebview窗口
        window = webview.create_window(
            APP_TITLE,
            'http://127.0.0.1:8080',
            width=1200,
            height=800,
        )
        
        # 在Windows上设置进程ID
        if os.name == 'nt':
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('WukongLanScanner')
            except Exception:
                pass
        
        # 窗口关闭事件处理
        def on_closing():
            # 强制退出整个程序
            os._exit(0)
        
        # 绑定关闭事件
        window.events.closing += on_closing
        
        # 启动pywebview
        webview.start()
    except Exception as e:
        # 如果出错，显示错误信息
        import traceback
        error_msg = f"启动失败：{str(e)}\n\n{traceback.format_exc()}"
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("启动错误", error_msg)
            root.destroy()
        except Exception:
            pass
        os._exit(1)


if __name__ in {"__main__", "__mp_main__"}:
    run_home()
