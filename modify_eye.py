import pyautogui
import tkinter as tk
import tkinter.messagebox
import time
import os
import shutil
import glob
from pynput import mouse
import config
import utils
import traceback
import pyperclip

# =========================================================
# 1. 核心算法：拖拽模式识别
# =========================================================

def detect_drag_pattern(lines, start_idx):
    """ 智能识别滑块逻辑 """
    try:
        start_line = lines[start_idx]
        parts = start_line.split(",")
        if parts[0] != "click_press": return False, start_idx
        
        start_x = int(parts[1])
        start_y = int(parts[2])
        button = parts[3] 
        
        min_x, max_x = start_x, start_x
        search_limit = 500 
        
        for i in range(1, search_limit):
            curr_idx = start_idx + i
            if curr_idx >= len(lines): break
            
            line = lines[curr_idx]
            p = line.split(",")
            action = p[0]
            
            if action == "move":
                mx, my = int(p[1]), int(p[2])
                if mx < min_x: min_x = mx
                if mx > max_x: max_x = mx
                if abs(my - start_y) > 80: return False, start_idx
            
            elif action == "click_release":
                if len(p) > 3 and p[3] == button:
                    if (max_x - min_x) > 50: return True, curr_idx 
                    else: return False, start_idx
                else: return False, start_idx
            
            elif action in ["click_press", "key_press", "image_click"]:
                return False, start_idx
                
        return False, start_idx
    except: return False, start_idx

# =========================================================
# 2. 定点与截图工具
# =========================================================

def wait_for_stationary(prompt, duration=2.0):
    utils.log(prompt, "cyan")
    last_pos = pyautogui.position()
    start_t = time.time()
    
    while True:
        utils.check_stop()
        curr = pyautogui.position()
        dist = utils.get_dist(curr, last_pos)
        
        if dist > 5: 
            start_t = time.time()
            last_pos = curr
            if time.time() % 1.0 < 0.1: utils.log(prompt, "cyan")
        
        elapsed = time.time() - start_t
        if elapsed > duration: return last_pos
        time.sleep(0.05)

def capture_slider_roi():
    utils.log("🧩 进入滑块标识模式...", "yellow")
    time.sleep(0.5)
    
    p1 = wait_for_stationary("👉 移至滑块【左上角】 -> 静止2秒", 2.0)
    utils.log(f"📍 左上角: ({p1.x}, {p1.y})", "green")
    time.sleep(1)
    
    p2 = wait_for_stationary("👉 移至滑块【右下角】 -> 静止2秒", 2.0)
    utils.log(f"📍 右下角: ({p2.x}, {p2.y})", "green")
    time.sleep(0.5)
    
    left, top = min(p1.x, p2.x), min(p1.y, p2.y)
    width, height = abs(p1.x - p2.x), abs(p1.y - p2.y)
    
    if width < 5 or height < 5:
        utils.log("⚠️ 区域太小，无效", "red"); return None
    return (left, top, width, height)

def capture_gui(x, y):
    utils.log("📷 进入截图模式...", "white")
    time.sleep(0.5)
    
    p1 = wait_for_stationary("👉 移至【边界点 1】 -> 静止 3秒", 3.0)
    utils.log(f"📍 边界1: ({p1.x}, {p1.y})", "green")
    time.sleep(1.0)
    
    p2 = wait_for_stationary("👉 移至【边界点 2】 -> 静止 3秒", 3.0)
    utils.log(f"📍 边界2: ({p2.x}, {p2.y})", "green")
    time.sleep(0.5)
    
    left, top = min(p1.x, p2.x), min(p1.y, p2.y)
    width, height = abs(p1.x - p2.x), abs(p1.y - p2.y)
    
    if width < config.MIN_SIZE or height < config.MIN_SIZE:
        utils.log("⚠️ 区域太小，无效", "red"); return None
        
    return (left, top, width, height)

# =========================================================
# 3. 转换主逻辑 (所见即所得版)
# =========================================================

def run(root, filename):
    try:
        script_path = os.path.join(config.SCRIPTS_DIR, filename)
        if not os.path.exists(script_path): return

        with open(script_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        new_lines = []
        skip_until_index = -1 
        
        utils.log(f"🛠️ 开始转换: {filename}", "cyan")
        
        i = 0
        while i < len(lines):
            utils.check_stop()
            
            if i <= skip_until_index:
                i += 1; continue
                
            line = lines[i]
            parts = line.split(",")
            action = parts[0].strip()

            # =========================================================
            # A. 键盘按键 / 粘贴 / 滚动 -> 延迟后真实执行
            # =========================================================
            if action.startswith("key_") or action == "Paste" or action == "scroll":
                new_lines.append(line)
                
                # 提示倒计时，给用户反应时间
                utils.log(f"⏳ 3秒后执行动作: {action}...", "orange")
                time.sleep(1)
                utils.log(f"⏳ 2...", "orange"); time.sleep(1)
                utils.log(f"⏳ 1...", "orange"); time.sleep(1)
                
                # --- 真实执行，确保界面同步 ---
                try:
                    if action == "key_press":
                        pyautogui.keyDown(parts[1])
                        utils.log(f"⌨️ 按下: {parts[1]}", "gray")
                    elif action == "key_release":
                        pyautogui.keyUp(parts[1])
                    elif action == "scroll":
                        pyautogui.scroll(int(parts[4])*100)
                    elif action == "Paste":
                        # Paste,x,y,file,line
                        # 粘贴动作通常包含点击，这里为了简单只执行粘贴内容
                        # 完整的点击逻辑在录制中通常会有单独的 click，这里只负责填内容
                        # 如果需要模拟点击输入框：
                        tx, ty = int(parts[1]), int(parts[2])
                        utils.human_move_to(tx, ty); utils.perform_human_click(tx, ty, precise=True)
                        
                        fpath, lidx = parts[3], int(parts[4])
                        real_path = os.path.join(config.SCRIPTS_DIR, fpath) if not os.path.isabs(fpath) else fpath
                        if os.path.exists(real_path):
                            with open(real_path, 'r', encoding='utf-8') as df: 
                                content = df.readlines()[lidx-1].strip()
                            pyperclip.copy(content)
                            ctrl = 'command' if os.name == 'posix' else 'ctrl'
                            pyautogui.hotkey(ctrl, 'v')
                            utils.log(f"📋 已粘贴内容", "gray")
                except Exception as e:
                    print(f"执行动作出错: {e}")
                
                i += 1
                continue

            # =========================================================
            # B. 检测滑块
            # =========================================================
            is_slider_processed = False
            if action == "click_press":
                tx, ty = int(parts[1]), int(parts[2])
                is_slider, end_idx = detect_drag_pattern(lines, i)
                
                if is_slider:
                    utils.human_move_to(tx, ty)
                    try:
                        is_confirm = tkinter.messagebox.askyesno(
                            "AutoMaster 智能发现", 
                            "检测到水平拖拽，是滑块验证码吗？\n(是 -> 截图并跳过拖拽)\n(否 -> 当作普通点击)",
                            parent=utils.hud_instance.root
                        )
                    except: is_confirm = False 
                    
                    if is_confirm:
                        rect = capture_slider_roi()
                        if rect:
                            ts = int(time.time()); img_name = f"slider_{ts}.png"
                            save_path = os.path.join(config.CAPTCHA_FOLDER, img_name)
                            pyautogui.screenshot(region=rect).save(save_path)
                            utils.log(f"✅ 保存滑块: {img_name}", "#00FF00")
                            
                            rel_path = os.path.join("captchas", img_name).replace("\\", "/")
                            new_lines.append(f"image_click,{rel_path}")
                            skip_until_index = end_idx
                            
                            # 注意：转换模式下很难完美模拟滑块破解(需要AI介入)
                            # 所以这里我们不做物理拖拽，提示用户手动拖一下或者跳过
                            utils.log("⚠️ 请手动拖动滑块通过验证 (5秒等待)", "red")
                            time.sleep(5)
                            is_slider_processed = True

            if is_slider_processed:
                i += 1; continue

            # =========================================================
            # C. 点击操作 (截图 或 保留) -> 必须执行点击！
            # =========================================================
            if action in ["click_press", "image_click", "image_double_click"]:
                tx, ty = int(parts[1]), int(parts[2])
                
                utils.human_move_to(tx, ty)
                utils.log("📍 移动鼠标开启截图 (静止则保留坐标)", "white")
                
                start_wait = time.time()
                need_capture = False
                
                # 等待 3 秒判断意图
                while time.time() - start_wait < config.DWELL_TIME:
                    if utils.get_dist(pyautogui.position(), (tx, ty)) > config.MOVE_THRESHOLD:
                        need_capture = True; break
                    time.sleep(0.1)
                
                final_x, final_y = tx, ty # 默认点击位置
                
                if need_capture:
                    # 进入截图流程
                    rect = capture_gui(tx, ty)
                    if rect:
                        ts = int(time.time()); img_name = f"target_{ts}.png"
                        save_path = os.path.join(config.IMG_FOLDER, img_name)
                        pyautogui.screenshot(region=rect).save(save_path)
                        
                        cmd = "image_double_click" if "double" in line else "image_click"
                        rel_path = os.path.join("images", img_name).replace("\\", "/")
                        new_lines.append(f"{cmd},{rel_path}")
                        
                        # 更新点击位置为截图中心
                        final_x = rect[0] + rect[2] // 2
                        final_y = rect[1] + rect[3] // 2
                        
                        # 跳过后续 release
                        for k in range(i + 1, min(i + 50, len(lines))):
                            if "click_release" in lines[k]:
                                skip_until_index = max(skip_until_index, k); break
                    else:
                        new_lines.append(line) # 截图取消
                else:
                    # 未移动鼠标，保留原指令
                    new_lines.append(line)
                    utils.log("⚓ 保留原始坐标", "gray")

                # =================================================
                # 【关键逻辑】无论是否截图，都执行一次点击，确保界面跳转
                # =================================================
                utils.log("⚡ 执行点击，同步界面状态...", "green")
                is_dbl = ("double" in line)
                utils.perform_human_click(final_x, final_y, is_double=is_dbl, precise=True)
            
            # =========================================================
            # D. 其他指令 (如单纯的 Move)
            # =========================================================
            else:
                new_lines.append(line)
                
            i += 1

        name, ext = os.path.splitext(filename)
        new_filename = f"{name}_smart{ext}"
        new_path = os.path.join(config.SCRIPTS_DIR, new_filename)
        with open(new_path, "w", encoding="utf-8") as f: f.write("\n".join(new_lines))
        
        utils.log(f"🎉 完成: {new_filename}", "#00FF00")
        tkinter.messagebox.showinfo("成功", f"新脚本已生成：\n{new_filename}", parent=utils.hud_instance.root)

    except Exception as e:
        traceback.print_exc()
        utils.log("❌ 发生错误", "red")
