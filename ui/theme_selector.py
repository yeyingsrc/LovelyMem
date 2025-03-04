from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QScrollArea, QWidget, QFontComboBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
import math
import json
from ui.styles import (main_window_style, candy_background, common_font_style, 
                       button_style, background_color, text_color, border_color)

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
        
        with open("config/style.json", "r", encoding="utf-8") as f:
            self.color_schemes = json.load(f)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        main_frame = QFrame(self)
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet(f"""
            QFrame#mainFrame {{
                {candy_background}
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
        """)
        frame_layout = QVBoxLayout(main_frame)
        
        title_bar = QFrame()
        title_bar.setFixedHeight(30)
        title_bar.setStyleSheet(f"""
            {candy_background}
            {common_font_style}
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        
        title_label = QLabel("选择主题")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_button = self.create_circle_button("rgba(255, 235, 238, 0.9)")
        close_button.clicked.connect(self.close)
        title_layout.addWidget(close_button)
        
        frame_layout.addWidget(title_bar)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)
        
        # 添加字体选择区域
        font_frame = QFrame()
        font_layout = QHBoxLayout(font_frame)
        font_label = QLabel("选择字体:")
        self.font_combo = QFontComboBox()
        self.font_combo.currentFontChanged.connect(self.on_font_selected)
        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_combo)
        
        content_layout.addWidget(font_frame)
        
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
                    row_layout.addWidget(button)
            themes_layout.addLayout(row_layout)

        content_layout.addLayout(themes_layout)
        scroll_layout.addLayout(content_layout)
        
        scroll_area.setWidget(scroll_content)
        frame_layout.addWidget(scroll_area)
        
        main_layout.addWidget(main_frame)
        
        self.setStyleSheet(main_window_style)

    def create_theme_button(self, theme_name):
        button = QPushButton(theme_name)
        #button.setFixedSize(100, 40)  # 将按钮大小改为长方形
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
                    border: 2px solid {border_color};
                    border-radius: 8px;
                    padding: 5px;
                    font-size: 14px;
                    font-weight: bold; 
                }}
                QPushButton:hover {{
                    background-color: {theme["button_hover_color"]};
                }}
            """)

    def create_circle_button(self, base_color):
        button = QPushButton()
        button.setFixedSize(12, 12)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {base_color};
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: rgba{QColor(base_color).darker(110).getRgb()};
            }}
        """)
        return button

    def on_theme_selected(self, theme_name):
        self.theme_selected.emit(theme_name)
        self.accept()

    def on_font_selected(self, font):
        # 保存字体设置到user_settings.json
        try:
            with open("config/user_settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
            
            # 更新字体设置
            if "font_settings" not in settings:
                settings["font_settings"] = {}
            settings["font_settings"]["font_family"] = font.family()
            
            # 保存更新后的设置
            with open("config/user_settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            
            # 发送字体更改信号
            self.font_selected.emit(font)
        except Exception as e:
            print(f"保存字体设置时出错: {e}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            self.move(event.globalPos() - self.drag_position)
            event.accept()