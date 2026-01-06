import tkinter as tk
import random
import time
import math
import pyautogui
import config

hud_instance = None

class HeadsUpDisplay:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-alpha", 0.75)
        self.root.configure(bg='black')
        self.root.geometry("650x80+10+10")
        
        self.label = tk.Label(self.root, text="🚀 AutoMaster 初始化...", font=("Microsoft YaHei UI", 12, "bold"), 
                              fg="#00FF00", bg="black", anchor="w", padx=10)
        self.label.pack(expand=True, fill='both')

    def update(self, text, color="#00FF00"):
        try: self.root.after(0, lambda: self._update_impl(text, color))
        except: pass

    def _update_impl(self, text, color):
        try: self.label.config(text=text, fg=color)
        except: pass

def init_hud(root):
    global hud_instance
    hud_instance = HeadsUpDisplay(root)

def log(text, color="#00FF00"):
    if hud_instance: hud_instance.update(text, color)
    else: print(text)

def check_stop():
    if config.STOP_EVENT.is_set():
        raise InterruptedError("用户强制停止")

# === 拟人化算法核心 ===
last_raw_x, last_raw_y = -1, -1
current_offset_x, current_offset_y = 0, 0
MOVE_TWEEN = pyautogui.easeInOutQuad

# 【新增】全局变量，用于记录拖拽开始时的固定偏移
drag_lock_offset_x = 0
drag_lock_offset_y = 0

def get_stable_random_pos(raw_x, raw_y):
    """普通移动/点击的随机坐标生成"""
    global last_raw_x, last_raw_y, current_offset_x, current_offset_y
    if raw_x == last_raw_x and raw_y == last_raw_y: pass
    else:
        current_offset_x = random.randint(-config.PIXEL_VARIANCE, config.PIXEL_VARIANCE)
        current_offset_y = random.randint(-config.PIXEL_VARIANCE, config.PIXEL_VARIANCE)
        last_raw_x, last_raw_y = raw_x, raw_y
    return raw_x + current_offset_x, raw_y + current_offset_y

def start_drag_lock(raw_x, raw_y):
    """【新增】开始拖拽：生成并锁定一个偏移量"""
    global drag_lock_offset_x, drag_lock_offset_y
    # 生成一个新的随机偏移，并在整个拖拽过程中复用它
    drag_lock_offset_x = random.randint(-config.PIXEL_VARIANCE, config.PIXEL_VARIANCE)
    drag_lock_offset_y = random.randint(-config.PIXEL_VARIANCE, config.PIXEL_VARIANCE)
    return raw_x + drag_lock_offset_x, raw_y + drag_lock_offset_y

def get_drag_pos(raw_x, raw_y):
    """【新增】获取拖拽过程中的坐标（使用锁定的偏移）"""
    return raw_x + drag_lock_offset_x, raw_y + drag_lock_offset_y

def human_move_to(x, y, duration=None):
    """普通悬停移动（带缓动）"""
    check_stop()
    tx, ty = get_stable_random_pos(x, y)
    if duration is None:
        curr_x, curr_y = pyautogui.position()
        dist = ((tx-curr_x)**2 + (ty-curr_y)**2)**0.5
        duration = 0.15 + (dist / 2000.0) 
    rand_dur = max(0.1, duration + random.uniform(-0.05, 0.05))
    pyautogui.moveTo(tx, ty, duration=rand_dur, tween=MOVE_TWEEN)

def human_drag_move(x, y, duration):
    """【新增】拖拽时的移动（线性，无新随机，无缓动）"""
    check_stop()
    # 使用锁定的偏移量，保证轨迹平行于录制轨迹
    tx, ty = get_drag_pos(x, y)
    # 强制线性移动，防止缓动造成拖拽迟滞
    pyautogui.moveTo(tx, ty, duration=duration, tween=pyautogui.linear)

def perform_human_click(x, y, is_double=False, button='left'):
    check_stop()
    tx, ty = get_stable_random_pos(x, y)
    pyautogui.mouseDown(x=tx, y=ty, button=button)
    time.sleep(random.uniform(0.08, 0.15))
    pyautogui.mouseUp(x=tx, y=ty, button=button)
    if is_double:
        time.sleep(random.uniform(0.05, 0.12))
        pyautogui.mouseDown(x=tx, y=ty, button=button)
        time.sleep(random.uniform(0.08, 0.15))
        pyautogui.mouseUp(x=tx, y=ty, button=button)

def get_dist(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
