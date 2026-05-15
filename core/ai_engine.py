from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Literal

import httpx

try:
    from zai import ZhipuAiClient
except Exception:  # pragma: no cover - 运行环境未安装或导入失败时降级
    ZhipuAiClient = None

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


AiProvider = Literal["zhipu", "groq"]

ZHIPU_DEFAULT_MODEL = "glm-5.1"
GROQ_DEFAULT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
ZHIPU_MODELS_URL = "https://open.bigmodel.cn/api/paas/v4/models"

DEFAULT_AI_PROVIDER: AiProvider = "groq"
DEFAULT_MODEL = GROQ_DEFAULT_MODEL

LAN_AUDIT_SYSTEM = (
    "你是一个资深的局域网网络安全与架构审计专家。"
    "直接输出最终《局域网全盘安全与资产审计报告》正文，禁止输出与报告无关的寒暄或隐性思考链。"
)

LAN_AUDIT_MAX_TOKENS = 8192


@dataclass(slots=True)
class AiRuntimeConfig:
    api_key: str
    model: str = GROQ_DEFAULT_MODEL
    provider: AiProvider = DEFAULT_AI_PROVIDER
    temperature: float = 0.7
    max_tokens: int = 4096


def build_asset_prompt(device: dict[str, Any] | None) -> str:
    if not device:
        return "请先在雷达探测页选择一个设备。"

    ip = device.get("ip", "未知IP")
    mac = device.get("mac", "-")
    vendor = device.get("vendor", "未知")
    device_type = device.get("device_type", "未知设备")
    device_name = device.get("device_name", "") or "未命名"
    hostname = device.get("hostname", "") or "未识别"
    response_ms = device.get("response_ms", "-")
    open_ports = device.get("open_ports", []) or []
    web_title = device.get("web_title", "") or "无"

    if open_ports:
        port_text = ", ".join(str(port) for port in open_ports)
    else:
        port_text = "全端口封闭"

    # 使用悟空侦探风格的提示词
    return f"""
你现在是独立开发神作【悟空雷达】的 AI 首席硬件侦探。
你不需要写无聊的合规安全报告，你的唯一任务是：帮用户分析局域网里这个【未知设备】到底特么的是个什么东西，并给出抓鬼策略。

【已知线索】
- 局域网段: 192.168.0.0/24
- 目标 IP: {ip}
- MAC 地址: {mac}
- 开放端口: {port_text} (如果是空，说明全端口封闭)
- 探测延迟: {response_ms} ms
- 厂商信息: {vendor}
- 设备类型: {device_type}
- 主机名: {hostname}
- 网页标题: {web_title}

请严格基于网络行为学进行深度推理，按以下格式用大白话输出（禁止打官腔，主打极客范）：

🎯 【侦探身份侧写】
(根据以下逻辑进行推理盲猜：
 1. 如果开放端口为空，且 MAC 地址第二位是 2, 6, A, E，直接告诉用户：'这 100% 是一台开启了随机 MAC 隐私保护的现代智能手机（iPhone 或高版本安卓）。'
 2. 结合延迟分析：如果延迟高达几百毫秒，告诉用户：'这个高延迟说明它刚刚处于深度息屏休眠状态，我们的第一波扫描刚把它从省电模式里打醒。'
 3. 如果开放了 8008 则是安卓/电视投屏；开放 62078 是苹果；开放 80 是网页硬件。请综合判断。)

🕵️‍♂️ 【悟空抓鬼行动指南】
(别给老子写'物理检查'这种废话！给用户提供 2-3 个在本地能立马动手实操的技术手段，把这个未命名设备逼出原形。例如：
 - 指引用户：'点亮你家里嫌疑手机的屏幕，在软件里重新点扫描，看它是否会释放出主机名。'
 - 指引用户：'在终端里对准它运行 mDNS 探测命令，强行抓取它的投屏服务名称。'
 - 或者是查看路由器的 DHCP 静态列表进行对账。)
"""


def build_global_network_prompt(network_data: list[dict[str, Any]]) -> str:
    """构建全网深度分析的提示词"""
    import json
    network_json = json.dumps(network_data, ensure_ascii=False, indent=2)
    
    return f"""
你现在是独立开发神作【悟空雷达】的 AI 首席网络战略指挥官。
现在用户在局域网（192.168.0.0/24）执行了一次深度网络拓扑测绘，以下是规则引擎上报的【全网存活资产 JSON 账本】。

【全网资产账本】
{network_json}

请你站在全局上帝视角，不要去单调复读每一台设备，而是对整个内网大局进行'沙盘推演'。请严格按照以下模块，用极其硬核、充满极客范、通俗易懂的大白话输出全局报告：

🌐 1. 【全网生态大盘综述】
(用大白话总结：整个网络一共有几台机器？什么设备占主流？比如：'当前内网呈现典型的[居家办公/小型工作室]生态。Windows 生产力大件和匿名移动终端五五开，网络边界由一台 TP-Link 骨干路由卡死。')

🕵️‍♂️ 2. 【异常群落与'隐形资产'穿透】
(盯着那些匿名、高延迟、全封闭的设备群落进行行为学扎堆分析。
 示例分析：'注意看 .101 和 .104 这两台匿名设备，它们共同呈现出[随机 MAC+全封闭+高延迟]的特征。这绝对不是巧合，说明当前局域网内至少有 2 台现代移动终端（如主人的 iPhone 和副机）处于息屏挂机状态。它们在共享你的网络带宽。')

⚔️ 3. 【内网火线防御建议（Top 2）】
(站在黑客攻防视角，如果有人连进这个 Wi-Fi，能怎么打穿这个内网？给出 2 条最致命的防守建议。
 示例：
 - .100 和 .102 共同暴露了 135 RPC 端口，内网横向移动的风险极高，一台被黑，全网遭殃。
 - 网关暴露了 1900 UPnP 投屏/发现协议，注意防范局域网流量劫持。)
"""


def _resolve_model(provider: AiProvider, model: str | None) -> str:
    if model and model.strip():
        return model.strip()
    return GROQ_DEFAULT_MODEL if provider == "groq" else ZHIPU_DEFAULT_MODEL


def _parse_models_payload(payload: Any) -> list[str]:
    """解析 Groq / 智谱「模型列表」类 JSON，提取模型 ID。"""
    if not isinstance(payload, dict):
        return []
    found: list[str] = []

    def _take_list(block: Any) -> None:
        if not isinstance(block, list):
            return
        for item in block:
            if isinstance(item, str) and item.strip():
                found.append(item.strip())
            elif isinstance(item, dict):
                mid = item.get("id") or item.get("model") or item.get("name")
                if mid:
                    found.append(str(mid).strip())

    _take_list(payload.get("data"))
    for key in ("models", "model_list", "chat_models"):
        _take_list(payload.get(key))

    seen: dict[str, None] = {}
    for mid in found:
        if mid and mid not in seen:
            seen[mid] = None
    return list(seen.keys())


def fetch_remote_model_list(
    api_key: str,
    provider: AiProvider,
    *,
    timeout: float = 45.0,
) -> list[str]:
    """使用当前 Key 请求服务商接口，返回当前账号可用的模型 ID 列表（已去重、按字母序）。"""
    if not api_key.strip():
        raise ValueError("请先填写 API Key。")
    key = api_key.strip()
    if provider == "groq":
        url = f"{GROQ_BASE_URL.rstrip('/')}/models"
        headers: dict[str, str] = {"Authorization": f"Bearer {key}"}
    else:
        url = ZHIPU_MODELS_URL
        headers = {
            "Authorization": f"Bearer {key}",
            "x-source-channel": "lan-scope",
            "Accept-Language": "zh-CN,zh",
        }

    with httpx.Client(timeout=timeout) as client:
        response = client.get(url, headers=headers)

    if response.status_code == 401:
        raise RuntimeError("API Key 无效或未授权，无法拉取模型列表。")
    if response.status_code >= 400:
        detail = response.text[:400].replace("\n", " ")
        raise RuntimeError(f"拉取模型列表失败（HTTP {response.status_code}）：{detail}")

    try:
        payload = response.json()
    except Exception as exc:
        raise RuntimeError(f"无法解析模型列表响应：{exc}") from exc

    ids = _parse_models_payload(payload)
    
    if not ids:
        raise RuntimeError("服务端未返回可用模型 ID，请检查接口或稍后再试。")
    return sorted(ids, key=str.lower)


def build_ai_config(
    api_key: str,
    model: str | None = None,
    *,
    provider: AiProvider = DEFAULT_AI_PROVIDER,
) -> AiRuntimeConfig:
    return AiRuntimeConfig(api_key=api_key, model=_resolve_model(provider, model), provider=provider)


def _extract_chunk_text(chunk: Any) -> str:
    choices = getattr(chunk, "choices", None) or []
    if not choices:
        return ""

    delta = getattr(choices[0], "delta", None)
    if delta is not None:
        reasoning_content = getattr(delta, "reasoning_content", None)
        if reasoning_content:
            return reasoning_content
        content = getattr(delta, "content", None)
        if content:
            return content

    message = getattr(choices[0], "message", None)
    if message is not None:
        content = getattr(message, "content", None)
        if content:
            return content

    return ""


def _build_zhipu_client(api_key: str) -> Any:
    if ZhipuAiClient is None:
        raise RuntimeError("zai-sdk 未安装或无法导入，请先安装 `zai-sdk`。")
    if not api_key.strip():
        raise ValueError("缺少智谱 API Key。")
    return ZhipuAiClient(api_key=api_key.strip())


def _stream_zhipu_messages(
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int,
) -> Iterator[str]:
    client = _build_zhipu_client(api_key)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        thinking={"type": "disabled"},
        stream=True,
        max_tokens=max_tokens,
        temperature=0.2,
    )
    for chunk in response:
        text = _extract_chunk_text(chunk)
        if text:
            yield text


def _stream_zhipu(
    prompt: str,
    api_key: str,
    model: str,
    max_tokens: int,
) -> Iterator[str]:
    messages = [
        {"role": "system", "content": "你是一个只输出最终结论的助手，禁止输出内部思考；直接给出最终报告。"},
        {"role": "user", "content": prompt},
    ]
    yield from _stream_zhipu_messages(api_key, model, messages, max_tokens)


def _stream_groq_messages(
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int,
) -> Iterator[str]:
    if OpenAI is None:
        raise RuntimeError("openai 包未安装，请先安装 `openai`。")
    if not api_key.strip():
        raise ValueError("缺少 Groq API Key。")
    client = OpenAI(api_key=api_key.strip(), base_url=GROQ_BASE_URL)
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        max_tokens=max_tokens,
        temperature=0.2,
    )
    for chunk in stream:
        text = _extract_chunk_text(chunk)
        if text:
            yield text


def _stream_groq(
    prompt: str,
    api_key: str,
    model: str,
    max_tokens: int,
) -> Iterator[str]:
    messages = [
        {"role": "system", "content": "你是一个只输出最终结论的助手，禁止输出内部思考；直接给出最终报告。"},
        {"role": "user", "content": prompt},
    ]
    yield from _stream_groq_messages(api_key, model, messages, max_tokens)


def stream_asset_report(
    device: dict[str, Any] | None,
    api_key: str,
    model: str | None = None,
    *,
    provider: AiProvider = DEFAULT_AI_PROVIDER,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> Iterator[str]:
    """按 provider 调用智谱或 Groq（OpenAI 兼容 Chat Completions），按块输出结果。"""
    del temperature  # 与历史签名兼容；实际温度固定为 0.2 以保持报告稳定
    resolved = _resolve_model(provider, model)
    prompt = build_asset_prompt(device)
    if not device:
        yield prompt
        return

    if not api_key.strip():
        yield "请先填写 Groq API Key。" if provider == "groq" else "请先填写智谱 API Key。"
        return

    try:
        if provider == "groq":
            yield from _stream_groq(prompt, api_key, resolved, max_tokens)
        else:
            yield from _stream_zhipu(prompt, api_key, resolved, max_tokens)
    except Exception as exc:  # pragma: no cover - 网络/协议/鉴权等异常
        yield f"AI 调用异常：{exc}"


def stream_global_network_report(
    network_data: list[dict[str, Any]],
    api_key: str,
    model: str | None = None,
    *,
    provider: AiProvider = DEFAULT_AI_PROVIDER,
    max_tokens: int = 4096,
) -> Iterator[str]:
    """全网深度分析的流式报告生成"""
    resolved = _resolve_model(provider, model)
    prompt = build_global_network_prompt(network_data)
    
    if not network_data:
        yield "暂无网络设备数据，请先执行扫描。"
        return

    if not api_key.strip():
        yield "请先填写 Groq API Key。" if provider == "groq" else "请先填写智谱 API Key。"
        return

    try:
        if provider == "groq":
            yield from _stream_groq(prompt, api_key, resolved, max_tokens)
        else:
            yield from _stream_zhipu(prompt, api_key, resolved, max_tokens)
    except Exception as exc:
        yield f"AI 调用异常：{exc}"


def build_asset_report(
    device: dict[str, Any] | None,
    api_key: str,
    model: str | None = None,
    *,
    provider: AiProvider = DEFAULT_AI_PROVIDER,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    return "".join(
        stream_asset_report(
            device,
            api_key=api_key,
            model=model,
            provider=provider,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    )


def pack_lan_scan_envelope(
    devices: list[dict[str, Any]],
    *,
    cidr: str,
    gateway: str,
) -> dict[str, Any]:
    """将标准模式扫描结果打成一份可交给大模型的资产 JSON 外壳。"""
    return {
        "scan_mode": "standard",
        "scan_target_cidr": cidr,
        "inferred_gateway": gateway,
        "online_host_count": len(devices),
        "devices": devices,
    }


def build_lan_audit_user_message(
    devices: list[dict[str, Any]],
    *,
    cidr: str,
    gateway: str,
) -> str:
    envelope = pack_lan_scan_envelope(devices, cidr=cidr, gateway=gateway)
    blob = json.dumps(envelope, ensure_ascii=False, indent=2, default=str)
    return (
        "接下来我会给你一段局域网标准扫描后的完整设备资产 JSON 数据。\n\n"
        "请不要重复单台设备的废话，直接结合全网数据，撰写一份宏观的《局域网全盘安全与资产审计报告》。\n\n"
        "报告必须包含以下板块：\n\n"
        "1. 整体网络场景推断（家庭/办公/公共）\n"
        "2. 资产关联性与异常指标研判（重点分析延迟反常、厂商冲突、随机 MAC 等宏观线索）\n"
        "3. 全网暴露面与潜在横向攻击风险评估\n"
        "4. 针对性的网络优化与防御建议\n\n"
        "请用硬核、专业、一针见血的工程师口吻回答，多用 Markdown 排版。\n\n"
        "以下是 JSON：\n\n"
        f"{blob}"
    )


def stream_lan_audit_report(
    devices: list[dict[str, Any]],
    api_key: str,
    model: str | None,
    *,
    provider: AiProvider = DEFAULT_AI_PROVIDER,
    cidr: str,
    gateway: str,
    max_tokens: int = LAN_AUDIT_MAX_TOKENS,
) -> Iterator[str]:
    """基于标准扫描全量设备 JSON，流式输出全盘安全审计报告。"""
    resolved = _resolve_model(provider, model)
    if not devices:
        yield "没有可审计的设备数据，请先完成标准扫描。"
        return
    if not api_key.strip():
        yield "请先填写 Groq API Key。" if provider == "groq" else "请先填写智谱 API Key。"
        return

    user_msg = build_lan_audit_user_message(devices, cidr=cidr, gateway=gateway)
    messages: list[dict[str, str]] = [
        {"role": "system", "content": LAN_AUDIT_SYSTEM},
        {"role": "user", "content": user_msg},
    ]
    try:
        if provider == "groq":
            yield from _stream_groq_messages(api_key, resolved, messages, max_tokens)
        else:
            yield from _stream_zhipu_messages(api_key, resolved, messages, max_tokens)
    except Exception as exc:  # pragma: no cover
        yield f"AI 调用异常：{exc}"


def build_lan_audit_report(
    devices: list[dict[str, Any]],
    api_key: str,
    model: str | None = None,
    *,
    provider: AiProvider = DEFAULT_AI_PROVIDER,
    cidr: str,
    gateway: str,
    max_tokens: int = LAN_AUDIT_MAX_TOKENS,
) -> str:
    return "".join(
        stream_lan_audit_report(
            devices,
            api_key=api_key,
            model=model,
            provider=provider,
            cidr=cidr,
            gateway=gateway,
            max_tokens=max_tokens,
        )
    )
