# 🚗✨ Mini Intelligent Car Multimode Interaction System

<p align="center">
  <img src="static/images/car_menu.jpg" alt="Car Menu" width="400"/>
</p>

> **一站式智能车载多模态交互系统**  
> <sub>集成语音识别 | 视觉感知 | 车辆管理 | 多媒体娱乐 | 智能导航 | 自动驾驶</sub>

---

## 🗂️ 目录
- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [安装方法](#安装方法)
- [使用说明](#使用说明)
- [文件结构](#文件结构)
- [依赖说明](#依赖说明)
- [功能使用](#功能使用)
- [常见问题](#常见问题)
- [开发指南](#开发指南)
- [许可证](#许可证)
- [联系方式](#联系方式)

---

## 🧩 项目简介

本项目致力于打造一个集成多种智能交互能力的车载系统。通过融合语音识别、深度学习视觉感知、车辆状态监控、多媒体娱乐、导航与自动驾驶等模块，用户可通过自然语言或界面操作实现对车辆的智能控制。系统适用于智能汽车、车载娱乐终端等场景，提升驾驶安全性与舒适性，推动车载人机交互体验升级。

---

## 🚀 功能特性

- 🎤 **语音识别与控制**：支持中文语音唤醒、指令识别，实现对车辆功能的语音操控。
- 🚘 **车辆状态监控**：实时展示车辆速度、电量、里程、胎压、发动机等核心信息。
- ❄️ **空调与多媒体控制**：通过语音或界面调节空调温度、风量，控制音乐播放、音量、切歌等。
- 🗺️ **智能导航**：集成导航模块，支持目的地设置、路线规划与实时导航信息展示。
- 🛡️ **防碰撞检测**：基于深度学习模型，实时分析摄像头画面，辅助驾驶安全。
- 🧠 **多模态人机交互**：结合语音、视觉与触控，提升交互的自然性与便捷性。
- 🤖 **语音大模型同步**：接入本地自定义大模型，实现语音指令识别、常见问答交互、知识库回答等。
- 🏁 **自动驾驶状态管理**：展示自动驾驶等级与当前状态，支持启停控制。
- 💻 **现代化UI界面**：美观易用的前端界面，适配多种车载屏幕。
- 🧩 **可扩展性强**：支持自定义扩展更多车载应用与功能模块。

---

## ⚙️ 安装方法

### 1. 克隆仓库

```bash
git clone https://github.com/Daniel-SunQ/MCs.git
cd MCs
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 环境配置

> **请在根目录下创建 `.env` 文件，配置如下API密钥：**

- 🗺️ 高德地图API（[获取](https://lbs.amap.com/)）：
  ```text
  AMAP_API_KEY=your_key
  AMAP_SECURITY_SECRET=your_secret
  ```
- ☁️ 和风天气API（[获取](https://dev.qweather.com/)）：
  ```text
  QWEATHER_API_KEY=your_key
  ```
- 🦜 PicoVoice API（[获取](https://console.picovoice.ai/)）：
  ```text
  PORCUPINE_ACCESS_KEY=your_key
  ```
- 🤖 Ollama大模型（本地模型名）：
  ```text
  MODEL_NAME=your_model_name
  ```

> **请确保 `depth_anything_v2_vits.pth`、`vosk-model-cn-0.22/`、`vosk-model-small-cn-0.22/` 等模型文件已放置于项目根目录。**

> **静态资源（音乐、图片、语音等）已包含在 static/ 目录下，无需额外下载。**

---

## 🏁 使用说明

### 启动项目

```bash
python app.py
```

> 启动后，在浏览器访问 [http://localhost:5001](http://localhost:5001) 即可进入智能车机系统主界面。

---

## 🗂️ 文件结构

```text
driving_stystem/
├── app.py                          # 主应用文件，包含Flask路由和核心逻辑
├── requirements.txt                # Python依赖包列表
├── LICENSE                         # 项目许可证文件
├── README.md                       # 项目说明文档
├── depth_anything_v2_vits.pth      # 深度估计模型权重文件
├── test.py                         # 测试文件
├── static/                         # 静态资源目录
│   ├── css/
│   │   └── style.css              # 样式文件
│   ├── js/
│   │   └── main.js                # JavaScript交互逻辑
│   ├── images/                    # 图片资源
│   │   ├── avatar.jpg
│   │   └── car_menu.jpg
│   ├── music/                     # 音乐文件目录
│   └── voice/                     # 语音文件目录
├── templates/                      # HTML模板目录
│   ├── index.html                 # 主页面模板
│   └── collision_page.html        # 防碰撞检测页面模板
├── vosk-model-cn-0.22/            # 中文语音识别模型
└── vosk-model-small-cn-0.22/      # 小型中文语音识别模型
```

<p align="center">
  <img src="static/images/avatar.jpg" alt="Avatar" width="120" style="border-radius:50%"/>
</p>

---

## 🧩 依赖说明

- **Python >= 3.8**
- **核心依赖库**：
  - Flask、Flask-CORS、Flask-SocketIO
  - torch、torchvision、transformers、timm、opencv-python-headless、accelerate
  - vosk、soundfile、pvporcupine、pvrecorder
  - mutagen、playsound
  - requests、httpx、openai、websockets
  - python-dotenv、numpy、PIL

> 详细依赖见 `requirements.txt`

- **系统要求**：
  - 摄像头设备（防碰撞检测）
  - 麦克风设备（语音识别）
  - 音频输出设备（语音播放）
  - 建议4GB以上内存

---

## 🛠️ 功能使用

- 🎙️ 语音控制：点击语音按钮或使用唤醒词激活语音识别，支持中文语音指令。
- 🚗 车辆状态查看：主界面实时查看车辆各项状态信息。
- ❄️ 空调控制：点击空调图标进入控制界面，可调节温度、风量等。
- 🎵 多媒体播放：支持播放本地音乐，控制播放、暂停、切歌等操作。
- 🗺️ 导航功能：设置目的地，查看实时导航信息。
- 🛡️ 防碰撞检测：点击功能卡片，打开防碰撞检测页面实时监控。

> **待开发功能**：设置功能、管理员功能、疲劳检测功能等。

---

## ❓ 常见问题

> 若有未提到的常见问题，可通过 `test.py` 查找并解决。

### 1. 🧠 模型初始化失败
- **问题**: 启动时出现模型加载错误
- **解决**: 确保 `depth_anything_v2_vits.pth` 文件存在于项目根目录，检查磁盘空间和内存。

### 2. 📷 摄像头无法打开
- **问题**: 防碰撞检测功能无法访问摄像头
- **解决**: 检查摄像头权限、设备占用、索引设置。

### 3. 🎤 语音识别不工作
- **问题**: 语音控制无响应
- **解决**: 检查麦克风权限、`vosk-model-cn-0.22/` 完整性、音频驱动。

### 4. 🎵 音乐播放器问题
- **问题**: 音乐无法播放或歌词无法加载
- **解决**: 检查音频设置、文件格式、`static/music/` 和 `static/voice/` 文件完整性。

### 5. 🖼️ 主界面图片加载异常
- **问题**: 用户头像或背景无法加载
- **解决**: 检查图片文件是否在 `static/images/`，文件名和格式是否正确。

### 6. ☁️ 天气获取失败
- **问题**: 天气异常或主界面天气获取失败
- **解决**: 检查API key配置，使用 `test.py` 测试。

### 7. 🤖 大模型回复问题
- **问题**: 回复慢或无法调用Function
- **解决**: 检查显存、Ollama运行状态、模型能力。

---

## 👨‍💻 开发指南

欢迎社区用户参与本项目开发与完善！如有兴趣贡献代码、文档或建议，请参考 [CONTRIBUTER.md](CONTRIBUTER.md)

---

## 📄 许可证

本项目采用 MIT/Apache-2.0/GPL-3.0 等许可证，详见 [LICENSE](LICENSE)。

---

## 📬 联系方式

- 👤 作者：Daniel-SunQ
- 📧 邮箱：Qingmu031127@gmail.com
- 💬 QQ：468652929

<p align="center">
  <img src="static/images/car_menu.jpg" alt="Car Menu" width="300"/>
</p>
