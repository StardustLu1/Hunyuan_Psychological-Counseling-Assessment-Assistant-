# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import (
    collect_submodules,
    collect_all
)

# ======================================================
# 项目路径配置
# ======================================================
project_root = Path(r"D:\project\YOLOv12\yolov12\finalwork2\Graduation project")
site_packages_path = r"C:\Users\ZeningLi\.conda\envs\yolov12\Lib\site-packages"

block_cipher = None

# ======================================================
# 1️⃣ 强制完整收集 Pillow（解决 _imaging 问题）
# ======================================================
pillow_datas, pillow_binaries, pillow_hidden = collect_all("PIL")

# ======================================================
# 2️⃣ 强制完整收集 setuptools / pkg_resources 生态
# ======================================================
setuptools_datas, setuptools_binaries, setuptools_hidden = collect_all("setuptools")
pkgres_datas, pkgres_binaries, pkgres_hidden = collect_all("pkg_resources")

# ======================================================
# 3️⃣ 你的项目 + 第三方隐藏依赖
# ======================================================
hidden_imports = (
    collect_submodules("pipeline") +
    collect_submodules("dialogue") +
    collect_submodules("assessment") +
    collect_submodules("ttkbootstrap") +
    collect_submodules("speech_recognition") +
    collect_submodules("tencentcloud") +
    pillow_hidden +
    setuptools_hidden +
    pkgres_hidden +
    [
        # setuptools 运行期常漏
        "platformdirs",
        "importlib_resources",
        "packaging",
        "jaraco.text",
        "jaraco.context",
        "jaraco.functools",
        "more_itertools",
        "backports.tarfile",
    ]
)

# ======================================================
# 4️⃣ Analysis
# ======================================================
a = Analysis(
    scripts=[
        str(project_root / "ui" / "psychology_main_ui.py")
    ],
    pathex=[
        str(project_root),
        site_packages_path,
    ],
    binaries=[
        *pillow_binaries,
        *setuptools_binaries,
        *pkgres_binaries,
    ],
    datas=[
        # ---- 你的数据文件 ----
        (str(project_root / "ui" / "users.json"), "ui"),
        (str(project_root / "ui" / "question_bank.json"), "ui"),

        # ---- 模型文件 ----
        (str(project_root / "models" / "psych_model.h5"), "models"),
        (str(project_root / "models" / "emotion_model.h5"), "models"),

        # ---- 第三方运行期数据 ----
        *pillow_datas,
        *setuptools_datas,
        *pkgres_datas,
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ======================================================
# 5️⃣ 打包 Python 字节码
# ======================================================
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# ======================================================
# 6️⃣ 生成 exe（GUI 程序）
# ======================================================
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="psychology_main_ui",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI 程序
    icon=str(project_root / "icon.ico"),
)

# ======================================================
# 7️⃣ 收集成最终 dist
# ======================================================
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="psychology_main_ui",
)
