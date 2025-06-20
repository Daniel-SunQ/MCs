# 智能车机系统

一个基于Web的现代化车机系统，提供完整的车载功能管理和控制界面。

## 功能特性

### 🚗 主要功能模块

1. **车辆状态监控**
   - 实时速度显示
   - 油量/电量监控
   - 发动机状态
   - 胎压监测
   - 里程表显示

2. **空调控制系统**
   - 温度调节（16-30°C）
   - 风速控制（1-5档）
   - 模式选择（自动/制冷/制热）
   - 除霜功能
   - 内循环控制

3. **多媒体娱乐**
   - 音乐播放控制
   - 音量调节
   - 音源切换（收音机/蓝牙/USB）
   - 播放列表管理

4. **导航系统**
   - 目的地设置
   - 路线规划
   - 实时导航信息
   - ETA和距离显示

5. **车载应用**
   - 电话功能
   - 消息应用
   - 日历管理
   - 天气信息
   - 摄像头查看
   - 游戏娱乐

6. **系统设置**
   - 显示设置（亮度/主题）
   - 声音设置
   - 连接管理（WiFi/蓝牙）

### 🎤 语音控制

- 支持语音命令识别
- 语音控制空调、音乐、导航等功能
- 实时语音状态显示

### 🤖 自动驾驶

- 自动驾驶状态监控
- 自动驾驶级别显示
- 状态指示器

## 技术架构

### 后端技术栈
- **Python 3.8+**
- **Flask** - Web框架
- **Flask-CORS** - 跨域支持

### 前端技术栈
- **HTML5** - 页面结构
- **CSS3** - 现代化样式设计
- **JavaScript (ES6+)** - 交互逻辑
- **Font Awesome** - 图标库

### 设计特点
- **响应式设计** - 适配不同屏幕尺寸
- **现代化UI** - 深色主题，毛玻璃效果
- **流畅动画** - 平滑的过渡效果
- **直观交互** - 简洁易用的操作界面

## 安装和运行

### 环境要求
- Python 3.8 或更高版本
- 现代浏览器（Chrome、Firefox、Safari、Edge）

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd driving_stystem
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行应用**
   ```bash
   python app.py
   ```

4. **访问系统**
   打开浏览器访问 `http://localhost:5000`

## 使用说明

### 基本操作
- **点击功能卡片** - 进入对应功能模块
- **返回按钮** - 返回主界面
- **语音控制按钮** - 开启/关闭语音控制

### 快捷键
- **ESC** - 返回主界面
- **空格键** - 切换语音控制
- **数字键 1-6** - 快速访问功能模块

### 语音命令示例
- "空调温度调高" - 提高空调温度
- "播放音乐" - 开始播放音乐
- "开启导航" - 进入导航模块
- "启动自动驾驶" - 启用自动驾驶

## 项目结构

```
driving_stystem/
├── app.py                 # Flask主应用
├── requirements.txt       # Python依赖
├── README.md             # 项目说明
├── templates/
│   └── index.html        # 主页面模板
└── static/
    ├── css/
    │   └── style.css     # 样式文件
    ├── js/
    │   └── main.js       # JavaScript逻辑
    └── images/           # 图片资源
```

## API接口

### 车辆状态
- `GET /api/vehicle/status` - 获取车辆状态
- `POST /api/vehicle/status` - 更新车辆状态

### 空调控制
- `GET /api/ac/status` - 获取空调状态
- `POST /api/ac/status` - 更新空调设置

### 多媒体
- `GET /api/media/status` - 获取多媒体状态
- `POST /api/media/status` - 更新多媒体设置

### 导航
- `GET /api/navigation/status` - 获取导航状态
- `POST /api/navigation/status` - 更新导航信息

### 自动驾驶
- `GET /api/autopilot/status` - 获取自动驾驶状态
- `POST /api/autopilot/status` - 更新自动驾驶设置

### 语音控制
- `GET /api/voice/status` - 获取语音状态
- `POST /api/voice/listen` - 开始语音监听
- `POST /api/voice/stop` - 停止语音监听
- `POST /api/voice/command` - 处理语音命令

## 开发说明

### 扩展功能
系统采用模块化设计，可以轻松添加新功能：

1. 在 `app.py` 中添加新的API路由
2. 在 `templates/index.html` 中添加对应的HTML模块
3. 在 `static/css/style.css` 中添加样式
4. 在 `static/js/main.js` 中添加交互逻辑

### 自定义主题
可以通过修改CSS变量来定制界面主题：
- 主色调：`#4ecdc4`
- 强调色：`#ff6b6b`
- 背景渐变：`linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)`

## 许可证

本项目采用 MIT 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 GitHub Issue
- 发送邮件至项目维护者

---

**注意**：这是一个演示项目，实际部署时需要根据具体需求进行安全性和功能性的完善。 