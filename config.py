import pyautogui
import os
import sys
import threading

# =========================================================
# 核心修改：路径定位逻辑
# =========================================================
# 判断当前是直接运行的 python 脚本，还是打包后的 exe 文件
if getattr(sys, 'frozen', False):
    # 如果是 exe，根目录就是 exe 文件所在的文件夹
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 如果是脚本，根目录就是 config.py 所在的文件夹
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- 目录配置 (使用绝对路径) ---
# 所有的脚本将保存在这个文件夹下
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
IMG_FOLDER = os.path.join(BASE_DIR, "images")

# 临时文件（录制未命名时暂存）
TEMP_FILE = "temp_recording.txt"

# 自动创建必要的文件夹，防止报错
if not os.path.exists(SCRIPTS_DIR): os.makedirs(SCRIPTS_DIR)
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

# =========================================================
# 全局控制与参数
# =========================================================

# 用于强制停止所有线程的信号 (F4 功能)
STOP_EVENT = threading.Event()

# --- 基础设置 ---
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01

# --- 拟人化参数 (模拟人类操作的随机性) ---
SPEED_FACTOR = 1.0        # 速度倍率 (1.0 = 原速)
TIME_VARIANCE = 0.2       # 时间波动幅度
PIXEL_VARIANCE = 3        # 鼠标落点抖动范围 (像素)
DOUBLE_CLICK_THRESHOLD = 0.3 # 双击判定阈值 (秒)

# --- ModifyEye (智能转换) 参数 ---
SLOW_MOVE_DURATION = 0.8  # 引导时的慢速移动时间
STEP_PAUSE = 0.5          # 到达位置后的停顿时间
DWELL_TIME = 3.0          # 确认截图的倒计时
MOVE_THRESHOLD = 15       # 判定是否开始画框的移动距离
JITTER_TOLERANCE = 5      # 手抖容忍度
MIN_SIZE = 10             # 最小截图尺寸 (防止误触)

# --- Imitate (播放) 参数 ---
MAX_RETRY_DURATION = 5.0  # 找图重试最大时长
MOUSE_DODGE_DIST = 300    # 找不到图时鼠标避让距离
