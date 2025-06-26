import json
from ollama import ChatResponse, chat
import requests
import os
from datetime import datetime
import argparse
import cv2
import glob
import matplotlib
import numpy as np
import os
import torch
import cv2
from transformers import pipeline
from PIL import Image
import requests
import time
import sys
#====================================================
#===============test_collision=======================
#====================================================
"""
    Here you can test the collision detection
    it show's the problem you may occur
"""
def test_collision():
    #----------------------------------------------------
    # load model test
    try:
        # load pipe
        pipe = pipeline(task="depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf")
    except Exception as e:
        print(f"Error: {e}, model problem!!!")
        return
    #----------------------------------------------------
    # open camera test
    try:
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("Error: Could not open video device.")
    except Exception as e:
        print(f"Error: {e}, camera problem!!!")
        return
    #----------------------------------------------------
    # set camera resolution test
    # TODO:here you can set the resolution you want, lower the resolution, the faster the fps
    width = 320
    height = 240

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    #----------------------------------------------------
    # get camera resolution test， if your resolution lower, but the fps is lower, you can find out the reason here
    actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"实际分辨率: {actual_width} x {actual_height}")

    #----------------------------------------------------
    fps = 0
    start_time = time.time()
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame.")
                break
            #----------------------------------------------------
            # fps test, you can see the fps in the window
            end_time = time.time()
            fps = 1 / (end_time - start_time)
            start_time = end_time
            text = f"FPS: {fps:.2f}"
            (text_width, text_height), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            cv2.rectangle(frame, (0, 0), (text_width, text_height + baseline), (0, 0, 0), cv2.FILLED)
            cv2.putText(frame, text, (0, text_height + baseline), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            #----------------------------------------------------
            # OpenCV 的 BGR 转 RGB，转为 PIL.Image
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            #----------------------------------------------------
            # inference test
            # 推理
            try:
                result = pipe(image)
                depth = result["depth"]
            except Exception as e:
                print(f"Error: {e}, inference problem!!!")
                continue
            #----------------------------------------------------
            # depth test
            # 归一化到 0-255 并转为 uint8
            try:
                depth_np = np.array(depth)
                depth_norm = (depth_np - depth_np.min()) / (depth_np.max() - depth_np.min()) * 255
                depth_uint8 = depth_norm.astype(np.uint8)
            except Exception as e:
                print(f"Error: {e}, depth problem!!!")
                continue
            #----------------------------------------------------
            # depth color test
            depth_color = cv2.applyColorMap(depth_uint8, cv2.COLORMAP_INFERNO)
            #----------------------------------------------------
            # show test
            # show the camera and depth image
            cv2.imshow("Camera", frame)
            cv2.imshow("Depth", depth_color)
            #----------------------------------------------------
            # exit test
            # press q to exit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except Exception as e:
        print(f"Error: {e}, inference problem!!!")
        return
    finally:
        cap.release()
        cv2.destroyAllWindows()
#====================================================
#===============test_collision=======================
#====================================================



#====================================================
#===============functions for tool_call_test=========
#====================================================
"""
    Here you can add your own functions for tool_call_test
"""
#---------weather_function------------------------
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

#---------get_date---------------------------------
def get_date():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#---------other functions-----------------------------
#TODO:here you can add your own functions for tool_call_test


#---------tool_call_test_config------------------------
#TODO:config is also important, --tools_prompt--,--tools--,--avaliable_functions--
tools_prompt = {
    "get_now_weather": "获取现在城市的天气，用户应该提供城市名",
    "get_forecast_weather_by_date": "如果用户问你某一个城市未来某一天的天气，你应该返回该天的天气，用户应该提供日期和城市",
    "get_date": "用户会询问现在的时间，你只需要返回时间"
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
    


#========================================================
#========functions and configs for tool_call_test========
#========================================================




#========================================================
#===============tool_call_test============================
#=========================================================
def tool_call():
    print('[TOOL CALL]:')

    #---------send_message-----------------------------
    try:
        def send_message(messages, is_stream=False,):
            response: ChatResponse = chat(
                'qwen3:1.7b',
                messages=messages,
                think=False,
                tools=tools,
                stream=is_stream,
            )
            return response
    except Exception as e:
        print(f"Error: {e}, send_message problem!!!")
        return
    
    #---------send_message_without_tool------------------
    try:
        def send_messsage_without_tool(messages, is_stream=False):
            response: ChatResponse = chat(
                'qwen3:1.7b',
                messages=messages,
                think=False,
                stream=is_stream,
                )
            return response
    except Exception as e:
        print(f"Error: {e}, send_messsage_without_tool problem!!!")
        return
    
    #---------message_test-----------------------------
    #TODO:here you can add your own prompt to get what you want from the model
    
    users_text = "现在的时间是什么"
    messages = [{"role": "user", "content": users_text}]
    print(f"first messages: {messages}")
    try:
        response = send_message(messages)
        print(f"response: {response}")
    except Exception as e:
        print(f"Error: {e}, message_test problem!!!")
        return
    try:
        if response.message.tool_calls:
            for tool_call in response.message.tool_calls:
                if functoin_to_call := avaliable_functions.get(tool_call.function.name):
                    result = functoin_to_call(**tool_call.function.arguments)
                    messages.append(response.message)
                    messages.append({"role": "tool", "name": tool_call.function.name, "content": str(result)})
                    print(f"second messages: {messages}")
    except Exception as e:
        print(f"Error: {e}, tool_call_test problem!!!")
        return
    
    #---------final_response-----------------------------
    try:
        final_response = send_messsage_without_tool(messages)
        print(f"final_response: {final_response}")
    except Exception as e:
        print(f"Error: {e}, final_response problem!!!")
        return

#====================================================
#===============test_weather=========================
#====================================================
"""
    测试天气API相关功能
    示例：python test.py --weather --city 重庆
"""
def test_weather(city="重庆"):
    from app import get_now_weather, get_forecast_weather_by_date
    print(f"测试城市：{city}")
    now = get_now_weather(city)
    print("当前天气：", now)
    # 未来三天
    from datetime import datetime, timedelta
    for i in range(3):
        date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
        forecast = get_forecast_weather_by_date(date, city)
        print(f"{date} 预报：", forecast)

#====================================================
#===============test_music===========================
#====================================================
"""
    测试音乐API相关功能
    示例：python test.py --music
"""
def test_music():
    from app import scan_music_directory
    playlist = scan_music_directory()
    print("音乐列表：")
    for song in playlist:
        print(song)

#====================================================
#===============test_voice===========================
#====================================================
"""
    测试语音识别功能（需本地vosk模型）
    示例：python test.py --voice
"""
def test_voice():
    from app import record_audio, recognize
    wav_path = record_audio(duration=5)
    print("录音完成，开始识别...")
    text = recognize(wav_path)
    print("识别结果：", text)

#====================================================
#===============test_tts=============================
#====================================================
"""
    测试TTS语音合成功能
    示例：python test.py --tts --text "你好，欢迎使用车载系统"
"""
def test_tts(text="你好，欢迎使用车载系统"):
    try:
        from app import tts_and_play
        print(f"合成并播放文本：{text}")
        tts_and_play(text)
        print("TTS合成与播放已完成。")
    except Exception as e:
        print(f"TTS测试失败: {e}")

#====================================================
#===============test_vehicle_status==================
#====================================================
"""
    测试车辆状态API
    示例：python test.py --vehicle_status
"""
def test_vehicle_status():
    try:
        import requests
        resp = requests.get("http://127.0.0.1:5001/api/vehicle/status")
        print("车辆状态：", resp.json())
        # 可选：测试POST更新
        update = {"speed": 88}
        resp2 = requests.post("http://127.0.0.1:5001/api/vehicle/status", json=update)
        print("更新后车辆状态：", resp2.json())
    except Exception as e:
        print(f"车辆状态API测试失败: {e}")

#====================================================
#===============test_ac_status=======================
#====================================================
"""
    测试空调状态API
    示例：python test.py --ac_status
"""
def test_ac_status():
    try:
        import requests
        resp = requests.get("http://127.0.0.1:5001/api/ac/status")
        print("空调状态：", resp.json())
        # 可选：测试POST更新
        update = {"temperature": 25}
        resp2 = requests.post("http://127.0.0.1:5001/api/ac/status", json=update)
        print("更新后空调状态：", resp2.json())
    except Exception as e:
        print(f"空调状态API测试失败: {e}")

#====================================================
#===============test_media_status====================
#====================================================
"""
    测试多媒体状态API
    示例：python test.py --media_status
"""
def test_media_status():
    try:
        import requests
        resp = requests.get("http://127.0.0.1:5001/api/media/status")
        print("多媒体状态：", resp.json())
        # 可选：测试POST更新
        update = {"volume": 80}
        resp2 = requests.post("http://127.0.0.1:5001/api/media/status", json=update)
        print("更新后多媒体状态：", resp2.json())
    except Exception as e:
        print(f"多媒体状态API测试失败: {e}")

#====================================================
#===============test_navigation_status===============
#====================================================
"""
    测试导航状态API
    示例：python test.py --navigation_status
"""
def test_navigation_status():
    try:
        import requests
        resp = requests.get("http://127.0.0.1:5001/api/navigation/status")
        print("导航状态：", resp.json())
        # 可选：测试POST更新
        update = {"destination": "解放碑"}
        resp2 = requests.post("http://127.0.0.1:5001/api/navigation/status", json=update)
        print("更新后导航状态：", resp2.json())
    except Exception as e:
        print(f"导航状态API测试失败: {e}")

#====================================================
#===============test_wake_word=======================
#====================================================
"""
    测试唤醒词检测功能（Porcupine）
    示例：python test.py --wake_word
"""
def test_wake_word():
    try:
        from app import detect_wake_word
        print("请说出唤醒词（如 hey siri）...")
        detected = detect_wake_word()
        if detected:
            print("唤醒词检测成功！")
        else:
            print("未检测到唤醒词。")
    except Exception as e:
        print(f"唤醒词检测测试失败: {e}")

#====================================================
#===============test_socketio_voice_status===========
#====================================================
"""
    测试SocketIO语音状态推送
    示例：python test.py --socketio_voice
"""
def test_socketio_voice():
    try:
        import socketio
        sio = socketio.Client()

        @sio.on('voice_status')
        def on_voice_status(data):
            print("收到voice_status事件：", data)

        sio.connect('http://127.0.0.1:5001')
        print("已连接SocketIO，等待事件推送（Ctrl+C退出）...")
        sio.wait()
    except Exception as e:
        print(f"SocketIO测试失败: {e}")

#====================================================
#===============test_voice_full======================
#====================================================
"""
    测试完整语音交互流程（唤醒->录音->识别->LLM->TTS）
    示例：python test.py --voice_full
"""
def test_voice_full():
    try:
        from app import detect_wake_word, record_audio, recognize, llm, tts_and_play
        print("请说出唤醒词...")
        if detect_wake_word():
            print("唤醒成功，开始录音...")
            wav_path = record_audio(duration=5)
            print("录音完成，开始识别...")
            text = recognize(wav_path)
            print("识别结果：", text)
            print("调用大模型推理...")
            ai_text = llm(text)
            print("大模型回复：", ai_text)
            print("TTS合成并播放...")
            tts_and_play(ai_text)
            print("流程结束。")
    except Exception as e:
        print(f"完整语音流程测试失败: {e}")

#====================================================
#===============test_amap_config=====================
#====================================================
"""
    测试高德地图API配置
    示例：python test.py --amap_config
"""
def test_amap_config():
    try:
        import requests
        resp = requests.get("http://127.0.0.1:5001/api/config")
        print("高德地图API配置：", resp.json())
    except Exception as e:
        print(f"高德地图API配置测试失败: {e}")

#====================================================
#===============test_lyrics_api======================
#====================================================
"""
    测试歌词API
    示例：python test.py --lyrics --song_id 0
"""
def test_lyrics_api(song_id=0):
    try:
        import requests
        resp = requests.get(f"http://127.0.0.1:5001/api/music/lyrics/{song_id}")
        print(f"歌曲ID {song_id} 的歌词：", resp.json())
    except Exception as e:
        print(f"歌词API测试失败: {e}")

#====================================================
#===============test_music_control_api===============
#====================================================
"""
    测试音乐播放控制API
    示例：python test.py --music_control --action play --song_id 0
"""
def test_music_control_api(action="play", song_id=0):
    try:
        import requests
        url_map = {
            "play": "/api/music/play",
            "pause": "/api/music/pause",
            "next": "/api/music/next",
            "prev": "/api/music/prev",
            "shuffle": "/api/music/shuffle",
            "repeat": "/api/music/repeat",
            "volume": "/api/music/volume"
        }
        url = url_map.get(action)
        if not url:
            print("不支持的action")
            return
        data = {}
        if action == "play":
            data = {"song_id": song_id}
        elif action == "volume":
            data = {"volume": 0.5}
        resp = requests.post(f"http://127.0.0.1:5001{url}", json=data)
        print(f"音乐控制 {action} 响应：", resp.json())
    except Exception as e:
        print(f"音乐控制API测试失败: {e}")

#====================================================
#===============test_tts_save_file===================
#====================================================
"""
    测试TTS语音合成并保存为文件
    示例：python test.py --tts_save --text "测试保存" --filename "output.mp3"
"""
def test_tts_save_file(text="测试保存", filename="output.mp3"):
    try:
        from app import tts_and_play
        import os
        print(f"合成文本：{text}，保存为：{filename}")
        tts_and_play(text, filename=f"static/voice/{filename}")
        if os.path.exists(f"static/voice/{filename}"):
            print("TTS音频文件保存成功！")
        else:
            print("TTS音频文件未找到！")
    except Exception as e:
        print(f"TTS保存文件测试失败: {e}")

#====================================================
#===============arg_parse============================
#====================================================
def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--collision", action="store_true", help="测试防碰撞检测（摄像头+深度）")
    parser.add_argument("--tool_call", action="store_true", help="测试大模型工具调用")
    parser.add_argument("--weather", action="store_true", help="测试天气API")
    parser.add_argument("--music", action="store_true", help="测试音乐API")
    parser.add_argument("--voice", action="store_true", help="测试语音识别")
    parser.add_argument("--tts", action="store_true", help="测试TTS语音合成")
    parser.add_argument("--text", type=str, default="你好，欢迎使用车载系统", help="TTS合成文本")
    parser.add_argument("--vehicle_status", action="store_true", help="测试车辆状态API")
    parser.add_argument("--ac_status", action="store_true", help="测试空调状态API")
    parser.add_argument("--media_status", action="store_true", help="测试多媒体状态API")
    parser.add_argument("--navigation_status", action="store_true", help="测试导航状态API")
    parser.add_argument("--wake_word", action="store_true", help="测试唤醒词检测")
    parser.add_argument("--socketio_voice", action="store_true", help="测试SocketIO语音状态推送")
    parser.add_argument("--voice_full", action="store_true", help="测试完整语音交互流程")
    parser.add_argument("--amap_config", action="store_true", help="测试高德地图API配置")
    parser.add_argument("--lyrics", action="store_true", help="测试歌词API")
    parser.add_argument("--song_id", type=int, default=0, help="歌词/音乐控制测试用歌曲ID")
    parser.add_argument("--music_control", action="store_true", help="测试音乐播放控制API")
    parser.add_argument("--action", type=str, default="play", help="音乐控制动作(play/pause/next/prev/shuffle/repeat/volume)")
    parser.add_argument("--tts_save", action="store_true", help="测试TTS语音合成并保存为文件")
    parser.add_argument("--filename", type=str, default="output.mp3", help="TTS保存文件名")
    parser.add_argument("--city", type=str, default="重庆", help="指定城市名（用于天气测试）")
    parser.add_argument("--help", action="store_true", help="显示帮助信息")
    return parser.parse_args()

if __name__ == "__main__":
    args = arg_parse()

    if len(sys.argv) < 2 or args.help:
        print("""Usage: 
              python test.py --collision
              python test.py --tool_call
              python test.py --weather --city 重庆
              python test.py --music
              python test.py --voice
              python test.py --tts --text "你好，欢迎使用车载系统"
              python test.py --vehicle_status
              python test.py --ac_status
              python test.py --media_status
              python test.py --navigation_status
              python test.py --wake_word
              python test.py --socketio_voice
              python test.py --voice_full
              python test.py --amap_config
              python test.py --lyrics --song_id 0
              python test.py --music_control --action play --song_id 0
              python test.py --tts_save --text "保存测试" --filename "output.mp3"
              --collision: 测试防碰撞检测
              --tool_call: 测试大模型工具调用
              --weather: 测试天气API
              --music: 测试音乐API
              --voice: 测试语音识别
              --tts: 测试TTS语音合成
              --text: TTS合成文本
              --vehicle_status: 测试车辆状态API
              --ac_status: 测试空调状态API
              --media_status: 测试多媒体状态API
              --navigation_status: 测试导航状态API
              --wake_word: 测试唤醒词检测
              --socketio_voice: 测试SocketIO语音状态推送
              --voice_full: 测试完整语音交互流程
              --amap_config: 测试高德地图API配置
              --lyrics: 测试歌词API
              --song_id: 歌词/音乐控制测试用歌曲ID
              --music_control: 测试音乐播放控制API
              --action: 音乐控制动作(play/pause/next/prev/shuffle/repeat/volume)
              --tts_save: 测试TTS语音合成并保存为文件
              --filename: TTS保存文件名
              --city: 指定城市名（用于天气测试）
              --help: 显示帮助信息
              """)
        exit()
    if args.collision:
        test_collision()
    elif args.tool_call:
        tool_call()
    elif args.weather:
        test_weather(args.city)
    elif args.music:
        test_music()
    elif args.voice:
        test_voice()
    elif args.tts:
        test_tts(args.text)
    elif args.vehicle_status:
        test_vehicle_status()
    elif args.ac_status:
        test_ac_status()
    elif args.media_status:
        test_media_status()
    elif args.navigation_status:
        test_navigation_status()
    elif args.wake_word:
        test_wake_word()
    elif args.socketio_voice:
        test_socketio_voice()
    elif args.voice_full:
        test_voice_full()
    elif args.amap_config:
        test_amap_config()
    elif args.lyrics:
        test_lyrics_api(args.song_id)
    elif args.music_control:
        test_music_control_api(args.action, args.song_id)
    elif args.tts_save:
        test_tts_save_file(args.text, args.filename)
    else:
        print("No test selected")
