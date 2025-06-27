# Mini Intelligent Car Multimode Interaction System 开发指南

## 项目简介

本项目是一个面向智能车载系统的多模态交互平台，集成了防碰撞检测、语音识别与合成、天气与导航、音乐娱乐、车辆状态管理等多种功能，支持本地与Web前端交互，便于二次开发和功能扩展。

---

## 主要功能模块

- **防碰撞检测**：基于深度学习模型和摄像头，实时显示原始与深度渲染画面。
- **语音识别与唤醒**：集成Vosk、Porcupine等，支持本地语音唤醒、识别、TTS合成。
- **天气与导航**：集成和风天气API，支持实时天气与未来预报，导航状态管理。
- **音乐娱乐**：本地音乐扫描、播放、歌词显示等。
- **车辆/空调/多媒体状态管理**：RESTful API接口，支持前端与后端状态同步。
- **SocketIO 实时推送**：支持语音状态等事件的实时推送。

---

## 开发环境与依赖

1. **Python 3.8+**（推荐3.9/3.10）
2. **依赖安装**  
   ```bash
   pip install -r requirements.txt
   ```
3. **环境变量**  
   - 需配置`.env`文件，包含API密钥（如QWEATHER_API_KEY、PORCUPINE_ACCESS_KEY等）。
   - 示例：
     ```
     QWEATHER_API_KEY=你的和风天气key
     PORCUPINE_ACCESS_KEY=你的Porcupine key
     ```

4. **模型文件**  
   - 需下载Vosk中文模型、Depth-Anything模型等，放置在指定目录。

---

## 运行与测试

### 1. 启动后端服务

```bash
python app.py
```
- 默认监听 `http://127.0.0.1:5001`
- 启动后可通过前端页面或API接口访问各功能

### 2. 前端访问

- 直接用浏览器访问 `http://127.0.0.1:5001`
- 支持多种模块切换、语音交互、音乐播放等

### 3. 模块化测试（推荐）

使用`test.py`可一键测试各主要模块，适合开发调试和二次开发：

```bash
python test.py --collision                # 测试防碰撞检测（本地弹窗）
python test.py --weather --city 重庆      # 测试天气API
python test.py --music                   # 测试音乐API
python test.py --voice                   # 测试语音识别
python test.py --tts --text "你好"        # 测试TTS语音合成
python test.py --vehicle_status          # 测试车辆状态API（需后端已启动）
python test.py --ac_status               # 测试空调状态API（需后端已启动）
python test.py --media_status            # 测试多媒体状态API（需后端已启动）
python test.py --navigation_status       # 测试导航状态API（需后端已启动）
python test.py --wake_word               # 测试唤醒词检测
python test.py --socketio_voice          # 测试SocketIO语音状态推送（需后端已启动）
python test.py --voice_full              # 测试完整语音交互流程
python test.py --amap_config                  # 测试高德地图API配置
python test.py --lyrics --song_id 0           # 测试歌词API
python test.py --music_control --action play --song_id 0   # 测试音乐播放控制API
python test.py --tts_save --text "保存测试" --filename "output.mp3"   # 测试TTS合成并保存为文件
```

> **注意：**  
> - 依赖API/SocketIO的测试（如`--vehicle_status`等）需先运行`python app.py`。
> - 本地模型、API密钥等需提前准备好。

---

## 文件结构说明

- `app.py`：主后端服务，集成所有API、SocketIO、模型推理等
- `test.py`：开发者测试入口，覆盖所有主要功能的测试用例
- `static/`：前端静态资源（JS、CSS、图片、音乐等）
- `templates/`：前端HTML模板
- `vosk-model-*/`：语音识别模型目录
- `requirements.txt`：依赖包列表
- `CONTRIBUTER.md`：开发指南（本文件）

---

## 常见问题

- **模型/依赖未安装**：请确保`requirements.txt`和模型文件已正确安装和放置。
- **API密钥无效**：请检查`.env`文件和API密钥是否正确。
- **摄像头/麦克风不可用**：请检查本地硬件和驱动。
- **端口冲突**：如5001端口被占用，可在`app.py`中修改端口。

---

## 二次开发建议

- **新增功能**：可在`app.py`和`test.py`中新增API、测试函数，参考现有模块风格。
- **前后端联动**：前端通过API与后端交互，建议RESTful风格。
- **模型替换/扩展**：可替换为更强的深度/语音/对话模型，注意依赖和接口兼容。
- **多用户/权限管理**：如需支持多用户，可扩展用户认证模块。

---

## 许可证

请参考`LICENSE`文件。

---

## 联系方式

如有问题或建议，欢迎提交Issue或PR，或联系项目维护者。