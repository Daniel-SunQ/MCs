#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
   Name:         inference
   Description:  YOLO + ViT drowsy detection with performance optimization
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
import numpy as np
import time


def get_device():
    """ device selection """
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")
    else:
        return torch.device("cpu")


device = get_device()
print("Device:", device)


def load_vit_model(vit_path):
    """ load vit model """
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
    """ classification with vit model """
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


# =============== state tracking =================
state_window = deque(maxlen=10)
previous_status = None  # used for state update


def state_update(new_state):
    """ 驾驶状态更新 """
    global previous_status

    state_window.append(new_state)

    if len(state_window) < state_window.maxlen:
        return "os is Initializing now...", (255, 255, 255)

    counter = Counter(state_window)

    if counter["Dangerous Driving"] >= 7:
        current_status, color, alert = "危险驾驶", (0, 0, 255), "注意！注意！危险驾驶!"
    elif counter["Safe Driving"] >= 7:
        current_status, color, alert = "安全驾驶", (0, 255, 0), "当前为安全驾驶"
    elif counter["Unknown"] >= 5:
        current_status, color, alert = "状态异常", (255, 255, 255), "检测异常，请调整姿态"
    else:
        current_status, color, alert = "状态不稳定", (255, 255, 255), "检测状态不稳定"

    if current_status != previous_status:
        previous_status = current_status

    return current_status, color


def draw_chinese_text(img, text, pos=(10, 20), font_size=30, color=(255, 255, 255)):
    """ 状态显示 """
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    font_path = r"/Users/lai/PycharmProjects/vehicleSystem/MCs/STHeiti Medium.ttc"  # macOS preChinese-font
    font = ImageFont.truetype(font_path, font_size)
    draw.text(pos, text, font=font, fill=color)
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


# ================== main detection ==================
def drowsy_test(yolo_weight_path, vit_model_path, frame_skip, input_resize):
    """ YOLO11 + ViT """
    yolo_model = YOLO(yolo_weight_path)
    yolo_model.to(device).eval()

    vit_model = load_vit_model(vit_model_path)

    # cap = cv2.VideoCapture(0)   # windows
    cap = cv2.VideoCapture(1, cv2.CAP_AVFOUNDATION)     # macOS
    if not cap.isOpened():
        print("can not open the webcam")
        return

    frame_count, fps, start_time = 0, 0, time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("read frame get wrongs")
            break

        frame = cv2.flip(frame, 1)  # mirror the image
        frame_count += 1

        if frame_count % frame_skip != 0:
            continue

        resized_frame = cv2.resize(frame, (input_resize, input_resize))
        results = yolo_model(resized_frame)

        label = "Unknown"
        if results[0].boxes is not None:
            for box in results[0].boxes.xyxy.cpu().numpy():
                x1, y1, x2, y2 = map(int, box[:4])
                scale_x = frame.shape[1] / input_resize
                scale_y = frame.shape[0] / input_resize
                x1, x2 = int(x1 * scale_x), int(x2 * scale_x)
                y1, y2 = int(y1 * scale_y), int(y2 * scale_y)
                face_crop = frame[y1:y2, x1:x2]
                if face_crop.size != 0:
                    label = classify_with_vit(vit_model, face_crop)
                    break

        current_state, state_color = state_update(label)  # update state

        elapsed = time.time() - start_time
        fps = frame_count / elapsed

        frame = draw_chinese_text(frame, f"{current_state} | FPS: {fps:.2f}", color=state_color)

        cv2.imshow('YOLO + ViT Real-Time Drowsy-detection', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    yolo_weight = r"/Users/lai/PycharmProjects/vehicleSystem/MCs/runs/detect/train/weights/best.pt"
    vit_weight = r"/Users/lai/PycharmProjects/vehicleSystem/MCs/checkpoints/new_best.pth"
    drowsy_test(yolo_weight, vit_weight, frame_skip=1, input_resize=780)

