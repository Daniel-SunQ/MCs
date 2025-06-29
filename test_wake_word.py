#!/usr/bin/env python3
"""
唤醒词检测测试脚本
用于测试不同环境下的唤醒词检测性能
"""

import os
import time
from dotenv import load_dotenv
import pvporcupine
from pvrecorder import PvRecorder
import sounddevice as sd
import numpy as np

load_dotenv()

def test_basic_wake_word():
    """测试基础唤醒词检测"""
    print("=== 测试基础唤醒词检测 ===")
    access_key = os.getenv('PORCUPINE_ACCESS_KEY')
    
    try:
        porcupine = pvporcupine.create(
            access_key=access_key, 
            keywords=["hey siri"],
            sensitivities=[0.8]
        )
        
        recorder = PvRecorder(
            device_index=1, 
            frame_length=porcupine.frame_length
        )
        
        print("请说 'hey siri' (5秒后自动停止)...")
        recorder.start()
        
        start_time = time.time()
        while time.time() - start_time < 5:
            pcm = recorder.read()
            keyword_index = porcupine.process(pcm)
            
            if keyword_index >= 0:
                print("✓ 检测到唤醒词!")
                return True
                
        print("✗ 未检测到唤醒词")
        return False
        
    except Exception as e:
        print(f"错误: {e}")
        return False
    finally:
        try:
            recorder.stop()
            recorder.delete()
            porcupine.delete()
        except:
            pass

def test_enhanced_wake_word():
    """测试增强版唤醒词检测"""
    print("\n=== 测试增强版唤醒词检测 ===")
    access_key = os.getenv('PORCUPINE_ACCESS_KEY')
    
    try:
        keywords = ["hey siri", "hey google"]
        porcupine = pvporcupine.create(
            access_key=access_key, 
            keywords=keywords,
            sensitivities=[0.6, 0.6]
        )
        
        recorder = PvRecorder(
            device_index=1, 
            frame_length=porcupine.frame_length
        )
        
        print("请说 'hey siri' 或 'hey google' (8秒后自动停止)...")
        recorder.start()
        
        detection_count = 0
        required_detections = 1  # 降低要求，只需要检测到1次
        start_time = time.time()
        
        while time.time() - start_time < 8:  # 增加检测时间到8秒
            pcm = recorder.read()
            keyword_index = porcupine.process(pcm)
            
            if keyword_index >= 0:
                detection_count += 1
                keyword = keywords[keyword_index]
                print(f"检测到唤醒词: {keyword} (第{detection_count}次)")
                
                if detection_count >= required_detections:
                    print("✓ 确认唤醒词!")
                    return True
            else:
                # 重置检测计数（可选，用于更严格的检测）
                # detection_count = 0
                pass
                
        print("✗ 未确认唤醒词")
        return False
        
    except Exception as e:
        print(f"错误: {e}")
        return False
    finally:
        try:
            recorder.stop()
            recorder.delete()
            porcupine.delete()
        except:
            pass

def test_noise_level():
    """测试环境噪声水平"""
    print("\n=== 测试环境噪声水平 ===")
    
    try:
        # 录制环境音频
        sample_rate = 16000
        duration = 3
        
        print(f"正在检测环境噪声 ({duration}秒)...")
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()
        
        # 计算音频能量
        audio_data = np.array(recording)
        energy = np.mean(np.abs(audio_data))
        
        print(f"音频能量: {energy:.2f}")
        
        # 根据噪声水平分类
        if energy < 1000:
            level = "安静环境"
            sensitivity = 0.8
        elif energy < 3000:
            level = "轻微噪声"
            sensitivity = 0.7
        elif energy < 6000:
            level = "中等噪声"
            sensitivity = 0.6
        else:
            level = "高噪声"
            sensitivity = 0.5
            
        print(f"环境分类: {level}")
        print(f"建议灵敏度: {sensitivity}")
        
        return level, sensitivity
        
    except Exception as e:
        print(f"错误: {e}")
        return "未知", 0.7

def test_adaptive_wake_word():
    """测试自适应唤醒词检测"""
    print("\n=== 测试自适应唤醒词检测 ===")
    
    # 先检测噪声水平
    noise_level, sensitivity = test_noise_level()
    
    access_key = os.getenv('PORCUPINE_ACCESS_KEY')
    
    try:
        # 根据噪声水平选择配置
        if noise_level in ["高噪声", "中等噪声"]:
            keywords = ["hey siri"]
            sensitivities = [sensitivity]
            print("使用单唤醒词模式")
        else:
            keywords = ["hey siri", "hey google"]
            sensitivities = [sensitivity, sensitivity]
            print("使用多唤醒词模式")
        
        porcupine = pvporcupine.create(
            access_key=access_key, 
            keywords=keywords,
            sensitivities=sensitivities
        )
        
        recorder = PvRecorder(
            device_index=1, 
            frame_length=porcupine.frame_length
        )
        
        print(f"请说唤醒词: {keywords} (5秒后自动停止)...")
        recorder.start()
        
        start_time = time.time()
        while time.time() - start_time < 5:
            pcm = recorder.read()
            keyword_index = porcupine.process(pcm)
            
            if keyword_index >= 0:
                keyword = keywords[keyword_index]
                print(f"✓ 检测到唤醒词: {keyword}")
                return True
                
        print("✗ 未检测到唤醒词")
        return False
        
    except Exception as e:
        print(f"错误: {e}")
        return False
    finally:
        try:
            recorder.stop()
            recorder.delete()
            porcupine.delete()
        except:
            pass

def main():
    """主测试函数"""
    print("唤醒词检测性能测试")
    print("=" * 50)
    
    # 检查环境变量
    if not os.getenv('PORCUPINE_ACCESS_KEY'):
        print("错误: 未设置 PORCUPINE_ACCESS_KEY 环境变量")
        return
    
    # 运行各种测试
    results = {}
    
    # 测试噪声水平
    noise_level, sensitivity = test_noise_level()
    results['noise_level'] = noise_level
    results['sensitivity'] = sensitivity
    
    # 测试基础检测
    results['basic'] = test_basic_wake_word()
    
    # 测试增强检测
    results['enhanced'] = test_enhanced_wake_word()
    
    # 测试自适应检测
    results['adaptive'] = test_adaptive_wake_word()
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print(f"环境噪声水平: {results['noise_level']}")
    print(f"建议灵敏度: {results['sensitivity']}")
    print(f"基础检测: {'✓ 通过' if results['basic'] else '✗ 失败'}")
    print(f"增强检测: {'✓ 通过' if results['enhanced'] else '✗ 失败'}")
    print(f"自适应检测: {'✓ 通过' if results['adaptive'] else '✗ 失败'}")
    
    # 给出建议
    print("\n建议:")
    if results['noise_level'] in ["高噪声", "中等噪声"]:
        print("- 建议使用自适应检测模式")
        print("- 考虑使用更简单的唤醒词")
        print("- 可以适当降低灵敏度")
    else:
        print("- 环境较安静，可以使用标准检测模式")
        print("- 可以使用多个唤醒词")

if __name__ == "__main__":
    main() 