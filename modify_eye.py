import pyautogui
import time
import os
import utils
import config

def track_gesture(origin_x, origin_y, progress_str):
    path_points = []
    is_moving_mode = False
    last_pos = pyautogui.position()
    stable_start_time = time.time()
    path_points.append(last_pos)

    while True:
        utils.check_stop() # 【新增】循环检测
        
        curr_pos = pyautogui.position()
        dist_last = utils.get_dist(curr_pos, last_pos)
        dist_origin = utils.get_dist(curr_pos, (origin_x, origin_y))
        
        if dist_last > config.JITTER_TOLERANCE:
            stable_start_time = time.time()
            last_pos = curr_pos
            path_points.append(curr_pos)
            if not is_moving_mode and dist_origin > config.MOVE_THRESHOLD:
                is_moving_mode = True
                path_points = [curr_pos]

        remaining = max(0.0, config.DWELL_TIME - (time.time() - stable_start_time))
        
        if not is_moving_mode:
            if remaining > 0:
                utils.log(f"{progress_str} ⚓ 保持不动跳过: {remaining:.1f}s\n👉 或移动鼠标截图", "gray")
            else: return "skip", None
        else:
            xs = [p[0] for p in path_points]
            ys = [p[1] for p in path_points]
            w, h = max(xs)-min(xs), max(ys)-min(ys)
            if remaining > 0:
                utils.log(f"{progress_str} 🖌️ 区域 ({w}x{h})...\n🛑 停止移动 {remaining:.1f}s 确认", "yellow")
            else: return "rect", (min(xs), min(ys), w, h)
        time.sleep(0.05)


def run(input_path, output_path):
    utils.log(f"⚙️ 开始转换: {os.path.basename(input_path)}", "white")
    config.STOP_EVENT.clear() # 重置信号
    time.sleep(1)
    
    with open(input_path, "r", encoding="utf-8") as f: lines = f.readlines()
    actions = []
    for line in lines:
        line = line.strip()
        if line: 
            p = line.split(",")
            if len(p)>=2: actions.append({'raw': line, 'type': p[0], 'data': p})

    # (双击合并逻辑保持不变...)
    skip_indices = set()
    for i in range(len(actions)):
        if i in skip_indices: continue
        curr = actions[i]
        if curr['type'] == 'click_press':
            for j in range(i+1, min(i+10, len(actions))):
                nxt = actions[j]
                if nxt['type'] == 'click_press':
                    try:
                        if abs(int(curr['data'][1])-int(nxt['data'][1]))<5:
                            curr['is_double'] = True
                            skip_indices.add(j)
                            break
                    except: pass
    
    new_lines = []
    img_count = 1
    total = len(actions)
    skip_release_until = 0

    for i, act in enumerate(actions):
        utils.check_stop() # 【新增】循环检测
        
        if i in skip_indices: continue
        if act['type'] == "click_release" and time.time() < skip_release_until: continue
        
        prog = f"[{i+1}/{total}]"
        
        if act['type'] == "click_press":
            parts = act['data']
            x, y = int(parts[1]), int(parts[2])
            btn = parts[3].replace('Button.', '')
            delay = parts[-1]
            is_double = act.get('is_double', False)

            utils.human_move_to(x, y, duration=config.SLOW_MOVE_DURATION)
            time.sleep(config.STEP_PAUSE)
            
            res_type, rect_data = track_gesture(x, y, prog)
            
            if res_type == "skip":
                utils.log(f"{prog} ⚓ 保留原坐标", "#00FF00")
                time.sleep(1)
                new_lines.append(act['raw'])
                utils.perform_human_click(x, y, is_double, btn)
                if is_double:
                    new_lines.append(f"click_release,{x},{y},{parts[3]},0.1")
                    new_lines.append(f"click_press,{x},{y},{parts[3]},0.1")

            elif res_type == "rect":
                rx, ry, w, h = rect_data
                if w < config.MIN_SIZE: w=config.MIN_SIZE; rx-=int((config.MIN_SIZE-w)/2)
                if h < config.MIN_SIZE: h=config.MIN_SIZE; ry-=int((config.MIN_SIZE-h)/2)
                
                timestamp = int(time.time())
                img_name = f"img_{timestamp}_{img_count}.png"
                img_path = os.path.join(config.IMG_FOLDER, img_name)
                pyautogui.screenshot(region=(rx, ry, w, h)).save(img_path)
                
                cmd = "image_double_click" if is_double else "image_click"
                new_lines.append(f"{cmd},{img_path},{delay}")
                
                utils.log(f"{prog} ✅ 截图成功!", "#00FF00")
                img_count += 1
                time.sleep(1)
                utils.perform_human_click(x, y, is_double, btn)
                skip_release_until = time.time() + (2 if is_double else 1)
        else:
            new_lines.append(act['raw'])
            if act['type'] not in ["click_release"]:
                utils.log(f"{prog} 处理: {act['type']}...", "#AAAAAA")

    with open(output_path, "w", encoding="utf-8") as f:
        for line in new_lines: f.write(line + "\n")
    
    utils.log(f"🎉 转换完成！", "#00FF00")
