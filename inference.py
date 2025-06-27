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
from PIL import Image


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
            return "Drowsy" if pred == 0 else "Awake"
    except Exception as e:
        print("ViT did the wrong classification：", e)
        return "Unknown"


def drowsy_test(yolo_weight_path, vit_model_path):

    yolo_model = YOLO(yolo_weight_path)
    yolo_model.to(device).eval()

    vit_model = load_vit_model(vit_model_path)

    # cap = cv2.VideoCapture(0)   # windows
    cap = cv2.VideoCapture(1, cv2.CAP_AVFOUNDATION)     # macOS
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
                x1, y1, x2, y2 = map(int, box[:4])
                face_crop = frame[y1:y2, x1:x2]
                if face_crop.size == 0:
                    continue

                label = classify_with_vit(vit_model, face_crop)

                color = (0, 255, 0) if label == "Awake" else (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        cv2.imshow('YOLO + ViT Real-Time Drowsy-detection', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    yolo_weight = r"/Users/lai/PycharmProjects/vehicleSystem/MCs/runs/detect/train/weights/best.pt"
    vit_weight = r"/Users/lai/PycharmProjects/vehicleSystem/MCs/checkpoints/best.pth"
    drowsy_test(yolo_weight, vit_weight)

