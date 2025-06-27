#!/usr/bin/env python3
"""
唤醒词检测配置文件
提供不同环境下的最佳配置参数
"""

# 环境配置
ENVIRONMENT_CONFIGS = {
    "quiet": {
        "description": "安静环境（家庭、办公室）",
        "sensitivity": 0.8,
        "keywords": ["hey siri", "hey google"],
        "required_detections": 1,
        "timeout": 5
    },
    "low_noise": {
        "description": "轻微噪声环境（咖啡厅、图书馆）",
        "sensitivity": 0.7,
        "keywords": ["hey siri", "hey google"],
        "required_detections": 1,
        "timeout": 6
    },
    "medium_noise": {
        "description": "中等噪声环境（商场、餐厅）",
        "sensitivity": 0.6,
        "keywords": ["hey siri"],
        "required_detections": 2,
        "timeout": 8
    },
    "high_noise": {
        "description": "高噪声环境（街道、车内）",
        "sensitivity": 0.5,
        "keywords": ["hey siri"],
        "required_detections": 2,
        "timeout": 10
    }
}

# 噪声水平阈值
NOISE_THRESHOLDS = {
    "quiet": 1000,      # 安静环境
    "low_noise": 3000,  # 轻微噪声
    "medium_noise": 6000, # 中等噪声
    "high_noise": float('inf')  # 高噪声
}

def get_environment_config(noise_level):
    """
    根据噪声水平获取最佳配置
    """
    if noise_level <= NOISE_THRESHOLDS["quiet"]:
        return ENVIRONMENT_CONFIGS["quiet"]
    elif noise_level <= NOISE_THRESHOLDS["low_noise"]:
        return ENVIRONMENT_CONFIGS["low_noise"]
    elif noise_level <= NOISE_THRESHOLDS["medium_noise"]:
        return ENVIRONMENT_CONFIGS["medium_noise"]
    else:
        return ENVIRONMENT_CONFIGS["high_noise"]

def print_config_recommendations():
    """
    打印配置建议
    """
    print("唤醒词检测配置建议:")
    print("=" * 50)
    
    for env_name, config in ENVIRONMENT_CONFIGS.items():
        print(f"\n{env_name.upper()} 环境:")
        print(f"  描述: {config['description']}")
        print(f"  灵敏度: {config['sensitivity']}")
        print(f"  唤醒词: {', '.join(config['keywords'])}")
        print(f"  检测次数: {config['required_detections']}")
        print(f"  超时时间: {config['timeout']}秒")
    
    print("\n使用建议:")
    print("- 在安静环境下，可以使用高灵敏度和多个唤醒词")
    print("- 在嘈杂环境下，建议降低灵敏度并使用单一唤醒词")
    print("- 连续检测机制可以减少误触发，但会增加响应时间")
    print("- 可以根据实际使用情况调整超时时间")

if __name__ == "__main__":
    print_config_recommendations() 