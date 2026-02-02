import pyautogui
import os
import sys
import threading

# =========================================================
# 路径定位逻辑
# =========================================================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- 目录配置 ---
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
IMG_FOLDER = os.path.join(BASE_DIR, "images")
# 两个专用子文件夹
POPUP_FOLDER = os.path.join(IMG_FOLDER, "popups")
CAPTCHA_FOLDER = os.path.join(IMG_FOLDER, "captchas")

TEMP_FILE = "temp_recording.txt"

# 自动创建
for folder in [SCRIPTS_DIR, IMG_FOLDER, POPUP_FOLDER, CAPTCHA_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# =========================================================
# 全局控制与参数
# =========================================================
STOP_EVENT = threading.Event()

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01

# 拟人化参数
SPEED_FACTOR = 1.0        
TIME_VARIANCE = 0.2       
PIXEL_VARIANCE = 3        
DOUBLE_CLICK_THRESHOLD = 0.3

# ModifyEye 参数
SLOW_MOVE_DURATION = 0.8  
STEP_PAUSE = 0.5          
DWELL_TIME = 3.0          
MOVE_THRESHOLD = 15       
JITTER_TOLERANCE = 5      
MIN_SIZE = 10             

# Imitate 参数
MAX_RETRY_DURATION = 5.0  
MOUSE_DODGE_DIST = 300
