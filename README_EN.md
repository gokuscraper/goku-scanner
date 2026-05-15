# 🐒 Goku Scanner (悟空局域网侦探)

> **AI-Powered Network Scanner - Make Every Device Visible**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

[🇨🇳 中文版](README.md)

---

## 📖 Introduction

**Goku Scanner** is an intelligent LAN scanning tool built with Python + NiceGUI, combining traditional network detection techniques with AI deep learning analysis to quickly discover, identify, and analyze all connected devices on your local network.

![Main Interface](https://asiaassets.gokuscraper.com/images/2026/05/16/3f80fe6171affd1e.webp)

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

### 2️⃣ AI Deep Mode (Goku Detective)

Automatic LLM analysis after scanning:

- 🕵️ **Device Profiling** - Identity inference based on network behavior patterns
- 📊 **Network Report** - Generates "LAN Security & Asset Audit Report"
- 💡 **Detection Guide** - Practical techniques to expose hidden devices
- 🎯 **Privacy Recognition** - Accurate identification of random MAC smartphones
- ⚡ **Sleep Analysis** - Explains high-latency devices in power-saving mode

**Supported AI Providers:**
- [Zhipu AI (GLM)](https://www.bigmodel.cn/invite?icode=Ejyge8QfoYB7jR0pVOFW7mczbXFgPRGIalpycrEwJ28%3D) - Chinese LLM with excellent language understanding
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

1. **Zhipu AI** - Register at [Zhipu Open Platform](https://www.bigmodel.cn/invite?icode=Ejyge8QfoYB7jR0pVOFW7mczbXFgPRGIalpycrEwJ28%3D) to get API Key
2. **Groq** - Register at [Groq Cloud](https://console.groq.com/) to get API Key

**Standard scan mode works without AI configuration!**

---

## 📸 Interface Preview

### Main Interface
![Main Interface](https://asiaassets.gokuscraper.com/images/2026/05/16/8076e0e60f58cd2f.webp)

### AI Deep Report Example

![AI Report](https://asiaassets.gokuscraper.com/images/2026/05/16/efa5145bad83cc0f.webp)

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

---

## 🔒 Privacy & Security

### Data Protection

- ✅ **Local Operation** - All scanning completes within LAN, no cloud upload
- ✅ **Key Encryption** - API keys encrypted with Windows DPAPI, decryptable only by current user
- ✅ **Open Source** - Fully transparent code, no backdoor risk
- ✅ **Minimal Permissions** - Runs without administrator privileges

---

## ❓ FAQ

### Q1: What if AI analysis fails?

**A**: 
1. Check if API keys are configured (top-right "Settings")
2. Confirm network connection is working
3. Check console error messages
4. Try switching AI provider (Zhipu/Groq)

### Q2: How to change scan network segment?

**A**: Modify CIDR format in top input box, e.g.:
- `192.168.1.0/24` - Scan 192.168.1.1-254
- `10.0.0.0/24` - Scan 10.0.0.1-254
- `172.16.0.0/24` - Scan 172.16.0.1-254

### Q3: Can I scan multiple network segments?

**A**: Currently supports single segment per scan. For multiple segments, modify input box content and rescan.

### Q4: Can I delete the `_internal` folder?

**A**: **No!** This contains PyInstaller packaged dependencies. Deleting it will break the application.

### Q5: What if antivirus software flags it?

**A**: PyInstaller packaged programs may trigger false positives. Solutions:

1. Add program to antivirus whitelist
2. Run from source (won't be flagged)
3. Submit false positive report to antivirus vendor

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

---

## 📞 Support

### Community Group

Scan QR code to join WeChat group for latest updates and technical support:

![Community QR Code](https://asiaassets.gokuscraper.com/images/2026/05/16/20f9855b37f18dd3.webp)

### Feedback Channels

- 🐛 [GitHub Issues](https://github.com/gokuscraper/goku-scanner/issues)
- 📧 Email: contact@gokuscraper.com
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

---

## 📈 Star History

If this project helps you, please give it a ⭐ Star!

---

**Made with ❤️ by GokuScraper**
