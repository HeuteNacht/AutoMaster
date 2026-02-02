import tkinter as tk
from tkinter import messagebox, simpledialog, Listbox, Scrollbar, Scale
import threading
import os
import traceback
from pynput import keyboard 
import config
import utils
import recorder
import modify_eye
import imitate
import code_lists

class AutoMasterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AutoMaster V2.7 (极速版)")
        self.root.geometry("400x500")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.is_visible = True
        self.current_task_thread = None
        
        self.setup_ui()
        
        self.hud_window = tk.Toplevel(self.root)
        utils.init_hud(self.hud_window)
        
        self.hotkeys = keyboard.GlobalHotKeys({
            '<alt>+<f9>': self.start_recording_flow,
            '<alt>+<f8>': self.start_modify_flow,
            '<alt>+<f1>': lambda: self.start_playback_flow(1),
            '<alt>+<f2>': lambda: self.start_playback_flow(2),
            '<f4>': self.emergency_stop,
            '<f12>': self.toggle_visibility_safe
        })
        self.hotkeys.start()
        
        utils.log("就绪。Alt+F1普通 | Alt+F2智能", "#00FFFF")

    def setup_ui(self):
        # 1. 顶部提示
        frame_top = tk.Frame(self.root)
        frame_top.pack(pady=5)
        tk.Label(frame_top, text="Alt+F1: 普通运行", fg="blue", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Label(frame_top, text="Alt+F2: 智能运行", fg="red", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.root, text="Alt+F9:录制 | Alt+F8:转换 | F4:停止", fg="gray").pack()
        
        # 2. 列表区
        frame_list = tk.Frame(self.root)
        frame_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.listbox = Listbox(frame_list, selectmode=tk.SINGLE, font=("Consolas", 10))
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = Scrollbar(frame_list)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox.yview)
        
        # =========================================================
        # 【核心修改】符合人类直觉的倍速条
        # =========================================================
        frame_speed = tk.LabelFrame(self.root, text="运行速度 (数值越大越快)", padx=5, pady=5)
        frame_speed.pack(fill=tk.X, padx=10, pady=5)
        
        # 提示：左边是慢，右边是快
        tk.Label(frame_speed, text="慢 🐢 <------- (1.0=原速) -------> ⚡ 快", fg="gray", font=("Arial", 8)).pack(anchor="n")

        # 范围：0.2倍速 ~ 3.0倍速
        self.speed_scale = tk.Scale(frame_speed, from_=0.2, to=3.0, resolution=0.1, 
                                    orient=tk.HORIZONTAL, command=self.update_speed)
        self.speed_scale.set(1.0) 
        self.speed_scale.pack(fill=tk.X, padx=5)

        # 3. 按钮区
        frame_btn = tk.Frame(self.root)
        frame_btn.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(frame_btn, text="🔄 刷新", command=self.refresh_list).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_btn, text="📖 指令手册", command=self.show_code_help).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_btn, text="🗑️ 删除", command=self.delete_script, fg="red").pack(side=tk.RIGHT, padx=5)

        self.refresh_list()

    def update_speed(self, val):
        # 【核心逻辑】将“速度倍率”转换为“延迟系数”
        # 速度 = 1 / 延迟。所以：延迟 = 1 / 速度
        speed_val = float(val)
        if speed_val <= 0: speed_val = 0.1
        
        # 计算延迟系数 (传给 config 使用)
        new_delay_factor = 1.0 / speed_val
        config.SPEED_FACTOR = new_delay_factor
        
        desc = ""
        if speed_val >= 2.0: desc = "(极速 🔥)"
        elif speed_val == 1.0: desc = "(原速)"
        elif speed_val <= 0.5: desc = "(慢动作 🐢)"
        
        # 只打印日志，不弹窗
        utils.log(f"⚙️ 速度: {speed_val}x {desc}", "magenta")

    def show_code_help(self):
        help_text = code_lists.get_help_text()
        help_win = tk.Toplevel(self.root)
        help_win.title("AutoMaster 指令手册")
        help_win.geometry("600x600")
        txt_box = tk.Text(help_win, font=("Consolas", 10), padx=10, pady=10)
        txt_box.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scroll = tk.Scrollbar(help_win, command=txt_box.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        txt_box.config(yscrollcommand=scroll.set)
        txt_box.insert(tk.END, help_text)
        txt_box.config(state=tk.DISABLED)

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        if os.path.exists(config.SCRIPTS_DIR):
            files = os.listdir(config.SCRIPTS_DIR)
            clean_names = []
            for f in files:
                if f.endswith(".txt") and not (f.endswith("_smart.txt") or f.endswith("_img.txt")):
                    name_without_ext = f[:-4] 
                    clean_names.append(name_without_ext)
            clean_names.sort()
            for name in clean_names:
                self.listbox.insert(tk.END, name)

    def get_selected_name(self):
        try:
            idx = self.listbox.curselection()[0]
            return self.listbox.get(idx)
        except IndexError:
            return None

    def delete_script(self):
        name = self.get_selected_name()
        if not name: return
        if messagebox.askyesno("确认删除", f"确定要永久删除脚本 [{name}] 吗？\n(包含其智能版副本)"):
            try:
                file_normal = os.path.join(config.SCRIPTS_DIR, f"{name}.txt")
                file_smart = os.path.join(config.SCRIPTS_DIR, f"{name}_smart.txt")
                file_img = os.path.join(config.SCRIPTS_DIR, f"{name}_img.txt")
                
                if os.path.exists(file_normal): os.remove(file_normal)
                if os.path.exists(file_smart): os.remove(file_smart)
                if os.path.exists(file_img): os.remove(file_img)
                
                utils.log(f"🗑️ 已删除: {name}", "gray")
                self.refresh_list()
            except Exception as e:
                messagebox.showerror("删除失败", str(e))

    def toggle_visibility_safe(self):
        self.root.after(0, self.toggle_visibility)

    def toggle_visibility(self):
        if self.is_visible:
            self.root.withdraw()
            self.is_visible = False
            utils.log("GUI 已隐藏 (F12唤出)", "gray")
        else:
            self.root.deiconify()
            self.is_visible = True
            utils.log("GUI 已显示", "white")

    def emergency_stop(self):
        config.STOP_EVENT.set()
        utils.log("🛑 正在强制停止...", "red")

    def run_task_wrapper(self, func, *args):
        if self.current_task_thread and self.current_task_thread.is_alive():
            utils.log("⚠️ 任务运行中，请先按 F4 停止", "orange")
            return
        def task():
            try:
                func(*args)
            except InterruptedError:
                utils.log("🛑 已终止", "red")
            except Exception as e:
                traceback.print_exc()
                utils.log(f"❌ 错误: {e}", "red")
        self.current_task_thread = threading.Thread(target=task, daemon=True)
        self.current_task_thread.start()

    def start_recording_flow(self):
        self.run_task_wrapper(self._record_logic)

    def _record_logic(self):
        temp_path = os.path.join(config.SCRIPTS_DIR, config.TEMP_FILE)
        recorder.run(temp_path)
        if not config.STOP_EVENT.is_set():
            self.root.after(0, lambda: self.ask_name_and_save(temp_path))

    def ask_name_and_save(self, temp_path):
        if not self.is_visible: self.toggle_visibility()
        name = simpledialog.askstring("保存录制", "请输入脚本名称 (无需后缀):", parent=self.root)
        if name:
            if name.endswith(".txt"): name = name[:-4]
            final_name = f"{name}.txt"
            new_path = os.path.join(config.SCRIPTS_DIR, final_name)
            
            if os.path.exists(new_path):
                if not messagebox.askyesno("覆盖警告", f"{name} 已存在，是否覆盖？"): return
            
            if os.path.exists(new_path): os.remove(new_path)
            os.rename(temp_path, new_path)
            utils.log(f"✅ 录制保存: {name}", "#00FF00")
            self.refresh_list()
        else:
            if os.path.exists(temp_path): os.remove(temp_path)

    def start_modify_flow(self):
        self.root.after(0, self._modify_check)

    def _modify_check(self):
        name = self.get_selected_name()
        if not name:
            utils.log("❌ 请先选择脚本", "red"); return
        filename = f"{name}.txt"
        utils.log(f"🛠️ 正在为 [{name}] 生成智能版...", "magenta")
        self.run_task_wrapper(modify_eye.run, None, filename)

    def start_playback_flow(self, mode):
        self.root.after(0, lambda: self._playback_check(mode))

    def _playback_check(self, mode):
        name = self.get_selected_name()
        if not name:
            utils.log("❌ 请先选择脚本", "red"); return
            
        normal_file = f"{name}.txt"
        smart_file = f"{name}_smart.txt"
        
        normal_path = os.path.join(config.SCRIPTS_DIR, normal_file)
        smart_path = os.path.join(config.SCRIPTS_DIR, smart_file)
        
        target_path = normal_path
        
        if mode == 2: # F2 智能模式
            if os.path.exists(smart_path):
                target_path = smart_path
                utils.log(f"🧠 智能运行: {name}", "cyan")
            else:
                utils.log(f"⚠️ 未找到智能版", "orange")
                choice = messagebox.askyesno("智能版不存在", f"[{name}] 未生成智能版。\n是否降级运行普通版？")
                if not choice: return 
                utils.log(f"⚠️ 降级运行: {name}", "orange")
        else: # F1 普通模式
            utils.log(f"▶️ 普通运行: {name}", "green")

        self.run_task_wrapper(imitate.run, target_path)

    def on_closing(self):
        self.hotkeys.stop()
        self.root.destroy()
        os._exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoMasterGUI(root)
    root.mainloop()
