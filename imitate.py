import pyautogui
import time
import os
import random
import traceback
import io
import pyperclip
import tkinter.messagebox
import utils
import config
import slider_solver

# =========================================================
# 1. 辅助功能：滑块破解
# =========================================================

def try_solve_slider(btn_x, btn_y):
    """ 尝试自动破解滑块验证码 """
    utils.log("🧩 正在尝试自动破解滑块...", "cyan")
    
    # 估算验证码背景图区域 (假设在按钮上方)
    # 你可以根据实际情况调整 w, h 和偏移量
    w, h = 340, 200 
    left = max(0, btn_x - 30)
    top = max(0, btn_y - h - 10)
    
    # 截图
    bg_img = pyautogui.screenshot(region=(int(left), int(top), int(w), int(h)))
    arr = io.BytesIO()
    bg_img.save(arr, format='PNG')
    
    # 调用 AI 或 算法识别缺口
    gap_x = slider_solver.get_gap_distance(arr.getvalue())
    
    if not gap_x:
        utils.log("❌ 无法识别缺口位置", "red")
        return False
    
    utils.log(f"🎯 缺口识别成功: {gap_x}px", "white")
    
    # 生成拟人化轨迹
    tracks = slider_solver.generate_tracks(gap_x)
    
    # 执行拖拽
    utils.human_move_to(btn_x, btn_y)
    time.sleep(0.2)
    pyautogui.mouseDown()
    
    for x, y, t in tracks:
        pyautogui.moveRel(x, y, duration=t, tween=pyautogui.linear)
        
    time.sleep(0.5)
    pyautogui.mouseUp()
    time.sleep(2.0) # 等待验证结果
    return True

# =========================================================
# 2. 智能找图逻辑
# =========================================================

def smart_locate(img_path):
    """
    智能找图：自动重试 -> 检查验证码 -> 人工介入 -> 更新截图
    """
    start = time.time()
    
    # --- 阶段一：自动快速查找 (3秒) ---
    while time.time() - start < 3.0: 
        utils.check_stop()
        try:
            loc = pyautogui.locateCenterOnScreen(img_path, confidence=0.8, grayscale=True)
            if loc: return loc
        except: pass
        
        # 快速轮询，提高响应速度
        time.sleep(0.1) 

    # --- 阶段二：检查是否出现了验证码 (自动处理) ---
    if os.path.exists(config.CAPTCHA_FOLDER):
        for f in os.listdir(config.CAPTCHA_FOLDER):
            if "slider" in f:
                path = os.path.join(config.CAPTCHA_FOLDER, f)
                try:
                    loc = pyautogui.locateCenterOnScreen(path, confidence=0.8)
                    if loc:
                        # 发现屏幕上有滑块特征，尝试破解
                        if try_solve_slider(loc.x, loc.y): 
                            return None # 破解动作已执行，无需返回坐标
                except: pass

    # --- 阶段三：人工介入 (找不到图时) ---
    # 弹窗询问，此时脚本暂停
    utils.log("❓ 找不到目标，请求人工介入...", "orange")
    choice = tkinter.messagebox.askyesno(
        "AutoMaster 助手", 
        "未找到目标图片，是否存在障碍物？\n\n【是】我已移除障碍物，请重试\n【否】目标样式变了，请重新截图", 
        parent=utils.hud_instance.root
    )
    
    if choice: # 用户选“是” -> 重试
        utils.log("🔄 正在重新搜索...", "white")
        time.sleep(2)
        try:
            return pyautogui.locateCenterOnScreen(img_path, confidence=0.8)
        except: pass
    
    else: # 用户选“否” -> 更新截图
        utils.log("📷 进入更新模式...", "yellow")
        import modify_eye # 动态导入，避免循环依赖
        
        # 复用 modify_eye 的双点定界功能
        rect = modify_eye.capture_gui(0, 0) 
        if rect:
            utils.log("💾 保存新截图...", "green")
            pyautogui.screenshot(region=rect).save(img_path)
            # 返回新截图的中心点，让脚本继续运行
            return pyautogui.Point(rect[0] + rect[2]//2, rect[1] + rect[3]//2)
            
    return None

# =========================================================
# 3. 路径拟合优化 (新增)
# =========================================================

def optimize_paths(lines):
    """
    分析录制脚本，合并密集的 move 指令，生成稀疏的关键点。
    这样可以让 utils.human_curl_move 发挥作用，画出平滑曲线。
    """
    optimized = []
    move_buffer = []

    for line in lines:
        line = line.strip()
        if not line: continue
        parts = line.split(",")
        
        # 如果是移动指令，先存起来
        if parts[0] == "move":
            move_buffer.append(line)
        else:
            # 遇到非移动指令（点击、按键等），先结算之前的移动
            if move_buffer:
                # 策略：只保留最后一次移动作为终点
                # 中间的轨迹交给 utils.human_curl_move 的贝塞尔算法去生成
                last_move = move_buffer[-1]
                
                # 计算这段路径的总耗时，作为移动的参考时间
                total_delay = 0
                for m in move_buffer:
                    p = m.split(",")
                    total_delay += float(p[3]) if len(p)>3 else 0.01
                
                # 重构 move 指令，把累加的时间放进去
                lm_parts = last_move.split(",")
                # move, x, y, total_delay
                optimized.append(f"move,{lm_parts[1]},{lm_parts[2]},{total_delay}")
                
                move_buffer = [] # 清空缓冲
            
            # 添加当前非移动指令
            optimized.append(line)
            
    # 处理末尾剩余的 move
    if move_buffer:
        last_move = move_buffer[-1]
        lm_parts = last_move.split(",")
        optimized.append(f"move,{lm_parts[1]},{lm_parts[2]},0.1")
        
    return optimized

# =========================================================
# 4. 执行主逻辑
# =========================================================

def execute_playback(filepath):
    if not os.path.exists(filepath): return
    
    with open(filepath, "r", encoding="utf-8") as f: 
        raw_lines = f.readlines()
    
    # 【新增】执行前先进行路径拟合优化
    # 这会将几百行密集的 move 压缩成几十个关键点
    lines = optimize_paths(raw_lines)
    
    utils.log(f"🚀 执行: {os.path.basename(filepath)} (路径已优化)", "#00FFFF")
    
    is_dragging = False
    
    for line in lines:
        utils.check_stop()
        line = line.strip()
        if not line: continue
        
        p = line.split(",")
        action = p[0]
        
        try:
            # === 指令 1: Paste (自动填表) ===
            if action == "Paste": 
                # Paste,x,y,filepath,line_index
                if len(p) < 5: continue
                tx, ty, fpath, lidx = int(p[1]), int(p[2]), p[3], int(p[4])
                
                # 路径处理
                real_path = os.path.join(config.SCRIPTS_DIR, fpath) if not os.path.isabs(fpath) else fpath
                if not os.path.exists(real_path):
                    real_path = os.path.join(config.BASE_DIR, fpath)

                if os.path.exists(real_path):
                    with open(real_path, 'r', encoding='utf-8') as df: 
                        file_content = df.readlines()
                        if 1 <= lidx <= len(file_content):
                            content = file_content[lidx-1].strip()
                            
                            # 动作：移动 -> 点击 -> 粘贴
                            utils.human_move_to(tx, ty)
                            utils.perform_human_click(tx, ty, precise=True)
                            pyperclip.copy(content)
                            
                            ctrl_key = 'command' if os.name == 'posix' else 'ctrl'
                            pyautogui.hotkey(ctrl_key, 'v')
                            time.sleep(0.2)
                        else:
                            utils.log(f"⚠️ 行号越界: {lidx}", "orange")
                else:
                    utils.log(f"❌ 文件未找到: {fpath}", "red")
                continue

            # === 指令 2: Image Click (智能找图) ===
            if action in ["image_click", "image_double_click"]:
                img = p[1]
                if not os.path.exists(img): 
                    img = os.path.join(config.IMG_FOLDER, img)
                
                # 调用智能找图
                loc = smart_locate(img) 
                if loc:
                    utils.human_move_to(loc.x, loc.y)
                    # 【核心修复】启用 precise=True (精准模式)
                    # 解决勾选框点不上的问题
                    is_double = (action == "image_double_click")
                    utils.perform_human_click(loc.x, loc.y, is_double=is_double, precise=True)
                continue

            # === 指令 3: Script (嵌套脚本) ===
            if action == "Script":
                sub_script = p[1]
                target_path = os.path.join(config.SCRIPTS_DIR, sub_script)
                if os.path.exists(target_path):
                    utils.log(f"↪️ 调用子脚本: {sub_script}", "cyan")
                    execute_playback(target_path)
                continue

            # === 普通指令 (Move, Click, Key...) ===
            
            # 解析延迟时间
            raw_d = float(p[-1]) if p[-1] else 0.1
            # 计算真实延迟：应用倍速系数 + 随机微扰
            # 注意：SPEED_FACTOR 在 main.py 里已被处理为延迟系数 (1/速度)
            if raw_d < 0.3: 
                real_d = max(0.02, raw_d)
            else: 
                real_d = max(0.1, raw_d * config.SPEED_FACTOR + random.uniform(-0.1, 0.1))

            if action == "move":
                tx, ty = int(p[1]), int(p[2])
                if is_dragging: 
                    # 拖拽状态下：保持线性移动，确保不松脱
                    utils.human_drag_move(tx, ty, float(p[3]))
                else: 
                    # 【核心优化】非拖拽状态下：使用贝塞尔曲线顺滑移动
                    # duration=None 让算法根据距离自动计算最自然的耗时
                    utils.human_move_to(tx, ty, duration=None)

            elif action == "click_press":
                # 记录拖拽起始点，锁定偏移
                utils.start_drag_lock(int(p[1]), int(p[2]))
                btn = p[3].replace("Button.","")
                pyautogui.mouseDown(x=int(p[1]), y=int(p[2]), button=btn)
                is_dragging = True
                
            elif action == "click_release":
                btn = p[3].replace("Button.","")
                pyautogui.mouseUp(x=int(p[1]), y=int(p[2]), button=btn)
                is_dragging = False
                
            elif action == "key_press": 
                pyautogui.keyDown(p[1])
                
            elif action == "key_release": 
                pyautogui.keyUp(p[1])
                
            elif action == "scroll": 
                # 滚轮幅度放大 100 倍
                pyautogui.scroll(int(p[4])*100)
            
            # 只有非移动指令才执行显式等待
            # 因为 move 指令在 human_move_to 内部已经消耗了时间
            if action != "move":
                time.sleep(real_d) 

        except Exception as e:
            traceback.print_exc()
            utils.log(f"⚠️ 执行出错: {e}", "red")
            
    utils.log("✅ 执行结束", "#00FF00")

def run(filepath):
    config.STOP_EVENT.clear() 
    execute_playback(filepath)
