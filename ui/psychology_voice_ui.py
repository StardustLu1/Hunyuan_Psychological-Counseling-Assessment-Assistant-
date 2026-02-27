# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
import threading
import sounddevice as sd
import soundfile as sf
import pyttsx3
import tempfile
import os
import numpy as np
import time
import speech_recognition as sr

from dialogue.hunyuan_client import HunyuanClient
from pipeline.psychology_pipeline import PsychologyChatPipeline


# =========================
# 麦克风选择（稳定）
# =========================
def find_microphone_device():
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if d["max_input_channels"] > 0:
            name = d["name"].lower()
            if "microphone" in name or "麦克风" in name or "array" in name or "阵列" in name:
                print(f"[Audio] 使用输入设备 {i}: {d['name']}")
                return i
    raise RuntimeError("未找到可用的麦克风设备")


class PsychologyVoiceUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("语音心理咨询")
        self.root.geometry("900x650")

        # =========================
        # 模型
        # =========================
        self.model_client = HunyuanClient(
            secret_id="",
            secret_key=""
        )
        self.chat_pipeline = PsychologyChatPipeline(self.model_client)

        # =========================
        # 音频参数
        # =========================
        self.fs = 16000
        self.device_id = find_microphone_device()

        self.recording = False
        self.audio_buffer = []

        # =========================
        # TTS 控制
        # =========================
        self.tts_lock = threading.Lock()
        self.playing = False

        self._build_ui()

    # =========================
    # UI
    # =========================
    def _build_ui(self):
        tk.Label(self.root, text="语音心理咨询",
                 font=("微软雅黑", 20, "bold")).pack(pady=10)

        tk.Label(self.root, text="按住按钮说话，松开后系统处理",
                 font=("微软雅黑", 11), fg="#555").pack()

        frame = ttk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.chat = tk.Text(frame, state="disabled", wrap="word",
                            font=("微软雅黑", 11))
        self.chat.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame, command=self.chat.yview)
        scrollbar.pack(side="right", fill="y")
        self.chat.config(yscrollcommand=scrollbar.set)

        self.volume_var = tk.DoubleVar(value=0)
        ttk.Progressbar(self.root, length=300,
                        maximum=100, variable=self.volume_var).pack(pady=5)

        self.btn = ttk.Button(self.root, text="按住说话", width=20)
        self.btn.pack(pady=10)
        self.btn.bind("<ButtonPress-1>", self.start_record)
        self.btn.bind("<ButtonRelease-1>", self.stop_record)

        self.append("咨询师", "你好，我在这里。你可以慢慢说。")

    # =========================
    # 聊天显示
    # =========================
    def append(self, role, text):
        self.chat.config(state="normal")
        color = "#2E8B57" if role == "咨询师" else "#000"
        self.chat.tag_config(role, foreground=color)
        self.chat.insert("end", f"{role}：\n{text}\n\n", role)
        self.chat.see("end")
        self.chat.config(state="disabled")

    # =========================
    # 录音
    # =========================
    def start_record(self, event=None):
        self.recording = True
        self.audio_buffer = []
        self.append("系统", "🎙 开始录音")
        self._stop_playback()

        threading.Thread(target=self._record_loop, daemon=True).start()
        threading.Thread(target=self._volume_monitor, daemon=True).start()

    def stop_record(self, event=None):
        self.recording = False
        time.sleep(0.2)

        if not self.audio_buffer:
            self.append("系统", "没有录到声音")
            return

        audio = np.concatenate(self.audio_buffer)
        rms = np.sqrt(np.mean(audio ** 2))
        if rms < 0.002:
            self.append("系统", "声音太小")
            return

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        sf.write(tmp.name, audio, self.fs)
        tmp.close()

        threading.Thread(
            target=self.process_audio,
            args=(tmp.name,),
            daemon=True
        ).start()

    def _record_loop(self):
        with sd.InputStream(
            samplerate=self.fs,
            channels=1,
            device=self.device_id,
            dtype="float32"
        ) as stream:
            while self.recording:
                data, _ = stream.read(1024)
                self.audio_buffer.append(data.copy())

    def _volume_monitor(self):
        while self.recording:
            if self.audio_buffer:
                vol = np.sqrt(np.mean(self.audio_buffer[-1] ** 2))
                self.root.after(0, self.volume_var.set,
                                min(int(vol * 5000), 100))
            time.sleep(0.1)
        self.root.after(0, self.volume_var.set, 0)

    # =========================
    # 稳定 TTS（核心）
    # =========================
    def _stop_playback(self):
        with self.tts_lock:
            sd.stop()
            self.playing = False

    def _play_tts(self, text):
        threading.Thread(
            target=self._tts_worker,
            args=(text,),
            daemon=True
        ).start()

    def _tts_worker(self, text):
        with self.tts_lock:
            self.playing = True

        # 生成临时 wav
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp.close()

        engine = pyttsx3.init()
        engine.setProperty("rate", 165)
        engine.setProperty("volume", 1.0)

        engine.save_to_file(text, tmp.name)
        engine.runAndWait()
        engine.stop()

        data, fs = sf.read(tmp.name, dtype="float32")
        os.remove(tmp.name)

        sd.play(data, fs)
        sd.wait()

        with self.tts_lock:
            self.playing = False

    # =========================
    # ASR + AI
    # =========================
    def process_audio(self, wav_path):
        self.append("系统", "正在识别语音...")

        try:
            r = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio = r.record(source)
                user_text = r.recognize_google(audio, language="zh-CN")
        except Exception as e:
            self.append("系统", f"语音识别失败: {e}")
            return
        finally:
            os.remove(wav_path)

        if not user_text.strip():
            self.append("系统", "未识别到有效语音内容")
            return

        self.append("你", user_text)

        ai_text = self.chat_pipeline.chat(user_text)
        self.append("咨询师", ai_text)
        self._play_tts(ai_text)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    PsychologyVoiceUI().run()

