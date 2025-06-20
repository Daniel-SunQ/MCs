// 全局变量
let currentModule = 'main';
let voiceListening = false;
let autopilotEnabled = false;
let currentPage = 0;
let fatigueLevel = 15;
let personalizationSettings = {
    auto: true,
    night: false,
    eco: false
};

// 触摸相关变量
let startX = 0;
let startY = 0;
let currentX = 0;
let currentY = 0;
let isDragging = false;

let mediaRecorder;
let audioChunks = [];

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    updateTime();
    setInterval(updateTime, 1000);
    loadVehicleStatus();
    loadACStatus();
    loadMediaStatus();
    loadNavigationStatus();
    loadAutopilotStatus();
    loadVoiceStatus();
    initFatigueDetection();
    initTouchEvents();
    updatePersonalizationDisplay();

    const voiceBtn = document.getElementById('voice-btn');
    const stopBtn = document.getElementById('stop-recording-btn');

    if (voiceBtn) {
        voiceBtn.addEventListener('click', startRecording);
    }
    if(stopBtn) {
        stopBtn.addEventListener('click', stopRecording);
    }
});

// 初始化触摸事件
function initTouchEvents() {
    const container = document.getElementById('main-container');
    
    container.addEventListener('touchstart', handleTouchStart, false);
    container.addEventListener('touchmove', handleTouchMove, false);
    container.addEventListener('touchend', handleTouchEnd, false);
    
    // 鼠标事件支持
    container.addEventListener('mousedown', handleMouseDown, false);
    container.addEventListener('mousemove', handleMouseMove, false);
    container.addEventListener('mouseup', handleMouseUp, false);
    container.addEventListener('mouseleave', handleMouseUp, false);
}

// 触摸开始
function handleTouchStart(e) {
    if (e.touches.length === 1) {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
        isDragging = true;
    }
}

// 触摸移动
function handleTouchMove(e) {
    if (!isDragging) return;
    
    e.preventDefault();
    currentX = e.touches[0].clientX;
    currentY = e.touches[0].clientY;
}

// 触摸结束
function handleTouchEnd(e) {
    if (!isDragging) return;
    
    isDragging = false;
    const deltaX = startX - currentX;
    const deltaY = startY - currentY;
    
    // 确保是水平滑动
    if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
        if (deltaX > 0) {
            // 向左滑动
            goToPage(Math.min(currentPage + 1, 2));
        } else {
            // 向右滑动
            goToPage(Math.max(currentPage - 1, 0));
        }
    }
}

// 鼠标按下
function handleMouseDown(e) {
    startX = e.clientX;
    startY = e.clientY;
    isDragging = true;
}

// 鼠标移动
function handleMouseMove(e) {
    if (!isDragging) return;
    currentX = e.clientX;
    currentY = e.clientY;
}

// 鼠标释放
function handleMouseUp(e) {
    if (!isDragging) return;
    
    isDragging = false;
    const deltaX = startX - currentX;
    const deltaY = startY - currentY;
    
    // 确保是水平滑动
    if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
        if (deltaX > 0) {
            // 向左滑动
            goToPage(Math.min(currentPage + 1, 2));
        } else {
            // 向右滑动
            goToPage(Math.max(currentPage - 1, 0));
        }
    }
}

// 跳转到指定页面
function goToPage(pageIndex) {
    const container = document.getElementById('main-container');
    const dots = document.querySelectorAll('.swipe-dot');
    
    currentPage = pageIndex;
    
    // 更新容器位置
    if (pageIndex === 0) {
        container.classList.remove('slide-left', 'slide-right');
    } else if (pageIndex === 1) {
        container.classList.add('slide-left');
        container.classList.remove('slide-right');
    } else if (pageIndex === 2) {
        container.classList.add('slide-right');
        container.classList.remove('slide-left');
    }
    
    // 更新指示器
    dots.forEach((dot, index) => {
        if (index === pageIndex) {
            dot.classList.add('active');
        } else {
            dot.classList.remove('active');
        }
    });
}

// 更新时间显示
function updateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    document.getElementById('current-time').textContent = timeString;
}

// 显示模块
function showModule(moduleName) {
    const swipeIndicator = document.querySelector('.swipe-indicator');
    if (swipeIndicator) swipeIndicator.style.display = 'none';

    // 隐藏所有模块
    const modules = document.querySelectorAll('.module');
    modules.forEach(module => {
        module.classList.remove('active');
    });
    
    // 隐藏主界面
    document.getElementById('main-container').style.display = 'none';
    
    // 显示指定模块
    const targetModule = document.getElementById(moduleName + '-module');
    if (targetModule) {
        targetModule.classList.add('active');
        currentModule = moduleName;
    }
}

// 返回主界面
function showMainInterface() {
    const swipeIndicator = document.querySelector('.swipe-indicator');
    if (swipeIndicator) swipeIndicator.style.display = 'flex';

    // 隐藏所有模块
    const modules = document.querySelectorAll('.module');
    modules.forEach(module => {
        module.classList.remove('active');
    });
    
    // 显示主界面
    document.getElementById('main-container').style.display = 'flex';
    currentModule = 'main';
}

// 快捷操作
function quickAction(action) {
    console.log('快捷操作:', action);
    
    switch(action) {
        case 'phone':
            alert('启动电话功能');
            break;
        case 'message':
            alert('打开消息应用');
            break;
        case 'camera':
            alert('启动环视摄像头');
            break;
        case 'weather':
            alert('显示天气信息');
            break;
        case 'calendar':
            alert('打开日程管理');
            break;
        case 'emergency':
            alert('紧急求助已激活');
            break;
    }
}

// 设置驾驶模式
function setDrivingMode(mode) {
    const buttons = document.querySelectorAll('.mode-selector .mode-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    
    const activeBtn = document.querySelector(`[onclick="setDrivingMode('${mode}')"]`);
    if (activeBtn) activeBtn.classList.add('active');
    
    console.log('驾驶模式切换为:', mode);
}

// 初始化疲劳检测
function initFatigueDetection() {
    updateFatigueDisplay();
    // 模拟疲劳度变化
    setInterval(() => {
        fatigueLevel += Math.random() * 2 - 1; // 随机增减
        fatigueLevel = Math.max(0, Math.min(100, fatigueLevel));
        updateFatigueDisplay();
    }, 3000);
}

// 更新疲劳检测显示
function updateFatigueDisplay() {
    const fatigueBar = document.getElementById('fatigue-bar');
    const fatigueLevelText = document.getElementById('fatigue-level');
    const fatigueStatusText = document.getElementById('fatigue-status-text');
    const fatigueIcon = document.getElementById('fatigue-icon');
    const fatigueIndicator = document.getElementById('fatigue-indicator');
    
    // 更新进度条
    fatigueBar.style.width = fatigueLevel + '%';
    
    // 更新文本
    fatigueLevelText.textContent = `疲劳度: ${Math.round(fatigueLevel)}%`;
    
    // 根据疲劳度更新状态
    if (fatigueLevel < 30) {
        fatigueStatusText.textContent = '状态正常';
        fatigueIcon.className = 'fas fa-eye';
        fatigueIndicator.classList.remove('active');
    } else if (fatigueLevel < 60) {
        fatigueStatusText.textContent = '轻度疲劳';
        fatigueIcon.className = 'fas fa-eye-slash';
        fatigueIndicator.classList.add('active');
    } else {
        fatigueStatusText.textContent = '严重疲劳';
        fatigueIcon.className = 'fas fa-exclamation-triangle';
        fatigueIndicator.classList.add('active');
        // 发出警告
        if (fatigueLevel > 80) {
            alert('警告：检测到严重疲劳，建议立即休息！');
        }
    }
}

// 切换个性化设置
function togglePersonalization(setting) {
    personalizationSettings[setting] = !personalizationSettings[setting];
    updatePersonalizationDisplay();
    
    // 应用设置
    switch(setting) {
        case 'auto':
            console.log('自动模式:', personalizationSettings.auto ? '开启' : '关闭');
            break;
        case 'night':
            console.log('夜间模式:', personalizationSettings.night ? '开启' : '关闭');
            if (personalizationSettings.night) {
                document.body.style.filter = 'brightness(0.8)';
            } else {
                document.body.style.filter = 'none';
            }
            break;
        case 'eco':
            console.log('节能模式:', personalizationSettings.eco ? '开启' : '关闭');
            break;
    }
}

// 更新个性化设置显示
function updatePersonalizationDisplay() {
    Object.keys(personalizationSettings).forEach(setting => {
        const toggle = document.querySelector(`[onclick="togglePersonalization('${setting}')"]`);
        if (personalizationSettings[setting]) {
            toggle.classList.add('active');
        } else {
            toggle.classList.remove('active');
        }
    });
}

// 语音控制切换
function updateVoiceStatus(text, showStopButton) {
    const voiceStatus = document.getElementById('voice-status');
    const voiceStatusText = document.getElementById('voice-status-text');
    const voiceBtn = document.getElementById('voice-btn');
    const stopBtn = document.getElementById('stop-recording-btn');

    if (text) {
        voiceStatus.classList.add('active');
        voiceBtn.classList.add('hidden'); // 隐藏主按钮
        voiceStatusText.textContent = text;
    } else {
        voiceStatus.classList.remove('active');
        voiceBtn.classList.remove('hidden'); // 显示主按钮
    }

    if (showStopButton) {
        stopBtn.classList.add('visible');
    } else {
        stopBtn.classList.remove('visible');
    }
}

async function startRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') return;
    
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        
        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = uploadAudio;
        
        audioChunks = [];
        mediaRecorder.start();
        voiceListening = true;
        updateVoiceStatus('正在聆听...', true);
    } catch (err) {
        console.error("无法获取麦克风:", err);
        updateVoiceStatus('无法访问麦克风', false);
        setTimeout(() => updateVoiceStatus(null, false), 2000);
    }
}

function stopRecording() {
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        return;
    }
    mediaRecorder.stop();
    // 停止所有媒体流轨道，这会关闭麦克风并移除浏览器标签上的红点
    if (mediaRecorder.stream) {
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
    voiceListening = false;
    updateVoiceStatus('正在识别...', false);
}

async function uploadAudio() {
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append('audio_data', audioBlob);

    updateVoiceStatus('正在处理...', false);

    try {
        const response = await fetch('/api/voice/recognize', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`服务器错误: ${response.statusText}`);
        }

        const result = await response.json();

        if (result.status === 'success') {
            updateVoiceStatus('操作成功', false);
            if (result.ac_status) {
                updateACStatusDisplay(result.ac_status);
            }
        } else {
            throw new Error(result.error || '未知错误');
        }

    } catch (error) {
        console.error('语音处理失败:', error);
        updateVoiceStatus('操作失败', false);
    } finally {
        setTimeout(() => {
            if (!voiceListening) {
                updateVoiceStatus(null, false);
            }
        }, 2000);
    }
}

// 加载车辆状态
async function loadVehicleStatus() {
    try {
        const response = await fetch('/api/vehicle/status');
        const data = await response.json();
        updateVehicleStatusDisplay(data);
    } catch (error) {
        console.error('加载车辆状态失败:', error);
    }
}

// 更新车辆状态显示
function updateVehicleStatusDisplay(status) {
    document.getElementById('vehicle-speed').textContent = status.speed + ' km/h';
    document.getElementById('vehicle-fuel').textContent = status.fuel + '%';
    document.getElementById('vehicle-temp').textContent = status.temperature + '°C';
    document.getElementById('vehicle-battery').textContent = status.battery + '%';
    document.getElementById('vehicle-tire').textContent = status.tire_pressure.join('/') + ' PSI';
    document.getElementById('vehicle-odometer').textContent = status.odometer.toLocaleString() + ' km';
}

// 加载空调状态
async function loadACStatus() {
    try {
        const response = await fetch('/api/ac/status');
        const data = await response.json();
        updateACStatusDisplay(data);
    } catch (error) {
        console.error('加载空调状态失败:', error);
    }
}

// 更新空调状态显示
function updateACStatusDisplay(status) {
    document.getElementById('ac-temperature').textContent = status.temperature + '°C';
    document.getElementById('ac-fan-speed').textContent = status.fan_speed;
    
    // 更新模式按钮状态
    const modeButtons = document.querySelectorAll('.mode-btn');
    modeButtons.forEach(btn => btn.classList.remove('active'));
    const activeModeBtn = document.querySelector(`[onclick="setACMode('${status.mode}')"]`);
    if (activeModeBtn) activeModeBtn.classList.add('active');
    
    // 更新功能按钮状态
    const defrostBtn = document.querySelector('[onclick="toggleDefrost()"]');
    const recirculationBtn = document.querySelector('[onclick="toggleRecirculation()"]');
    
    if (status.defrost) {
        defrostBtn.classList.add('active');
    } else {
        defrostBtn.classList.remove('active');
    }
    
    if (status.recirculation) {
        recirculationBtn.classList.add('active');
    } else {
        recirculationBtn.classList.remove('active');
    }
}

// 调整温度
async function adjustTemperature(delta) {
    const currentTemp = parseInt(document.getElementById('ac-temperature').textContent);
    const newTemp = Math.max(16, Math.min(30, currentTemp + delta));
    
    try {
        const response = await fetch('/api/ac/status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ temperature: newTemp })
        });
        const data = await response.json();
        updateACStatusDisplay(data.data);
    } catch (error) {
        console.error('调整温度失败:', error);
    }
}

// 调整风速
async function adjustFanSpeed(delta) {
    const currentSpeed = parseInt(document.getElementById('ac-fan-speed').textContent);
    const newSpeed = Math.max(1, Math.min(5, currentSpeed + delta));
    
    try {
        const response = await fetch('/api/ac/status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ fan_speed: newSpeed })
        });
        const data = await response.json();
        updateACStatusDisplay(data.data);
    } catch (error) {
        console.error('调整风速失败:', error);
    }
}

// 设置空调模式
async function setACMode(mode) {
    try {
        const response = await fetch('/api/ac/status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ mode: mode })
        });
        const data = await response.json();
        updateACStatusDisplay(data.data);
    } catch (error) {
        console.error('设置空调模式失败:', error);
    }
}

// 切换除霜功能
async function toggleDefrost() {
    const defrostBtn = document.querySelector('[onclick="toggleDefrost()"]');
    const currentState = defrostBtn.classList.contains('active');
    
    try {
        const response = await fetch('/api/ac/status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ defrost: !currentState })
        });
        const data = await response.json();
        updateACStatusDisplay(data.data);
    } catch (error) {
        console.error('切换除霜功能失败:', error);
    }
}

// 切换内循环功能
async function toggleRecirculation() {
    const recirculationBtn = document.querySelector('[onclick="toggleRecirculation()"]');
    const currentState = recirculationBtn.classList.contains('active');
    
    try {
        const response = await fetch('/api/ac/status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ recirculation: !currentState })
        });
        const data = await response.json();
        updateACStatusDisplay(data.data);
    } catch (error) {
        console.error('切换内循环功能失败:', error);
    }
}

// 加载多媒体状态
async function loadMediaStatus() {
    try {
        const response = await fetch('/api/media/status');
        const data = await response.json();
        updateMediaStatusDisplay(data);
    } catch (error) {
        console.error('加载多媒体状态失败:', error);
    }
}

// 更新多媒体状态显示
function updateMediaStatusDisplay(status) {
    document.getElementById('current-track').textContent = status.current_track;
    document.getElementById('current-artist').textContent = status.artist;
    document.getElementById('volume-slider').value = status.volume;
    
    const playBtn = document.getElementById('play-btn');
    if (status.playing) {
        playBtn.innerHTML = '<i class="fas fa-pause"></i>';
    } else {
        playBtn.innerHTML = '<i class="fas fa-play"></i>';
    }
    
    // 更新音源按钮状态
    const sourceButtons = document.querySelectorAll('.source-btn');
    sourceButtons.forEach(btn => btn.classList.remove('active'));
    const activeSourceBtn = document.querySelector(`[onclick="changeSource('${status.source}')"]`);
    if (activeSourceBtn) activeSourceBtn.classList.add('active');
}

// 切换播放/暂停
async function togglePlay() {
    const playBtn = document.getElementById('play-btn');
    const isPlaying = playBtn.innerHTML.includes('pause');
    
    try {
        const response = await fetch('/api/media/status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ playing: !isPlaying })
        });
        const data = await response.json();
        updateMediaStatusDisplay(data.data);
    } catch (error) {
        console.error('切换播放状态失败:', error);
    }
}

// 上一首
async function previousTrack() {
    console.log('播放上一首');
}

// 下一首
async function nextTrack() {
    console.log('播放下一首');
}

// 调整音量
async function adjustVolume(volume) {
    try {
        const response = await fetch('/api/media/status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ volume: parseInt(volume) })
        });
        const data = await response.json();
        updateMediaStatusDisplay(data.data);
    } catch (error) {
        console.error('调整音量失败:', error);
    }
}

// 切换音源
async function changeSource(source) {
    try {
        const response = await fetch('/api/media/status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ source: source })
        });
        const data = await response.json();
        updateMediaStatusDisplay(data.data);
    } catch (error) {
        console.error('切换音源失败:', error);
    }
}

// 加载导航状态
async function loadNavigationStatus() {
    try {
        const response = await fetch('/api/navigation/status');
        const data = await response.json();
        updateNavigationStatusDisplay(data);
    } catch (error) {
        console.error('加载导航状态失败:', error);
    }
}

// 更新导航状态显示
function updateNavigationStatusDisplay(status) {
    document.getElementById('nav-destination').textContent = status.destination;
    document.getElementById('nav-eta').textContent = status.eta;
    document.getElementById('nav-distance').textContent = status.distance;
}

// 设置目的地
async function setDestination() {
    const destination = document.getElementById('destination-input').value;
    if (!destination.trim()) {
        alert('请输入目的地');
        return;
    }
    
    try {
        const response = await fetch('/api/navigation/status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                destination: destination,
                eta: '25分钟',
                distance: '8.5公里'
            })
        });
        const data = await response.json();
        updateNavigationStatusDisplay(data.data);
        document.getElementById('destination-input').value = '';
    } catch (error) {
        console.error('设置目的地失败:', error);
    }
}

// 加载自动驾驶状态
async function loadAutopilotStatus() {
    try {
        const response = await fetch('/api/autopilot/status');
        const data = await response.json();
        updateAutopilotStatusDisplay(data);
    } catch (error) {
        console.error('加载自动驾驶状态失败:', error);
    }
}

// 更新自动驾驶状态显示
function updateAutopilotStatusDisplay(status) {
    const autopilotIndicator = document.getElementById('autopilot-indicator');
    if (status.enabled) {
        autopilotIndicator.classList.add('active');
        autopilotEnabled = true;
    } else {
        autopilotIndicator.classList.remove('active');
        autopilotEnabled = false;
    }
}

// 加载语音状态
async function loadVoiceStatus() {
    try {
        const response = await fetch('/api/voice/status');
        const data = await response.json();
        updateVoiceStatusDisplay(data);
    } catch (error) {
        console.error('加载语音状态失败:', error);
    }
}

// 更新语音状态显示
function updateVoiceStatusDisplay(status) {
    const voiceIndicator = document.getElementById('voice-indicator');
    if (status.listening) {
        voiceIndicator.classList.add('active');
        voiceListening = true;
    } else {
        voiceIndicator.classList.remove('active');
        voiceListening = false;
    }
}

// 模拟语音命令处理
function processVoiceCommand(command) {
    console.log('处理语音命令:', command);
    
    // 简单的语音命令识别
    if (command.includes('空调') || command.includes('温度')) {
        if (command.includes('调高') || command.includes('升高')) {
            adjustTemperature(1);
        } else if (command.includes('调低') || command.includes('降低')) {
            adjustTemperature(-1);
        }
    } else if (command.includes('音乐') || command.includes('播放')) {
        if (command.includes('播放') || command.includes('开始')) {
            togglePlay();
        } else if (command.includes('暂停') || command.includes('停止')) {
            togglePlay();
        }
    } else if (command.includes('导航')) {
        showModule('navigation');
    } else if (command.includes('自动驾驶')) {
        if (command.includes('开启') || command.includes('启动')) {
            enableAutopilot();
        } else if (command.includes('关闭') || command.includes('停止')) {
            disableAutopilot();
        }
    }
}

// 启用自动驾驶
async function enableAutopilot() {
    try {
        const response = await fetch('/api/autopilot/status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                enabled: true,
                status: '运行中'
            })
        });
        const data = await response.json();
        updateAutopilotStatusDisplay(data.data);
    } catch (error) {
        console.error('启用自动驾驶失败:', error);
    }
}

// 禁用自动驾驶
async function disableAutopilot() {
    try {
        const response = await fetch('/api/autopilot/status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                enabled: false,
                status: '待机'
            })
        });
        const data = await response.json();
        updateAutopilotStatusDisplay(data.data);
    } catch (error) {
        console.error('禁用自动驾驶失败:', error);
    }
}

// 按键控制
document.addEventListener('keyup', (event) => {
    if (event.key === 'ArrowRight') {
        goToPage((currentPage + 1) % 3);
    } else if (event.key === 'ArrowLeft') {
        goToPage((currentPage - 1 + 3) % 3);
    }
});

// 定期更新数据
setInterval(() => {
    if (currentModule === 'vehicle') {
        loadVehicleStatus();
    } else if (currentModule === 'ac') {
        loadACStatus();
    } else if (currentModule === 'media') {
        loadMediaStatus();
    } else if (currentModule === 'navigation') {
        loadNavigationStatus();
    }
    
    loadAutopilotStatus();
    loadVoiceStatus();
}, 5000); // 每5秒更新一次 