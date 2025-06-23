from flask import Flask, render_template, jsonify, request, Response
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

# 启用 MPS 后备方案以处理不受支持的操作 (现在可以移除了，因为我们修复了根本原因)
# os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'

load_dotenv()

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

# 全局变量来缓存模型和摄像头
camera = None
image_processor = None
model = None
device = None

# 猴子补丁函数，用于替换 transformers 库中不兼容 MPS 的函数
def new_interpolate_pos_encoding(self, embeddings: torch.Tensor, height: int, width: int) -> torch.Tensor:
    """
    此函数是 Dinov2 中原始 interpolate_pos_encoding 函数的猴子补丁版本。
    它将 `bicubic` 插值替换为 `bilinear`，以使其与 Apple Silicon 上的 PyTorch MPS 后端兼容，
    从而避免缓慢的 CPU 回退。
    """
    if self.position_embeddings is None:
        return None
        
    num_patches = embeddings.shape[1] - 1
    num_positions = self.position_embeddings.shape[1] - 1
    if num_patches == num_positions and height == self.patch_embeddings.image_size[0] and width == self.patch_embeddings.image_size[1]:
        return self.position_embeddings
    
    class_pos_embed = self.position_embeddings[:, 0]
    patch_pos_embed = self.position_embeddings[:, 1:]
    dim = embeddings.shape[-1]
    
    h0 = height // self.patch_embeddings.patch_size[0]
    w0 = width // self.patch_embeddings.patch_size[1]
    
    h_orig = self.patch_embeddings.image_size[0] // self.patch_embeddings.patch_size[0]
    w_orig = self.patch_embeddings.image_size[1] // self.patch_embeddings.patch_size[1]

    patch_pos_embed = patch_pos_embed.reshape(1, h_orig, w_orig, dim).permute(0, 3, 1, 2)
    
    # 核心改动：将 mode 从 "bicubic" 改为 "bilinear"
    patch_pos_embed = torch.nn.functional.interpolate(
        patch_pos_embed,
        scale_factor=(h0 / h_orig, w0 / w_orig),
        mode="bilinear",
        align_corners=False,
    )
    
    patch_pos_embed = patch_pos_embed.permute(0, 2, 3, 1).view(1, -1, dim)
    return torch.cat((class_pos_embed.unsqueeze(0), patch_pos_embed), dim=1)

def initialize_resources():
    """初始化模型和摄像头"""
    global camera, image_processor, model, device

    if model is None:
        print("Initializing Depth Anything V2 model...")
        try:
            if torch.backends.mps.is_available():
                device = torch.device("mps")
                torch_dtype = torch.float16
            elif torch.cuda.is_available():
                device = torch.device("cuda")
                torch_dtype = torch.float32  # CUDA 下强制 float32，避免 float16 报错
            else:
                device = torch.device("cpu")
                torch_dtype = torch.float32

            print(f"Using device: {device} with dtype: {torch_dtype}")
            model_name = "depth-anything/Depth-Anything-V2-Small-hf"
            image_processor = AutoImageProcessor.from_pretrained(model_name)
            model = AutoModelForDepthEstimation.from_pretrained(
                model_name,
                torch_dtype=torch_dtype,
                low_cpu_mem_usage=True
            ).to(device)

            # --- 针对 MPS 的猴子补丁 ---
            if device.type == 'mps':
                print("Applying monkey-patch for MPS compatibility.")
                target_object = model.backbone.embeddings
                target_object.interpolate_pos_encoding = types.MethodType(
                    new_interpolate_pos_encoding, target_object
                )

            print("Model initialized successfully.")
        except Exception as e:
            print(f"Error initializing model: {e}")
            model = "error"

    if camera is None:
        print("Initializing camera...")
        camera = cv2.VideoCapture(0)  # 0 for default camera
        if not camera.isOpened():
            print("Cannot open camera")
            camera = "error"
        else:
            # 为提升性能，设置较低的摄像头分辨率
            desired_width = 640
            desired_height = 480
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, desired_width)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, desired_height)
            # 核实最终确定的分辨率
            width = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
            print(f"Camera initialized. Requested {desired_width}x{desired_height}, got {int(width)}x{int(height)}.")

def generate_collision_frames():
    """生成防碰撞检测的视频帧"""
    initialize_resources()
    
    # 检查初始化是否出错
    if model == "error" or camera == "error":
        # 创建一个显示错误的图像
        error_img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(error_img, "Error: Model or Camera Failed", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        _, buffer = cv2.imencode('.jpg', error_img)
        frame = buffer.tobytes()
        while True:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    last_frame_time = time.time()
    fps = 0

    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # 1. 预处理图像
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            inputs = image_processor(images=image, return_tensors="pt")
            # 先全部转到 device
            inputs = {k: v.to(device) for k, v in inputs.items()}
            # 针对不同 device 类型处理 dtype
            if "pixel_values" in inputs:
                try:
                    if model is not None and not isinstance(model, str) and device is not None:
                        if hasattr(device, 'type') and device.type == 'mps':
                            if hasattr(model, 'dtype'):
                                inputs["pixel_values"] = inputs["pixel_values"].to(model.dtype)
                        elif hasattr(device, 'type') and device.type == 'cuda':
                            inputs["pixel_values"] = inputs["pixel_values"].to(torch.float32)
                        else:
                            inputs["pixel_values"] = inputs["pixel_values"].to(torch.float32)
                except Exception as e:
                    print(f"[pixel_values] .to(dtype) failed: {e}")
            # 打印 dtype 以便调试
            # print("model.dtype:", getattr(model, 'dtype', None))
            # print("inputs['pixel_values'].dtype:", inputs['pixel_values'].dtype)

            # 2. 模型推理
            with torch.no_grad():
                outputs = model(**inputs)
                predicted_depth = outputs.predicted_depth

            # 3. 后处理
            # 插值到原始尺寸
            prediction = torch.nn.functional.interpolate(
                predicted_depth.unsqueeze(1),
                size=image.size[::-1],
                mode="bilinear",
                align_corners=False,
            ).squeeze()

            output_normalized = (prediction - prediction.min()) / (prediction.max() - prediction.min()) * 255
            output_normalized = output_normalized.cpu().numpy().astype(np.uint8)
            
            # 应用伪彩色映射
            colored_depth = cv2.applyColorMap(output_normalized, cv2.COLORMAP_INFERNO)

            # 计算FPS
            current_time = time.time()
            fps = 1 / (current_time - last_frame_time)
            last_frame_time = current_time
            
            # 在画面上显示FPS
            cv2.putText(colored_depth, f"FPS: {fps:.2f}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # 编码为JPEG
            ret, buffer = cv2.imencode('.jpg', colored_depth)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed_collision')
def video_feed_collision():
    """防碰撞检测视频流"""
    return Response(generate_collision_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/collision_detection_page')
def collision_detection_page():
    """渲染独立的防碰撞检测页面"""
    return render_template('collision_page.html')


def release_resources():
    """释放摄像头资源"""
    global camera
    if camera and camera != "error" and camera.isOpened():
        camera.release()
        camera = None
        print("Camera released.")

# 在应用退出时注册清理函数
import atexit
atexit.register(release_resources)

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


@app.route('/api/config')
def get_config():
    """安全地向前端提供API配置"""
    return jsonify({
        'amap_key': os.getenv('AMAP_API_KEY'),
        'amap_security_secret': os.getenv('AMAP_SECURITY_SECRET')
    })


#weather interface
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

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
