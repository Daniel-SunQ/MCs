from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import openai
import re
import tempfile
import requests
import soundfile as sf
from vosk import Model, KaldiRecognizer
import zipfile
import shutil
from openai import OpenAI
import librosa

# 加载环境变量
load_dotenv()

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("启动错误: DEEPSEEK_API_KEY 未在 .env 文件中设置或加载失败。\n请确认项目根目录下存在 .env 文件，且其中包含 DEEPSEEK_API_KEY='sk-...'")

# 设置OpenAI API密钥
openai.api_key = os.getenv("OPENAI_API_KEY")

deepseek_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

app = Flask(__name__)
CORS(app)

# Vosk模型路径和URL (使用1.3GB大模型)
VOSK_MODEL_PATH = "vosk-model-small-cn-0.22"
VOSK_MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-large-cn-0.22-lgraph.zip"
VOSK_MODEL_ZIP_NAME = "vosk-model-large-cn.zip"
VOSK_MODEL_EXTRACTED_FOLDER = "vosk-model-large-cn-0.22-lgraph"

# 检查并下载模型
def setup_vosk_model():
    if not os.path.exists(VOSK_MODEL_PATH):
        print("Vosk大模型不存在，开始下载 (约1.3GB)...")
        r = requests.get(VOSK_MODEL_URL, stream=True)
        with open(VOSK_MODEL_ZIP_NAME, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print("下载完成，开始解压...")
        with zipfile.ZipFile(VOSK_MODEL_ZIP_NAME, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        print(f"解压完成，重命名文件夹 {VOSK_MODEL_EXTRACTED_FOLDER} -> {VOSK_MODEL_PATH}")
        shutil.move(VOSK_MODEL_EXTRACTED_FOLDER, VOSK_MODEL_PATH)
        os.remove(VOSK_MODEL_ZIP_NAME)
        print("模型准备就绪。")

setup_vosk_model()
vosk_model = Model(VOSK_MODEL_PATH)

# 模拟车辆状态数据
vehicle_status = {
    "speed": 0,
    "fuel": 85,
    "temperature": 22,
    "engine_status": "running",
    "battery": 90,
    "tire_pressure": [32, 31, 33, 32],
    "odometer": 12500,
}

# 模拟空调状态
ac_status = {
    "temperature": 22,
    "fan_speed": 2,
    "mode": "auto",
    "defrost": False,
    "recirculation": False,
    "status": "listening"
}

# 模拟多媒体状态
media_status = {
    "playing": False,
    "current_track": "未知歌曲",
    "artist": "未知艺术家",
    "volume": 50,
    "source": "radio",
}

# 模拟导航状态
navigation_status = {
    "destination": "未设置目的地",
    "eta": "未知",
    "distance": "未知",
    "route": [],
}

# 模拟自动驾驶状态
autopilot_status = {"enabled": False, "level": "L2", "status": "待机"}

# 模拟语音控制状态
voice_status = {"listening": False, "last_command": "无"}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/vehicle/status")
def get_vehicle_status():
    return jsonify(vehicle_status)


@app.route("/api/vehicle/status", methods=["POST"])
def update_vehicle_status():
    global vehicle_status
    data = request.json
    vehicle_status.update(data)
    return jsonify({"status": "success", "data": vehicle_status})


@app.route("/api/ac/status")
def get_ac_status():
    return jsonify(ac_status)


@app.route("/api/ac/status", methods=["POST"])
def update_ac_status():
    global ac_status
    data = request.json
    ac_status.update(data)
    return jsonify({"status": "success", "data": ac_status})


@app.route("/api/media/status")
def get_media_status():
    return jsonify(media_status)


@app.route("/api/media/status", methods=["POST"])
def update_media_status():
    global media_status
    data = request.json
    media_status.update(data)
    return jsonify({"status": "success", "data": media_status})


@app.route("/api/navigation/status")
def get_navigation_status():
    return jsonify(navigation_status)


@app.route("/api/navigation/status", methods=["POST"])
def update_navigation_status():
    global navigation_status
    data = request.json
    navigation_status.update(data)
    return jsonify({"status": "success", "data": navigation_status})


@app.route("/api/autopilot/status")
def get_autopilot_status():
    return jsonify(autopilot_status)


@app.route("/api/autopilot/status", methods=["POST"])
def update_autopilot_status():
    global autopilot_status
    data = request.json
    autopilot_status.update(data)
    return jsonify({"status": "success", "data": autopilot_status})


@app.route("/api/voice/status")
def get_voice_status():
    return jsonify(voice_status)


@app.route("/api/voice/command", methods=["POST"])
def voice_command():
    global voice_status
    data = request.json
    command = data.get("command", "")
    voice_status["last_command"] = command
    voice_status["listening"] = False

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


@app.route("/api/voice/listen", methods=["POST"])
def start_voice_listening():
    global voice_status
    voice_status["listening"] = True
    return jsonify({"status": "success", "message": "开始语音监听"})


@app.route("/api/voice/stop", methods=["POST"])
def stop_voice_listening():
    global voice_status
    voice_status["listening"] = False
    return jsonify({"status": "success", "message": "停止语音监听"})


@app.route('/api/voice/recognize', methods=['POST'])
def recognize_voice():
    if 'audio_data' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files['audio_data']
    print("\n[后端日志] 音频文件已成功接收，准备进行本地识别...")
    
    in_tmp, out_tmp = None, None
    try:
        # 1. 将上传的音频流保存到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as in_tmp:
            audio_file.save(in_tmp.name)

        # 2. 使用librosa从临时文件路径加载并重采样
        y, sr = librosa.load(in_tmp.name, sr=16000)

        # 3. 将重采样后的音频保存到另一个临时WAV文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as out_tmp:
            sf.write(out_tmp.name, y, 16000)

        # 4. 本地Vosk语音识别
        rec = KaldiRecognizer(vosk_model, 16000)
        rec.SetWords(True)
        
        with open(out_tmp.name, "rb") as wav_f:
            while True:
                data = wav_f.read(4000)
                if len(data) == 0:
                    break
                rec.AcceptWaveform(data)
        
        result = json.loads(rec.FinalResult())
        user_command = result.get('text', '').replace(" ", "")
        print(f"[后端日志] Vosk识别结果: '{user_command}'")

    except Exception as e:
        import traceback
        print("!!!!!! [后端错误] An exception occurred: !!!!!!")
        traceback.print_exc()
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return jsonify({"error": f"Vosk或Librosa处理失败: {e}"}), 500
    finally:
        if in_tmp and os.path.exists(in_tmp.name):
            os.remove(in_tmp.name)
        if out_tmp and os.path.exists(out_tmp.name):
            os.remove(out_tmp.name)

    if not user_command:
        return jsonify({"status": "success", "command": {"module": "error", "action": "no_speech_detected"}})

    # 2. 使用DeepSeek Function Calling解析意图
    try:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "control_air_conditioner",
                    "description": "控制车载空调系统，可以设置温度、风速和模式。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "description": "要执行的具体操作。",
                                "enum": ["set_temperature", "adjust_temperature", "set_fan_speed", "adjust_fan_speed", "set_mode"]
                            },
                            "value": {
                                "type": "string",
                                "description": "操作所需的值。例如: 温度'25', 风速'3', 模式'cool', 调整'increase'/'decrease'。"
                            }
                        },
                        "required": ["action", "value"]
                    }
                }
            }
        ]

        chat_completion = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个智能车载助手，请根据用户的指令调用合适的工具函数。"},
                {"role": "user", "content": user_command},
            ],
            tools=tools,
            tool_choice="auto",
            max_tokens=150,
            temperature=0,
        )
        
        response_message = chat_completion.choices[0].message
        tool_calls = response_message.tool_calls
        command = None

        if tool_calls:
            tool_call = tool_calls[0]
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            if function_name == "control_air_conditioner":
                command = {
                    "module": "ac",
                    "action": function_args.get("action"),
                    "value": function_args.get("value")
                }
                
                # 3. 执行指令
                action = command.get('action')
                value = command.get('value')
                
                # 尝试将value转为整数，失败则保持为字符串
                try:
                    numeric_value = int(value)
                except (ValueError, TypeError):
                    numeric_value = value

                if action == 'set_temperature':
                    ac_status['temperature'] = numeric_value
                elif action == 'adjust_temperature':
                    ac_status['temperature'] += 1 if value == 'increase' else -1
                elif action == 'set_fan_speed':
                    ac_status['fan_speed'] = numeric_value
                elif action == 'adjust_fan_speed':
                    ac_status['fan_speed'] += 1 if value == 'increase' else -1
                elif action == 'set_mode':
                    ac_status['mode'] = value
        
        if command is None:
             command = {"module": "error", "action": "unknown_command"}

        return jsonify({"status": "success", "command": command, "ac_status": ac_status, "text": user_command})

    except Exception as e:
        print(f"DeepSeek处理失败或指令执行错误: {e}")
        return jsonify({"error": str(e), "text": user_command}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
