import time
from pynput import mouse, keyboard
import config
import utils

def run(filepath):
    utils.log("🔴 正在录制... [ESC]结束 [F4]中止", "red")
    
    # 重置停止信号
    config.STOP_EVENT.clear()
    
    record_data = []
    last_time = time.time()
    last_move_time = 0
    MIN_MOVE_INTERVAL = 0.02 # 【优化】稍微调小间隔，让拖拽更顺滑

    def get_delay():
        nonlocal last_time
        curr = time.time()
        delay = curr - last_time
        last_time = curr
        return round(delay, 4)

    def on_move(x, y):
        # 即使在录制，也要响应停止信号
        if config.STOP_EVENT.is_set(): return False
        
        nonlocal last_move_time
        curr = time.time()
        if curr - last_move_time < MIN_MOVE_INTERVAL: return
        record_data.append(f"move,{x},{y},{get_delay()}")
        last_move_time = curr

    def on_click(x, y, button, pressed):
        if config.STOP_EVENT.is_set(): return False
        act = "click_press" if pressed else "click_release"
        # 【修复】兼容 Button.middle 和 Button.left/right
        btn_name = str(button).replace("Button.", "")
        record_data.append(f"{act},{x},{y},{btn_name},{get_delay()}")

    def on_scroll(x, y, dx, dy):
        if config.STOP_EVENT.is_set(): return False
        # 【修复】dy 通常是 1 或 -1，记录下来
        record_data.append(f"scroll,{x},{y},{dx},{dy},{get_delay()}")

    def on_release(key):
        if config.STOP_EVENT.is_set(): return False
        if key == keyboard.Key.esc: return False
        # F4 停止逻辑在 main.py 处理，这里只需正常记录按键
        
        try: k = key.char
        except: k = str(key).replace("Key.", "")
        record_data.append(f"key_release,{k},{get_delay()}")

    def on_press(key):
        if config.STOP_EVENT.is_set(): return False
        try: k = key.char
        except: k = str(key).replace("Key.", "")
        record_data.append(f"key_press,{k},{get_delay()}")

    # 启动监听
    with mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll) as ml, \
         keyboard.Listener(on_press=on_press, on_release=on_release) as kl:
        # 主线程等待，同时检查停止信号
        while ml.running and kl.running:
            if config.STOP_EVENT.is_set():
                ml.stop()
                kl.stop()
                utils.log("🛑 录制被强制终止", "gray")
                return # 强制停止不保存
            time.sleep(0.1)

    # 正常结束才保存
    if not config.STOP_EVENT.is_set():
        with open(filepath, "w", encoding="utf-8") as f:
            for line in record_data: f.write(line + "\n")
        utils.log(f"✅ 录制结束", "#00FF00")
