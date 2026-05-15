# 🐒 悟空局域网侦探 (Goku Scanner)

> **让局域网设备无所遁形的 AI 智能扫描器**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

[🇺🇸 English Version](README_EN.md)

---

## 📖 项目简介

**悟空局域网侦探**是一款基于 Python + NiceGUI 开发的智能局域网扫描工具，融合了传统网络探测技术与 AI 深度学习分析，能够快速发现、识别和分析局域网内的所有联网设备。

![image-20260516055417160](https://asiaassets.gokuscraper.com/images/2026/05/16/3f80fe6171affd1e.webp)

### ✨ 核心特色

- 🚀 **极速扫描** - 32线程并发，254个IP仅需4秒
- 🤖 **AI 侦探模式** - 智能识别设备类型，生成专业分析报告
- 🗺️ **拓扑可视化** - 自动生成网络设备关系图
- 🔍 **深度探测** - Ping、端口、MAC、Web标题多维度分析
- 💾 **数据导出** - 支持CSV表格和Markdown报告导出
- 🔒 **隐私保护** - 本地运行，API密钥加密存储

---

## 🎯 功能特性

### 1️⃣ 标准扫描模式

快速扫描指定网段，获取设备基础信息：

- ✅ **在线检测** - ICMP Ping探测（250ms超时）
- ✅ **端口扫描** - 7个特征端口（135, 80, 62078, 8008, 8009, 5555, 1900）
- ✅ **MAC识别** - SendARP + ARP表查询，自动匹配厂商
- ✅ **设备分类** - 智能识别路由器、手机、电脑、IoT设备等
- ✅ **Web抓取** - 自动提取HTTP页面标题

### 2️⃣ AI 深度模式（悟空侦探）

扫描完成后自动调用大语言模型进行深度分析：

- 🕵️ **设备侧写** - 基于网络行为学推断设备身份
- 📊 **全网报告** - 生成《局域网全盘安全与资产审计报告》
- 💡 **抓鬼指南** - 提供实操技术手段逼出隐藏设备
- 🎯 **隐私识别** - 精准识别随机MAC的智能手机

**支持的AI提供商：**
- [智谱AI (GLM)](https://open.bigmodel.cn/) - 国产大模型，中文理解优秀
- [Groq (Llama)](https://groq.com/) - 超高速推理，免费额度充足

### 3️⃣ 网络拓扑图

自动生成可视化的网络设备关系图：

- 🟢 **在线设备** - 绿色节点，显示IP和名称
- 🔴 **离线设备** - 红色节点，历史记忆
- 🔗 **连接关系** - 展示网关与终端设备的层级
- 📱 **设备图标** - 根据类型显示不同图标

### 4️⃣ 数据管理

- 📥 **CSV导出** - 导出设备列表为Excel可读格式
- 📄 **报告下载** - AI分析报告保存为Markdown文件
- 💾 **本地存储** - 设备记录保存在 `data/devices.json`
- 📁 **下载目录** - 导出文件统一存放在 `downloads/` 文件夹

---

## 🚀 快速开始

### 方式一：直接运行（推荐）

1. 下载最新版本的 [悟空雷达.zip](releases)
2. 解压到任意目录
3. 双击运行 `悟空局域网侦探.exe`
4. 点击"开始扫描"即可使用

**无需安装Python或任何依赖！**

### 方式二：源码运行

#### 环境要求

- Python 3.10+
- Windows 10/11（支持pywebview原生窗口）

#### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/gokuscraper/goku-scanner.git
cd goku-scanner

# 2. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动程序
python main.py
```

#### 配置AI密钥（可选）

首次使用时，点击右上角"设置"按钮：

1. **智谱AI** - 注册 [智谱开放平台](https://www.bigmodel.cn/invite?icode=Ejyge8QfoYB7jR0pVOFW7mczbXFgPRGIalpycrEwJ28%3D) 获取API Key
2. **Groq** - 注册 [Groq Cloud](https://console.groq.com/) 获取API Key

**不配置也可以使用标准扫描模式！**

---

## 📸 界面预览

### 主界面
![image-20260516055824001](https://asiaassets.gokuscraper.com/images/2026/05/16/8076e0e60f58cd2f.webp)

### AI深度报告示例

![image-20260516060343012](https://asiaassets.gokuscraper.com/images/2026/05/16/efa5145bad83cc0f.webp)

---

## 🛠️ 技术架构

### 核心技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| **UI框架** | [NiceGUI](https://nicegui.io/) | 基于Vue3的Python Web UI |
| **桌面窗口** | [pywebview](https://pywebview.flowrl.com/) | 原生桌面应用容器 |
| **AI引擎** | OpenAI SDK / Zhipu SDK | 多模型支持，流式输出 |
| **网络探测** | 原生socket + subprocess | 高性能并发扫描 |
| **数据持久化** | JSON文件 | 轻量级本地存储 |
| **加密存储** | Windows DPAPI | 系统级密钥保护 |



---

## 🔒 隐私与安全

### 数据保护

- ✅ **本地运行** - 所有扫描在局域网内完成，不上传云端
- ✅ **密钥加密** - API密钥使用Windows DPAPI加密，仅当前用户可解密
- ✅ **开源透明** - 代码完全公开，无后门风险
- ✅ **最小权限** - 无需管理员权限即可运行

---

## ❓ 常见问题

### Q1: AI分析失败怎么办？

**答**: 
1. 检查是否配置了API密钥（右上角"设置"）
2. 确认网络连接正常
3. 查看控制台错误信息
4. 可以尝试切换AI提供商（智谱/Groq）

### Q2: 如何修改扫描网段？

**答**: 在顶部输入框修改CIDR格式，例如：
- `192.168.1.0/24` - 扫描192.168.1.1-254
- `10.0.0.0/24` - 扫描10.0.0.1-254
- `172.16.0.0/24` - 扫描172.16.0.1-254

### Q3: 可以扫描多个网段吗？

**答**: 目前支持单次扫描一个网段。如需扫描多个，可以修改输入框内容后重新扫描。

### Q4: `_internal` 文件夹能删除吗？

**答**: **不能删除！** 这是PyInstaller打包的依赖库，删除后程序无法运行。

### Q5: 杀毒软件报毒怎么办？

**答**: PyInstaller打包的程序可能被误报。解决方法：

1. 将程序添加到杀毒软件白名单
2. 从源码运行（不会被误报）
3. 提交误报到杀毒软件厂商

---

## 🗺️ 开发路线

### ✅ 已完成

- [x] 基础网络扫描功能
- [x] AI深度分析模式
- [x] 网络拓扑可视化
- [x] CSV/MD报告导出
- [x] pywebview原生窗口
- [x] 性能优化（32线程并发）
- [x] PyInstaller打包

### 🚧 计划中

- [ ] 多网段批量扫描
- [ ] 设备实时监控
- [ ] 告警通知功能
- [ ] 插件系统（自定义探测脚本）
- [ ] Web远程访问模式
- [ ] 移动端APP

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

---

## 📞 技术支持

### 交流群

扫码加入微信交流群，获取最新资讯和技术支持：

![交流群二维码](https://asiaassets.gokuscraper.com/images/2026/05/16/20f9855b37f18dd3.webp)

### 反馈渠道

- 🐛 [GitHub Issues](https://github.com/gokuscraper/goku-scanner/issues)
- 📧 Email: contact@gokuscraper.com
- 💬 微信群：扫码上方二维码

---

## 📄 许可证

本项目采用 [Apache License 2.0](LICENSE) 开源协议。

---

## 🙏 致谢

感谢以下开源项目：

- [NiceGUI](https://nicegui.io/) - 优雅的Python Web UI框架
- [pywebview](https://pywebview.flowrl.com/) - 轻量级桌面应用容器
- [mac-vendor-lookup](https://pypi.org/project/mac-vendor-lookup/) - MAC地址厂商查询

---

## 📈 Star History

如果这个项目对你有帮助，请给个 ⭐ Star 支持一下！

---

**Made with ❤️ by GokuScraper**
