import tkinter as tk
import random
import time
import math
import pyautogui
# import numpy as np # 不需要 numpy
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

# =========================================================
# 拟人化核心算法
# =========================================================

last_raw_x, last_raw_y = -1, -1
current_offset_x, current_offset_y = 0, 0
drag_lock_offset_x, drag_lock_offset_y = 0, 0

def get_stable_random_pos(raw_x, raw_y):
    global last_raw_x, last_raw_y, current_offset_x, current_offset_y
    if raw_x == last_raw_x and raw_y == last_raw_y: pass
    else:
        current_offset_x = random.randint(-config.PIXEL_VARIANCE, config.PIXEL_VARIANCE)
        current_offset_y = random.randint(-config.PIXEL_VARIANCE, config.PIXEL_VARIANCE)
        last_raw_x, last_raw_y = raw_x, raw_y
    return raw_x + current_offset_x, raw_y + current_offset_y

def start_drag_lock(raw_x, raw_y):
    global drag_lock_offset_x, drag_lock_offset_y
    drag_lock_offset_x = random.randint(-config.PIXEL_VARIANCE, config.PIXEL_VARIANCE)
    drag_lock_offset_y = random.randint(-config.PIXEL_VARIANCE, config.PIXEL_VARIANCE)
    return raw_x + drag_lock_offset_x, raw_y + drag_lock_offset_y

def get_drag_pos(raw_x, raw_y):
    return raw_x + drag_lock_offset_x, raw_y + drag_lock_offset_y

# --- 贝塞尔曲线算法 ---
def calculate_bezier_point(t, p0, p1, p2, p3):
    u = 1 - t
    tt = t * t
    uu = u * u
    uuu = uu * u
    ttt = tt * t
    res = (uuu * p0) + (3 * uu * t * p1) + (3 * u * tt * p2) + (ttt * p3)
    return res

# --- 【关键修复】独立的直线移动函数 ---
def human_move_to_linear(x, y, duration=None):
    """ 
    专门用于短距离移动。
    它直接调用 pyautogui，绝不回调其他逻辑，从而切断死循环。
    """
    tx, ty = get_stable_random_pos(x, y)
    if duration is None: duration = 0.1
    # 强制使用线性移动
    pyautogui.moveTo(tx, ty, duration=duration, tween=pyautogui.linear)

def human_curl_move(target_x, target_y, duration=None):
    """ 智能顺滑移动 """
    check_stop()
    start_x, start_y = pyautogui.position()
    dist = math.hypot(target_x - start_x, target_y - start_y)
    
    # 【核心修复点】
    # 之前这里错误地调用了 human_move_to，导致死循环。
    # 现在改为调用 human_move_to_linear。
    if dist < 50:
        human_move_to_linear(target_x, target_y, duration) 
        return

    if duration is None:
        duration = 0.3 + (dist / 1500.0) 
    
    # 随机控制点
    control_1_x = start_x + (target_x - start_x) * 0.3 + random.randint(-80, 80)
    control_1_y = start_y + (target_y - start_y) * 0.3 + random.randint(-80, 80)
    control_2_x = start_x + (target_x - start_x) * 0.7 + random.randint(-80, 80)
    control_2_y = start_y + (target_y - start_y) * 0.7 + random.randint(-80, 80)

    fps = 60
    steps = int(max(15, duration * fps))
    
    start_time = time.time()
    
    for i in range(steps + 1):
        check_stop()
        t = i / steps
        next_x = calculate_bezier_point(t, start_x, control_1_x, control_2_x, target_x)
        next_y = calculate_bezier_point(t, start_y, control_1_y, control_2_y, target_y)
        
        try:
            pyautogui.platformModule._moveTo(int(next_x), int(next_y))
        except:
            pyautogui.moveTo(int(next_x), int(next_y))
        
        expected_time = (i / steps) * duration
        elapsed = time.time() - start_time
        if elapsed < expected_time:
            time.sleep(expected_time - elapsed)

def human_move_to(x, y, duration=None):
    """ 统一入口 """
    tx, ty = get_stable_random_pos(x, y)
    
    if duration is None:
        curr_x, curr_y = pyautogui.position()
        dist = ((tx-curr_x)**2 + (ty-curr_y)**2)**0.5
        duration = 0.15 + (dist / 2000.0) 
    
    real_dur = max(0.1, duration / config.SPEED_FACTOR) 
    
    # 这里调用曲线移动，如果距离近，human_curl_move 内部会转交给 linear
    human_curl_move(tx, ty, real_dur)

def human_drag_move(x, y, duration):
    check_stop()
    tx, ty = get_drag_pos(x, y)
    pyautogui.moveTo(tx, ty, duration=duration, tween=pyautogui.linear)

def perform_human_click(x, y, is_double=False, button='left', precise=False):
    check_stop()
    if precise:
        tx, ty = x, y
        hold_time = 0.15 
    else:
        tx, ty = get_stable_random_pos(x, y)
        hold_time = random.uniform(0.08, 0.15)
        
    pyautogui.mouseDown(x=tx, y=ty, button=button)
    time.sleep(hold_time)
    pyautogui.mouseUp(x=tx, y=ty, button=button)
    
    if is_double:
        time.sleep(random.uniform(0.05, 0.12))
        pyautogui.mouseDown(x=tx, y=ty, button=button)
        time.sleep(hold_time)
        pyautogui.mouseUp(x=tx, y=ty, button=button)

def get_dist(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
