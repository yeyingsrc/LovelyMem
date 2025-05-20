from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, QHBoxLayout, QMessageBox, QMenu
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from ui.styles import quick_check_style
import random
import os

class MiaoMiaoButton(QPushButton):
    def __init__(self, text, function=None):
        super().__init__(text)
        if function:
            self.clicked.connect(function)

class CollapsibleButtonGroup(QWidget):
    def __init__(self, title, buttons, main_window):
        super().__init__()
        self.title = title
        self.buttons = buttons
        self.main_window = main_window
        self.is_expanded = True
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.title_button = MiaoMiaoButton(self.title)
        self.title_button.clicked.connect(self.toggle_expand)
        layout.addWidget(self.title_button)

        self.content_widget = QWidget()
        self.content_layout = QGridLayout(self.content_widget)
        for i, button in enumerate(self.buttons):
            row = i // 2
            col = i % 2
            self.content_layout.addWidget(button, row, col)
        self.content_widget.setVisible(True)
        layout.addWidget(self.content_widget)
        
        # 添加右键菜单功能
        for button in self.buttons:
            button.setContextMenuPolicy(Qt.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda pos, btn=button: self.show_context_menu(pos, btn))

    def show_context_menu(self, pos, button):
        if hasattr(self.main_window, 'preset_manager'):
            context_menu = self.main_window.preset_manager.create_context_menu(button, source_area="MiaoMiaoTools")
            context_menu.exec(button.mapToGlobal(pos))

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)

class MiaoMiaoToolsArea(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setStyleSheet(quick_check_style)
        layout = QVBoxLayout(self)
        
        # 基本功能组
        basic_buttons = [
            QPushButton("Base64编码解码"),
            QPushButton("高级计算器"),
        ]
        
        for button in basic_buttons:
            button.clicked.connect(lambda checked, name=button.text(): self.tool_clicked(name))
            
        self.basic_group = CollapsibleButtonGroup("小工具", basic_buttons, self.main_window)
        layout.addWidget(self.basic_group)
        
        layout.addStretch()
        

    
    def tool_clicked(self, tool_name):
        """处理工具按钮点击事件"""
        if tool_name == "Base64编码解码":
            self.show_base64_tool()
        elif tool_name == "高级计算器":
            self.show_calculator()
        else:
            QMessageBox.information(self, "妙妙工具", f"你点击了 {tool_name}，此功能尚未实现。")
            
    def show_base64_tool(self):
        """显示Base64编码解码工具"""
        from plugin.othertools import Base64Tool
        self.base64_tool = Base64Tool(main_window=self.main_window)
        self.base64_tool.setWindowTitle("Base64编码解码工具")
        self.base64_tool.resize(800, 600)
        self.base64_tool.show()
        
    def show_calculator(self):
        """显示高级计算器"""
        from plugin.othertools.calculator import Calculator
        self.calculator = Calculator(main_window=self.main_window)
        self.calculator.setWindowTitle("高级计算器")
        self.calculator.resize(960, 540)  # 16:9比例
        self.calculator.show()
