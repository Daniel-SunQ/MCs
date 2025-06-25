##Mini Intelegent car multimode  interaction system

本项目是一个基于Flask的智能车载多模态交互系统，集成了语音识别、深度学习视觉感知、车辆状态管理、多媒体娱乐、导航与自动驾驶等功能。系统支持自然语言语音控制，具备实时车辆信息展示、空调与多媒体控制、防碰撞检测等能力，旨在为智能汽车提供安全、便捷、智能的人机交互体验。

## 目录

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

## 项目简介

本项目致力于打造一个集成多种智能交互能力的车载系统。通过融合语音识别、深度学习视觉感知、车辆状态监控、多媒体娱乐、导航与自动驾驶等模块，用户可通过自然语言或界面操作实现对车辆的智能控制。系统适用于智能汽车、车载娱乐终端等场景，提升驾驶安全性与舒适性，推动车载人机交互体验升级。

## 功能特性

- 语音识别与控制：支持中文语音唤醒、指令识别，实现对车辆功能的语音操控。
- 车辆状态监控：实时展示车辆速度、电量、里程、胎压、发动机等核心信息。
- 空调与多媒体控制：通过语音或界面调节空调温度、风量，控制音乐播放、音量、切歌等。
- 智能导航：集成导航模块，支持目的地设置、路线规划与实时导航信息展示。
- 防碰撞检测：基于深度学习模型，实时分析摄像头画面，辅助驾驶安全。
- 多模态人机交互：结合语音、视觉与触控，提升交互的自然性与便捷性。
- 语音大模型同步：接入本地自定义大模型，实现语音指令识别、常见问答交互、知识库回答等。
- 自动驾驶状态管理：展示自动驾驶等级与当前状态，支持启停控制。
- 现代化UI界面：美观易用的前端界面，适配多种车载屏幕。
- 可扩展性强：支持自定义扩展更多车载应用与功能模块。

## 安装方法

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

**部分内容需要网络，请在根目录下创建`.env`文件，需要配置的api如下：**
- 高德地图API，在[高德地图开发者平台](https://lbs.amap.com/ "高德地图开发者平台")获取：
```text
AMAP_API_KEY=your key
AMAP_SECURITY_SECRET=your secret
```
- 和风天气API，在[和风天气开发者平台](https://dev.qweather.com/ "和风天气开发者平台")获取：
```text
QWEATHER_API_KEY=your key
```
- pico voice API，在[PICOVOICE-Developer](https://console.picovoice.ai/ "PICOVOICE-Developer")获取：
```text
PORCUPINE_ACCESS_KEY=your key
```

**部分内容需要自行download模型，请在根目录下放置模型文件或ollama本地部署**
请确保 `depth_anything_v2_vits.pth`、`vosk-model-cn-0.22/`、`vosk-model-small-cn-0.22/` 等模型文件已放置于项目根目录。

**静态资源（音乐、图片、语音等）已包含在 static/ 目录下，无需额外下载。**

具体细节请参考后续内容。
- 防碰撞检测模型（深度估计模型）:
若自行下载模型，请放置在根目录下，名为`depth-anything/Depth-Anything-V2-Small-hf`，若不下载，则无需配置。
- 语音识别模型：
请放在根目录下，名为`vosk-model-small-cn-0.22/`。
- 本地LLM：
通过Ollama进行下载支持tools的模型，若不知道如何运行

## 使用说明

### 启动项目

```bash
python app.py
```
请确保网络畅通，因为会使用到SocketIO等实时功能。

### 访问方式

启动后，在浏览器中访问 http://localhost:5001 即可进入智能车机系统主界面。

## 文件结构
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
└── vosk-model-cn-0.22/            # 中文语音识别模型
    └── vosk-model-small-cn-0.22/  # 小型中文语音识别模型

- app.py: 系统核心，包含所有API接口、语音识别、深度学习模型初始化、车辆状态管理等
- templates/index.html: 主界面，提供车辆状态展示、空调控制、多媒体播放等功能
- templates/collision_page.html: 防碰撞检测专用页面
- static/js/main.js: 前端交互逻辑，处理用户操作和API调用
- static/css/style.css: 界面样式，提供现代化的UI设计

## 依赖说明

###Python版本要求
- Python >= 3.8

###核心依赖库
- Web框架与扩展
- Flask==2.3.3 - Web应用框架
- Flask-CORS==4.0.0 - 跨域资源共享支持
- Flask-SocketIO - 实时通信支持

####深度学习与计算机视觉
- torch==2.1.0 - PyTorch深度学习框架
- torchvision==0.16.0 - 计算机视觉工具包
- transformers==4.41.2 - Hugging Face模型库
- timm==1.0.7 - 图像模型库
- opencv-python-headless==4.10.0.82 - 计算机视觉库
- accelerate==0.31.0 - 模型加速库

####语音识别与处理
- vosk==0.3.44 - 离线语音识别
- soundfile==0.12.1 - 音频文件处理
- pvporcupine - 语音唤醒词检测
- pvrecorder - 音频录制

####多媒体处理
- mutagen==1.47.0 - 音频元数据处理
- playsound - 音频播放

####网络与API
- requests==2.31.0 - HTTP请求库
- httpx==0.25.2 - 异步HTTP客户端
- openai==1.3.0 - OpenAI API客户端
- websockets==11.0.3 - WebSocket支持

####其他工具
- python-dotenv==1.0.0 - 环境变量管理
- numpy - 数值计算
- PIL - 图像处理

###系统要求
- 支持摄像头设备（用于防碰撞检测）
- 麦克风设备（用于语音识别）
- 音频输出设备（用于语音播放）
- 建议4GB以上内存（用于深度学习模型运行）

##功能使用
- 语音控制：点击语音按钮或使用唤醒词激活语音识别，支持中文语音指令。
- 车辆状态查看：在主界面可实时查看车辆各项状态信息。
- 空调控制：点击空调图标进入控制界面，可调节温度、风量等。
- 多媒体播放：支持播放本地音乐，控制播放、暂停、切歌等操作。
- 导航功能：设置目的地，查看实时导航信息。
- 防碰撞检测：点击相应功能卡片，可打开防碰撞检测页面进行实时监控。
待开发功能：
- 设置功能：...
- 管理员功能：...
- 疲劳检测功能：...

## 常见问题

**1. 模型初始化失败**
**问题**: 启动时出现模型加载错误
```text
Error initializing model
```
**解决方案**:
确保 depth_anything_v2_vits.pth 文件存在于项目根目录
检查是否有足够的磁盘空间和内存
对于Apple Silicon Mac，确保PyTorch版本支持MPS

**2. 摄像头无法打开**
```text
Error initializing camera
```
**问题**: 防碰撞检测功能无法访问摄像头

**解决方案**:

- 检查摄像头权限设置
- 确保摄像头未被其他程序占用
- 尝试修改 app.py 中的摄像头索引（默认是0）

**3. 语音识别不工作**

**问题**: 语音控制功能无响应
**解决方案:**

- 检查麦克风权限和连接状态，运行我们的测试文件`test.py`，检查麦克风的index（默认为0）
- 确保 `vosk-model-cn-0.22/` 模型文件完整
- 检查音频设备驱动是否正常

**4. 音乐播放器问题**

**问题**: 音乐无法播放或歌词无法加载
**解决方案**:

- 检查系统音频设置和音量
- 确保音频文件格式支持（ 'MP3,  WAVE, OggVorbis，FLAC, MP4等）
- 检查 `static/music/` 和` static/voice/` 目录下的文件完整性
- `static/music/`目录下应为MP3和对应的lyric，例：`song1.mp3`对应`song1.lrc`。

**5.主界面紊乱问题**

**问题**：主界面用户头像以及主界面背景无法加载

**解决方案**：

- 检查图片文件配置是否正确，应放在`static/images/`目录下，用户头像名为**avatar**，背景名为**car_menu**
- 检查文件格式是否为jpg、png格式
- 通过网页console检查

**5.天气获取失败，加载天气异常**

**问题**：大模型得到的天气异常（非本城市），主界面右上角天气获取失败

**解决方案**：

- 检查APIkey是否配置正确
- 通过test.py进行测试，查看输出结果

**6.大模型回复问题**

**问题**：大模型回复较慢或大模型无法call对应的Function
```text
llm failure
no tool to call
LLM do not have tool parameter
```

**解决方案**：

- 检查显存，建议与Ollama的显存推荐同步下载对应的大模型
- 检查Ollama是否正确运行
- 当前大模型的能力较弱，无法进行正确的Function calling

##开发指南

非常欢迎社区用户参与本项目的开发与完善！如有兴趣贡献代码、文档或提出建议，请参考【开发指南】CONTRIBUTER.MD

## 许可证

本项目采用 MIT/Apache-2.0/GPL-3.0 等许可证，详见[LICENSE](LICENSE)。

## 联系方式

- 作者：Daniel-SunQ
- 邮箱：Qingmu031127@gmail.com
- 其他联系方式（QQ:468652929）