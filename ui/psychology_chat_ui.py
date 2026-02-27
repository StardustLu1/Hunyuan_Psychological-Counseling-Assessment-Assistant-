# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox

from dialogue.hunyuan_client import HunyuanClient
from pipeline.psychology_pipeline import PsychologyChatPipeline


class PsychologyChatUI:
    """
    在线心理咨询 UI
    只负责：
    - 聊天窗口展示
    - 用户输入
    - 调用 PsychologyChatPipeline
    """

    def __init__(self, master=None):
        self.root = master or tk.Tk()
        self.root.title("在线心理咨询")
        self.root.geometry("1000x800")

        # =========================
        # 初始化模型与流水线
        # =========================
        try:
            self.model_client = HunyuanClient(
                secret_id="AKIDJVVJuHQM4ZrvmPo24BLI1XqvnY7Silbw",
                secret_key="GMFxc6NRM4bv25z86xHYcWFnBQWR8bzA"
            )
            self.chat_pipeline = PsychologyChatPipeline(self.model_client)
        except Exception as e:
            messagebox.showerror(
                "初始化失败",
                f"混元模型初始化失败：\n{e}"
            )
            raise

        self._build_ui()

    # =========================
    # UI 构建
    # =========================
    def _build_ui(self):
        # -------- 顶部标题 --------
        title = tk.Label(
            self.root,
            text="在线心理咨询",
            font=("微软雅黑", 20, "bold")
        )
        title.pack(pady=10)

        # -------- 快捷问题区 --------
        quick_frame = ttk.LabelFrame(self.root, text="常见心理困扰（可直接点击）")
        quick_frame.pack(fill="x", padx=10, pady=5)

        quick_questions = [
            "我最近学习 / 工作压力很大",
            "我总是感到焦虑、紧张",
            "最近情绪低落，对什么都提不起兴趣",
            "晚上睡不着，白天没精神",
            "人际关系让我很困扰",
            "我对未来感到迷茫"
        ]

        for q in quick_questions:
            btn = ttk.Button(
                quick_frame,
                text=q,
                command=lambda text=q: self._fill_input(text)
            )
            btn.pack(side="left", padx=5, pady=5)

        # -------- 聊天显示区 --------
        chat_frame = ttk.Frame(self.root)
        chat_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.chat_display = tk.Text(
            chat_frame,
            state="disabled",
            wrap="word",
            font=("微软雅黑", 11)
        )
        self.chat_display.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            chat_frame,
            orient="vertical",
            command=self.chat_display.yview
        )
        scrollbar.pack(side="right", fill="y")

        self.chat_display.config(yscrollcommand=scrollbar.set)

        # -------- 输入区 --------
        input_frame = ttk.Frame(self.root)
        input_frame.pack(fill="x", padx=10, pady=5)

        self.input_box = tk.Entry(
            input_frame,
            font=("微软雅黑", 12)
        )
        self.input_box.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.input_box.bind("<Return>", self._on_send)

        send_btn = ttk.Button(
            input_frame,
            text="发送",
            width=8,
            command=self._on_send
        )
        send_btn.pack(side="right")

        # -------- 底部操作区 --------
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill="x", padx=10, pady=5)

        reset_btn = ttk.Button(
            bottom_frame,
            text="开始新的咨询",
            command=self._reset_chat
        )
        reset_btn.pack(side="right")

        # -------- 初始提示 --------
        self._append_message(
            "咨询师",
            "你好，我是你的心理咨询助手 😊\n\n"
            "你可以：\n"
            "• 点击上方的【常见心理困扰】快速开始\n"
            "• 或直接在下方输入你想倾诉的内容\n\n"
            "我会尽力给你温和、专业的回应。"
        )

    # =========================
    # 交互逻辑
    # =========================
    def _fill_input(self, text: str):
        """点击快捷问题，填充输入框"""
        self.input_box.delete(0, tk.END)
        self.input_box.insert(0, text)
        self.input_box.focus()

    def _on_send(self, event=None):
        user_text = self.input_box.get().strip()
        if not user_text:
            return

        self.input_box.delete(0, tk.END)

        # 先显示用户消息，再回调发送给AI
        self._append_message("你", user_text, callback=lambda: self._send_ai_response(user_text))

    def _send_ai_response(self, user_text):
        try:
            # 将用户真实输入传给心理咨询流水线
            response = self.chat_pipeline.chat(user_text)
            # 显示AI回复
            self._append_message("咨询师", response)
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("错误", f"咨询过程中出现问题：\n{e}")

    def _append_message(self, role: str, text: str, callback=None):
        """
        在聊天框中显示消息，逐字生成（打字机效果）
        callback: 显示完成后执行的函数
        """
        self.chat_display.config(state="normal")

        # 设置颜色
        if role == "咨询师":
            color = "#2E8B57"  # 深绿色
        else:
            color = "#000000"  # 黑色

        tag = role
        self.chat_display.tag_config(tag, foreground=color, font=("微软雅黑", 11))

        # 插入角色前缀+换行
        self.chat_display.insert("end", f"{role}：\n", tag)
        self.chat_display.see("end")

        # 打字机逐字显示
        def typewriter(index=0):
            if index < len(text):
                self.chat_display.insert("end", text[index], tag)
                self.chat_display.see("end")
                self.root.after(15, lambda: typewriter(index + 1))
            else:
                # 消息完成后换两行，分隔下一条消息
                self.chat_display.insert("end", "\n\n")
                self.chat_display.see("end")
                self.chat_display.config(state="disabled")
                # 执行回调（比如发送AI回复）
                if callback:
                    callback()

        typewriter()

    def _reset_chat(self):
        """重置对话"""
        if messagebox.askyesno("确认", "确定要开始新的咨询吗？当前对话将被清空。"):
            try:
                self.chat_pipeline.reset()
            except Exception:
                pass

            self.chat_display.config(state="normal")
            self.chat_display.delete("1.0", tk.END)
            self.chat_display.config(state="disabled")

            self._append_message(
                "咨询师",
                "好的，我们重新开始吧。\n你现在最想聊的是什么？"
            )

    # =========================
    # 启动
    # =========================
    def run(self):
        self.root.mainloop()


# -----------------------------
# 独立运行测试
# -----------------------------
if __name__ == "__main__":
    app = PsychologyChatUI()
    app.run()
