# Graduation project/config.py
# -*- coding: utf-8 -*-

# -----------------------
# 1. 混元客户端配置
# -----------------------
HUNYUAN_CREDENTIAL = {
    "secret_id": "AKIDJVVJuHQM4ZrvmPo24BLI1XqvnY7Silbw",
    "secret_key": "GMFxc6NRM4bv25z86xHYcWFnBQWR8bzA",
    "region": "ap-guangzhou"
}

# -----------------------
# 2. FastAPI Web 配置
# -----------------------
WEB_HOST = "0.0.0.0"
WEB_PORT = 8000
WEB_RELOAD = True

# -----------------------
# 3. 默认量表
# -----------------------
DEFAULT_SCALE = "PHQ-9"

# -----------------------
# 4. YOLO 模型路径（如仍使用图像识别模块）
# -----------------------
YOLO_MODEL_PATH = "/runs/train/school_logo_yolov124/weights/best.pt"
