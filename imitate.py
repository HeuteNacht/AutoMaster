import pyautogui
import time
import os
import random
import traceback
from pynput import keyboard
import tkinter.messagebox # 【新增】用于弹窗
import utils
import config

def wait_for_stationary_start():
    """
    【新增】等待鼠标在某处静止 3 秒，作为截图的起始点（左上角）
    """
    utils.log("👉 请将鼠标移至目标【左上角】并静止 3秒...", "cyan")
    
    last_pos = pyautogui.position()
    stable_start_time = time.time()
    
    while True:
        utils.check_stop()
        curr_pos = pyautogui.position()
        dist = utils.get_dist(curr_pos, last_pos)
        
        # 如果移动了，重置计时器
        if dist > 5: # 5像素容差
            stable_start_time = time.time()
            last_pos = curr_pos
            # 只有当时间被重置时才更新UI，避免闪烁，但要保持提示
            if time.time() % 1.0 < 0.1: 
                utils.log("👉 请移至左上角 -> 静止 3秒", "cyan")
        
        # 计算静止时长
        elapsed = time.time() - stable_start_time
        remaining = 3.0 - elapsed
        
        if remaining <= 0:
            # 静止时间达标
            return last_pos
        
        time.sleep(0.1)

def track_gesture_update(start_pos):
    """
    【修改】基于确定的起点，等待用户划动并静止以确认终点
    """
    utils.log("🟢 起点已锁定！请向右下划动框选...", "#00FF00")
    # 播放提示音 (可选)
    # print('\a')
    
    path = [start_pos]
    moving = False
    last_pos_time = time.time()
    last_pos = start_pos
    
    while True:
        utils.check_stop()
        curr = pyautogui.position()
        
        # 检测是否开始移动（划框）
        if utils.get_dist(curr, start_pos) > config.MOVE_THRESHOLD:
            moving = True
            path.append(curr)
            
            # 检测是否在终点停住了 (静止 2秒 确认)
            if utils.get_dist(curr, last_pos) < config.JITTER_TOLERANCE:
                if time.time() - last_pos_time > 2.0:
                    # 确认框选结束
                    xs, ys = [p[0] for p in path], [p[1] for p in path]
                    w, h = max(xs) - min(xs), max(ys) - min(ys)
                    return (min(xs), min(ys), w, h)
            else:
                # 还在移动，更新最后位置的时间
                last_pos_time = time.time()
                last_pos = curr
                
            # 实时显示当前大小
            curr_w = abs(curr[0] - start_pos[0])
            curr_h = abs(curr[1] - start_pos[1])
            utils.log(f"📐 当前区域: {curr_w}x{curr_h}", "yellow")
            
        time.sleep(0.05)

def smart_locate(img_path):
    """
    智能找图：自动重试 -> 障碍物清除交互 -> 重新查找 -> 手势更新
    """
    start = time.time()
    attempt = 1
    
    # === 阶段一：初始自动重试 (避让鼠标) ===
    # 稍微减少这里的重试时间，因为后面有人工介入
    while time.time() - start < 3.0: 
        utils.check_stop()
        try:
            loc = pyautogui.locateCenterOnScreen(img_path, confidence=0.8, grayscale=True)
            if loc: return loc
        except: pass
        
        utils.log(f"⚠️ 未找到(第{attempt}次)，避让...", "orange")
        cx, cy = pyautogui.position()
        pyautogui.moveTo(cx + 200, cy + 200, 0.2)
        time.sleep(1)
        attempt += 1

    # === 阶段二：障碍物清除循环 ===
    while True:
        utils.check_stop()
        utils.log("⏳ 请在 3秒 内帮我去除障碍物...", "magenta")
        time.sleep(3)
        
        # 弹窗询问 (使用 utils.hud_instance.root 作为父窗口，避免弹窗在后面)
        # 注意：askyesno 会阻塞线程，这正是我们需要的
        is_cleared = tkinter.messagebox.askyesno(
            "AutoMaster 助手", 
            "是否移除障碍物完毕？", 
            parent=utils.hud_instance.root
        )
        
        if is_cleared: # 用户选“是”
            utils.log("🔄 正在重新搜索图片...", "white")
            
            # 再次尝试查找 2 次
            for i in range(2):
                utils.check_stop()
                try:
                    loc = pyautogui.locateCenterOnScreen(img_path, confidence=0.8, grayscale=True)
                    if loc: 
                        utils.log("✅ 障碍清除后找到了！", "#00FF00")
                        return loc
                except: pass
                time.sleep(1)
            
            # 如果找了2次还是没找到，跳出循环，进入阶段三（更新截图）
            break 
            
        else: # 用户选“否”
            # 继续循环提示去除障碍物
            continue

    # === 阶段三：手势更新截图 (防误触版) ===
    utils.log("❌ 仍未找到。请告知更新范围...", "red")
    time.sleep(1.5)
    
    # 1. 等待用户在左上角静止 3秒
    start_pos = wait_for_stationary_start()
    
    # 2. 开始划动轨迹
    rect = track_gesture_update(start_pos)
    ux, uy, uw, uh = rect
    
    # 3. 校验尺寸
    if uw < 10: uw = 10
    if uh < 10: uh = 10
    
    # 4. 执行修复
    utils.log("💾 正在更新图片...", "yellow")
    pyautogui.screenshot(region=(ux, uy, uw, uh)).save(img_path)
    utils.log("✅ 图片已修复，继续执行", "#00FF00")
    
    return pyautogui.Point(ux + uw // 2, uy + uh // 2)

def execute_playback(filepath):
    if not os.path.exists(filepath): return
    with open(filepath, "r", encoding="utf-8") as f: lines = f.readlines()
    
    utils.log(f"🚀 执行: {os.path.basename(filepath)}", "#00FFFF")
    
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
                
                # 调用新的智能查找逻辑
                loc = smart_locate(img)
                
                if loc:
                    utils.log("✅ 锁定 -> 操作")
                    utils.human_move_to(loc.x, loc.y)
                    time.sleep(0.5)
                    utils.perform_human_click(loc.x, loc.y, action == "image_double_click")
                continue

            # --- 普通指令部分保持不变 ---
            raw_d = float(parts[-1]) if parts[-1] else 0.1
            if raw_d < 0.3:
                real_d = max(0.02, raw_d)
            else:
                real_d = max(0.1, raw_d * config.SPEED_FACTOR + random.uniform(-0.1, 0.1))
            
            if action == "move":
                tx, ty = int(parts[1]), int(parts[2])
                if is_dragging:
                    utils.human_drag_move(tx, ty, duration=raw_d)
                else:
                    move_dur = max(real_d * 0.8, 0.05) if raw_d >= 0.3 else 0.02
                    utils.human_move_to(tx, ty, move_dur)
                    
            elif action == "click_press":
                btn = parts[3].replace("Button.", "")
                rx, ry = int(parts[1]), int(parts[2])
                is_dragging = True
                tx, ty = utils.start_drag_lock(rx, ry)
                utils.log(f"🖱️ 按下 {btn}")
                time.sleep(real_d)
                pyautogui.mouseDown(x=tx, y=ty, button=btn, _pause=False)
                
            elif action == "click_release":
                btn = parts[3].replace("Button.", "")
                rx, ry = int(parts[1]), int(parts[2])
                tx, ty = utils.get_drag_pos(rx, ry)
                is_dragging = False
                utils.log(f"🖱️ 松开 {btn}")
                pyautogui.mouseUp(x=tx, y=ty, button=btn, _pause=False)
                
            elif action == "scroll":
                scroll_amount = int(parts[4])
                utils.log(f"📜 滚动 {scroll_amount}")
                pyautogui.scroll(scroll_amount * 100)
                time.sleep(real_d)
                
            elif action == "key_press":
                k = parts[1].replace("'", "")
                utils.log(f"⌨️ 按键: {k}")
                if k != 'None': pyautogui.keyDown(k)
                time.sleep(real_d)
                
            elif action == "key_release":
                k = parts[1].replace("'", "")
                if k != 'None': pyautogui.keyUp(k)
        
        except Exception as e:
            traceback.print_exc()
            utils.log(f"⚠️ 异常: {e}", "red")

    utils.log(f"✅ 执行结束", "#00FF00")

def run(filepath):
    config.STOP_EVENT.clear() 
    execute_playback(filepath)
