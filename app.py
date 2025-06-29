from flask import Flask, render_template, jsonify, request, Response, stream_with_context, session, redirect, url_for
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
from sympy import false
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
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import pygame
from pygame import mixer
import socket



# 启用 MPS 后备方案以处理不受支持的操作 (现在可以移除了，因为我们修复了根本原因)
# os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# 配置CORS，允许所有源
CORS(app, resources={r"/*": {"origins": "*"}})

# 配置Socket.IO，允许所有源，并启用WebSocket
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='threading',
                   ping_timeout=60,
                   ping_interval=25)

simulator_socket = None
simulator_thread = None
event_loop = None
is_running = True

# 全局状态
vehicle_state = {
    'speed': 0.0,          # 速度 (km/h)
    'direction': 'straight',  # 方向
    'gear': 'P',           # 档位 (P/R/N/D)
    'lights': {
        'left_turn': False,   # 左转向灯
        'right_turn': False,  # 右转向灯
        'high_beam': False,   # 远光灯
        'low_beam': False,    # 近光灯
        'position': False,    # 位置灯
        'fog': False,         # 雾灯
        'warning': False      # 警示灯
    },
    'engine_temp': 25.0,   # 发动机温度 (°C)
    'fuel_level': 100.0    # 油量百分比
}

ac_status = {
    "ac_status": "off",
    "driver_temp": 25,
    "passenger_temp": 25,
    "fan_speed": 1,
    "mode": "auto"
}

media_status = {
    "playing": False,
    "current_track": None,
    "volume": 0.7,
    "playlist": [],
    "shuffle": False,
    "repeat": False
}

navigation_status = {
    "active": False,
    "destination": None,
    "route": None,
    "eta": None
}

voice_status = {
    "listening": False,
    "processing": False,
    "speaking": False
}

# =======================================================================
# =========================== DATABASE SETUP ============================
# =======================================================================

def init_database():
    """初始化数据库"""
    conn = sqlite3.connect('driving_system.db')
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            avatar TEXT DEFAULT '/static/images/avatar.jpg',
            phone TEXT,
            bio TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建用户设置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            setting_key TEXT NOT NULL,
            setting_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, setting_key)
        )
    ''')
    
    # 创建车辆设置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicle_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            setting_key TEXT NOT NULL,
            setting_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, setting_key)
        )
    ''')
    
    # 检查是否已有用户数据
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    
    # 只有在没有用户时才创建默认用户
    if user_count == 0:
        print("数据库为空，创建默认用户...")
        # 使用pbkdf2:sha256方法而不是默认的scrypt，提高兼容性
        default_password = generate_password_hash('admin123', method='pbkdf2:sha256')
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, bio)
            VALUES (?, ?, ?, ?)
        ''', ('admin', 'admin@drivingsystem.com', default_password, '系统管理员'))
        
        user_id = cursor.lastrowid
        
        # 为默认用户创建默认设置
        default_settings = {
            'driver_temp': '22.5',
            'passenger_temp': '22.5',
            'volume': '0.7',
            'shuffle': 'false',
            'repeat': 'none',
            'system_notifications': 'true',
            'security_alerts': 'true',
            'driving_suggestions': 'false',
            'marketing_info': 'false',
            'location_permission': 'true',
            'voice_recognition': 'true',
            'theme': 'dark',
            'language': 'zh-CN',
            'auto_lock': '5'
        }
        
        for key, value in default_settings.items():
            cursor.execute('''
                INSERT INTO user_settings (user_id, setting_key, setting_value)
                VALUES (?, ?, ?)
            ''', (user_id, key, value))
        
        # 为默认用户创建车辆设置
        default_vehicle_settings = {
            'driver_seat_position': 'normal',  # normal, sport, comfort
            'driver_seat_height': '0.5',       # 0.0-1.0
            'driver_seat_recline': '0.3',      # 0.0-1.0
            'driver_seat_lumbar': '0.5',       # 0.0-1.0
            'passenger_seat_position': 'normal',
            'passenger_seat_height': '0.5',
            'passenger_seat_recline': '0.3',
            'passenger_seat_lumbar': '0.5',
            'steering_wheel_position': 'normal', # normal, sport, comfort
            'steering_wheel_height': '0.5',      # 0.0-1.0
            'steering_wheel_telescope': '0.5',   # 0.0-1.0
            'mirror_driver_side': '0.5',         # 0.0-1.0
            'mirror_passenger_side': '0.5',      # 0.0-1.0
            'mirror_rear_view': '0.5',           # 0.0-1.0
            'ac_driver_temp': '22.0',
            'ac_passenger_temp': '22.0',
            'ac_fan_speed': '3',                 # 1-5
            'ac_mode': 'auto',                   # auto, manual, eco
            'ac_circulation': 'false',
            'ac_defrost': 'false',
            'ac_rear_defrost': 'false',
            'lighting_interior': '0.7',          # 0.0-1.0
            'lighting_ambient': '0.5',           # 0.0-1.0
            'lighting_color': 'white',           # white, blue, green, red, purple
            'suspension_mode': 'normal',         # normal, sport, comfort
            'steering_mode': 'normal',           # normal, sport, comfort
            'brake_mode': 'normal',              # normal, sport, comfort
            'drive_mode': 'normal'               # normal, sport, eco, snow
        }
        
        for key, value in default_vehicle_settings.items():
            cursor.execute('''
                INSERT INTO vehicle_settings (user_id, setting_key, setting_value)
                VALUES (?, ?, ?)
            ''', (user_id, key, value))
        
        print(f"已创建默认用户 'admin' (密码: admin123) 和 {len(default_settings)} 项用户设置、{len(default_vehicle_settings)} 项车辆设置")
    else:
        print(f"数据库已存在 {user_count} 个用户，跳过默认用户创建")
    
    conn.commit()
    conn.close()

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect('driving_system.db')
    conn.row_factory = sqlite3.Row
    return conn

# =======================================================================
# =========================== USER AUTHENTICATION =======================
# =======================================================================

def get_current_user():
    """获取当前登录用户"""
    if 'user_id' not in session:
        return None
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return user

def get_user_settings(user_id):
    """获取用户设置"""
    conn = get_db_connection()
    settings = {}
    rows = conn.execute('SELECT setting_key, setting_value FROM user_settings WHERE user_id = ?', (user_id,)).fetchall()
    for row in rows:
        settings[row['setting_key']] = row['setting_value']
    conn.close()
    return settings

def get_vehicle_settings(user_id):
    """获取车辆设置"""
    conn = get_db_connection()
    settings = {}
    rows = conn.execute('SELECT setting_key, setting_value FROM vehicle_settings WHERE user_id = ?', (user_id,)).fetchall()
    for row in rows:
        settings[row['setting_key']] = row['setting_value']
    conn.close()
    return settings

def save_user_setting(user_id, key, value):
    """保存用户设置"""
    conn = get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO user_settings (user_id, setting_key, setting_value, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, key, value))
    conn.commit()
    conn.close()

def save_vehicle_setting(user_id, key, value):
    """保存车辆设置"""
    conn = get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO vehicle_settings (user_id, setting_key, setting_value, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, key, value))
    conn.commit()
    conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return jsonify({'success': True, 'message': '登录成功'})
        else:
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return jsonify({'success': False, 'message': '请填写所有必填字段'}), 400
        
        try:
            conn = get_db_connection()
            
            # 检查用户名是否已存在
            existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            if existing_user:
                conn.close()
                return jsonify({'success': False, 'message': '用户名已存在'}), 400
            
            # 检查邮箱是否已存在
            existing_email = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            if existing_email:
                conn.close()
                return jsonify({'success': False, 'message': '邮箱已被注册'}), 400
            
            # 创建新用户
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            cursor = conn.execute('''
                INSERT INTO users (username, email, password_hash, bio)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, '欢迎使用智能驾驶系统'))
            
            user_id = cursor.lastrowid
            
            # 为新用户创建默认设置
            default_settings = {
                'driver_temp': '22.5',
                'passenger_temp': '22.5',
                'volume': '0.7',
                'shuffle': 'false',
                'repeat': 'none',
                'system_notifications': 'true',
                'security_alerts': 'true',
                'driving_suggestions': 'false',
                'marketing_info': 'false',
                'location_permission': 'true',
                'voice_recognition': 'true',
                'theme': 'dark',
                'language': 'zh-CN',
                'auto_lock': '5'
            }
            
            for key, value in default_settings.items():
                conn.execute('''
                    INSERT INTO user_settings (user_id, setting_key, setting_value)
                    VALUES (?, ?, ?)
                ''', (user_id, key, value))
            
            # 为新用户创建车辆设置
            default_vehicle_settings = {
                'driver_seat_position': 'normal',
                'driver_seat_height': '0.5',
                'driver_seat_recline': '0.3',
                'driver_seat_lumbar': '0.5',
                'passenger_seat_position': 'normal',
                'passenger_seat_height': '0.5',
                'passenger_seat_recline': '0.3',
                'passenger_seat_lumbar': '0.5',
                'steering_wheel_position': 'normal',
                'steering_wheel_height': '0.5',
                'steering_wheel_telescope': '0.5',
                'mirror_driver_side': '0.5',
                'mirror_passenger_side': '0.5',
                'mirror_rear_view': '0.5',
                'ac_driver_temp': '22.0',
                'ac_passenger_temp': '22.0',
                'ac_fan_speed': '3',
                'ac_mode': 'auto',
                'ac_circulation': 'false',
                'ac_defrost': 'false',
                'ac_rear_defrost': 'false',
                'lighting_interior': '0.7',
                'lighting_ambient': '0.5',
                'lighting_color': 'white',
                'suspension_mode': 'normal',
                'steering_mode': 'normal',
                'brake_mode': 'normal',
                'drive_mode': 'normal'
            }
            
            for key, value in default_vehicle_settings.items():
                conn.execute('''
                    INSERT INTO vehicle_settings (user_id, setting_key, setting_value)
                    VALUES (?, ?, ?)
                ''', (user_id, key, value))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': '注册成功'})
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'注册失败: {str(e)}'}), 500
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# =======================================================================
# =========================== USER SETTINGS API =========================
# =======================================================================

@app.route('/api/user/settings')
def get_settings():
    """获取当前用户的设置"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未登录'}), 401
    
    settings = get_user_settings(user['id'])
    return jsonify(settings)

@app.route('/api/user/settings', methods=['POST'])
def update_settings():
    """更新用户设置"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未登录'}), 401
    
    data = request.get_json()
    for key, value in data.items():
        save_user_setting(user['id'], key, str(value))
    
    return jsonify({'success': True, 'message': '设置已保存'})

@app.route('/api/vehicle/settings')
def get_vehicle_settings_api():
    """获取车辆设置"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未登录'}), 401
    
    settings = get_vehicle_settings(user['id'])
    return jsonify(settings)

@app.route('/api/vehicle/settings', methods=['POST'])
def update_vehicle_settings():
    """更新车辆设置"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未登录'}), 401
    
    data = request.get_json()
    for key, value in data.items():
        save_vehicle_setting(user['id'], key, str(value))
    
    return jsonify({'success': True, 'message': '车辆设置已保存'})

@app.route('/api/user/profile')
def get_profile():
    """获取用户资料"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未登录'}), 401
    
    return jsonify({
        'username': user['username'],
        'email': user['email'],
        'avatar': user['avatar'],
        'phone': user['phone'],
        'bio': user['bio']
    })

@app.route('/api/user/profile', methods=['POST'])
def update_profile():
    """更新用户资料"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未登录'}), 401
    
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    phone = data.get('phone')
    bio = data.get('bio')
    
    try:
        conn = get_db_connection()
        
        # 检查用户名是否已被其他用户使用
        if username != user['username']:
            existing = conn.execute('SELECT * FROM users WHERE username = ? AND id != ?', 
                                  (username, user['id'])).fetchone()
            if existing:
                conn.close()
                return jsonify({'error': '用户名已被使用'}), 400
        
        # 检查邮箱是否已被其他用户使用
        if email != user['email']:
            existing = conn.execute('SELECT * FROM users WHERE email = ? AND id != ?', 
                                  (email, user['id'])).fetchone()
            if existing:
                conn.close()
                return jsonify({'error': '邮箱已被使用'}), 400
        
        # 更新用户资料
        conn.execute('''
            UPDATE users 
            SET username = ?, email = ?, phone = ?, bio = ?
            WHERE id = ?
        ''', (username, email, phone, bio, user['id']))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '资料更新成功'})
        
    except Exception as e:
        return jsonify({'error': f'更新失败: {str(e)}'}), 500

@app.route('/api/user/password', methods=['POST'])
def change_password():
    """修改密码"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未登录'}), 401
    
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': '请填写所有密码字段'}), 400
    
    # 验证当前密码
    if not check_password_hash(user['password_hash'], current_password):
        return jsonify({'error': '当前密码错误'}), 400
    
    try:
        # 更新密码
        new_password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        conn = get_db_connection()
        conn.execute('UPDATE users SET password_hash = ? WHERE id = ?', 
                    (new_password_hash, user['id']))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '密码修改成功'})
        
    except Exception as e:
        return jsonify({'error': f'密码修改失败: {str(e)}'}), 500

# =======================================================================
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
    # 检查用户是否已登录
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    return render_template("index.html", user=user)


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
    

def get_now_weather(location="重庆"):
    """获取指定城市的当前天气
    Args:
        location: 城市名称，默认为重庆
    Returns:
        dict: 包含天气信息的字典
    """
    try:
        location_id = get_location_id(location)
        url = f"{url_api_weather}now?location={location_id}&key={os.getenv('QWEATHER_API_KEY')}"
        response = requests.get(url).json()
        data = {
            'msg': f"{location}当前天气：温度{response['now']['temp']}度，{response['now']['text']}，湿度{response['now']['humidity']}%，{response['now']['windDir']}{response['now']['windSpeed']}级",
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
            'msg': f"抱歉，获取{location}天气信息失败",
            '温度': '20',
            '湿度': '50',
            '风速': '10',
        }
    return data

def get_forecast_weather_by_date(date, location):
    try:
        location_id = get_location_id(location)
        # print(f"location: {location}")
        # print(f"date: {date}")
        url = f"{url_api_weather}7d?location={location_id}&key={os.getenv('QWEATHER_API_KEY')}"
        # print(f"url: {url}")
        reseponse = requests.get(url).json()['daily']
        info = reseponse
    except Exception as e:
        print(f"Error: {e}, return default forecastweather")
        return None
    result = { 
        'msg': {
            '日期': i['fxDate'],
            '最高温度': i['tempMax'],
            '最低温度': i['tempMin'],
            '天气': i['textDay'],
            '风速': i['windSpeedDay'],
            '紫外线强度': i['uvIndex'],
        }
        for i in info if i['fxDate'] == date
    }
    return result

#===============get_date=======================
def get_date():
    result = {  
        'msg': datetime.now().strftime("%Y-%m-%d"),
        'date': datetime.now().strftime("%Y-%m-%d"),
    }
    return result

#===============get_current_user=======================
ac_status = {
    'driver_temp': '22.5',
    'passenger_temp': '22.5',
    'ac_status': 'on',
    'ac_mode': 'auto',
    'ac_circulation': 'false',
}
navigation_status = {
    'navigating': False,
    'destination': '',
}
#===============control_ac=============================
def control_ac(action=None, value=None, zone='driver', delta=None, mode=None):
    """控制空调
    Args:
        action: 动作类型 ('set_temp', 'temp_up', 'temp_down', 'on', 'off', 'set_mode')
        value: 温度值（用于set_temp）
        zone: 区域 ('driver', 'passenger', 'all')
        delta: 温度变化值（用于temp_up/temp_down）
        mode: 空调模式 ('auto', 'cool', 'heat', 'ventilate')
    Returns:
        dict: 包含操作结果的字典
    """
    global ac_status
    result = {'status': 'success', 'msg': ''}
    
    # 确定要调整的区域
    zones = ['driver', 'passenger'] if zone == 'all' else [zone]
    
    try:
        if action == 'set_temp' and value is not None:
            temp = float(value)
            # 限制温度范围在16-30度之间
            temp = max(16, min(30, temp))
            for z in zones:
                ac_status[f'{z}_temp'] = temp
            result['msg'] = f"{'、'.join(zones)}温度已设为{temp}度"
            
        elif action == 'temp_up':
            delta_value = float(delta) if delta else 1
            for z in zones:
                current_temp = float(ac_status[f'{z}_temp'])
                new_temp = min(30, current_temp + delta_value)
                ac_status[f'{z}_temp'] = new_temp
            result['msg'] = f"{'、'.join(zones)}温度已升高{delta_value}度"
            
        elif action == 'temp_down':
            delta_value = float(delta) if delta else 1
            for z in zones:
                current_temp = float(ac_status[f'{z}_temp'])
                new_temp = max(16, current_temp - delta_value)
                ac_status[f'{z}_temp'] = new_temp
            result['msg'] = f"{'、'.join(zones)}温度已降低{delta_value}度"
            
        elif action == 'on':
            ac_status['ac_status'] = 'on'
            result['msg'] = "空调已开启"
            
        elif action == 'off':
            ac_status['ac_status'] = 'off'
            result['msg'] = "空调已关闭"
            
        elif action == 'set_mode' and mode:
            ac_status['mode'] = mode
            result['msg'] = f"空调模式已设置为{mode}"
            
        else:
            result = {'status': 'error', 'msg': '无效的空调控制命令'}
            
        # 通过WebSocket发送更新后的状态到前端
        socketio.emit('ac_status_update', {
            'status': ac_status,
            'message': result['msg']
        })
        
    except Exception as e:
        result = {'status': 'error', 'msg': f'空调控制出错: {str(e)}'}
        print(f"[AC Control Error] {str(e)}")
    
    return result

@socketio.on('connect')
def handle_connect():
    """客户端连接时，发送当前状态"""
    socketio.emit('ac_status_update', {
        'status': ac_status,
        'message': '已连接空调控制系统'
    })

@socketio.on('request_ac_status')
def handle_ac_status_request():
    """响应前端的空调状态请求"""
    socketio.emit('ac_status_update', {
        'status': ac_status,
        'message': '空调状态已更新'
    })

# ===============music_control function=================
def music_control(action, song_id=None, volume=None, mode=None, shuffle=None):
    """
    智能音乐播放器控制
    参数说明：
      action: 操作类型，play/pause/next/prev/set_volume/toggle_shuffle/toggle_repeat
      song_id: 歌曲ID（可选，切歌/播放时用）
      volume: 音量（0-1，设置音量时用）
      mode: 循环模式（none/one/all，切换循环时用）
      shuffle: 是否随机（true/false，切换随机时用）
    """
    global music_player
    result = {}

    # 检查播放列表是否为空
    if not music_player["playlist"]:
        music_player["playlist"] = scan_music_directory()
        if not music_player["playlist"]:
            result["msg"] = "播放列表为空，请先添加音乐文件"
            return result

    if action == "play":
        # 如果指定了歌曲ID，检查是否有效
        if song_id is not None:
            try:
                song_id = int(song_id)
                if 0 <= song_id < len(music_player["playlist"]):
                    music_player["current_song"] = song_id
                else:
                    # 如果 song_id 超出范围，默认播放第一首
                    music_player["current_song"] = 0
            except (ValueError, TypeError):
                # 如果 song_id 不是有效的整数，默认播放第一首
                music_player["current_song"] = 0
        # 如果没有指定歌曲ID且当前没有选中歌曲，默认播放第一首
        elif music_player["current_song"] >= len(music_player["playlist"]):
            music_player["current_song"] = 0
            
        music_player["is_playing"] = True
        result["msg"] = f"正在播放：{music_player['playlist'][music_player['current_song']]['title']}"
    
    elif action == "pause":
        music_player["is_playing"] = False
        result["msg"] = "音乐已暂停"
    
    elif action == "next":
        if music_player["shuffle"]:
            # 随机播放
            import random
            music_player["current_song"] = random.randint(0, len(music_player["playlist"]) - 1)
        else:
            # 顺序播放
            music_player["current_song"] = (music_player["current_song"] + 1) % len(music_player["playlist"])
        result["msg"] = f"切换到：{music_player['playlist'][music_player['current_song']]['title']}"
        # 自动开始播放
        music_player["is_playing"] = True
    
    elif action == "prev":
        if music_player["shuffle"]:
            # 随机播放
            import random
            music_player["current_song"] = random.randint(0, len(music_player["playlist"]) - 1)
        else:
            # 顺序播放
            music_player["current_song"] = (music_player["current_song"] - 1) % len(music_player["playlist"])
        result["msg"] = f"切换到：{music_player['playlist'][music_player['current_song']]['title']}"
        # 自动开始播放
        music_player["is_playing"] = True
    
    elif action == "set_volume" and volume is not None:
        music_player["volume"] = max(0.0, min(1.0, float(volume)))
        result["msg"] = f"音量已设置为{int(music_player['volume']*100)}%"
    
    elif action == "toggle_shuffle":
        music_player["shuffle"] = not music_player["shuffle"]
        result["msg"] = "随机播放已" + ("开启" if music_player["shuffle"] else "关闭")
    
    elif action == "toggle_repeat":
        repeat_modes = ["none", "one", "all"]
        current_index = repeat_modes.index(music_player["repeat"])
        music_player["repeat"] = repeat_modes[(current_index + 1) % len(repeat_modes)]
        result["msg"] = f"循环模式：{music_player['repeat']}"
    
    else:
        result["msg"] = "未识别的音乐操作"

    # 更新状态
    result["music_status"] = {
        "current_song": music_player["current_song"],
        "is_playing": music_player["is_playing"],
        "volume": music_player["volume"],
        "shuffle": music_player["shuffle"],
        "repeat": music_player["repeat"]
    }

    # 通过 WebSocket 广播状态更新
    socketio.emit('media_status_update', {
        'status': result["music_status"],
        'message': result["msg"]
    })

    return result

#===============other_functions=======================
##TODO: 添加其他函数，例如操控音乐，操控空调，或者操控导航等等


#===============navigation_control=======================
def navigation_control(action, destination=None):
    """
    智能导航控制
    参数说明：
      action: 操作类型，start/start_navigation/stop/stop_navigation
      destination: 目的地（仅在开始导航时用）
    """
    global navigation_status
    result = {}
    if action in ["start", "start_navigation"] and destination:
        navigation_status["navigating"] = True
        navigation_status["destination"] = destination
        # 发送 WebSocket 事件，通知前端打开导航界面并搜索
        socketio.emit('navigation_control', {
            'action': 'open_and_search',
            'destination': destination
        })
        # 等待前端返回导航信息
        time.sleep(2)  # 给前端一些时间处理导航请求
        
        if navigation_status.get('error'):
            result["msg"] = f"导航失败：{navigation_status['error']}"
            navigation_status["navigating"] = False
            navigation_status["destination"] = ""
        else:
            # 构建导航信息
            distance = navigation_status.get('distance', '未知')
            duration = navigation_status.get('duration', '未知')
            steps = navigation_status.get('steps', [])
            
            msg = f"已开始导航到{destination}，"
            msg += f"距离约{distance}公里，预计需要{duration}分钟。\n"
            if steps:
                msg += "接下来您需要：\n"
                msg += "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))
            
            result["msg"] = msg
            
    elif action in ["stop", "stop_navigation"]:
        navigation_status["navigating"] = False
        navigation_status["destination"] = ""
        result["msg"] = "已停止导航"
        # 发送 WebSocket 事件，通知前端停止导航
        socketio.emit('navigation_control', {
            'action': 'stop'
        })
    else:
        result["msg"] = "未识别的导航操作"
    
    result["navigation_status"] = navigation_status
    return result

#===========================================================
#===============tools and avaliable_functions===============
tools_prompt = {
    "get_now_weather": "获取现在城市的天气，用户应该提供城市名",
    "get_forecast_weather_by_date": "如果用户问你某一个城市未来某一天的天气，你应该返回该天的天气，用户应该提供日期和城市",
    "get_date": "获取现在的时间",
    "control_ac":"智能空调控制，支持温度设定、升降温、开关、模式切换等。参数：action（操作类型）、value（目标温度）、zone（区域）、delta（变化量）、mode（模式）",
    "music_control": "智能音乐播放器控制，支持播放、暂停、切歌、音量、随机、循环等。参数：action（操作类型）、song_id（歌曲ID）、volume（音量0-1）、mode（循环模式）、shuffle（是否随机）",
    "navigation_control": "智能导航控制，支持开始/停止导航。参数：action（操作类型），destination（目的地，开始导航时用）"
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
    {
        'type': 'function',
        'function': {
        'name': 'control_ac',
        'description': tools_prompt['control_ac'],
        'parameters': {
            'type': 'object',
            'properties': {
                'action': {'type': 'string', 'description': '操作类型，如设置温度到25度、升高2度、降低2度、打开空调、关闭空调、切换到制冷模式等，'
                           '，可选值：set_temp、temp_up、temp_down、on、off、set_mode'},
                'value': {'type': 'number', 'description': '目标温度，默认22.5'},
                'zone': {'type': 'string', 'description': '区域，可选值：driver、passenger，默认driver和passenger同步'},
                'delta': {'type': 'number', 'description': '变化量，默认2'},
                'mode': {'type': 'string', 'description': '模式，如制冷、制热、除湿、送风、自动等，可选值：auto、manual、eco、cool、heat、dry、fan_only、heat_cool'},
            },
            'required': ['action'],
            'additionalProperties': False,
        },
    }
    },
    {
        'type': 'function',
        'function': {
            'name': 'music_control',
            'description': tools_prompt['music_control'],
            'parameters': {
                'type': 'object',
                'properties': {
                    'action': {
                        'type': 'string',
                        'description': '操作类型，可选值：play、pause、next、prev、set_volume、toggle_shuffle、toggle_repeat'
                    },
                    'song_id': {
                        'type': 'integer',
                        'description': '歌曲ID，切歌/播放时用，必须是0到播放列表长度减1之间的整数，如果超出范围会默认播放第一首歌',
                        'minimum': 0,
                        'maximum': 100
                    },
                    'volume': {
                        'type': 'number',
                        'description': '音量，0-1之间'
                    },
                    'mode': {
                        'type': 'string',
                        'description': '循环模式，none/one/all'
                    },
                    'shuffle': {
                        'type': 'boolean',
                        'description': '是否随机播放'
                    }
                },
                'required': ['action'],
                'additionalProperties': False,
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'navigation_control',
            'description': tools_prompt['navigation_control'],
            'parameters': {
                'type': 'object',
                'properties': {
                    'action': {
                        'type': 'string',
                        'description': '操作类型，可选值：start、start_navigation、stop、stop_navigation'
                    },
                    'destination': {
                        'type': 'string',
                        'description': '目的地，仅开始导航时用'
                    }
                },
                'required': ['action'],
                'additionalProperties': False,
            }
        }
    }
]

avaliable_functions = {
    "get_now_weather": get_now_weather,
    "get_forecast_weather_by_date": get_forecast_weather_by_date,
    "get_date": get_date,
    "control_ac": control_ac,
    "music_control": music_control,
    "navigation_control": navigation_control,
}

#===============call_llama===============
def call_llama(messages, is_stream=False):
    response: ChatResponse = chat(
        f'{os.getenv("MODEL_NAME")}',
        messages=messages,
        think=False,
        tools=tools,
        stream=is_stream,
    )
    return response

def call_llama_without_tool(messages, is_stream=False):
    response: ChatResponse = chat(
        f'{os.getenv("MODEL_NAME")}',
        messages=messages,
        think=False,
        stream=is_stream,
    )
    return response

# 增强版唤醒词检测函数
def detect_wake_word_enhanced():
    """
    增强版唤醒词检测，包含噪声抑制和音频预处理
    适用于嘈杂环境
    """
    access_key = os.getenv('PORCUPINE_ACCESS_KEY')
    
    try:
        # 使用更保守的配置，减少误触发
        porcupine = pvporcupine.create(
            access_key=access_key, 
            keywords=["hey siri", "hey google", "alexa"],  # 多个唤醒词
            sensitivities=[0.6, 0.6, 0.6]  # 更低的灵敏度
        )
        
        # 优化录音器设置
        recorder = PvRecorder(
            device_index=1, 
            frame_length=porcupine.frame_length
        )
        
        print("[增强唤醒词检测] 开始监听...")
        recorder.start()
        
        # 添加连续检测逻辑，减少误触发
        detection_count = 0
        required_detections = 1  # 需要连续检测到2次才确认
        
        try:
            while True:
                pcm = recorder.read()
                keyword_index = porcupine.process(pcm)
                
                if keyword_index >= 0:
                    detection_count += 1
                    keyword = ["hey siri", "hey google", "alexa"][keyword_index]
                    print(f'[增强唤醒词检测] 检测到唤醒词: {keyword} (第{detection_count}次)')
                    
                    if detection_count >= required_detections:
                        print(f'[增强唤醒词检测] 确认唤醒词: {keyword}')
                        return True
                else:
                    # 重置检测计数
                    detection_count = 0
                    
        except KeyboardInterrupt:
            print("[增强唤醒词检测] 用户中断")
            return False
            
    except Exception as e:
        print(f"[增强唤醒词检测] 错误: {e}")
        return False
        
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
    
    return False

# 环境噪声检测函数
def check_ambient_noise(duration=3):
    """
    检测环境噪声水平，用于动态调整唤醒词检测参数
    """
    try:
        import numpy as np
        
        # 录制环境音频
        sample_rate = 16000
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()
        
        # 计算音频能量
        audio_data = np.array(recording)
        energy = np.mean(np.abs(audio_data))
        
        # 根据噪声水平返回建议的灵敏度
        if energy < 1000:  # 安静环境
            return "quiet", 0.8
        elif energy < 3000:  # 轻微噪声
            return "low_noise", 0.7
        elif energy < 6000:  # 中等噪声
            return "medium_noise", 0.6
        else:  # 高噪声
            return "high_noise", 0.5
            
    except Exception as e:
        print(f"[噪声检测] 错误: {e}")
        return "unknown", 0.7

# 自适应唤醒词检测函数
def detect_wake_word_adaptive():
    """
    自适应唤醒词检测，根据环境噪声动态调整参数
    """
    access_key = os.getenv('PORCUPINE_ACCESS_KEY')
    
    # 检测环境噪声
    noise_level, sensitivity = check_ambient_noise()
    print(f"[自适应唤醒词检测] 环境噪声水平: {noise_level}, 建议灵敏度: {sensitivity}")
    
    try:
        # 根据噪声水平选择唤醒词
        if noise_level in ["high_noise", "medium_noise"]:
            # 嘈杂环境使用更简单的唤醒词
            keywords = ["hey siri"]
            sensitivities = [sensitivity]
        else:
            # 安静环境可以使用更多唤醒词
            keywords = ["hey siri", "hey google"]
            sensitivities = [sensitivity, sensitivity]
        
        porcupine = pvporcupine.create(
            access_key=access_key, 
            keywords=keywords,
            sensitivities=sensitivities
        )
        
        recorder = PvRecorder(
            device_index=1, 
            frame_length=porcupine.frame_length
        )
        
        print(f"[自适应唤醒词检测] 开始监听，使用唤醒词: {keywords}")
        recorder.start()
        
        try:
            while True:
                pcm = recorder.read()
                keyword_index = porcupine.process(pcm)
                
                if keyword_index >= 0:
                    keyword = keywords[keyword_index]
                    print(f'[自适应唤醒词检测] 检测到唤醒词: {keyword}')
                    return True
                    
        except KeyboardInterrupt:
            print("[自适应唤醒词检测] 用户中断")
            return False
            
    except Exception as e:
        print(f"[自适应唤醒词检测] 错误: {e}")
        return False
        
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
    
    return False

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
    """处理用户输入，调用大模型获取回复
    Args:
        user_text: 用户输入的文本
    Returns:
        str: 大模型的回复
    """
    messages = [{"role": "user", "content": user_text + '，你是一个车载语音助手，回复指令时可以大胆调用工具，不要担心工具调用失败，最后给我一个精简的回复'}]
    print(f"【用户信息】: {messages}")
    
    # 调用大模型
    try:
        response = call_llama(messages)
        print(f"大模型回复【1】: {response.message}")
        
        # 检查是否有tool_calls
        if hasattr(response, 'message') and getattr(response.message, 'tool_calls', None):
            # 记录已处理的函数调用，避免重复
            processed_calls = set()
            
            for tool_call in response.message.tool_calls:
                # 生成唯一标识（函数名+参数）
                call_id = f"{tool_call.function.name}:{str(tool_call.function.arguments)}"
                
                # 跳过重复的调用
                if call_id in processed_calls:
                    continue
                processed_calls.add(call_id)
                
                if functoin_to_call := avaliable_functions.get(tool_call.function.name):
                    try:
                        print(f"【调用函数】: {tool_call.function.name}, 参数: {tool_call.function.arguments}")
                        result = functoin_to_call(**tool_call.function.arguments)
                        messages.append({"role": "tool", "name": tool_call.function.name, "content": str(result.get('msg', ''))})
                        print(f"【函数返回】: {result}")
                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        print(error_msg)
                        messages.append({"role": "tool", "name": tool_call.function.name, "content": error_msg})
            
            # 获取最终回复
            final_reply = call_llama_without_tool(messages)
            if '</think>' in str(final_reply.message.content):
                return str(final_reply.message.content).split('</think>')[1].strip()
            return final_reply.message.content
    except Exception as e:
        print(f"Error: {e}, llm failed")
        return "抱歉，我现在无法正确理解您的请求。"
    
    return response.message.content

def tts_and_play(text, filename=None):
    if filename is None:
        # 生成临时文件名
        temp_dir = "static/voice"
        os.makedirs(temp_dir, exist_ok=True)
        filename = os.path.join(temp_dir, f"tts_{uuid.uuid4().hex}.mp3")

    async def tts_task():
        print(f"[TTS] 合成文本: {text}")
        communicate = edge_tts.Communicate(text=text, voice="zh-CN-XiaoxiaoNeural")
        await communicate.save(filename)
    
    # 运行 TTS 合成
    asyncio.run(tts_task())

    # 推送播放状态到前端（可选）
    try:
        audio = MP3(filename)
        duration = audio.info.length
        socketio.emit('voice_status', {'status': 'streaming', 'text': text, 'duration': duration})
    except Exception:
        duration = None

    # 定义播放并在结束后删除文件的包装函数
    def _play_and_cleanup(path):
        try:
            # 初始化 pygame mixer
            if not pygame.get_init():
                pygame.init()
            if not mixer.get_init():
                mixer.init()
            
            # 加载并播放音频
            mixer.music.load(path)
            mixer.music.play()
            
            # 等待播放完成
            while mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            # 停止播放并卸载
            mixer.music.stop()
            mixer.music.unload()
        except Exception as e:
            print(f"[TTS] 播放音频失败: {e}")
        finally:
            try:
                os.remove(path)
                print(f"[TTS] 已删除临时音频文件: {path}")
            except Exception as e:
                print(f"[TTS] 删除文件失败: {e}")
    
    # 后台线程播放并自动清理
    threading.Thread(target=_play_and_cleanup, args=(filename,), daemon=True).start()

# 语音主流程线程
voice_status_queue = queue.Queue()
def voice_loop():
    while True:
        # 1. 唤醒检测
        try:
            if detect_wake_word_enhanced():
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
                    if ai_text == "":
                        return None
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
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    return render_template('user_center.html', user=user)

# 添加导航信息的 WebSocket 处理器
@socketio.on('navigation_info')
def handle_navigation_info(data):
    global navigation_status
    if data.get('error'):
        navigation_status['error'] = data['message']
    else:
        navigation_status.update(data)

@socketio.on('gear_change')
def handle_gear_change(data):
    """处理档位变更"""
    print(f"档位变更: {data}")
    # 广播档位变更
    socketio.emit('vehicle_status_update', {'status': data})

@socketio.on('lights_change')
def handle_lights_change(data):
    """处理灯光变更"""
    print(f"灯光变更: {data}")
    # 广播灯光变更
    socketio.emit('vehicle_status_update', {'status': data})

#====================模拟器通信====================
def connect_to_simulator():
    """连接到模拟器"""
    global simulator_socket
    try:
        simulator_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        simulator_socket.connect(('localhost', 5001))  # 连接到模拟器的新端口
        simulator_socket.setblocking(False)
        print("已连接到模拟器")
        return True
    except Exception as e:
        print(f"连接模拟器失败: {e}")
        if simulator_socket:
            simulator_socket.close()
            simulator_socket = None
        return False
def receive_simulator_data():
    """接收模拟器数据"""
    global simulator_socket, is_running
    
    while is_running:
        try:
            if simulator_socket:
                try:
                    # 接收数据
                    data = simulator_socket.recv(1024)
                    if data:
                        try:
                            # 解析并处理数据
                            simulator_data = json.loads(data.decode())
                            print(f"收到模拟器数据: {simulator_data}")
                            # 通过WebSocket广播状态
                            formatted_data = {
                                'status': simulator_data['state'],
                                'message': '已接收模拟器数据',
                                'timestamp': simulator_data['timestamp']
                            }
                            socketio.emit('simulator_update', formatted_data, namespace='/')
                        except json.JSONDecodeError:
                            print("无效的JSON数据")
                        except Exception as e:
                            print(f"处理模拟器数据时出错: {e}")
                    else:
                        # 连接断开，尝试重连
                        print("模拟器连接断开，尝试重连...")
                        simulator_socket.close()
                        simulator_socket = None
                        time.sleep(2)
                        connect_to_simulator()
                except BlockingIOError:
                    # 非阻塞模式下没有数据可读
                    time.sleep(0.1)
                except Exception as e:
                    print(f"接收数据时出错: {e}")
                    time.sleep(0.1)
            else:
                # 如果没有连接，尝试重连
                if connect_to_simulator():
                    print("重新连接成功")
                else:
                    time.sleep(2)
        except Exception as e:
            print(f"处理模拟器数据时出错: {e}")
            time.sleep(0.1)



def run_simulator_loop():
    """运行模拟器数据接收循环"""
    try:
        receive_simulator_data()
    except Exception as e:
        print(f"模拟器循环出错: {e}")
    finally:
        if simulator_socket:
            simulator_socket.close()

def start_simulator_connection():
    """启动模拟器连接"""
    global simulator_thread, is_running
    
    is_running = True
    if connect_to_simulator():
        # 创建并启动模拟器数据接收线程
        simulator_thread = threading.Thread(target=run_simulator_loop)
        simulator_thread.daemon = True
        simulator_thread.start()
        return True
    return False

# 在if __name__ == '__main__'部分之前添加
def stop_simulator_connection():
    """停止模拟器连接"""
    global is_running, simulator_socket, event_loop
    
    is_running = False
    if simulator_socket:
        simulator_socket.close()
        simulator_socket = None
    
    if event_loop and event_loop.is_running():
        event_loop.stop()

# 修改main部分
# Socket.IO事件处理
@socketio.on('connect')
def handle_connect():
    print('客户端已连接')
    socketio.emit('server_response', {'data': '连接成功！'})

@socketio.on('disconnect')
def handle_disconnect():
    print('客户端断开连接')


if __name__ == '__main__':
    try:
        # 初始化数据库
        init_database()
        
        # 启动模拟器连接
        start_simulator_connection()

        
        # 启动Flask应用（使用不同的端口）
        socketio.run(app, host='0.0.0.0', port=8080, debug=False)
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        stop_simulator_connection()
    except Exception as e:
        print(f"启动失败: {e}")
        stop_simulator_connection()
