# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import json
import hashlib
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox

# ==============================
# 统一资源路径管理
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path):
    """
    获取资源文件的绝对路径
    relative_path: 相对于项目根目录 finalwork2 的路径
    """
    if hasattr(sys, "_MEIPASS"):
        # 打包 exe 后使用临时目录
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(BASE_DIR, relative_path)

# JSON 数据库
USER_DB = resource_path("ui/users.json")
QUESTION_BANK = resource_path("ui/question_bank.json")
# H5 模型路径
PSYCH_MODEL = resource_path("models/psych_model.h5")
EMOTION_MODEL = resource_path("models/emotion_model.h5")

# -----------------------------
# 用户数据操作
# -----------------------------
def load_users():
    os.makedirs(os.path.dirname(USER_DB), exist_ok=True)
    if not os.path.exists(USER_DB):
        with open(USER_DB, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(USER_DB, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    os.makedirs(os.path.dirname(USER_DB), exist_ok=True)
    with open(USER_DB, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# -----------------------------
# 主界面类
# -----------------------------
class PsychologyMainUI:
    """
    心理健康支持系统（现代美化版）
    - 登录界面（学号+密码，注册、找回密码）
    - 主界面 Launcher（心理测评、在线咨询、语音聊天室）
    """

    def __init__(self):
        self.root = tb.Window(
            title="心理健康咨询系统",
            size=(900, 600),
            themename="flatly",
            resizable=(False, False)
        )
        self._show_login()

    # -----------------------------
    # 登录界面
    # -----------------------------
    def _show_login(self):
        self.login_frame = tb.Frame(self.root, padding=40)
        self.login_frame.place(relx=0.5, rely=0.5, anchor=CENTER)

        tb.Label(self.login_frame, text="心理健康咨询系统", font=("微软雅黑", 28, "bold")).pack(pady=(0, 15))
        tb.Label(self.login_frame, text="请登录后使用系统", font=("微软雅黑", 14), bootstyle="secondary").pack(pady=(0, 20))

        form = tb.Frame(self.login_frame)
        form.pack(pady=10)
        tb.Label(form, text="学号：", width=12, anchor="e").grid(row=0, column=0, pady=6)
        tb.Label(form, text="密码：", width=12, anchor="e").grid(row=1, column=0, pady=6)

        self.username_var = tb.StringVar()
        self.password_var = tb.StringVar()

        tb.Entry(form, textvariable=self.username_var, width=30).grid(row=0, column=1, pady=6)
        tb.Entry(form, textvariable=self.password_var, width=30, show="*").grid(row=1, column=1, pady=6)

        btn_frame = tb.Frame(self.login_frame)
        btn_frame.pack(pady=10)
        tb.Button(btn_frame, text="登 录", bootstyle="success", width=22, command=self._login).grid(row=0, column=0, padx=5)
        tb.Button(btn_frame, text="注册账号", bootstyle="info-outline", width=22, command=self._register).grid(row=0, column=1, padx=5)
        tb.Button(btn_frame, text="找回密码", bootstyle="warning-outline", width=22, command=self._reset_password).grid(row=0, column=2, padx=5)

        tb.Label(self.login_frame, text="※ 本系统仅用于教学演示与心理健康辅助", font=("微软雅黑", 10), bootstyle="secondary").pack(pady=10)

    # -----------------------------
    # 登录校验
    # -----------------------------
    def _login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        users = load_users()
        if username in users and users[username]["password"] == hash_password(password):
            messagebox.showinfo("成功", f"学号 {username} 登录成功")
            self.login_frame.destroy()
            self._build_main_ui()
        else:
            messagebox.showerror("登录失败", "学号不存在或密码错误")

    # -----------------------------
    # 注册账号
    # -----------------------------
    def _register(self):
        win = tb.Toplevel(self.root)
        win.title("注册账号")
        win.geometry("450x350")
        win.resizable(False, False)

        tb.Label(win, text="注册新账号", font=("微软雅黑", 16, "bold")).pack(pady=10)
        frm = tb.Frame(win)
        frm.pack(pady=10)

        tb.Label(frm, text="学号:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        entry_user = tb.Entry(frm)
        entry_user.grid(row=0, column=1, padx=5, pady=5)

        tb.Label(frm, text="手机号/邮箱:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        entry_phone = tb.Entry(frm)
        entry_phone.grid(row=1, column=1, padx=5, pady=5)

        tb.Label(frm, text="密码:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        entry_pass = tb.Entry(frm, show="*")
        entry_pass.grid(row=2, column=1, padx=5, pady=5)

        tb.Label(frm, text="确认密码:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        entry_confirm = tb.Entry(frm, show="*")
        entry_confirm.grid(row=3, column=1, padx=5, pady=5)

        def do_register():
            user = entry_user.get().strip()
            phone = entry_phone.get().strip()
            pwd = entry_pass.get().strip()
            confirm = entry_confirm.get().strip()

            if not user or not pwd or not phone:
                messagebox.showerror("错误", "学号、手机号/邮箱和密码不能为空")
                return
            if pwd != confirm:
                messagebox.showerror("错误", "两次密码输入不一致")
                return

            users = load_users()
            if user in users:
                messagebox.showerror("错误", "学号已存在")
                return
            users[user] = {"password": hash_password(pwd), "contact": phone}
            save_users(users)
            messagebox.showinfo("成功", f"学号 {user} 注册成功")
            win.destroy()

        tb.Button(win, text="注册", bootstyle="success-outline", width=25, command=do_register).pack(pady=10)

    # -----------------------------
    # 找回密码（手机号/邮箱验证模式）
    # -----------------------------
    def _reset_password(self):
        win = tb.Toplevel(self.root)
        win.title("找回密码")
        win.geometry("500x380")
        win.resizable(False, False)

        tb.Label(win, text="找回密码", font=("微软雅黑", 18, "bold")).pack(pady=15)

        frm = tb.Frame(win)
        frm.pack(pady=10)

        tb.Label(frm, text="学号:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        entry_user = tb.Entry(frm, width=30)
        entry_user.grid(row=0, column=1, padx=5, pady=5)

        tb.Label(frm, text="手机号/邮箱:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        entry_contact = tb.Entry(frm, width=30)
        entry_contact.grid(row=1, column=1, padx=5, pady=5)

        # 验证码 + 新密码
        code_var = tb.StringVar()
        new_pwd_var = tb.StringVar()

        tb.Label(frm, text="验证码:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        entry_code = tb.Entry(frm, textvariable=code_var, width=30, state="disabled")
        entry_code.grid(row=2, column=1, padx=5, pady=5)

        tb.Label(frm, text="新密码:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        entry_new_pwd = tb.Entry(frm, textvariable=new_pwd_var, show="*", width=30, state="disabled")
        entry_new_pwd.grid(row=3, column=1, padx=5, pady=5)

        # 重置按钮
        btn_reset = tb.Button(frm, text="重置密码", bootstyle="warning-outline", width=22, state="disabled")
        btn_reset.grid(row=5, column=0, columnspan=2, pady=15)

        def send_code():
            user = entry_user.get().strip()
            contact = entry_contact.get().strip()
            users = load_users()
            if not user or not contact:
                messagebox.showerror("错误", "学号和手机号/邮箱不能为空")
                return
            if user not in users:
                messagebox.showerror("错误", "学号不存在")
                return
            if users[user]["contact"] != contact:
                messagebox.showerror("错误", "手机号/邮箱与注册信息不匹配")
                return
            code_var.set("123456")
            messagebox.showinfo("验证码发送", "验证码已发送（本地模拟123456）")
            entry_code.config(state="normal")
            entry_new_pwd.config(state="normal")
            btn_reset.config(state="normal")

        def do_reset():
            user = entry_user.get().strip()
            code = entry_code.get().strip()
            new_pwd = entry_new_pwd.get().strip()
            if code != code_var.get():
                messagebox.showerror("错误", "验证码错误")
                return
            if not new_pwd:
                messagebox.showerror("错误", "新密码不能为空")
                return
            users = load_users()
            users[user]["password"] = hash_password(new_pwd)
            save_users(users)
            messagebox.showinfo("成功", f"学号 {user} 密码已重置")
            win.destroy()

        tb.Button(frm, text="发送验证码", bootstyle="info-outline", width=22, command=send_code).grid(row=4, column=0,
                                                                                                 columnspan=2, pady=10)
        btn_reset.config(command=do_reset)

    # -----------------------------
    # 主界面 UI
    # -----------------------------
    def _build_main_ui(self):
        main_frame = tb.Frame(self.root, padding=20)
        main_frame.place(relx=0.5, rely=0.5, anchor=CENTER)

        tb.Label(main_frame, text="心理健康咨询系统", font=("微软雅黑", 28, "bold")).pack(pady=(0, 15))
        tb.Label(main_frame, text="请选择你需要的功能", font=("微软雅黑", 14), bootstyle="secondary").pack(pady=(0, 20))

        btn_frame = tb.Frame(main_frame)
        btn_frame.pack(pady=10)

        tb.Button(btn_frame, text="🧠 心理测评（问卷）", width=32, bootstyle="info", command=self._open_assessment).pack(pady=8)
        tb.Button(btn_frame, text="💬 在线心理咨询（文字）", width=32, bootstyle="info", command=self._open_chat).pack(pady=8)
        tb.Button(btn_frame, text="🎤 语音聊天室", width=32, bootstyle="info", command=self._open_voice_chat).pack(pady=8)

        tb.Label(main_frame, text="本系统不能替代专业心理医生诊断", font=("微软雅黑", 10), bootstyle="secondary").pack(pady=15)

    # -----------------------------
    # 功能跳转（支持 exe + 源码模式）
    # -----------------------------
    def _open_assessment(self):
        try:
            if getattr(sys, 'frozen', False):
                from psychology_ui_multi import QuizUI
                win = tb.Toplevel(self.root)
                QuizUI(master=win)
            else:
                python = sys.executable
                script_path = os.path.join(BASE_DIR, "psychology_ui_multi.py")
                subprocess.Popen([python, script_path])
        except Exception as e:
            messagebox.showerror("启动失败", f"无法打开心理测评模块：\n{e}")

    def _open_chat(self):
        try:
            from psychology_chat_ui import PsychologyChatUI
            win = tb.Toplevel(self.root)
            PsychologyChatUI(master=win)
        except Exception as e:
            messagebox.showerror("启动失败", f"无法打开在线心理咨询模块：\n{e}")

    def _open_voice_chat(self):
        try:
            if getattr(sys, 'frozen', False):
                from psychology_voice_ui import PsychologyVoiceUI
                win = tb.Toplevel(self.root)
                PsychologyVoiceUI(master=win)
            else:
                python = sys.executable
                script_path = os.path.join(BASE_DIR, "psychology_voice_ui.py")
                subprocess.Popen([python, script_path])
        except Exception as e:
            messagebox.showerror("启动失败", f"无法打开语音聊天室模块：\n{e}")

    # -----------------------------
    # 启动
    # -----------------------------
    def run(self):
        self.root.mainloop()


# ==========================
# 独立运行
# ==========================
if __name__ == "__main__":
    app = PsychologyMainUI()
    app.run()
