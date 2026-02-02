import time
from pynput import mouse, keyboard
import config
import utils
import math

def run(filepath):
    utils.log("🔴 正在录制... [ESC]结束 [F4]中止", "red")
    
    config.STOP_EVENT.clear()
    
    record_data = []
    last_time = time.time()
    last_move_time = 0
    
    # 【新增】记录上一次坐标，用于计算距离
    last_x, last_y = 0, 0
    MIN_DIST_sq = 25 # 最小移动距离平方 (5像素)，小于此距离不记录move

    def get_delay():
        nonlocal last_time
        curr = time.time()
        delay = curr - last_time
        last_time = curr
        return round(delay, 4)

    def on_move(x, y):
        if config.STOP_EVENT.is_set(): return False
        
        nonlocal last_move_time, last_x, last_y
        curr = time.time()
        
        # 【优化】过滤高频微小移动
        # 1. 时间间隔检查 (0.05s)
        if curr - last_move_time < 0.05: return
        
        # 2. 距离间隔检查 (防止原地抖动)
        dist_sq = (x - last_x)**2 + (y - last_y)**2
        if dist_sq < MIN_DIST_sq: return

        record_data.append(f"move,{x},{y},{get_delay()}")
        last_move_time = curr
        last_x, last_y = x, y

    def on_click(x, y, button, pressed):
        if config.STOP_EVENT.is_set(): return False
        act = "click_press" if pressed else "click_release"
        btn_name = str(button).replace("Button.", "")
        record_data.append(f"{act},{x},{y},{btn_name},{get_delay()}")

    def on_scroll(x, y, dx, dy):
        if config.STOP_EVENT.is_set(): return False
        record_data.append(f"scroll,{x},{y},{dx},{dy},{get_delay()}")

    def on_release(key):
        if config.STOP_EVENT.is_set(): return False
        if key == keyboard.Key.esc: return False
        try: k = key.char
        except: k = str(key).replace("Key.", "")
        record_data.append(f"key_release,{k},{get_delay()}")

    def on_press(key):
        if config.STOP_EVENT.is_set(): return False
        try: k = key.char
        except: k = str(key).replace("Key.", "")
        record_data.append(f"key_press,{k},{get_delay()}")

    with mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll) as ml, \
         keyboard.Listener(on_press=on_press, on_release=on_release) as kl:
        while ml.running and kl.running:
            if config.STOP_EVENT.is_set():
                ml.stop()
                kl.stop()
                utils.log("🛑 录制被强制终止", "gray")
                return 
            time.sleep(0.1)

    if not config.STOP_EVENT.is_set():
        with open(filepath, "w", encoding="utf-8") as f:
            for line in record_data: f.write(line + "\n")
        utils.log(f"✅ 录制结束", "#00FF00")
