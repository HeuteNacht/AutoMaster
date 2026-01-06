import pyautogui
import time
import os
import random
import traceback
from pynput import keyboard
import utils
import config

# (track_gesture_help 和 smart_locate 保持不变，请直接保留原代码)
def track_gesture_help():
    path = []
    moving = False
    start_t = time.time()
    last = pyautogui.position()
    path.append(last)
    while True:
        utils.check_stop()
        curr = pyautogui.position()
        if utils.get_dist(curr, last) > config.JITTER_TOLERANCE:
            start_t = time.time()
            last = curr
            path.append(curr)
            if not moving and len(path)>5: moving = True
        
        rem = max(0.0, 2.0 - (time.time()-start_t))
        if moving:
            xs, ys = [p[0] for p in path], [p[1] for p in path]
            w, h = max(xs)-min(xs), max(ys)-min(ys)
            if rem > 0: utils.log(f"🖍️ 感知区域 {w}x{h}...\n🛑 停住 {rem:.1f}s 确认", "yellow")
            else: return (min(xs), min(ys), w, h)
        else:
            utils.log(f"❓ 找不到图! 请圈出位置...", "red")
        time.sleep(0.05)

def smart_locate(img_path):
    start = time.time()
    attempt = 1
    while time.time() - start < config.MAX_RETRY_DURATION:
        utils.check_stop()
        try:
            loc = pyautogui.locateCenterOnScreen(img_path, confidence=0.8, grayscale=True)
            if loc: return loc
        except: pass
        utils.log(f"⚠️ 未找到(第{attempt}次)，避让...", "orange")
        cx, cy = pyautogui.position()
        pyautogui.moveTo(cx+200, cy+200, 0.2)
        time.sleep(1)
        attempt += 1
    
    while True:
        utils.check_stop()
        rect = track_gesture_help()
        ux, uy, uw, uh = rect
        if uw<10: uw=10
        if uh<10: uh=10
        search_reg = (max(0,int(ux-uw*0.5)), max(0,int(uy-uh*0.5)), int(uw*2), int(uh*2))
        
        utils.log("🔍 深度搜索...", "cyan")
        loc = pyautogui.locateCenterOnScreen(img_path, region=search_reg, confidence=0.7, grayscale=True)
        if loc: 
            utils.log("✅ 找到了！", "#00FF00")
            return loc
        
        utils.log("❌ 找不到。按 [Space] 修复，[ESC] 跳过", "red")
        act = "wait"
        def on_k(k):
            nonlocal act
            if k == keyboard.Key.space: act="fix"; return False
            if k == keyboard.Key.esc: act="skip"; return False
        with keyboard.Listener(on_press=on_k) as l: l.join()
        
        if act == "skip": return None
        if act == "fix":
            utils.log("💾 修复图片...", "yellow")
            pyautogui.screenshot(region=(ux, uy, uw, uh)).save(img_path)
            utils.log("✅ 修复完成", "#00FF00")
            return pyautogui.Point(ux+uw//2, uy+uh//2)

def execute_playback(filepath):
    if not os.path.exists(filepath): return
    with open(filepath, "r", encoding="utf-8") as f: lines = f.readlines()
    
    utils.log(f"🚀 执行: {os.path.basename(filepath)}", "#00FFFF")
    
    # 【新增】拖拽状态标记
    is_dragging = False
    
    for i, line in enumerate(lines):
        utils.check_stop()
        
        line = line.strip()
        if not line: continue
        parts = line.split(",")
        action = parts[0]
        
        try:
            if action == "Script":
                target = os.path.join(config.SCRIPTS_DIR, parts[1])
                if not os.path.exists(target):
                    target = os.path.join(parts[2], parts[1])
                utils.log(f"↪️ 子脚本: {parts[1]}", "orange")
                execute_playback(target)
                continue

            if action in ["image_click", "image_double_click"]:
                img = parts[1]
                if not os.path.exists(img):
                    utils.log(f"❌ 图片缺失: {img}", "red"); continue
                
                utils.log(f"👁️ 搜索: {os.path.basename(img)}", "yellow")
                loc = smart_locate(img)
                if loc:
                    utils.log("✅ 锁定 -> 操作")
                    utils.human_move_to(loc.x, loc.y)
                    time.sleep(0.5)
                    utils.perform_human_click(loc.x, loc.y, action=="image_double_click")
                continue

            # 普通指令
            raw_d = float(parts[-1]) if parts[-1] else 0.1
            real_d = max(0.05, raw_d) if raw_d < 0.3 else max(0.1, raw_d * config.SPEED_FACTOR + random.uniform(-0.1,0.1))
            
            if action == "move":
                tx, ty = int(parts[1]), int(parts[2])
                
                if is_dragging:
                    # 【核心修改】如果是拖拽状态，使用专用函数
                    # 拖拽时，移动时间通常就是录制的间隔，保持线性
                    utils.human_drag_move(tx, ty, duration=raw_d) # 使用 raw_d 保持原始节奏，或 real_d
                else:
                    # 正常悬停移动
                    move_dur = max(real_d * 0.8, 0.05) if raw_d >= 0.3 else 0.02
                    utils.human_move_to(tx, ty, move_dur)
                    
            elif action == "click_press":
                btn = parts[3].replace("Button.", "")
                rx, ry = int(parts[1]), int(parts[2])
                
                # 【核心修改】按下时，开启拖拽模式，锁定随机偏移
                is_dragging = True
                tx, ty = utils.start_drag_lock(rx, ry)
                
                utils.log(f"🖱️ 按下 {btn}")
                time.sleep(real_d)
                pyautogui.mouseDown(x=tx, y=ty, button=btn)
                
            elif action == "click_release":
                btn = parts[3].replace("Button.", "")
                rx, ry = int(parts[1]), int(parts[2])
                
                # 【核心修改】松开时，使用锁定的偏移，并结束拖拽模式
                tx, ty = utils.get_drag_pos(rx, ry)
                is_dragging = False
                
                utils.log(f"🖱️ 松开 {btn}")
                time.sleep(random.uniform(0.05, 0.1))
                pyautogui.mouseUp(x=tx, y=ty, button=btn)
                
            elif action == "scroll":
                scroll_amount = int(parts[4])
                utils.log(f"📜 滚动 {scroll_amount}")
                pyautogui.scroll(scroll_amount * 100)
                time.sleep(real_d)
            elif action == "key_press":
                k = parts[1].replace("'", "")
                utils.log(f"⌨️ 按键: {k}")
                if k!='None': pyautogui.keyDown(k)
                time.sleep(real_d)
            elif action == "key_release":
                k = parts[1].replace("'", "")
                if k!='None': pyautogui.keyUp(k)
        
        except Exception as e:
            traceback.print_exc()
            utils.log(f"⚠️ 异常: {e}", "red")

    utils.log(f"✅ 执行结束", "#00FF00")

def run(filepath):
    config.STOP_EVENT.clear() 
    execute_playback(filepath)
