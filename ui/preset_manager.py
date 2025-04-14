from PySide6.QtWidgets import QMenu
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction
import sqlite3
import os

class PresetManager(QObject):
    preset_added = Signal(str, str)  # 参数为(预设名称, 按钮文本)

    def __init__(self):
        super().__init__()
        self.memory_workbench = None  # 稍后我们会设置它

    def create_context_menu(self, button, source_area):
        context_menu = QMenu()
        
        # 添加"添加到预设"选项
        add_to_preset_action = context_menu.addAction("添加到预设")
        add_to_preset_action.triggered.connect(lambda: self.add_to_preset(button.text(), source_area))

        return context_menu
    
    # 新增方法，返回预设操作的列表而不是菜单
    def create_preset_actions(self, button, source_area):
        actions = []
        
        # 创建"添加到预设"操作
        add_to_preset_action = QAction("添加到预设")
        add_to_preset_action.triggered.connect(lambda: self.add_to_preset(button.text(), source_area))
        actions.append(add_to_preset_action)
        
        return actions

    def add_to_preset(self, button_text, source_area):
        if self.memory_workbench:
            preset_name = self.memory_workbench.get_current_preset()
            if preset_name:
                self.save_preset(preset_name, f"{source_area}-{button_text}")
                self.preset_added.emit(preset_name, f"{source_area}-{button_text}")
            else:
                print("请先选择或创建一个预设")
        else:
            print("错误: memory_workbench 未设置")

    def save_preset(self, preset_name, button_text):
        conn = sqlite3.connect('db/presets.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS presets
                     (name TEXT, button_text TEXT)''')
        c.execute("INSERT INTO presets (name, button_text) VALUES (?, ?)", (preset_name, button_text))
        conn.commit()
        conn.close()
