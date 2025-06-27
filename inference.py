#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
   Name:         inference
   Description:  
   Author:       longnightyouno
   Email:        1986577242@qq.com/ longnightyouno@gamil.com
   Date:           2025/6/25
-------------------------------------------------------------------------------
   Change Activity:
                 2025/6/25
"""

__author__ = "AaLai"
__version__ = "1.0.0"

from ultralytics import YOLO
import cv2
import torch
import torch.nn as nn
from torchvision import transforms
from torchvision.models import vit_b_16
from PIL import Image, ImageFont, ImageDraw
from collections import deque, Counter
import os
import numpy as np
import time


def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")
    else:
        return torch.device("cpu")


device = get_device()
print("Device:", device)


def load_vit_model(vit_path):
    model = vit_b_16(weights=None)
    model.heads = nn.Linear(model.heads.head.in_features, 2)
    model.load_state_dict(torch.load(vit_path, map_location=device))
    model.to(device)
    model.eval()
    return model


vit_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])


def classify_with_vit(vit_model, face_img_np):
    try:
        face_pil = Image.fromarray(cv2.cvtColor(face_img_np, cv2.COLOR_BGR2RGB))
        input_tensor = vit_transform(face_pil).unsqueeze(0).to(device)
        with torch.no_grad():
            output = vit_model(input_tensor)
            pred = torch.argmax(output, dim=1).item()
            return "Dangerous Driving" if pred == 0 else "Safe Driving"
    except Exception as e:
        print("ViT did the wrong classification：", e)
        return "Unknown"


state_window = deque(maxlen=10)
previous_status = None  # used for state update


def state_update(new_state, window=state_window):
    """ 驾驶状态更新 """
    global previous_status

    window.append(new_state)

    if len(window) < window.maxlen:
        return "os is Initializing now...", (255, 255, 255)

    counter = Counter(window)

    if counter["Dangerous Driving"] >= 7:
        current_status = "危险驾驶"
        alert_text = "注意！注意！检测到危险驾驶！"
    elif counter["Safe Driving"] >= 7:
        current_status = "安全驾驶"
        alert_text = "当前为安全驾驶状态。"
    elif counter["Unknown"] >= 5:
        current_status = "状态异常"
        alert_text = "当前检测异常，请调整姿态。"
    else:
        current_status = "状态不稳定"
        alert_text = "检测状态不稳定"

    if current_status != previous_status:
        print(current_status)
        os.system(f"say {alert_text}")  # macOS voice announcement
        previous_status = current_status

    if current_status == "危险驾驶":
        state_color = (0, 0, 255)  # red
        return current_status, state_color
    elif current_status == "安全驾驶":
        state_color = (0, 255, 0)  # green
        return current_status, state_color
    else:
        state_color = (255, 255, 255)  # white
        return current_status, state_color

    return current_status, state_color


def draw_chinese_text(img, text, pos=(10, 20), font_size=30, color=(255, 255, 255)):
    """ 状态显示 """
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    font_path = r"/Users/lai/PycharmProjects/vehicleSystem/MCs/STHeiti Medium.ttc"  # macOS preChinese-font
    font = ImageFont.truetype(font_path, font_size)
    draw.text(pos, text, font=font, fill=color)
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


fps_text = 0
def drowsy_test(yolo_weight_path, vit_model_path):
    """ YOLO11 + ViT """
    yolo_model = YOLO(yolo_weight_path)
    yolo_model.to(device).eval()

    vit_model = load_vit_model(vit_model_path)

    # cap = cv2.VideoCapture(0)   # windows
    cap = cv2.VideoCapture(1, cv2.CAP_AVFOUNDATION)     # macOS
    prev_time = time.time()
    frame_count = 0
    global fps_text
    if not cap.isOpened():
        print("can not open the webcam")
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("read frame get wrongs")
            break

        frame = cv2.flip(frame, 1)
        results = yolo_model(frame)

        if results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()  # x1, y1, x2, y2

            for box in boxes:
                frame_count += 1
                current_time = time.time()
                elapsed = current_time - prev_time

                if elapsed >= 1.0:  # update by second
                    fps = frame_count / elapsed
                    fps_text = f"FPS: {fps:.2f}"
                    prev_time = current_time
                    frame_count = 0

                # x1, y1, x2, y2 = map(int, box[:4])
                # face_crop = frame[y1:y2, x1:x2]
                # if face_crop.size == 0:
                #     continue
                #
                # label = classify_with_vit(vit_model, face_crop)
                #
                # color = (0, 255, 0) if label == "Safe Driving" else (0, 0, 255)
                # cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                # cv2.putText(frame, label, (x1, y1 - 10),
                #             cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

                x1, y1, x2, y2 = map(int, box[:4])
                face_crop = frame[y1:y2, x1:x2]
                if face_crop.size == 0:
                    continue

                label = classify_with_vit(vit_model, face_crop)
                current_state, state_color = state_update(label)  # update state and voice announcement

                # color = (0, 255, 0) if label == "Safe Driving" else (0, 0, 255)
                # cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                # cv2.putText(frame, label, (x1, y1 - 10),
                #             cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

                # 把状态显示在图像左上角
                # cv2.putText(frame, current_state, (10, 30),
                #             cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                frame = draw_chinese_text(frame, current_state, color=state_color)

        cv2.putText(frame, fps_text, (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 0), 2)

        cv2.imshow('YOLO + ViT Real-Time Drowsy-detection', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    yolo_weight = r"/Users/lai/PycharmProjects/vehicleSystem/MCs/runs/detect/train/weights/best.pt"
    vit_weight = r"/Users/lai/PycharmProjects/vehicleSystem/MCs/checkpoints/new_best.pth"
    drowsy_test(yolo_weight, vit_weight)

