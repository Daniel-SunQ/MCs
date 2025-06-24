# 智能车机系统

一个基于 Flask + 前端现代化技术的智能车机系统，支持车辆状态、空调、多媒体、导航、语音控制、自动驾驶、疲劳监测、防碰撞检测等功能。

---

## 主要功能

- 车辆状态监控
- 空调控制
- 多媒体娱乐（本地音乐播放、歌词显示）
- 导航与地图
- 车载应用扩展
- 系统设置
- 语音控制
- 自动驾驶状态
- 疲劳监测
- **防碰撞检测（基于深度估计，独立页面展示）**

---

## 技术栈

- **后端**：Python 3.8+，Flask，Flask-CORS
- **深度估计**：PyTorch，transformers，timm，opencv-python-headless
- **前端**：HTML5，CSS3，JavaScript (ES6+)，Font Awesome

---

## 安装与运行

### 1. 克隆项目

```bash
git clone <repository-url>
cd driving_stystem
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行服务

```bash
python app.py
```

### 4. 访问系统

- 主界面：[http://localhost:5000](http://localhost:5000)
- 防碰撞检测独立页面：[http://localhost:5000/collision_detection_page](http://localhost:5000/collision_detection_page)

---

## 防碰撞检测功能说明

- 该功能基于 Depth Anything V2 Small 模型，利用摄像头实时深度估计，结果以伪彩色图像流形式展示。
- **Mac 用户优化**：已针对 Apple Silicon (M1/M2/M3) 进行深度优化，自动使用 MPS 加速，并修复了 PyTorch MPS 插值兼容性问题。
- **性能建议**：如需更高帧率，可进一步降低摄像头分辨率，或在高性能 GPU 设备上运行。

## 语音智能控制说明
- 该功能基于 Llama 3.2 latest 模型，利用ollama本地部署，进行实时解析Vosk模型识别到的语音命令，调用Function calling，能够正确的调用多种Function，实现llm的agent功能。
- **性能建议**：如需更加高效的模型，可以进一步增加LLM的体量。
---

## 必要的本地/未上传文件说明

> ⚠️ 下列文件/文件夹因体积或隐私原因未纳入版本控制（.gitignore），请根据实际需求自行准备：

- `.env`  
  用于存放API密钥等敏感信息。示例内容：
  ```
  QWEATHER_API_KEY=你的和风天气API密钥
  AMAP_API_KEY=你的高德地图API密钥
  AMAP_SECURITY_SECRET=你的高德安全密钥
  ```
- `vosk-model-cn-0.22/`、`vosk-model-small-cn-0.22/`  
  语音识别模型文件夹，需从 [Vosk 官方](https://alphacephei.com/vosk/models) 下载中文模型并解压到项目根目录。
- `static/music/`  
  本地音乐与歌词文件夹。可自行添加 `.mp3` 和对应 `.lrc` 歌词文件。
- `depth_anything`模型需要自行添加到根目录。
- `llama 3.2 latest`模型需要自行利用ollama进行配置。
- 其他 `.DS_Store`、缓存、临时文件等。

---

## 项目结构

```
driving_stystem/
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   ├── index.html
│   └── collision_page.html
├── static/
│   ├── css/
│   ├── js/
│   ├── images/
│   └── music/
├── vosk-model-cn-0.22/         # (未上传，需手动下载)
├── vosk-model-small-cn-0.22/   # (未上传，需手动下载)
├── depth_anything.pth          # (未上传，需手动下载)
└── .env                        # (未上传，需手动创建)
```

---

## 常见问题

- **模型/依赖下载慢**：建议使用国内镜像或提前下载好模型文件。
- **摄像头无法打开**：请检查本地摄像头权限，或尝试更换设备。
- **深度估计卡顿**：Mac 用户已做极致优化，若仍卡顿建议降低分辨率或使用更强显卡。
- **语音响应较慢**：已经使用最优的队列算法进行语音分chunk生成逻辑，由于语音生成基于网络API，请尝试更强的网络速度。
---

## 许可证

MIT License

---

如有问题欢迎提交 Issue 或 PR，或通过邮箱联系维护者。

---

如需进一步定制或遇到特殊环境问题，欢迎随时咨询！ 