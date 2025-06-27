from flask import Flask, render_template, jsonify, request, Response, stream_with_context   
from flask_cors import CORS
import json
import os
from datetime import datetime
import httpx
from dotenv import load_dotenv
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
import hashlib # 用于生成唯一文件名
import cv2
import torch
from transformers import AutoImageProcessor, AutoModelForDepthEstimation
from PIL import Image
import numpy as np
import time
import math
import types
import wave
import tempfile
from openai import OpenAI
from vosk import Model, KaldiRecognizer
import json as pyjson
import subprocess
import sys
import edge_tts
import asyncio
from playsound import playsound
from ollama import ChatResponse, chat
import requests
from flask_socketio import SocketIO, emit
import threading
import queue
import pvporcupine
from pvrecorder import PvRecorder
import struct
from datetime import datetime
from multiprocessing import Process
import sounddevice as sd
from scipy.io.wavfile import write



# 启用 MPS 后备方案以处理不受支持的操作 (现在可以移除了，因为我们修复了根本原因)
# os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'

load_dotenv()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

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

# ======================================================================= */
# =========================== DEPTH ANYTHING V2 ========================== */
# ======================================================================= */


from threading import Thread

def run_local_collision_detection():
    from transformers import pipeline
    import cv2
    from PIL import Image
    import numpy as np
    try:
        pipe = pipeline(task="depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf")
    except Exception as e:
        print(f"Error: {e}, model problem!!!")
        return
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open video device.")
        return
    width, height = 320, 240
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        try:
            result = pipe(image)
            depth = result["depth"]
            depth_np = np.array(depth)
            depth_norm = (depth_np - depth_np.min()) / (depth_np.max() - depth_np.min()) * 255
            depth_uint8 = depth_norm.astype(np.uint8)
            depth_color = cv2.applyColorMap(depth_uint8, cv2.COLORMAP_INFERNO)
        except Exception as e:
            print(f"Error: {e}, inference problem!!!")
            continue
        cv2.imshow("Camera", frame)
        cv2.imshow("Depth", depth_color)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

@app.route('/api/start_collision_detection', methods=['POST'])
def start_collision_detection():
    p = Process(target=run_local_collision_detection)
    p.daemon = True
    p.start()
    return jsonify({"status": "started"})

# ======================================================================= */
# ======================================================================= */
def scan_music_directory():
    """扫描音乐目录，提取元数据，构建播放列表"""
    playlist = []
    music_dir = "static/music"
    default_cover = "/static/images/car_menu.jpg"

    supported_formats = {
        '.mp3': MP3, '.wav': WAVE, '.ogg': OggVorbis,
        '.flac': FLAC, '.m4a': MP4,
    }
    
    if not os.path.exists(music_dir): os.makedirs(music_dir)

    song_id = 0
    for filename in sorted(os.listdir(music_dir)):
        filepath = os.path.join(music_dir, filename)
        _, ext = os.path.splitext(filename)

        if ext.lower() in supported_formats:
            try:
                audio = supported_formats[ext.lower()](filepath)
                
                title = audio.get('TIT2', [os.path.splitext(filename)[0]])[0]
                artist = audio.get('TPE1', ['未知艺术家'])[0]
                album = audio.get('TALB', ['未知专辑'])[0]
                
                lrc_path = os.path.splitext(filepath)[0] + '.lrc'
                has_lyrics = os.path.exists(lrc_path)
                
                playlist.append({
                    "id": song_id,
                    "title": title,
                    "artist": artist,
                    "album": album,
                    "duration": int(audio.info.length),
                    "file_path": "/" + filepath.replace("\\", "/"),
                    "cover": default_cover, 
                    "has_lyrics": has_lyrics
                })
                song_id += 1
            except Exception as e:
                print(f"处理文件失败 {filepath}: {e}")
    
    return playlist

# 音乐播放器状态 (动态初始化)
music_player = {
    "current_song": 0,
    "is_playing": False,
    "volume": 0.7,
    "shuffle": False,
    "repeat": "none",  # none, one, all
    "playlist": scan_music_directory()
}

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


@app.route('/api/config')
def get_config():
    """安全地向前端提供API配置"""
    return jsonify({
        'amap_key': os.getenv('AMAP_API_KEY'),
        'amap_security_secret': os.getenv('AMAP_SECURITY_SECRET')
    })

@app.route('/api/start_fatigue_detection', methods=['POST'])
## drowsy detection
def start_drowsy_detection():
    # print("start fatigue detection")
    # return jsonify({"status": "started"})
    try:
        # 构造脚本路径
        script_path = os.path.join(os.path.dirname(__file__), 'inference.py')

        # 使用 python 启动 inference.py 子进程（可切换为 'python3'）
        subprocess.Popen([sys.executable, script_path])

        return jsonify({"status": "started"})
    except Exception as e:
        print("open drowsy detection missed sth wrong：", e)
        return jsonify({"status": "error", "message": str(e)}), 500



#weather interface for quick view
@app.route('/api/weather')
def get_weather():
    city_name = request.args.get('city')
    api_key = os.getenv('QWEATHER_API_KEY')

    if not city_name or not api_key:
        return jsonify({"error": "缺少城市名称或API密钥"}), 400

    with httpx.Client() as client:
        try:
            # 1. 获取城市ID
            geo_url = f"https://geoapi.qweather.com/v2/city/lookup?location={city_name}&key={api_key}"
            geo_response = client.get(geo_url)
            geo_response.raise_for_status()
            geo_data = geo_response.json()

            if geo_data.get("code") != "200" or not geo_data.get("location"):
                return jsonify({"error": "找不到该城市"}), 404
            
            location_id = geo_data["location"][0]["id"]

            # 2. 获取实时天气
            weather_url = f"https://devapi.qweather.com/v7/weather/now?location={location_id}&key={api_key}"
            weather_response = client.get(weather_url)
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            if weather_data.get("code") != "200":
                 return jsonify({"error": "获取天气信息失败", "details": weather_data}), 500

            return jsonify(weather_data.get("now", {}))

        except httpx.HTTPStatusError as e:
            return jsonify({"error": f"API请求失败: {e.response.status_code}", "details": str(e)}), 500
        except Exception as e:
            return jsonify({"error": "服务器内部错误", "details": str(e)}), 500

# ======================================================================= */
# =========================== MUSIC PLAYER APIs ========================== */
# ======================================================================= */

@app.route('/api/music/playlist')
def get_music_playlist():
    """获取播放列表"""
    return jsonify({
        "playlist": music_player["playlist"],
        "current_song": music_player["current_song"],
        "is_playing": music_player["is_playing"],
        "volume": music_player["volume"],
        "shuffle": music_player["shuffle"],
        "repeat": music_player["repeat"]
    })

@app.route('/api/music/play', methods=['POST'])
def play_music():
    """播放音乐"""
    global music_player
    data = request.json
    song_id = data.get('song_id', music_player["current_song"])
    
    # 如果指定了歌曲ID，更新当前歌曲
    if song_id != music_player["current_song"]:
        music_player["current_song"] = song_id
    
    music_player["is_playing"] = True
    
    current_song = music_player["playlist"][music_player["current_song"]]
    return jsonify({
        "status": "success",
        "message": f"正在播放: {current_song['title']}",
        "current_song": current_song,
        "is_playing": True
    })

@app.route('/api/music/pause', methods=['POST'])
def pause_music():
    """暂停音乐"""
    global music_player
    music_player["is_playing"] = False
    return jsonify({
        "status": "success",
        "message": "音乐已暂停",
        "is_playing": False
    })

@app.route('/api/music/next', methods=['POST'])
def next_song():
    """下一首"""
    global music_player
    if music_player["shuffle"]:
        # 随机播放
        import random
        music_player["current_song"] = random.randint(0, len(music_player["playlist"]) - 1)
    else:
        # 顺序播放
        music_player["current_song"] = (music_player["current_song"] + 1) % len(music_player["playlist"])
    
    current_song = music_player["playlist"][music_player["current_song"]]
    return jsonify({
        "status": "success",
        "message": f"切换到: {current_song['title']}",
        "current_song": current_song,
        "current_song_index": music_player["current_song"]
    })

@app.route('/api/music/prev', methods=['POST'])
def prev_song():
    """上一首"""
    global music_player
    if music_player["shuffle"]:
        # 随机播放
        import random
        music_player["current_song"] = random.randint(0, len(music_player["playlist"]) - 1)
    else:
        # 顺序播放
        music_player["current_song"] = (music_player["current_song"] - 1) % len(music_player["playlist"])
    
    current_song = music_player["playlist"][music_player["current_song"]]
    return jsonify({
        "status": "success",
        "message": f"切换到: {current_song['title']}",
        "current_song": current_song,
        "current_song_index": music_player["current_song"]
    })

@app.route('/api/music/volume', methods=['POST'])
def set_volume():
    """设置音量"""
    global music_player
    data = request.json
    volume = data.get('volume', 0.7)
    music_player["volume"] = max(0.0, min(1.0, volume))
    
    return jsonify({
        "status": "success",
        "volume": music_player["volume"]
    })

@app.route('/api/music/shuffle', methods=['POST'])
def toggle_shuffle():
    """切换随机播放"""
    global music_player
    music_player["shuffle"] = not music_player["shuffle"]
    
    return jsonify({
        "status": "success",
        "shuffle": music_player["shuffle"],
        "message": "随机播放已开启" if music_player["shuffle"] else "随机播放已关闭"
    })

@app.route('/api/music/repeat', methods=['POST'])
def toggle_repeat():
    """切换循环模式"""
    global music_player
    repeat_modes = ["none", "one", "all"]
    current_index = repeat_modes.index(music_player["repeat"])
    music_player["repeat"] = repeat_modes[(current_index + 1) % len(repeat_modes)]
    
    return jsonify({
        "status": "success",
        "repeat": music_player["repeat"],
        "message": f"循环模式: {music_player['repeat']}"
    })

@app.route('/api/music/status')
def get_music_status():
    """获取音乐播放状态"""
    current_song = music_player["playlist"][music_player["current_song"]]
    return jsonify({
        "current_song": current_song,
        "current_song_index": music_player["current_song"],
        "is_playing": music_player["is_playing"],
        "volume": music_player["volume"],
        "shuffle": music_player["shuffle"],
        "repeat": music_player["repeat"]
    })

@app.route('/api/music/lyrics/<int:song_id>')
def get_lyrics(song_id):
    """根据歌曲ID获取歌词"""
    if song_id < 0 or song_id >= len(music_player['playlist']):
        return jsonify({"error": "无效的歌曲ID"}), 404

    song = music_player['playlist'][song_id]
    
    if not song.get('has_lyrics'):
        return jsonify({"error": "该歌曲没有歌词"}), 404
    
    # 构建lrc文件路径 (移除开头的'/' )
    base_filepath = song['file_path'].lstrip('/')
    lrc_filepath = os.path.splitext(base_filepath)[0] + '.lrc'

    if not os.path.exists(lrc_filepath):
        return jsonify({"error": "歌词文件未找到"}), 404
        
    try:
        with open(lrc_filepath, 'r', encoding='utf-8') as f:
            lyrics = f.read()
        return jsonify({"lyrics": lyrics})
    except Exception as e:
        return jsonify({"error": f"读取歌词文件失败: {e}"}), 500
    
# ======================================================================= */
# =========================== VOICE COMMAND RECOGNITION ================== */
# ======================================================================= */

# 初始化vosk模型（只加载一次）
VOSK_MODEL_PATH = "vosk-model-small-cn-0.22" if os.path.exists("vosk-model-small-cn-0.22") else "vosk-model-cn-0.22"
vosk_model = None
if os.path.exists(VOSK_MODEL_PATH):
    vosk_model = Model(VOSK_MODEL_PATH)
else:
    print(f"[警告] 未找到Vosk模型文件夹: {VOSK_MODEL_PATH}")


#====================================================
#==============functions_for_call_tool===============

#===============weather_function===============
url_api_weather = 'https://devapi.qweather.com/v7/weather/'
url_api_geo = 'https://geoapi.qweather.com/v2/city/'
url_api_rain = 'https://devapi.qweather.com/v7/minutely/5m'
url_api_air = 'https://devapi.qweather.com/v7/air/now'

def get_location_id(location):
    try:
        url = f"{url_api_geo}lookup?location={location}&range=cn&key={os.getenv('QWEATHER_API_KEY')}"
        response = requests.get(url).json()
        return response['location'][0]['id']
    except Exception as e:
        print(f"Error: {e}, return default location id")
        #北京的location_id
        return "101010100"              
    # 默认返回第一个location的id
    

def get_now_weather(location):
    location_id = get_location_id(location)
    try:
        url = f"{url_api_weather}now?location={location_id}&key={os.getenv('QWEATHER_API_KEY')}"
        response = requests.get(url).json()
        data = {
            '温度': response['now']['temp'],
            '湿度': response['now']['humidity'],
            '风速': response['now']['windSpeed'],
            '风向': response['now']['windDir'],
            '天气': response['now']['text'],
            '体感温度': response['now']['feelsLike'],
            '气压': response['now']['pressure'],
            '能见度': response['now']['vis'],
        }
    except Exception as e:
        print(f"Error: {e}, return default now weather")
        data = {
            '温度': '20',
            '湿度': '50',
            '风速': '10',
        }
    return data

def get_forecast_weather_by_date(date, location):
    try:
        location_id = get_location_id(location)
        print(f"location: {location}")
        print(f"date: {date}")
        url = f"{url_api_weather}7d?location={location_id}&key={os.getenv('QWEATHER_API_KEY')}"
        print(f"url: {url}")
        reseponse = requests.get(url).json()['daily']
        info = reseponse
    except Exception as e:
        print(f"Error: {e}, return default forecastweather")
        return None
    data = [ 
        {
            '日期': i['fxDate'],
            '最高温度': i['tempMax'],
            '最低温度': i['tempMin'],
            '天气': i['textDay'],
            '白天风向': i['windDirDay'],
            '风速': i['windSpeedDay'],
            '湿度': i['humidity'],
            '紫外线强度': i['uvIndex'],
            '能见度': i['vis'],
        }
        for i in info if i['fxDate'] == date
        ]
    return data

#===============get_date=======================
def get_date():
    return datetime.now().strftime("%Y-%m-%d")

#===============other_functions=======================
##TODO: 添加其他函数，例如操控音乐，操控空调，或者操控导航等等
## when you add new function, you should add the function to the tools and avaliable_functions
## also, you should add the function to the tools_prompt

#===========================================================
#===============tools and avaliable_functions===============
tools_prompt = {
    "get_now_weather": "获取现在城市的天气，用户应该提供城市名",
    "get_forecast_weather_by_date": "如果用户问你某一个城市未来某一天的天气，你应该返回该天的天气，用户应该提供日期和城市",
    "get_date": "获取现在的时间"
}
tools = [
    {
        'type': 'function',
        'function': {
            'name': 'get_now_weather',
            'description': tools_prompt['get_now_weather'],
            'parameters': {
                'type': 'object',
                "properties":{
                    'location':{
                        'type': 'string',
                        'description': '城市名称，必须是中国的标准城市名(必须是中文)，例如："长沙"、"重庆"等，不要填写商铺、品牌或其他非地名',
                    }
                },
                'required': ['location'],
                'additionalProperties': False,
            },
        }

    },
    {
        'type': 'function',
        'function': {
            'name': 'get_forecast_weather_by_date',
            'description': tools_prompt['get_forecast_weather_by_date'],
            'parameters': {
                'type': 'object',
                'properties': {
                    'date': {
                        'type': 'string',
                        'description': '时间，格式为2025-MM-DD',
                        'default': datetime.now().strftime("%Y-%m-%d")
                    },
                    'location': {
                        'type': 'string',
                        'description': '必须是中国的标准城市名(必须是中文)，例如："长沙"、"重庆"等，不要填写商铺、品牌或其他非地名',
                        'default': '重庆'
                    }
                },
                'required': ['location'],
                'additionalProperties': False,
            },
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_date',
            'description': tools_prompt['get_date'],
            'parameters': {
                'type': 'object',
                'properties': {},
                'required': [],
                'additionalProperties': False,
            },
        }
    },
]

avaliable_functions = {
    "get_now_weather": get_now_weather,
    "get_forecast_weather_by_date": get_forecast_weather_by_date,
    "get_date": get_date,
}

#===============call_llama===============
def call_llama(messages, is_stream=False):
    response: ChatResponse = chat(
        'qwen3:1.7b',
        messages=messages,
        think=False,
        tools=tools,
        stream=is_stream,
    )
    return response

def call_llama_without_tool(messages, is_stream=False):
    response: ChatResponse = chat(
        'qwen3:1.7b',
        messages=messages,
        think=False,
        stream=is_stream,
    )
    return response

# 唤醒词检测函数
def detect_wake_word():
    """
    检测唤醒词。集成Porcupine唤醒词检测。
    返回True表示检测到唤醒词，否则返回False。
    """
    access_key = os.getenv('PORCUPINE_ACCESS_KEY')
    porcupine = pvporcupine.create(access_key=access_key, keywords=["hey siri"])
    recorder = PvRecorder(device_index=0, frame_length=512)
    recorder.start()
    try:
        while True:
            pcm = recorder.read()
            result = porcupine.process(pcm)
            if result >= 0:
                print('detected')
                break
    finally:
        try:
            recorder.stop()
        except Exception:
            pass
        try:
            recorder.delete()
        except Exception:
            pass
        try:
            porcupine.delete()
        except Exception:
            pass
    return True

def record_audio(duration=7, sample_rate=16000, channels=1):
    """
    使用sounddevice录音，返回临时wav文件路径。适配vosk识别。
    """
    print(f"[录音] 开始录音 {duration} 秒...")
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels, dtype='int16')
    sd.wait()
    print("[录音] 录音结束")
    temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    write(temp_wav.name, sample_rate, recording)
    return temp_wav.name

def recognize(wav_path):
    """
    用vosk对wav音频进行语音识别，返回识别到的文本。
    wav_path: 临时wav文件路径
    """
    rec = KaldiRecognizer(vosk_model, 16000)
    wf = wave.open(wav_path, "rb")
    transcript = ""
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            res = pyjson.loads(rec.Result())
            transcript += res.get("text", "")
    res = pyjson.loads(rec.FinalResult())
    transcript += res.get("text", "")
    wf.close()
    # 删除临时文件
    os.remove(wav_path)
    return transcript.strip()

def llm(user_text):
    """
    调用原有Function calling和大模型推理逻辑，返回AI回复字符串。
    user_text: 用户语音识别后的文本
    """
    messages = [{"role": "user", "content": user_text + ', 给我精简的回答'}]
    print(f"messages: {messages}")
    response = call_llama(messages)
    # 检查是否有tool_calls
    if response.message.tool_calls:
        for tool_call in response.message.tool_calls:
            if functoin_to_call := avaliable_functions.get(tool_call.function.name):
                result = functoin_to_call(**tool_call.function.arguments)
                messages.append(response.message)
                messages.append({"role": "tool", "name": tool_call.function.name, "content": str(result)})
        final_response = call_llama(messages)
        # ai_text = ""
        # for chunk in final_response:
        #     ai_text += chunk.message.content
        return final_response.message.content
    else:
        final_response = call_llama_without_tool(messages)
        # ai_text = ""
        # for chunk in final_response:
        #     ai_text += chunk.message.content
        return final_response.message.content

def tts_and_play(text, filename="static/voice/tts_output.mp3"):
    async def tts_task():
        print(f"text: {text}")
        communicate = edge_tts.Communicate(text=text, voice="zh-CN-XiaoxiaoNeural")
        await communicate.save(filename)
    asyncio.run(tts_task())

    audio = MP3(filename)
    duration = audio.info.length

    socketio.emit('voice_status', {'status': 'streaming', 'text': text, 'duration': duration})
    threading.Thread(target=playsound, args=(filename,), daemon=True).start()
    

# 语音主流程线程
voice_status_queue = queue.Queue()
def voice_loop():
    while True:
        # 1. 唤醒检测
        try:
            if detect_wake_word():
                socketio.emit('voice_status', {'status': 'wake'})
                # 2. 录音 返回temp_file_path
                try:
                    socketio.emit('voice_status', {'status': 'recording'})
                    audio = record_audio()  
                except Exception as e:
                    print(f"Error: {e}, audio record failed")
                    return None
                # 3. 识别
                try:
                    socketio.emit('voice_status', {'status': 'processing'})
                    text = recognize(audio) 
                except Exception as e:
                    print(f"Error: {e}, audio recognize failed")
                    return None
                # 4. LLM+TTS+本地播放
                try:
                    ai_text = llm(text) 
                except Exception as e:
                    print(f"Error: {e}, llm failed")
                    return None
                try:
                    tts_and_play(ai_text) 
                except Exception as e:
                    print(f"Error: {e}, tts failed")
                    break
                # 5. 推送AI回复
                socketio.emit('voice_status', {'status': 'result', 'text': ai_text})
        except Exception as e:
            print(f"Error: {e}, voice loop failed")
            break
        time.sleep(0.1)


@app.route('/user_center')
def user_center():
    return render_template('user_center.html')


if __name__ == "__main__":
    threading.Thread(target=voice_loop, daemon=True).start()
    socketio.run(app, debug=True, host="0.0.0.0", port=5001, use_reloader=False)
