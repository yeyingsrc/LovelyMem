from PySide6.QtWidgets import QMenu
from PySide6.QtCore import QObject, Signal
import sqlite3
import os

class FavoriteManager(QObject):
    favorite_added = Signal(str)
    favorite_removed = Signal(str)
    preset_added = Signal(str, str)  # 新增信号,参数为(预设名称, 按钮文本)

    def __init__(self, favorite_group):
        super().__init__()
        self.favorite_group = favorite_group
        self.right_panel = None  # 添加这行,稍后我们会设置它

    def create_context_menu(self, button, is_favorite=False, source_area=None):
        context_menu = QMenu()
        if is_favorite:
            remove_from_favorite_action = context_menu.addAction("从喜爱中移除")
            remove_from_favorite_action.triggered.connect(lambda: self.remove_favorite(button))
        else:
            add_to_favorite_action = context_menu.addAction("添加到喜爱")
            add_to_favorite_action.triggered.connect(lambda: self.add_favorite(button, source_area))
        
        # 添加"添加到预设"选项
        add_to_preset_action = context_menu.addAction("添加到预设")
        add_to_preset_action.triggered.connect(lambda: self.add_to_preset(button.text(), source_area))

        return context_menu

    def add_to_preset(self, button_text, source_area):
        if self.right_panel:
            preset_name = self.right_panel.get_current_preset()
            if preset_name:
                self.save_preset(preset_name, f"{source_area}-{button_text}")
                self.preset_added.emit(preset_name, f"{source_area}-{button_text}")
            else:
                print("请先选择或创建一个预设")
        else:
            print("错误: right_panel 未设置")

    def save_preset(self, preset_name, button_text):
        conn = sqlite3.connect('db/presets.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS presets
                     (name TEXT, button_text TEXT)''')
        c.execute("INSERT INTO presets (name, button_text) VALUES (?, ?)", (preset_name, button_text))
        conn.commit()
        conn.close()

    def add_favorite(self, button, source_area):
        if self.favorite_group:
            self.favorite_group.add_favorite(button, source_area)
            self.favorite_added.emit(button.text())
        else:
            print("错误: favorite_group 未设置")

    def remove_favorite(self, button):
        if self.favorite_group:
            self.favorite_group.remove_favorite(button)
            self.favorite_removed.emit(button.text())
        else:
            print("错误: favorite_group 未设置")