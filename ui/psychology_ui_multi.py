# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import scrolledtext, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import json
import random
import threading
import time
from collections import deque, Counter

import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import tensorflow as tf

from pipeline.psychology_pipeline import PsychologyPipeline
from dialogue.hunyuan_client import HunyuanClient

import os

# ===========================
# 路径统一管理（核心）
# ===========================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))          # Graduation project/ui
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))  # Graduation project

# ---------------------------
# 1. 初始化混元客户端
# ---------------------------
model_client = HunyuanClient(
    secret_id="AKIDJVVJuHQM4ZrvmPo24BLI1XqvnY7Silbw",
    secret_key="GMFxc6NRM4bv25z86xHYcWFnBQWR8bzA"
)

# ---------------------------
# 2. 初始化心理分析流水线
# ---------------------------
psychology_pipeline = PsychologyPipeline(
    model_client=model_client
)

# ---------------------------
# 3. 加载题库（与 UI 同目录）
# ---------------------------
QUESTION_PATH = os.path.join(CURRENT_DIR, "question_bank.json")
if not os.path.exists(QUESTION_PATH):
    raise FileNotFoundError(f"未找到题库文件: {QUESTION_PATH}")

with open(QUESTION_PATH, "r", encoding="utf-8") as f:
    QUESTION_BANK = json.load(f)["question_bank"]

def get_random_questions(num_questions=40):
    if num_questions > len(QUESTION_BANK):
        num_questions = len(QUESTION_BANK)
    return random.sample(QUESTION_BANK, k=num_questions)

# ---------------------------
# 4. 表情识别模型（修正路径）
# ---------------------------
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "emotion_model.h5")
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"未找到表情模型文件: {MODEL_PATH}")

emotion_model = tf.keras.models.load_model(MODEL_PATH)

EMOTION_LABELS = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']

# ---------------------------
# 5. 分页答题 UI
# ---------------------------
class QuizUI:
    def __init__(self, master=None, num_questions=40, page_size=10):
        if master:
            self.root = tb.Toplevel(master)
            self.root.title("心理测评问卷")
        else:
            self.root = tb.Window(
                themename="flatly",
                title="心理测评问卷",
                size=(1100, 900)
            )

        self.root.resizable(False, False)

        self.questions = get_random_questions(num_questions)
        self.page_size = page_size
        self.current_page = 0
        self.answers = {}
        self.vars = []

        # 表情采集
        self.emotion_queue = deque(maxlen=10)
        self.current_emotion = tk.StringVar(value="neutral")

        # UI
        self.create_widgets()
        self.show_page(0)

        # 摄像头线程
        self.capture_thread = threading.Thread(
            target=self.start_emotion_capture,
            daemon=True
        )
        self.capture_thread.start()

        # 表情统计刷新
        self.update_emotion_display()

    def create_widgets(self):
        self.title_label = tb.Label(
            self.root,
            text="心理测评问卷",
            font=("Arial", 18, "bold")
        )
        self.title_label.pack(pady=10)

        self.q_frame = tb.Frame(self.root)
        self.q_frame.pack(fill=BOTH, expand=True, padx=20, pady=5)

        btn_frame = tb.Frame(self.root)
        btn_frame.pack(pady=10)

        self.prev_btn = tb.Button(
            btn_frame,
            text="上一页",
            bootstyle="secondary-outline",
            command=self.prev_page
        )
        self.prev_btn.grid(row=0, column=0, padx=5)

        self.next_btn = tb.Button(
            btn_frame,
            text="下一页",
            bootstyle="secondary-outline",
            command=self.next_page
        )
        self.next_btn.grid(row=0, column=1, padx=5)

        self.submit_btn = tb.Button(
            btn_frame,
            text="提交问卷",
            bootstyle="success-outline",
            command=self.submit_quiz
        )
        self.submit_btn.grid(row=0, column=2, padx=5)

        self.output = scrolledtext.ScrolledText(
            self.root,
            width=120,
            height=50
        )
        self.output.pack(padx=10, pady=10)

        # 表情统计窗口
        self.stats_win = tk.Toplevel(self.root)
        self.stats_win.title("表情统计")

        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.stats_win)
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=True)

    def show_page(self, page_idx):
        for widget in self.q_frame.winfo_children():
            widget.destroy()
        self.vars.clear()

        start_idx = page_idx * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.questions))

        for idx, q in enumerate(self.questions[start_idx:end_idx]):
            tb.Label(
                self.q_frame,
                text=f"{start_idx + idx + 1}. {q['text']}",
                wraplength=850,
                justify="left"
            ).grid(row=idx * 2, column=0, sticky="w", pady=2)

            var = tk.StringVar(value=self.answers.get(q["id"], "0"))
            self.vars.append((q["id"], var))

            for opt_idx, opt_text in enumerate(q["options"]):
                tb.Radiobutton(
                    self.q_frame,
                    text=opt_text,
                    variable=var,
                    value=str(opt_idx)
                ).grid(row=idx * 2 + 1, column=opt_idx, padx=5, sticky="w")

        self.prev_btn.config(state=NORMAL if page_idx > 0 else DISABLED)
        self.next_btn.config(state=NORMAL if end_idx < len(self.questions) else DISABLED)

    def save_current_page_answers(self):
        for qid, var in self.vars:
            self.answers[qid] = var.get()

    def next_page(self):
        self.save_current_page_answers()
        self.current_page += 1
        self.show_page(self.current_page)

    def prev_page(self):
        self.save_current_page_answers()
        self.current_page -= 1
        self.show_page(self.current_page)

    def start_emotion_capture(self):
        cap = cv2.VideoCapture(0)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                face_img = gray[y:y + h, x:x + w]
                face_img = cv2.resize(face_img, (48, 48))
                face_img = face_img.astype("float32") / 255.0
                face_img = np.expand_dims(face_img, axis=(0, -1))

                preds = emotion_model.predict(face_img, verbose=0)
                emotion = EMOTION_LABELS[np.argmax(preds)]
                self.emotion_queue.append(emotion)

            time.sleep(1)

    def update_emotion_display(self):
        if self.emotion_queue:
            counter = Counter(self.emotion_queue)
            self.ax.clear()
            emotions = EMOTION_LABELS
            counts = [counter.get(e, 0) for e in emotions]
            self.ax.plot(emotions, counts, marker='o')
            self.ax.set_title("表情统计（滑动窗口）")
            self.ax.set_ylabel("次数")
            self.ax.set_ylim(0, max(counts) + 1)
            self.canvas.draw()

        self.root.after(2000, self.update_emotion_display)

    def submit_quiz(self):
        self.save_current_page_answers()
        answers_dict = {qid: int(v) for qid, v in self.answers.items()}
        emotion_list = list(self.emotion_queue)

        try:
            result = psychology_pipeline.run(
                scale_name="综合心理测评",
                answers=answers_dict,
                emotion_list=emotion_list
            )
        except Exception as e:
            messagebox.showerror("错误", str(e))
            return

        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, f"量表评分: {result.get('scale_result')}\n")
        self.output.insert(tk.END, f"综合风险: {result.get('overall_risk')}\n")
        self.output.insert(tk.END, f"表情统计: {result.get('emotion_summary')}\n")
        self.output.insert(tk.END, "-" * 50 + "\n")
        self.output.insert(tk.END, result.get('response'))

# ---------------------------
# 6. 主入口
# ---------------------------
if __name__ == "__main__":
    app = QuizUI(None)
    app.root.mainloop()
