# code_lists.py
COMMANDS = {
    "move": {
        "format": "move,x,y,delay",
        "desc": "移动鼠标到指定坐标"
    },
    "click_press": {
        "format": "click_press,x,y,button,delay",
        "desc": "按下鼠标 (left/right/middle)"
    },
    "click_release": {
        "format": "click_release,x,y,button,delay",
        "desc": "松开鼠标"
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
        "desc": "视觉识别：单击图片"
    },
    "image_double_click": {
        "format": "image_double_click,image_path,delay",
        "desc": "视觉识别：双击图片"
    },
    "Script": {
        "format": "Script,filename.txt",
        "desc": "嵌套执行另一个脚本"
    },
    "Paste": {
        "format": "Paste,x,y,filename,line_index",
        "desc": "自动填表：读取文件第N行，点击坐标并粘贴"
    },
    "type_file": {
        "format": "type_file,filepath,interval,enter_flag",
        "desc": "读取文件内容并模拟打字(支持中文), enter_flag为1表示最后按回车"
    }
}

def get_help_text():
    txt = "=== AutoMaster 指令手册 ===\n\n"
    for cmd, info in COMMANDS.items():
        txt += f"🟢 [{cmd}]\n   格式: {info['format']}\n   说明: {info['desc']}\n\n"
    return txt
