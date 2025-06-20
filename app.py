from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 模拟车辆状态数据
vehicle_status = {
    "speed": 0,
    "fuel": 85,
    "temperature": 22,
    "engine_status": "running",
    "battery": 90,
    "tire_pressure": [32, 31, 33, 32],
    "odometer": 12500
}

# 模拟空调状态
ac_status = {
    "temperature": 22,
    "fan_speed": 2,
    "mode": "auto",
    "defrost": False,
    "recirculation": False
}

# 模拟多媒体状态
media_status = {
    "playing": False,
    "current_track": "未知歌曲",
    "artist": "未知艺术家",
    "volume": 50,
    "source": "radio"
}

# 模拟导航状态
navigation_status = {
    "destination": "未设置目的地",
    "eta": "未知",
    "distance": "未知",
    "route": []
}

# 模拟自动驾驶状态
autopilot_status = {
    "enabled": False,
    "level": "L2",
    "status": "待机"
}

# 模拟语音控制状态
voice_status = {
    "listening": False,
    "last_command": "无"
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/vehicle/status')
def get_vehicle_status():
    return jsonify(vehicle_status)

@app.route('/api/vehicle/status', methods=['POST'])
def update_vehicle_status():
    global vehicle_status
    data = request.json
    vehicle_status.update(data)
    return jsonify({"status": "success", "data": vehicle_status})

@app.route('/api/ac/status')
def get_ac_status():
    return jsonify(ac_status)

@app.route('/api/ac/status', methods=['POST'])
def update_ac_status():
    global ac_status
    data = request.json
    ac_status.update(data)
    return jsonify({"status": "success", "data": ac_status})

@app.route('/api/media/status')
def get_media_status():
    return jsonify(media_status)

@app.route('/api/media/status', methods=['POST'])
def update_media_status():
    global media_status
    data = request.json
    media_status.update(data)
    return jsonify({"status": "success", "data": media_status})

@app.route('/api/navigation/status')
def get_navigation_status():
    return jsonify(navigation_status)

@app.route('/api/navigation/status', methods=['POST'])
def update_navigation_status():
    global navigation_status
    data = request.json
    navigation_status.update(data)
    return jsonify({"status": "success", "data": navigation_status})

@app.route('/api/autopilot/status')
def get_autopilot_status():
    return jsonify(autopilot_status)

@app.route('/api/autopilot/status', methods=['POST'])
def update_autopilot_status():
    global autopilot_status
    data = request.json
    autopilot_status.update(data)
    return jsonify({"status": "success", "data": autopilot_status})

@app.route('/api/voice/status')
def get_voice_status():
    return jsonify(voice_status)

@app.route('/api/voice/command', methods=['POST'])
def voice_command():
    global voice_status
    data = request.json
    command = data.get('command', '')
    voice_status['last_command'] = command
    voice_status['listening'] = False
    
    # 简单的语音命令处理逻辑
    response = {"status": "success", "message": f"收到命令: {command}"}
    
    if "空调" in command:
        if "温度" in command:
            response["action"] = "ac_temperature"
        elif "风速" in command:
            response["action"] = "ac_fan"
    elif "音乐" in command or "播放" in command:
        response["action"] = "media_play"
    elif "导航" in command:
        response["action"] = "navigation"
    elif "自动驾驶" in command:
        response["action"] = "autopilot"
    
    return jsonify(response)

@app.route('/api/voice/listen', methods=['POST'])
def start_voice_listening():
    global voice_status
    voice_status['listening'] = True
    return jsonify({"status": "success", "message": "开始语音监听"})

@app.route('/api/voice/stop', methods=['POST'])
def stop_voice_listening():
    global voice_status
    voice_status['listening'] = False
    return jsonify({"status": "success", "message": "停止语音监听"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 