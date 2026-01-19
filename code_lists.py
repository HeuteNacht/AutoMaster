# code_lists.py
# 【新增文件】用于记录 AutoMaster 支持的所有指令格式与说明

COMMANDS = {
    "move": {
        "format": "move,x,y,delay",
        "desc": "移动鼠标到指定坐标 (x, y)，delay 为录制时的延迟"
    },
    "click_press": {
        "format": "click_press,x,y,button,delay",
        "desc": "在 (x, y) 处按下鼠标。button: left/right/middle"
    },
    "click_release": {
        "format": "click_release,x,y,button,delay",
        "desc": "在 (x, y) 处松开鼠标"
    },
    "key_press": {
        "format": "key_press,key_name,delay",
        "desc": "按下键盘按键"
    },
    "key_release": {
        "format": "key_release,key_name,delay",
        "desc": "松开键盘按键"
    },
    "scroll": {
        "format": "scroll,x,y,dx,dy,delay",
        "desc": "鼠标滚轮滚动"
    },
    "image_click": {
        "format": "image_click,image_path,delay",
        "desc": "视觉识别：寻找图片中心并单击"
    },
    "image_double_click": {
        "format": "image_double_click,image_path,delay",
        "desc": "视觉识别：寻找图片中心并双击"
    },
    "Script": {
        "format": "Script,script_filename.txt",
        "desc": "嵌套调用：执行另一个脚本文件"
    },
    "Paste": {
        "format": "Paste,x,y,filename,line_index",
        "desc": "【新增功能】数据填充：\n1. 读取 filename 的第 line_index 行(从1开始)\n2. 点击坐标 (x,y)\n3. 粘贴文字"
    }
}

def get_help_text():
    """生成格式化的帮助文本"""
    txt = "=== AutoMaster 指令手册 ===\n\n"
    for cmd, info in COMMANDS.items():
        txt += f"🟢 [{cmd}]\n"
        txt += f"   格式: {info['format']}\n"
        txt += f"   说明: {info['desc']}\n\n"
    return txt
