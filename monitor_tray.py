import win32com.client as wincl
import pythoncom
import os
import sys
import time
import threading
import shutil
import tempfile
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from playwright.sync_api import sync_playwright
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
from winotify import Notification, audio


# ================================================================
# 1) ПРАВИЛЬНИЙ BASE_DIR ДЛЯ ONEFILE EXE
# ================================================================
if hasattr(sys, "_MEIPASS"):
    BASE_DIR = sys._MEIPASS       # розпаковка onefile у temp/_MEIxxxx
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOGFILE = os.path.join(BASE_DIR, "monitor_log.txt")
ICONFILE = os.path.join(BASE_DIR, "icon.png")


# ================================================================
# 2) ГАРАНТОВАНЕ СТВОРЕННЯ СПРАВЖНЬОГО ICON.PNG У TEMP ПАПЦІ
# ================================================================
def get_temp_icon():
    temp_icon = os.path.join(tempfile.gettempdir(), "monitor_tray_icon.png")
    try:
        shutil.copyfile(ICONFILE, temp_icon)
        return temp_icon
    except Exception:
        return ICONFILE


# ================================================================
# 3) PLAYWRIGHT SUPPORT FOR ONEFILE EXE
# ================================================================
if hasattr(sys, "_MEIPASS"):
    extracted = os.path.join(sys._MEIPASS, "playwright")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = extracted
else:
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(
        os.environ["USERPROFILE"],
        "AppData", "Local", "ms-playwright"
    )


# ================================================================
# ГРУПИ ДЛЯ ПОШУКУ
# ================================================================
GROUPS = [
    "Група 1.1.", "Група 1.2.",
    "Група 2.1.", "Група 2.2.",
    "Група 3.1.", "Група 3.2.",
    "Група 4.1.", "Група 4.2.",
    "Група 5.1.", "Група 5.2.",
    "Група 6.1.", "Група 6.2."
]


# ================================================================
# ФУНКЦІЯ ЛОГУВАННЯ
# ================================================================
def log(text):
    with open(LOGFILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {text}\n")


# ================================================================
# ГОЛОС (COM в окремому потоці)
# ================================================================
def speak(text):
    try:
        speaker = wincl.Dispatch("SAPI.SpVoice")
        speaker.Speak(text)
    except Exception as e:
        log(f"Помилка SAPI: {e}")


# ================================================================
# ОТРИМАННЯ ТЕКСТУ СТОРІНКИ
# ================================================================
def fetch_page_text():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://poweron.loe.lviv.ua", timeout=60000)
            text = page.inner_text("body")
            browser.close()
            return text
    except Exception as e:
        log(f"Помилка Playwright: {e}")
        return ""


# ================================================================
# Windows Notification через winotify
# ================================================================
def send_notification(text):
    try:
        n = Notification(
            app_id="Моніторинг груп",
            title="Моніторинг груп",
            msg=text,
            icon=get_temp_icon()
        )
        n.set_audio(audio.Default, loop=False)
        n.show()
    except Exception as e:
        log(f"Помилка winotify: {e}")


# ================================================================
# ГОЛОВНИЙ МОНІТОРИНГ ПОТОКУ
# ================================================================
last_state = ""


def monitor():
    pythoncom.CoInitialize()  # обов’язково для SAPI в потоці

    global last_state

    while True:
        text = fetch_page_text()
        if not text:
            time.sleep(60)
            continue

        found_lines = []
        for line in text.split("\n"):
            for g in GROUPS:
                if g in line:
                    found_lines.append(line.strip())

        new_state = "\n".join(found_lines)

        if new_state != last_state and found_lines:
            last_state = new_state

            log("ЗМІНА ВИЯВЛЕНА:")
            for x in found_lines:
                log(f"  {x}")

            # Toast
            send_notification("\n".join(found_lines))

            # Голос
            speak("Attention! Changes to the schedule have been detected.")

            # Messagebox поверх усіх
            root = tk.Tk()
            root.withdraw()
            try:
                root.iconphoto(False, tk.PhotoImage(file=get_temp_icon()))
            except:
                pass
            root.attributes("-topmost", True)
            messagebox.showinfo("Зміни на сайті", "\n".join(found_lines))
            root.destroy()

        time.sleep(60)


# ================================================================
# ІКОНКА ДЛЯ ТРЕЮ
# ================================================================
def create_image_fallback():
    img = Image.new("RGB", (64, 64), "black")
    d = ImageDraw.Draw(img)
    d.rectangle([8, 8, 56, 56], outline="white")
    d.line((8, 8, 56, 56), fill="white", width=3)
    d.line((8, 56, 56, 8), fill="white", width=3)
    return img


def on_exit(icon, item):
    icon.stop()
    os._exit(0)


def run_tray():
    try:
        tray_icon = Image.open(get_temp_icon())
    except:
        tray_icon = create_image_fallback()

    icon = pystray.Icon(
        "monitor",
        tray_icon,
        "Моніторинг сайту виключень світла",
        menu=pystray.Menu(item("Вихід", on_exit))
    )
    icon.run()


# ================================================================
# ГОЛОВНИЙ СТАРТ
# ================================================================
if __name__ == "__main__":
    log("=== Запуск програми ===")

    t = threading.Thread(target=monitor, daemon=True)
    t.start()

    run_tray()
