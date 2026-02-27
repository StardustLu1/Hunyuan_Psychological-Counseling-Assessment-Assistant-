# psychology_ui_multi.py
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import random

from pipeline.psychology_pipeline import PsychologyPipeline
from dialogue.hunyuan_client import HunyuanClient

# ---------------------------
# 1. 初始化混元客户端
# ---------------------------
model_client = HunyuanClient(
    secret_id="",
    secret_key=""
)

# ---------------------------
# 2. 初始化心理分析流水线
# ---------------------------
psychology_pipeline = PsychologyPipeline(
    model_client=model_client
)

# ---------------------------
# 3. 加载题库
# ---------------------------
with open("question_bank.json", "r", encoding="utf-8") as f:
    QUESTION_BANK = json.load(f)["question_bank"]  # ✅ 对应你的 JSON 顶层 key

def get_random_questions(num_questions=40):
    if num_questions > len(QUESTION_BANK):
        num_questions = len(QUESTION_BANK)
    return random.sample(QUESTION_BANK, k=num_questions)

# ---------------------------
# 4. 分页答题 UI
# ---------------------------
class QuizUI:
    def __init__(self, root, num_questions=40, page_size=10):
        self.root = root
        self.root.title("心理测评问卷")
        self.root.geometry("900x700")

        self.questions = get_random_questions(num_questions)
        self.page_size = page_size
        self.current_page = 0
        self.answers = {}
        self.vars = []

        self.create_widgets()
        self.show_page(0)

    def create_widgets(self):
        self.title_label = ttk.Label(
            self.root, text="心理测评问卷", font=("Arial", 16, "bold")
        )
        self.title_label.pack(pady=10)

        self.q_frame = ttk.Frame(self.root)
        self.q_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.prev_btn = ttk.Button(btn_frame, text="上一页", command=self.prev_page)
        self.prev_btn.grid(row=0, column=0, padx=5)

        self.next_btn = ttk.Button(btn_frame, text="下一页", command=self.next_page)
        self.next_btn.grid(row=0, column=1, padx=5)

        self.submit_btn = ttk.Button(btn_frame, text="提交问卷", command=self.submit_quiz)
        self.submit_btn.grid(row=0, column=2, padx=5)

        self.output = scrolledtext.ScrolledText(self.root, width=100, height=15)
        self.output.pack(padx=10, pady=10)

    def show_page(self, page_idx):
        for widget in self.q_frame.winfo_children():
            widget.destroy()
        self.vars.clear()

        start_idx = page_idx * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.questions))
        page_questions = self.questions[start_idx:end_idx]

        for idx, q in enumerate(page_questions):
            q_label = ttk.Label(
                self.q_frame,
                text=f"{start_idx + idx + 1}. {q['text']}",
                wraplength=800
            )
            q_label.grid(row=idx * 2, column=0, sticky="w", pady=2)

            var = tk.StringVar(value=self.answers.get(q["id"], "0"))
            self.vars.append((q["id"], var))

            for opt_idx, opt_text in enumerate(q["options"]):
                rb = ttk.Radiobutton(
                    self.q_frame,
                    text=opt_text,
                    variable=var,
                    value=str(opt_idx)
                )
                rb.grid(row=idx * 2 + 1, column=opt_idx, padx=5, sticky="w")

        self.prev_btn.config(state=tk.NORMAL if page_idx > 0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if end_idx < len(self.questions) else tk.DISABLED)

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

    def submit_quiz(self):
        self.save_current_page_answers()

        # 将答案字典转换成整数
        answers_dict = {
            qid: int(val)
            for qid, val in self.answers.items()
        }

        try:
            result = psychology_pipeline.run(
                scale_name="综合心理测评",
                answers=answers_dict
            )
        except Exception as e:
            messagebox.showerror("错误", f"生成心理分析失败:\n{str(e)}")
            return

        # 输出结果到文本框
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, f"量表评分: {result['scale_result']}\n")
        self.output.insert(tk.END, f"综合风险: {result['overall_risk']}\n")
        self.output.insert(tk.END, "-" * 50 + "\n")
        self.output.insert(tk.END, f"心理咨询回复:\n{result['response']}\n")

# ---------------------------
# 5. 运行界面
# ---------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = QuizUI(root, num_questions=40, page_size=10)
    root.mainloop()

