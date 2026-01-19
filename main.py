import tkinter as tk
from tkinter import messagebox, simpledialog, Listbox, Scrollbar
import threading
import os
import traceback
from pynput import keyboard 
import config
import utils
import recorder
import modify_eye
import imitate
import code_lists # 【新增】导入指令库

class AutoMasterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AutoMaster V2.0")
        self.root.geometry("400x400") # 【修改】稍微调高一点以容纳新按钮
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
        
        utils.log("就绪。Alt+F9录制 | Alt+F8转换 | F4停止", "#00FFFF")

    def setup_ui(self):
        lbl_tip = tk.Label(self.root, text="Alt+F9:录制 | Alt+F8:转换 | Alt+F1/F2:播放 | F4:停止", fg="blue")
        lbl_tip.pack(pady=5)
        
        frame_list = tk.Frame(self.root)
        frame_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.listbox = Listbox(frame_list, selectmode=tk.SINGLE, font=("Consolas", 10))
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = Scrollbar(frame_list)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox.yview)
        
        frame_btn = tk.Frame(self.root)
        frame_btn.pack(fill=tk.X, padx=10, pady=10)
        
        # 【修改】调整按钮布局，加入指令帮助按钮
        tk.Button(frame_btn, text="刷新", command=self.refresh_list).pack(side=tk.LEFT, padx=5)
        # 【新增】帮助按钮
        tk.Button(frame_btn, text="📖 指令帮助", command=self.show_code_help).pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_btn, text="删除", command=self.delete_script).pack(side=tk.RIGHT, padx=5)

        self.refresh_list()

    # 【新增】显示指令帮助弹窗
    def show_code_help(self):
        help_text = code_lists.get_help_text()
        
        # 创建一个新窗口来显示帮助
        help_win = tk.Toplevel(self.root)
        help_win.title("AutoMaster 指令手册")
        help_win.geometry("500x600")
        
        # 使用 Text 控件支持多行和滚动
        txt = tk.Text(help_win, font=("Consolas", 10), padx=10, pady=10)
        txt.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scroll = tk.Scrollbar(help_win, command=txt.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        txt.config(yscrollcommand=scroll.set)
        
        # 插入文本并设置为只读
        txt.insert(tk.END, help_text)
        txt.config(state=tk.DISABLED)

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        if os.path.exists(config.SCRIPTS_DIR):
            files = [f for f in os.listdir(config.SCRIPTS_DIR) if f.endswith(".txt") and not f.endswith("_img.txt")]
            for f in files:
                self.listbox.insert(tk.END, f)

    def get_selected_script(self):
        try:
            idx = self.listbox.curselection()[0]
            return self.listbox.get(idx)
        except IndexError:
            return None

    def delete_script(self):
        sel = self.get_selected_script()
        if not sel: return
        if messagebox.askyesno("确认", f"确定删除 {sel}？"):
            try:
                base = os.path.join(config.SCRIPTS_DIR, sel)
                img = base.replace(".txt", "_img.txt")
                if os.path.exists(base): os.remove(base)
                if os.path.exists(img): os.remove(img)
                self.refresh_list()
            except Exception as e: messagebox.showerror("错误", str(e))

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
        """F4 强制停止"""
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
            finally:
                pass

        self.current_task_thread = threading.Thread(target=task, daemon=True)
        self.current_task_thread.start()

    # === 业务流程 ===
    def start_recording_flow(self):
        self.run_task_wrapper(self._record_logic)

    def _record_logic(self):
        temp_path = os.path.join(config.SCRIPTS_DIR, config.TEMP_FILE)
        recorder.run(temp_path)
        # 如果不是被 F4 强制终止的，则询问保存
        if not config.STOP_EVENT.is_set():
            self.root.after(0, lambda: self.ask_name_and_save(temp_path))

    def ask_name_and_save(self, temp_path):
        if not self.is_visible: self.toggle_visibility()
        name = simpledialog.askstring("保存", "输入脚本名称:", parent=self.root)
        if name:
            new_path = os.path.join(config.SCRIPTS_DIR, f"{name}.txt")
            if os.path.exists(new_path):
                if not messagebox.askyesno("覆盖", "文件已存在，是否覆盖？"): return
            if os.path.exists(new_path): os.remove(new_path)
            os.rename(temp_path, new_path)
            utils.log(f"✅ 已保存: {name}", "#00FF00")
            self.refresh_list()
        else:
            if os.path.exists(temp_path): os.remove(temp_path)

    def start_modify_flow(self):
        # 必须在主线程获取 listbox 选项
        self.root.after(0, self._modify_check)

    def _modify_check(self):
        sel = self.get_selected_script()
        if not sel:
            utils.log("❌ 请先选择脚本", "red"); return
        input_path = os.path.join(config.SCRIPTS_DIR, sel)
        output_path = input_path.replace(".txt", "_img.txt")
        self.run_task_wrapper(modify_eye.run, input_path, output_path)

    def start_playback_flow(self, mode):
        self.root.after(0, lambda: self._playback_check(mode))

    def _playback_check(self, mode):
        sel = self.get_selected_script()
        if not sel:
            utils.log("❌ 请先选择脚本", "red"); return
        base_path = os.path.join(config.SCRIPTS_DIR, sel)
        target = base_path if mode == 1 else base_path.replace(".txt", "_img.txt")
        if mode == 2 and not os.path.exists(target):
            utils.log("❌ 请先按 Alt+F8 转换", "red"); return
        self.run_task_wrapper(imitate.run, target)

    def on_closing(self):
        self.hotkeys.stop()
        self.root.destroy()
        os._exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoMasterGUI(root)
    root.mainloop()
