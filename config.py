import pyautogui
import os
import threading # 【新增】

# --- 目录配置 ---
SCRIPTS_DIR = "scripts"
IMG_FOLDER = "images"
TEMP_FILE = "temp_recording.txt"

if not os.path.exists(SCRIPTS_DIR): os.makedirs(SCRIPTS_DIR)
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

# --- 全局控制 ---
# 【新增】用于强制停止所有线程的信号
STOP_EVENT = threading.Event()

# --- 基础设置 ---
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01

# --- 拟人化参数 ---
SPEED_FACTOR = 1.0        
TIME_VARIANCE = 0.2       
PIXEL_VARIANCE = 3        
DOUBLE_CLICK_THRESHOLD = 0.3

# --- ModifyEye 参数 ---
SLOW_MOVE_DURATION = 0.8  
STEP_PAUSE = 0.5          
DWELL_TIME = 3.0          
MOVE_THRESHOLD = 15       
JITTER_TOLERANCE = 5      
MIN_SIZE = 10             

# --- Imitate 参数 ---
MAX_RETRY_DURATION = 5.0  
MOUSE_DODGE_DIST = 300
