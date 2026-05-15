# 🐒 Goku Scanner (悟空局域网侦探)

> **AI-Powered Network Scanner - Make Every Device Visible**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

[🇨🇳 中文版](README.md)

---

## 📖 Introduction

**Goku Scanner** is an intelligent LAN scanning tool built with Python + NiceGUI, combining traditional network探测 techniques with AI deep learning analysis to quickly discover, identify, and analyze all connected devices on your local network.

### ✨ Key Features

- 🚀 **Lightning Fast** - 32-thread concurrency, scans 254 IPs in just 4 seconds
- 🤖 **AI Detective Mode** - Intelligent device identification with professional analysis reports
- 🗺️ **Topology Visualization** - Auto-generates network device relationship maps
- 🔍 **Deep Detection** - Multi-dimensional analysis: Ping, ports, MAC, web titles
- 💾 **Data Export** - CSV spreadsheet and Markdown report export
- 🔒 **Privacy Protection** - Local operation, encrypted API key storage

---

## 🎯 Features

### 1️⃣ Standard Scan Mode

Quick scan of specified network segments with basic device information:

- ✅ **Online Detection** - ICMP Ping detection (250ms timeout)
- ✅ **Port Scanning** - 7 signature ports (135, 80, 62078, 8008, 8009, 5555, 1900)
- ✅ **MAC Identification** - SendARP + ARP table query with vendor matching
- ✅ **Device Classification** - Smart recognition of routers, phones, PCs, IoT devices
- ✅ **Web Scraping** - Automatic HTTP page title extraction
- ✅ **History Records** - Device uptime tracking with note management

### 2️⃣ AI Deep Mode (Goku Detective)

Automatic LLM analysis after scanning:

- 🕵️ **Device Profiling** - Identity inference based on network behavior patterns
- 📊 **Network Report** - Generates "LAN Security & Asset Audit Report"
- 💡 **Detection Guide** - Practical techniques to expose hidden devices
- 🎯 **Privacy Recognition** - Accurate identification of random MAC smartphones
- ⚡ **Sleep Analysis** - Explains high-latency devices in power-saving mode

**Supported AI Providers:**
- [Zhipu AI (GLM)](https://open.bigmodel.cn/) - Chinese LLM with excellent language understanding
- [Groq (Llama)](https://groq.com/) - Ultra-fast inference with generous free tier

### 3️⃣ Network Topology

Auto-generated visual network device relationship map:

- 🟢 **Online Devices** - Green nodes showing IP and name
- 🔴 **Offline Devices** - Red nodes for historical memory
- 🔗 **Connections** - Displays gateway-to-device hierarchy
- 📱 **Device Icons** - Different icons based on device type

### 4️⃣ Data Management

- 📥 **CSV Export** - Export device list to Excel-readable format
- 📄 **Report Download** - Save AI analysis as Markdown files
- 💾 **Local Storage** - Device records saved in `data/devices.json`
- 📁 **Download Directory** - Exported files stored in `downloads/` folder

---

## 🚀 Quick Start

### Option 1: Direct Run (Recommended)

1. Download latest [Goku Scanner.zip](releases)
2. Extract to any directory
3. Double-click `悟空局域网侦探.exe`
4. Click "Start Scan" to begin

**No Python installation or dependencies required!**

### Option 2: Run from Source

#### Requirements

- Python 3.10+
- Windows 10/11 (supports pywebview native window)

#### Installation Steps

```bash
# 1. Clone repository
git clone https://github.com/gokuscraper/goku-scanner.git
cd goku-scanner

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch application
python main.py
```

#### Configure AI Keys (Optional)

First-time setup: Click "Settings" button in top-right corner:

1. **Zhipu AI** - Register at [Zhipu Open Platform](https://open.bigmodel.cn/) to get API Key
2. **Groq** - Register at [Groq Cloud](https://console.groq.com/) to get API Key

**Standard scan mode works without AI configuration!**

---

## 📸 Interface Preview

### Main Interface
```
┌─────────────────────────────────────────────┐
│  🐒 Goku Scanner  [Search] [Devices] [Map] │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │  Network: 192.168.0.0/24              │  │
│  │  [Standard] [AI Deep Mode]            │  │
│  │  [Start Scan]                         │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  Device List (5 online):                    │
│  ├─ 192.168.0.1     Router       Online 🟢 │
│  ├─ 192.168.0.100   Windows PC   Online 🟢 │
│  ├─ 192.168.0.101   iPhone       Online 🟢 │
│  └─ ...                                     │
└─────────────────────────────────────────────┘
```

### AI Deep Report Example

```markdown
# 🎯 Detective Identity Profile

**Device IP**: 192.168.0.101  
**Inference**: This is 100% an iPhone 14 Pro with random MAC privacy protection enabled

**Reasoning**:
- Second MAC digit is `a` (0x0A),符合 Apple's random MAC specification
- All ports closed, indicating sleep mode
- 48ms latency proves it was just woken from power-saving mode by our scan

# 🕵️‍♂️ Goku Ghost-Hunting Guide

1. **Screen Wake Method**: Pick up this iPhone, unlock the screen, then rescan. It will immediately reveal hostname "iPhone-ZhangSan"
2. **AirDrop Detection**: Open AirDrop on the same network to see if this device appears
3. **Router Cross-Check**: Log into router admin panel, check DHCP lease list, match MAC address `5a:8f:aa:8e:bd:92`
```

---

## 🛠️ Technical Architecture

### Core Tech Stack

| Component | Technology | Description |
|-----------|------------|-------------|
| **UI Framework** | [NiceGUI](https://nicegui.io/) | Vue3-based Python Web UI |
| **Desktop Window** | [pywebview](https://pywebview.flowrl.com/) | Native desktop app container |
| **AI Engine** | OpenAI SDK / Zhipu SDK | Multi-model support with streaming |
| **Network Detection** | Native socket + subprocess | High-performance concurrent scanning |
| **Data Persistence** | JSON files | Lightweight local storage |
| **Encrypted Storage** | Windows DPAPI | System-level key protection |

### Performance Optimization

- ✅ **32-thread concurrency** - Balanced speed and resource usage
- ✅ **Smart timeouts** - Ping 250ms, ports 200ms, DNS/NetBIOS disabled
- ✅ **Caching mechanism** - LRU cache for MAC vendor database
- ✅ **Async processing** - asyncio + ThreadPoolExecutor hybrid architecture

### Scanning Process

```
User clicks "Start Scan"
    ↓
Generate 254 IP list (192.168.0.1-254)
    ↓
32 threads execute scan_one() concurrently
    ├─ Ping detection (250ms timeout)
    ├─ Port scanning (7 ports × 200ms)
    ├─ MAC acquisition (SendARP + ARP table)
    ├─ Web title (if port 80 open)
    └─ Device classification (rule engine)
    ↓
Aggregate results → Update UI
    ↓
If AI Deep Mode → Call LLM analysis → Popup report
```

---

## 📊 Performance Comparison

| Metric | Value | Description |
|--------|-------|-------------|
| **Scan Speed** | 4.17 seconds | 254 IPs, 5 devices found |
| **Memory Usage** | ~250MB | Runtime peak |
| **Package Size** | ~90MB | Including all dependencies |
| **Startup Time** | 3-5 seconds | First launch (with antivirus scan) |
| **CPU Usage** | <5% | After scan completion |

---

## 🔒 Privacy & Security

### Data Protection

- ✅ **Local Operation** - All scanning completes within LAN, no cloud upload
- ✅ **Key Encryption** - API keys encrypted with Windows DPAPI, decryptable only by current user
- ✅ **Open Source** - Fully transparent code, no backdoor risk
- ✅ **Minimal Permissions** - Runs without administrator privileges

### `.gitignore` Protection

Sensitive files excluded from Git:

```
.zhipu_api_key          # Zhipu API key (encrypted)
.groq_api_key           # Groq API key (encrypted)
data/devices.json       # Device history (contains internal IPs)
framework_settings.json # Configuration file
downloads/              # Exported files
```

---

## ❓ FAQ

### Q1: Why are the last few IPs particularly slow to scan?

**A**: This is normal. Offline devices require waiting for Ping timeout (250ms). When most IPs are offline, the final batch appears slower. Actual total time is only about 4 seconds.

### Q2: What if AI analysis fails?

**A**: 
1. Check if API keys are configured (top-right "Settings")
2. Confirm network connection is working
3. Check console error messages
4. Try switching AI provider (Zhipu/Groq)

### Q3: How to change scan network segment?

**A**: Modify CIDR format in top input box, e.g.:
- `192.168.1.0/24` - Scan 192.168.1.1-254
- `10.0.0.0/24` - Scan 10.0.0.1-254
- `172.16.0.0/24` - Scan 172.16.0.1-254

### Q4: Can I scan multiple network segments?

**A**: Currently supports single segment per scan. For multiple segments, modify input box content and rescan.

### Q5: Can I delete the `_internal` folder?

**A**: **No!** This contains PyInstaller packaged dependencies. Deleting it will break the application.

### Q6: What if antivirus software flags it?

**A**: PyInstaller packaged programs may trigger false positives. Solutions:
1. Add program to antivirus whitelist
2. Run from source (won't be flagged)
3. Submit false positive report to antivirus vendor

---

## 📦 Packaging & Distribution

### PyInstaller Packaging

```bash
# 1. Install PyInstaller
pip install pyinstaller

# 2. Execute packaging
python -m PyInstaller --clean build.spec

# 3. Output location
dist/悟空局域网侦探/
```

### Packaging Configuration

- **Mode**: `--onedir` (single folder distribution)
- **Console**: `--windowed` (no console window)
- **Icon**: `app.ico` (custom application icon)
- **Resources**: Includes all images, databases, config files

---

## 🗺️ Roadmap

### ✅ Completed

- [x] Basic network scanning functionality
- [x] AI deep analysis mode
- [x] Network topology visualization
- [x] CSV/MD report export
- [x] pywebview native window
- [x] Performance optimization (32-thread concurrency)
- [x] PyInstaller packaging

### 🚧 Planned

- [ ] Multi-segment batch scanning
- [ ] Real-time device monitoring
- [ ] Alert notification system
- [ ] Plugin system (custom detection scripts)
- [ ] Web remote access mode
- [ ] Mobile APP

---

## 🤝 Contributing

Issues and Pull Requests are welcome!

### Development Setup

```bash
# 1. Fork this repository
# 2. Clone to local
git clone https://github.com/gokuscraper/goku-scanner.git

# 3. Create branch
git checkout -b feature/your-feature

# 4. Commit code
git commit -m "Add: new feature description"
git push origin feature/your-feature

# 5. Open PR
```

### Code Standards

- Follow PEP 8 style
- Add docstrings to functions and classes
- Maintain backward compatibility

---

## 📞 Support

### Community Group

Scan QR code to join WeChat group for latest updates and technical support:

![Community QR Code](gzh.jpg)

### Feedback Channels

- 🐛 [GitHub Issues](https://github.com/gokuscraper/goku-scanner/issues)
- 📧 Email: your-email@example.com
- 💬 WeChat Group: Scan QR code above

---

## 📄 License

This project is licensed under the [Apache License 2.0](LICENSE).

```
MIT License

Copyright (c) 2026 Goku Scanner

Permission is hereby granted...
```

---

## 🙏 Acknowledgments

Thanks to these open source projects:

- [NiceGUI](https://nicegui.io/) - Elegant Python Web UI framework
- [pywebview](https://pywebview.flowrl.com/) - Lightweight desktop app container
- [mac-vendor-lookup](https://pypi.org/project/mac-vendor-lookup/) - MAC address vendor lookup
- [Zhipu AI](https://open.bigmodel.cn/) - Chinese large language model
- [Groq](https://groq.com/) - Ultra-fast AI inference platform

---

## 📈 Star History

If this project helps you, please give it a ⭐ Star!

---

**Made with ❤️ by Goku Scanner Team**
