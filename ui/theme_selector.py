from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QScrollArea, QWidget, QFontComboBox
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QColor, QFont
import math
import json
from ui.styles import (main_window_style, candy_background, common_font_style, 
                       button_style, background_color, text_color, border_color,
                       button_bg_color, button_text_color, button_hover_color,
                       theme_button_color, minimize_button_color, maximize_button_color, close_button_color)

class ThemeSelectorDialog(QDialog):
    theme_selected = Signal(str)
    font_selected = Signal(QFont)

    def __init__(self, themes):
        super().__init__(None)  # 设置为顶级窗口
        self.setWindowTitle("选择主题")
        self.setFixedSize(800, 800)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.drag_position = None  # 初始化拖动位置
        self.themes = themes  # 存储主题列表
        
        # 存储需要动态更新样式的组件引用
        self.main_frame = None
        self.title_bar = None
        self.close_button = None
        self.font_frame = None
        self.font_label = None
        self.font_combo = None
        self.scroll_area = None
        self.theme_buttons = []
        
        with open("config/style.json", "r", encoding="utf-8") as f:
            self.color_schemes = json.load(f)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("mainFrame")
        self.main_frame.setStyleSheet(f"""
            QFrame#mainFrame {{
                {candy_background}
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
            {button_style}
        """)
        frame_layout = QVBoxLayout(self.main_frame)
        
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet(f"""
            {candy_background}
            {common_font_style}
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            border: none;
        """)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        
        title_label = QLabel("选择主题")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        self.close_button = self.create_circle_button(close_button_color)
        self.close_button.clicked.connect(self.close)
        title_layout.addWidget(self.close_button)
        
        frame_layout.addWidget(self.title_bar)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {background_color};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {button_bg_color};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {button_hover_color};
            }}
        """)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)
        
        # 添加字体选择区域
        self.font_frame = QFrame()
        self.font_frame.setStyleSheet(f"""
            QFrame {{
                {candy_background}
                border: 1px solid {border_color};
                border-radius: 5px;
                padding: 5px;
            }}
        """)
        font_layout = QHBoxLayout(self.font_frame)
        self.font_label = QLabel("选择字体:")
        self.font_label.setStyleSheet(common_font_style)
        self.font_combo = QFontComboBox()
        self.font_combo.setStyleSheet(f"""
            QFontComboBox {{
                background-color: {button_bg_color};
                color: {button_text_color};
                border: 1px solid {border_color};
                border-radius: 3px;
                padding: 5px;
            }}
            QFontComboBox:hover {{
                background-color: {button_hover_color};
            }}
        """)
        self.font_combo.currentFontChanged.connect(self.on_font_selected)
        font_layout.addWidget(self.font_label)
        font_layout.addWidget(self.font_combo)
        
        content_layout.addWidget(self.font_frame)
        
        themes_layout = QVBoxLayout()
        themes_per_row = 8
        rows = math.ceil(len(themes) / themes_per_row)

        for row in range(rows):
            row_layout = QHBoxLayout()
            for col in range(themes_per_row):
                index = row * themes_per_row + col
                if index < len(themes):
                    theme_name = themes[index]
                    button = self.create_theme_button(theme_name)
                    self.theme_buttons.append(button)  # 存储按钮引用
                    row_layout.addWidget(button)
            themes_layout.addLayout(row_layout)

        content_layout.addLayout(themes_layout)
        scroll_layout.addLayout(content_layout)
        
        self.scroll_area.setWidget(scroll_content)
        frame_layout.addWidget(self.scroll_area)
        
        main_layout.addWidget(self.main_frame)
        
        # 应用与主窗口一致的样式
        self.setStyleSheet(f"""
            QDialog {{
                {candy_background}
                {common_font_style}
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
            {button_style}
        """)

    def create_theme_button(self, theme_name):
        button = QPushButton(theme_name)
        button.setMinimumHeight(35)  # 设置最小高度
        button.clicked.connect(lambda: self.on_theme_selected(theme_name))
        self.apply_theme_to_button(button, theme_name)
        return button

    def apply_theme_to_button(self, button, theme_name):
        if theme_name in self.color_schemes:
            theme = self.color_schemes[theme_name]["light"]
            bg_color = theme["background_color"]
            text_color = theme["text_color"]
            border_color = theme["border_color"]
            
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: {text_color};
                    border: 1px solid {border_color};
                    border-radius: 5px;
                    padding: 8px 12px;
                    font-size: 13px;
                    font-family: {common_font_style.split('font-family:')[1].split(';')[0].strip() if 'font-family:' in common_font_style else 'Microsoft YaHei'};
                    font-weight: normal;
                    min-height: 25px;
                }}
                QPushButton:hover {{
                    background-color: {theme["button_hover_color"]};
                    border-color: {theme["button_hover_color"]};
                }}
                QPushButton:pressed {{
                    background-color: {theme["border_color"]};
                }}
            """)

    def create_circle_button(self, base_color):
        button = QPushButton()
        button.setFixedSize(14, 14)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {base_color};
                border-radius: 7px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {button_hover_color};
            }}
        """)
        return button

    def on_theme_selected(self, theme_name):
        self.theme_selected.emit(theme_name)
        self.accept()

    def on_font_selected(self, font):
        """字体选择事件处理"""
        font_name = font.family()
        self.font_selected.emit(font_name)
        print(f"选择字体: {font_name}")
    
    def update_styles(self):
        """更新所有组件的样式以反映主题变化"""
        from ui.styles import (candy_background, common_font_style, 
                              button_bg_color, button_text_color, button_hover_color,
                              border_color, background_color, button_style)
        
        # 更新主对话框样式
        self.setStyleSheet(f"""
            QDialog {{
                {candy_background}
                {common_font_style}
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
            {button_style}
        """)
        
        # 更新主框架样式
        self.main_frame.setStyleSheet(f"""
            QFrame {{
                {candy_background}
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
        """)
        
        # 更新标题栏样式
        self.title_bar.setStyleSheet(f"""
            QFrame {{
                {candy_background}
                {common_font_style}
                border: none;
                border-radius: 10px 10px 0 0;
                padding: 5px;
            }}
        """)
        
        # 更新字体选择区域样式
        self.font_frame.setStyleSheet(f"""
            QFrame {{
                {candy_background}
                border: 1px solid {border_color};
                border-radius: 5px;
                padding: 5px;
            }}
        """)
        
        # 更新字体标签样式
        self.font_label.setStyleSheet(common_font_style)
        
        # 更新字体选择框样式
        self.font_combo.setStyleSheet(f"""
            QFontComboBox {{
                background-color: {button_bg_color};
                color: {button_text_color};
                border: 1px solid {border_color};
                border-radius: 5px;
                padding: 5px;
                {common_font_style}
            }}
            QFontComboBox:hover {{
                background-color: {button_hover_color};
            }}
            QFontComboBox::drop-down {{
                border: none;
            }}
        """)
        
        # 更新滚动区域样式
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {background_color};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {button_bg_color};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {button_hover_color};
            }}
        """)
        
        # 更新所有主题按钮样式
        for i, button in enumerate(self.theme_buttons):
            if i < len(self.themes):
                theme_name = self.themes[i]
                self.apply_theme_to_button(button, theme_name)
        
        # 更新关闭按钮样式
        self.apply_circle_button_style(self.close_button)
    
    def apply_circle_button_style(self, button):
        """应用圆形按钮样式"""
        from ui.styles import button_hover_color
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: #ff5f56;
                border: none;
                border-radius: 7px;
                color: white;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {button_hover_color};
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.position().toPoint() + self.mapToGlobal(QPoint(0, 0)) - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            self.move(event.position().toPoint() + self.mapToGlobal(QPoint(0, 0)) - self.drag_position)
            event.accept()