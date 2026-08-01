#!/usr/bin/env python3
"""
UPS Tracking Checker - GUI Application with Microsoft Edge Bot
==============================================================
Paste tracking numbers, checks each one via headless Edge, saves CSV.

  - Real-time progress updates with colored log
  - Automatic CSV saving every 10 results
  - Edge browser automation (headless)
  - Cancel operation at any time

Ship this file together with GFH_Telecom_TBLogo.ico and GFH_Telecom_Logo.png
in the same folder for the window/taskbar icon and header logo.

Created by Abad Umair Channa  |  Copyright 2026
"""

import re
import time
import csv
import os
import shutil
import tempfile
import subprocess
import sys
import threading
import queue
from datetime import datetime
from typing import List, Optional, Dict, Callable

# GUI imports
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox, filedialog
except ImportError:
    print("Tkinter is required but not installed.")
    sys.exit(1)

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.edge.options import Options
    from selenium.webdriver.edge.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
except ImportError as e:
    messagebox.showerror("Missing Dependency",
        f"Required package is missing: {e}\n\n"
        "Please run: pip install selenium")
    sys.exit(1)

# Optional PIL for logo / icon handling
try:
    from PIL import Image as _PI, ImageTk as _PIT
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pillow",
                        "--quiet", "--disable-pip-version-check"],
                       capture_output=True)
        from PIL import Image as _PI, ImageTk as _PIT
        HAS_PIL = True
    except Exception:
        pass

# ─────────────────────────────────────────────────────────────────────────────
# BRAND / WINDOW CONFIG  (kept in sync with GFH_Inventory_Aging_Processor.pyw)
# ─────────────────────────────────────────────────────────────────────────────
NAVY  = "#090d26"
RED   = "#e8212a"
WHITE = "#ffffff"
LIGHT = "#f0f4fa"
LOG_BG   = "#10182e"
LOG_FG   = "#a8d8ff"

ICON_ICO_NAME = "GFH_Telecom_TBLogo.ico"
LOGO_PNG_NAME = "GFH_Telecom_Logo.png"
COPYRIGHT_TEXT = "Created by Abad Umair Channa  |  Copyright © 2026  |  All rights reserved."
ICON_ICO_B64 = "AAABAAEAICAAAAEAIACoEAAAFgAAACgAAAAgAAAAQAAAAAEAIAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAA0GRv/NBkb/zQZG/80GRv/NBkb/zUZG/81GRv/NRkb/zUZG/81GRv/NRkb/zQZG/81GRv/NBgb/zUZG/81GRv/NBkb/zQZG/80GBv/NRkb/zQYG/80GRv/NBkb/zQZG/80GRv/NBkb/zQZG/81GRv/NRkb/zQZG/80GRv/NBgb/zUZG/80GRv/NBkb/zUZG/81GRv/NRkb/zUZG/81GRv/NRkb/zUZG/81GRv/NRkb/zUZG/81GRv/NRkb/zUZG/81GRv/NRkb/zUZG/81GRv/NRkb/zUZG/81GRv/NRkb/zUZG/81GRv/NRkb/zUZG/81GRv/NRkb/zUZG/81GBv/NRgb/zUYG/81GRv/NRkb/zUZG/81GRv/NRkb/zUZG/81GRv/NRkb/zUZG/81GRv/NRkb/zUZG/81GRv/NRkb/zUZG/81GRv/NRkb/zUZG/81GRv/NRkb/zUZG/81GRv/NRkb/zUZG/81GRv/NRkb/zYZHP81GRv/NRkb/zUYG/81GRv/NRkb/zUZG/81GRv/NRkc/zUZG/81GRz/Nhkc/zYZG/82GRz/Nhkc/zYZHP82GRv/NRkb/zUZG/81GRv/NRkb/zUZG/81GRv/NRkb/zUZG/81GRv/NRkb/zUZG/81GRv/NRkb/zUYG/8/JCf/TDM2/zYaHP81GRv/NRgb/zUZG/81GRv/NRkb/zYZG/82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRv/Nhkb/zYZHP81GRv/NRkb/zYZHP82GRz/Nhkc/zYZHP82GRv/Nhkb/zYZG/82GRz/NRkb/zoeIP8/JCf/Nhkb/zUZG/81GRv/Nhkb/zYZG/82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRv/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zUYG/82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZG/82GRv/Nhkb/zYZG/82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZG/82GRr/NRkh/zMZKv8zGS3/Mxkn/zUZHv82GRr/Nhkb/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRv/Mxoy/yseZv8lIIn/IyCS/yIfkf8iHoz/JB16/ywbUP80GSX/Nhka/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRv/Nhke/y8eWf8mI53/JyGL/y0dW/8wG0H/MBo7/y4aRf8pHGT/IR6O/yMdg/8wGjr/Nhkb/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHf8uIGj/JyWn/y8eWf80Giv/MRxH/ywfaP8rH3D/LR1e/zIaOf8zGS3/Jxxr/yEekv8wGj//Nhka/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRr/MR9S/ykorP8xHk3/Mxw4/yojjf8nJKD/KSGD/ysgd/8oIIj/JSKb/yoecP8vG0f/KB1t/yMfjv8zGi7/Nhkb/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zcZHP83GRz/Nxkb/zUaKP8sKKL/MCJu/zQbM/8qJqD/LCOE/zQaMv83GRv/Nxkb/zYZHf8uHVn/IyOp/yQhnP8sHWX/Jh+G/yodav82GRv/Nxkc/zYZHP82GRz/Nhkc/zYZHP82GRz/Nhkc/zcZHP82GRz/Nxkc/zcZHP83GRz/Nxkc/zcZHP83GRn/NCBT/y4rsP81GzL/LyWD/y0mkv82GiP/NRsu/y8hcP8sI4T/MB5Z/zAdSv8mI6H/JiOc/ywfbP8vHEz/JiGW/zQaKv83GRv/Nxkc/zcZHP83GRz/Nxkc/zcZHP82GRz/Nxkc/zYZHP83GRz/Nxkc/zYZHP83GRz/Nxkc/zcZGv8yJX3/MSeR/zUbNf8uKrL/NB5K/zYaJv8tJpb/LCaY/y4hdv8pJqT/LiFy/y4eX/8sH3D/NBou/zQaK/8mIpn/MRxC/zcZGv83GRz/Nxkc/zcZHP83GRz/Nxkc/zcZHP82GBv/Nhgb/zYYG/82GRz/Nhkc/zYZHP82GRz/Nxkb/zIplP8zJnr/NB5I/y8ss/81Giz/Mx9P/y0qrv81GzD/NxgX/zEeUf8pKLD/LSN//y0iev8tInn/LCF9/yclq/8wHU3/NxgZ/zcZHP83GRz/Nxkc/zcZHP83GRz/Nhkc/zYYG/82GBv/Nhgc/zYZHP82GBz/Nhgb/zYYG/82GR//Miyi/zIrnf80IVv/MS62/zUbLP8zH0//Lyyy/zUbMf82GBf/Mh9U/ysqtP8uI4D/LiJ7/y0iev8tIXn/Lh9r/zQaK/82GBv/Nhgb/zYYHP82GRz/Nhkc/zYYHP82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/NhgZ/zUfSf8yM8X/MjHC/zIrmv8xMLv/NCBO/zUZJv8xKp//MCul/zElgP8uK7H/MSNz/zYYGf82GBf/NhgY/zUaK/8zHUL/Nhgc/zYYG/82GBv/Nhgc/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBn/NSBL/zM0yf8yM8X/MyiB/zMqkf8yLaP/Nhok/zUbL/8yJXr/MSiQ/zIiY/81GSH/NRst/zMfUv80HDX/Mxw+/zEiaP82GSD/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GR//NSJb/zQpiv81I1z/NRw5/zIwuf8zLJr/NRw3/zYYGv80H0n/MimS/zMmfP8wK6j/Lyy4/y8qrv80HT7/Nhke/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBb/NSFS/zMzyP81Ilf/NR09/zIuqP8yMsT/Myh//zEtpf8xLrP/MDLP/zInh/80HDn/MCyx/zMiZv82GBj/Nhgb/zYYG/82GBv/Nxgb/zYYG/82GBv/Nxgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GR7/NSh//zQ0zf81JWr/NRsu/zQhVf80I2L/MyeE/zExxf8yLar/NB1D/zInh/8wL7v/NB1A/zYYGf82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYGv82GR//NSZv/zQ0yv80MLL/NSZy/zUgT/81IVP/MyiI/zIsnf8xMLz/MS6v/zQfSv82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBr/NR07/zUogv80MLX/NDLE/zQyxf8zMb3/Myyj/zQjZ/81Gin/NhgZ/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBn/NhgZ/zUZIv82Gy//NRw0/zUaK/82GB7/NhgY/zYYGv82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/83GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYGv82GBr/Nhga/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/NRgb/zUYG/81GBv/NRgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zUYG/81GBv/NRgb/zYYG/81GBv/Nhgb/zYYG/81GBv/NRgb/zUYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/81GBv/NRgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/82GBv/Nhgb/zYYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/82GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/NRgb/zYZG/81GBv/NRgb/zUYG/81GBv/NRgb/zUZG/81GBv/NRgb/zUYG/81GBv/NRgb/zUYG/81GBv/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="


def _script_dir() -> str:
    """Directory containing this .pyw (or .exe when frozen)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def _set_window_icon(root):
    """Set taskbar + titlebar icon from the embedded GFH_Telecom_TBLogo.ico."""
    try:
        import base64, tempfile, atexit
        data = base64.b64decode(ICON_ICO_B64.strip())
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".ico")
        tmp.write(data); tmp.close()
        atexit.register(lambda p=tmp.name: os.path.exists(p) and os.unlink(p))
        root.iconbitmap(default=False, bitmap=tmp.name)
        root.iconbitmap(tmp.name)
        return
    except Exception:
        pass
    # Fallback: use the brand PNG as the window icon
    png_path = os.path.join(_script_dir(), LOGO_PNG_NAME)
    try:
        if os.path.exists(png_path) and HAS_PIL:
            root.iconphoto(True, _PIT.PhotoImage(_PI.open(png_path)))
    except Exception:
        pass


# ============================================================================
# BOT LOGIC
# ============================================================================

def run_cmd(args, timeout=5) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return (result.stdout or "") + (result.stderr or "")
    except Exception:
        return ""


def extract_major(version_text: str) -> Optional[int]:
    match = re.search(r"(\d+)\.\d+\.\d+\.\d+", version_text or "")
    return int(match.group(1)) if match else None


def get_edge_major_version() -> Optional[int]:
    if sys.platform == "win32":
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Microsoft\Edge\Application\msedge.exe"),
        ]
        for path in edge_paths:
            if os.path.exists(path):
                version_text = run_cmd([path, "--version"])
                major = extract_major(version_text)
                if major:
                    return major
        try:
            import winreg
            reg_paths = [
                r"Software\Microsoft\Edge\BLBeacon",
                r"Software\WOW6432Node\Microsoft\Edge\BLBeacon",
            ]
            for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                for reg_path in reg_paths:
                    try:
                        key = winreg.OpenKey(root, reg_path)
                        version, _ = winreg.QueryValueEx(key, "version")
                        major = extract_major(version)
                        if major:
                            return major
                    except Exception:
                        pass
        except Exception:
            pass
    return None


MONTH_MAP = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "Jun": 6, "Jul": 7, "Aug": 8,
    "Sep": 9, "Sept": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

STATUS_WORDS = (
    "Delivered", "Out for Delivery", "On the Way", "Label Created",
    "Delivery Attempted", "Exception", "Processing", "Returned",
    "Shipment Ready", "The delivery date will be provided",
)


class UPSTrackingBot:
    """UPS tracking bot with callback support for GUI integration"""

    def __init__(self, headless: bool = True, progress_callback: Optional[Callable] = None):
        self.headless = headless
        self.driver = None
        self.wait = None
        self.results: List[Dict[str, str]] = []
        self.saved_count = 0
        self.profile_dir = tempfile.mkdtemp(prefix="ups_edge_profile_")
        self.progress_callback = progress_callback
        self.is_cancelled = False

    def make_options(self):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(f"--user-data-dir={self.profile_dir}")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        )
        return options

    def start_driver(self):
        if self.driver:
            try: self.driver.quit()
            except Exception: pass
        get_edge_major_version()
        self.log("Launching Microsoft Edge...")
        try:
            self.driver = webdriver.Edge(service=Service(), options=self.make_options())
            self.wait = WebDriverWait(self.driver, 40)
            self.driver.set_page_load_timeout(60)
            self.log("Browser ready.\n")
        except Exception as e:
            raise RuntimeError(
                f"Microsoft Edge could not launch.\n"
                f"Run: python -m pip install --upgrade selenium\nError: {e}")

    def log(self, message: str):
        if self.progress_callback:
            self.progress_callback("log", message)
        else:
            print(message)

    def update_progress(self, current: int, total: int, tracking: str, result: str):
        if self.progress_callback:
            self.progress_callback("progress", {
                "current": current, "total": total,
                "tracking": tracking, "result": result})

    def extract_tracking_numbers(self, text: str) -> List[str]:
        text = text.replace(",", "\n")
        candidates = []
        for line in text.splitlines():
            for part in line.split():
                candidates.append(part.strip())
        patterns = [r"\b1Z[A-Z0-9]{16}\b", r"\b\d{9,26}\b", r"\b[A-Z]{2}\d{9}[A-Z]{2}\b"]
        tracking = []
        for cand in candidates:
            clean = re.sub(r"[^A-Za-z0-9]", "", cand).upper()
            for pattern in patterns:
                if re.fullmatch(pattern, clean, re.IGNORECASE):
                    tracking.append(clean)
                    break
        seen = set(); unique = []
        for tn in tracking:
            if tn not in seen:
                seen.add(tn); unique.append(tn)
        return unique

    def wait_for_ups_result(self, tracking_number: str) -> str:
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        deadline = time.time() + 40
        last_text = ""
        while time.time() < deadline:
            if self.is_cancelled: return ""
            try:
                body_text = self.driver.find_element(By.TAG_NAME, "body").text
                last_text = body_text
                if tracking_number in body_text and any(w in body_text for w in STATUS_WORDS):
                    return body_text
                try:
                    if self.driver.find_element(By.ID, "stApp_nameKey").text.strip():
                        return body_text
                except Exception: pass
                try:
                    if self.driver.find_element(By.ID, "st_App_PkgStsMonthNum").text.strip():
                        return body_text
                except Exception: pass
                if any(w in body_text for w in STATUS_WORDS):
                    return body_text
            except Exception: pass
            time.sleep(1)
        return last_text

    def is_delivered(self, body_text: str) -> bool:
        try:
            status_elem = self.driver.find_element(By.ID, "stApp_nameKey")
            if re.search(r"\bDelivered\b", status_elem.text.strip(), re.IGNORECASE):
                return True
        except Exception: pass
        lines = [re.sub(r"\s+", " ", x).strip() for x in (body_text or "").splitlines() if x.strip()]
        for line in lines[:25]:
            if line.lower() == "delivered" or line.lower().startswith("delivered "):
                return True
        return False

    def get_delivery_date(self) -> Optional[str]:
        try:
            elem = self.wait.until(EC.presence_of_element_located((By.ID, "st_App_PkgStsMonthNum")))
            text = re.sub(r"\s+", " ", elem.text).strip()
            match = re.search(
                r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+([A-Za-z]+)\s+(\d{1,2})",
                text, re.IGNORECASE)
            if match:
                month_num = MONTH_MAP.get(match.group(2).replace(".", ""))
                if month_num:
                    return f"{month_num}/{int(match.group(3))}/{datetime.now().year}"
            match = re.search(r"\b([A-Za-z]+)\s+(\d{1,2})\b", text, re.IGNORECASE)
            if match:
                month_num = MONTH_MAP.get(match.group(1).replace(".", ""))
                if month_num:
                    return f"{month_num}/{int(match.group(2))}/{datetime.now().year}"
            self.log(f"Date selector found but could not parse: {text}")
            return None
        except Exception as e:
            self.log(f"Date extraction error: {e}")
            return None

    def check_tracking(self, tracking_number: str) -> Dict[str, str]:
        try:
            url = (f"https://www.ups.com/track?track=yes&trackNums={tracking_number}"
                   "&loc=en_US&requester=ST/trackdetails")
            self.driver.get(url)
            body_text = self.wait_for_ups_result(tracking_number)
            if self.is_cancelled:
                return {"Tracking": tracking_number, "Result": "Cancelled"}
            if not body_text:
                return {"Tracking": tracking_number, "Result": "Not delivered"}
            if not self.is_delivered(body_text):
                return {"Tracking": tracking_number, "Result": "Not delivered"}
            date_str = self.get_delivery_date()
            if date_str:
                return {"Tracking": tracking_number, "Result": f"Delivered {date_str}"}
            return {"Tracking": tracking_number, "Result": "Delivered"}
        except TimeoutException:
            return {"Tracking": tracking_number, "Result": "Not delivered"}
        except Exception as e:
            return {"Tracking": tracking_number, "Result": f"ERROR: {e}"}

    def save_results(self, output_file: str, force: bool = False):
        SAVE_EVERY = 10
        total_results = len(self.results)
        if not force and total_results - self.saved_count < SAVE_EVERY: return
        if total_results <= self.saved_count: return
        new_rows = self.results[self.saved_count:total_results]
        with open(output_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for row in new_rows:
                writer.writerow([row.get("Tracking", ""), row.get("Result", "")])
        self.saved_count = total_results
        self.log(f"Saved {len(new_rows)} results. Total saved: {self.saved_count}")

    def process_all(self, tracking_numbers: List[str], output_file: str):
        total = len(tracking_numbers)
        self.log(f"Total unique tracking numbers: {total}")
        if not tracking_numbers:
            self.log("No valid tracking numbers found."); return
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["Tracking", "Result"])
        self.log(f"Output file: {output_file}")
        self.log(f"\nChecking one by one. Saving after every 10 results.\n")
        for i, tn in enumerate(tracking_numbers, 1):
            if self.is_cancelled:
                self.log("\nOperation cancelled by user."); break
            self.log(f"[{i}/{total}] {tn}...")
            row = self.check_tracking(tn)
            self.results.append(row)
            self.update_progress(i, total, tn, row["Result"])
            self.save_results(output_file, force=False)
            if i < total and not self.is_cancelled: time.sleep(2)
        self.save_results(output_file, force=True)
        delivered_count = sum(1 for r in self.results if r["Result"].startswith("Delivered"))
        self.log(f"\nFinal CSV saved to: {output_file}")
        self.log(f"Summary: {delivered_count} out of {len(self.results)} packages delivered.")
        return delivered_count, len(self.results)

    def cancel(self):
        self.is_cancelled = True

    def close(self):
        if self.driver:
            try: self.driver.quit()
            except Exception: pass
        try: shutil.rmtree(self.profile_dir, ignore_errors=True)
        except Exception: pass


# ═══════════════════════════════════════════════════════════════════════════
# GUI  (styled to match GFH_Inventory_Aging_Processor.pyw)
# ═══════════════════════════════════════════════════════════════════════════
class UPSGuiApp:

    def __init__(self, root):
        self.root = root
        self.bot = None
        self.active_bot = None
        self.worker_thread = None
        self.is_processing = False
        self.output_file = None
        self.update_queue = queue.Queue()
        self._logo_img = None

        root.title("GFH Telecom - UPS Tracking System")
        # Size relative to screen resolution (deducting a margin) so it always fits.
        # Widened from 800 -> 1150 so the Progress & Results log has real breathing
        # room instead of being squeezed into ~370px alongside the input panel.
        root.update_idletasks()
        _sw,_sh=root.winfo_screenwidth(),root.winfo_screenheight()
        _w,_h=min(1150,_sw-80),min(680,_sh-120)
        root.geometry(f"{_w}x{_h}+{(_sw-_w)//2}+{(_sh-_h)//2}")
        root.minsize(900, 560)
        root.configure(bg=LIGHT); root.eval("tk::PlaceWindow . center")
        _set_window_icon(root)
        root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self._styles(); self._header(); self._body(); self._copyright_bar()
        self.process_queue()

    # ── styles ─────────────────────────────────────────────────────────────
    def _styles(self):
        s = ttk.Style(); s.theme_use("clam")
        s.configure("Run.TButton", background=RED, foreground=WHITE,
                    font=("Calibri", 11, "bold"), padding=(16, 9), borderwidth=0)
        s.map("Run.TButton",
              background=[("active", "#c01820"), ("disabled", "#aaa")])
        s.configure("Browse.TButton", background=NAVY, foreground=WHITE,
                    font=("Calibri", 10), padding=(10, 6), borderwidth=0)
        s.map("Browse.TButton", background=[("active", "#1a2550")])
        s.configure("Cancel.TButton", background="#1a2550", foreground=WHITE,
                    font=("Calibri", 10), padding=(10, 6), borderwidth=0)
        s.map("Cancel.TButton", background=[("active", "#2a3560")])
        s.configure("Accent.Horizontal.TProgressbar",
                    troughcolor="#dde6f0", background=RED, borderwidth=0)

    # ── header (matches Aging Processor: NAVY 108px, logo left, title center) ──
    def _header(self):
        hdr = tk.Frame(self.root, bg=NAVY, height=108)
        hdr.pack(fill="x"); hdr.pack_propagate(False)

        # Logo on the left - composite on NAVY, thumbnail to 260x82
        logo_path = os.path.join(_script_dir(), LOGO_PNG_NAME)
        if os.path.exists(logo_path) and HAS_PIL:
            try:
                img = _PI.open(logo_path).convert("RGBA")
                bg2 = _PI.new("RGBA", img.size, (9, 13, 38, 255))
                bg2.paste(img, mask=img.split()[3])
                img = bg2.convert("RGB")
                img.thumbnail((260, 82), _PI.Resampling.LANCZOS)
                self._logo_img = _PIT.PhotoImage(img)
            except Exception:
                self._logo_img = None

        lf = tk.Frame(hdr, bg=NAVY)
        lf.place(relx=0, rely=0.5, anchor="w", x=24)
        if self._logo_img:
            tk.Label(lf, image=self._logo_img, bg=NAVY).pack()
        else:
            tk.Label(lf, text="GFH TELECOM", font=("Calibri", 16, "bold"),
                     fg=RED, bg=NAVY).pack()

        tf = tk.Frame(hdr, bg=NAVY)
        tf.place(relx=0.58, rely=0.5, anchor="center")
        tk.Label(tf, text="UPS TRACKING SYSTEM",
                 font=("Calibri", 18, "bold"), fg=WHITE, bg=NAVY).pack()
        tk.Label(tf, text="Real-time package verification via Edge",
                 font=("Calibri", 9), fg=WHITE, bg=NAVY).pack()

    # ── body ───────────────────────────────────────────────────────────────
    def _body(self):
        body = tk.Frame(self.root, bg=LIGHT)
        body.pack(fill="both", expand=True, padx=24, pady=18)

        # ── Two-column panel area ──────────────────────────────────────────
        panels = tk.Frame(body, bg=LIGHT)
        panels.pack(fill="both", expand=True)
        # Weighted grid (not equal pack) so the log panel gets more real
        # estate — tracking-number lines are short, but result rows
        # ("Tracking Number: ... - Status: ... - Date: ...") run long.
        panels.grid_rowconfigure(0, weight=1)
        panels.grid_columnconfigure(0, weight=4)   # input: 40%
        panels.grid_columnconfigure(1, weight=6)   # log:   60%

        # Left panel - Tracking Numbers input
        left = tk.Frame(panels, bg=LIGHT)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tk.Label(left, text="Tracking Numbers",
                 font=("Calibri", 10, "bold"), fg=NAVY, bg=LIGHT).pack(anchor="w", pady=(0, 6))
        self.input_text = scrolledtext.ScrolledText(
            left, height=10, font=("Consolas", 9), wrap=tk.WORD,
            bg=WHITE, fg=NAVY, relief="flat",
            highlightbackground="#b0c4de", highlightthickness=1)
        self.input_text.pack(fill="both", expand=True)
        btn_row = tk.Frame(left, bg=LIGHT)
        btn_row.pack(fill="x", pady=(6, 0))
        self.paste_btn = ttk.Button(btn_row, text="Paste from Clipboard",
                                    style="Browse.TButton", command=self.paste_from_clipboard)
        self.paste_btn.pack(side="left", padx=(0, 6))
        self.clear_btn = ttk.Button(btn_row, text="Clear",
                                    style="Browse.TButton", command=self.clear_input)
        self.clear_btn.pack(side="left")

        # Right panel - Progress & Results log
        right = tk.Frame(panels, bg=LIGHT)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        tk.Label(right, text="Progress & Results",
                 font=("Calibri", 10, "bold"), fg=NAVY, bg=LIGHT).pack(anchor="w", pady=(0, 6))
        self.output_log = scrolledtext.ScrolledText(
            right, height=10, font=("Consolas", 9), wrap=tk.WORD,
            bg=LOG_BG, fg=LOG_FG, relief="flat")
        self.output_log.pack(fill="both", expand=True)
        for tag, clr in [("success", "#68D391"), ("error", "#FC8181"),
                         ("info", "#90CDF4"), ("warning", "#F6E05E")]:
            self.output_log.tag_config(tag, foreground=clr)

        # ── Progress bar ───────────────────────────────────────────────────
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            body, variable=self.progress_var, mode="determinate",
            style="Accent.Horizontal.TProgressbar")
        self.progress_bar.pack(fill="x", pady=(10, 6))

        # ── Action buttons + inline status ─────────────────────────────────
        act = tk.Frame(body, bg=LIGHT)
        act.pack(fill="x", pady=(0, 6))
        self.start_btn = ttk.Button(act, text="Start Tracking",
                                    style="Run.TButton", command=self.start_tracking)
        self.start_btn.pack(side="left")
        self.cancel_btn = ttk.Button(act, text="Cancel",
                                     style="Cancel.TButton", command=self.cancel_tracking,
                                     state="disabled")
        self.cancel_btn.pack(side="left", padx=8)
        self.open_csv_btn = ttk.Button(act, text="Open CSV Folder",
                                       style="Browse.TButton", command=self.open_csv_folder,
                                       state="disabled")
        self.open_csv_btn.pack(side="left", padx=(0, 8))
        self.progress_label = tk.Label(act, text="Ready", bg=LIGHT, fg=NAVY,
                                       font=("Calibri", 9))
        self.progress_label.pack(side="left")
        self.status_label = tk.Label(act, text="", bg=LIGHT, fg=NAVY,
                                     font=("Calibri", 9))
        self.status_label.pack(side="right")

    def _copyright_bar(self):
        bar = tk.Frame(self.root, bg=NAVY, height=26)
        bar.pack(fill="x", side="bottom"); bar.pack_propagate(False)
        tk.Label(bar, text=COPYRIGHT_TEXT, bg=NAVY, fg="#9d9db8",
                 font=("Calibri", 8)).pack(pady=4)

    # ── GUI logic methods ──────────────────────────────────────────────────
    def log_message(self, level: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}\n"
        tag_map = {"log": "info", "success": "success", "error": "error", "warning": "warning"}
        self.output_log.insert(tk.END, formatted, tag_map.get(level, "info"))
        self.output_log.see(tk.END)

    def update_progress_display(self, data: dict):
        current = data.get("current", 0)
        total = data.get("total", 0)
        tracking = data.get("tracking", "")
        result = data.get("result", "")
        if total > 0:
            self.progress_var.set((current / total) * 100)
            self.progress_label.config(text=f"{current}/{total} - {tracking}")
        else:
            self.progress_label.config(text=f"{tracking} - {result}")
        self.status_label.config(text=f"Checking: {tracking}")
        if "Delivered" in result:
            self.log_message("success", f"  {tracking}: {result}")
        elif "ERROR" in result:
            self.log_message("error", f"  {tracking}: {result}")
        else:
            self.log_message("log", f"  {tracking}: {result}")

    def queue_callback(self, callback_type: str, data):
        self.update_queue.put((callback_type, data))

    def handle_callback(self, callback_type: str, data):
        if callback_type == "log":
            self.log_message("log", data)
        elif callback_type == "progress":
            self.update_progress_display(data)

    def paste_from_clipboard(self):
        try:
            self.input_text.insert(tk.END, self.root.clipboard_get())
            self.log_message("log", "Text pasted from clipboard")
        except Exception as e:
            self.log_message("error", f"Failed to paste: {e}")

    def clear_input(self):
        self.input_text.delete(1.0, tk.END)
        self.log_message("log", "Input cleared")

    def start_tracking(self):
        if self.is_processing:
            messagebox.showwarning("Processing", "Already processing!"); return
        input_content = self.input_text.get(1.0, tk.END).strip()
        if not input_content:
            messagebox.showwarning("No Input", "Please paste tracking numbers first!"); return
        tracking_numbers = UPSTrackingBot().extract_tracking_numbers(input_content)
        if not tracking_numbers:
            messagebox.showwarning("No Valid Numbers",
                                  "No valid UPS tracking numbers found!"); return
        if not messagebox.askyesno("Start Tracking",
                                   f"Found {len(tracking_numbers)} tracking number(s).\n\n"
                                   "This will check each one.\n"
                                   "Results saved automatically.\n\nProceed?"):
            return
        self.output_log.delete(1.0, tk.END)
        self.progress_var.set(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_file = os.path.join(os.path.expanduser("~/Downloads"),
                                       f"ups_tracking_results_{timestamp}.csv")
        self.is_processing = True
        self.start_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.paste_btn.config(state="disabled")
        self.clear_btn.config(state="disabled")
        self.open_csv_btn.config(state="disabled")
        self.log_message("log", f"Starting tracking for {len(tracking_numbers)} packages...")
        self.log_message("log", f"Results: {self.output_file}")
        self.status_label.config(text=f"Processing {len(tracking_numbers)} numbers...")
        self.worker_thread = threading.Thread(target=self.run_tracking_worker,
                                              args=(tracking_numbers, True), daemon=True)
        self.worker_thread.start()

    def run_tracking_worker(self, tracking_numbers: List[str], is_headless: bool):
        bot = None
        try:
            bot = UPSTrackingBot(headless=is_headless, progress_callback=self.queue_callback)
            self.active_bot = bot
            bot.start_driver()
            bot.process_all(tracking_numbers, self.output_file)
            self.update_queue.put(("completed", None))
        except Exception as e:
            error_msg = f"Fatal error: {str(e)}"
            self.log_message("error", error_msg)
            self.update_queue.put(("error", error_msg))
        finally:
            if bot: bot.close()

    def cancel_tracking(self):
        if self.is_processing:
            self.log_message("warning", "Cancelling... Please wait")
            self.status_label.config(text="Cancelling...")
            self.cancel_btn.config(state="disabled")
            if hasattr(self, "active_bot") and self.active_bot:
                self.active_bot.cancel()

    def on_tracking_completed(self):
        self.is_processing = False; self.active_bot = None
        self.start_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")
        self.paste_btn.config(state="normal")
        self.clear_btn.config(state="normal")
        if self.output_file and os.path.exists(self.output_file):
            self.open_csv_btn.config(state="normal")
        self.status_label.config(text="Tracking completed")
        self.progress_label.config(text="Complete!")
        messagebox.showinfo("Tracking Complete",
                           f"Tracking check completed!\n\nResults:\n{self.output_file}")

    def on_tracking_error(self, error_msg: str):
        self.is_processing = False; self.active_bot = None
        self.start_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")
        self.paste_btn.config(state="normal")
        self.clear_btn.config(state="normal")
        self.status_label.config(text="Error occurred")
        messagebox.showerror("Tracking Error",
                            f"An error occurred:\n\n{error_msg}")

    def open_csv_folder(self):
        if self.output_file and os.path.exists(self.output_file):
            folder = os.path.dirname(self.output_file)
            if sys.platform == "win32": os.startfile(folder)
            elif sys.platform == "darwin": subprocess.run(["open", folder])
            else: subprocess.run(["xdg-open", folder])
        else:
            messagebox.showwarning("No File", "No results file found yet!")

    def process_queue(self):
        try:
            while True:
                msg_type, data = self.update_queue.get_nowait()
                if msg_type == "completed": self.on_tracking_completed()
                elif msg_type == "error": self.on_tracking_error(data)
                elif msg_type in ("log", "progress"): self.handle_callback(msg_type, data)
        except queue.Empty: pass
        self.root.after(100, self.process_queue)

    def on_closing(self):
        if self.is_processing:
            if not messagebox.askyesno("Confirm Exit",
                                       "Tracking is still in progress.\n\nExit?"):
                return
        self.root.destroy()


def main():
    root = tk.Tk()
    UPSGuiApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
