import logging
import os
import json
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QIcon, QPixmap, QMouseEvent
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QFrame, QCheckBox)
from ui.styles import (background_color, text_color, button_bg_color, 
                      button_hover_color, border_color)
from core.config_manager import get_saved_theme

logger = logging.getLogger(__name__)

class WelcomeDialog(QDialog):
    """自定义无边框欢迎对话框"""
    def __init__(self, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.dont_show_again = False
        
        # 用于移动窗口的变量
        self.dragging = False
        self.drag_position = QPoint()
        
        self.setup_ui()
        
        # 应用当前主题
        self.apply_theme()
    
    def setup_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建主框架
        self.main_frame = QFrame()
        self.main_frame.setObjectName("mainFrame")
        
        frame_layout = QVBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题栏
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(30)
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        
        # 添加图标
        icon_label = QLabel()
        icon_label.setPixmap(QIcon('res/logo.ico').pixmap(20, 20))
        title_layout.addWidget(icon_label)
        
        # 添加标题
        self.title_label = QLabel("欢迎使用 LovelyMem")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        
        frame_layout.addWidget(self.title_bar)
        
        # 内容区域
        content_layout = QVBoxLayout()
        
        # 欢迎图片
        self.logo_label = QLabel()
        logo_pixmap = QPixmap("res/logo_100.png")
        if not logo_pixmap.isNull():
            self.logo_label.setPixmap(logo_pixmap)
            self.logo_label.setAlignment(Qt.AlignCenter)
        else:
            logger.error("无法加载图片: res/logo_100.png")
        content_layout.addWidget(self.logo_label)
        
        # 欢迎文本
        welcome_text = """
<h2 style='text-align:center;'>LovelyMem 内存取证工具</h2>

<p>LovelyMem 是一款功能强大的内存取证分析工具，集成了多种内存分析引擎：</p>
<ul>
    <li><b>MemProcFS</b> - 快速内存文件系统分析</li>
    <li><b>Volatility 2</b> - 经典的Volatility 2内存取证框架</li>
    <li><b>Volatility 3</b> - 新一代Volatility 3内存取证框架</li>
</ul>

<p><b>使用步骤：</b></p>
<ol>
    <li>点击左上角的"打开内存镜像"按钮加载内存文件</li>
    <li>选择相应的分析引擎和功能</li>
    <li>在打开的表格中右键可以使用对应的功能</li>
    <li>查看右侧的输出结果和文件列表</li>
    <li>使用"打包文件"功能保存分析结果</li>
</ol>

<p><b>提示：</b>如果您是首次使用，建议先检查"配置设置"确保工具路径正确设置。</p>
"""
        self.welcome_label = QLabel()
        self.welcome_label.setTextFormat(Qt.RichText)
        self.welcome_label.setText(welcome_text)
        self.welcome_label.setWordWrap(True)
        content_layout.addWidget(self.welcome_label)
        
        # 不再显示复选框
        checkbox_layout = QHBoxLayout()
        self.dont_show_checkbox = QCheckBox("不再显示此欢迎界面")
        self.dont_show_checkbox.clicked.connect(self.toggle_dont_show)
        checkbox_layout.addWidget(self.dont_show_checkbox)
        checkbox_layout.addStretch()
        content_layout.addLayout(checkbox_layout)
        
        # 确定按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.ok_button = QPushButton("开始使用")
        self.ok_button.setMinimumWidth(100)
        self.ok_button.clicked.connect(self.on_ok_clicked)
        button_layout.addWidget(self.ok_button)
        content_layout.addLayout(button_layout)
        
        frame_layout.addLayout(content_layout)
        main_layout.addWidget(self.main_frame)
        
        # 设置窗口大小
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)
    
    def apply_theme(self):
        """应用当前主题样式"""
        theme = get_saved_theme()
        
        # 主框架样式
        self.main_frame.setStyleSheet(f"""
            #mainFrame {{
                background-color: {background_color};
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
        """)
        
        # 标题栏样式
        self.title_bar.setStyleSheet(f"""
            background-color: transparent;
        """)
        
        # 标题样式
        self.title_label.setStyleSheet(f"""
            color: {text_color};
            font-size: 14px;
            font-weight: bold;
        """)
        
        # 欢迎文本样式
        self.welcome_label.setStyleSheet(f"""
            color: {text_color};
            padding: 10px;
        """)
        
        # 复选框样式
        self.dont_show_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {text_color};
            }}
            QCheckBox::indicator {{
                width: 15px;
                height: 15px;
            }}
        """)
        
        # 确定按钮样式
        self.ok_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {button_bg_color};
                color: {text_color};
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }}
            QPushButton:hover {{
                background-color: {button_hover_color};
            }}
        """)
    
    def toggle_dont_show(self, checked):
        """复选框状态变化时的处理函数"""
        self.dont_show_again = checked
    
    def on_ok_clicked(self):
        """点击确定按钮时的处理函数"""
        # 再次检查复选框状态，确保获取最新状态
        self.dont_show_again = self.dont_show_checkbox.isChecked()
        
        # 保存设置
        self.save_settings()
        
        # 关闭对话框
        self.accept()
    
    def save_settings(self):
        """保存用户设置"""
        if self.dont_show_again:
            try:
                user_settings_file = os.path.join(os.getcwd(), "config", "user_settings.json")
                
                if os.path.exists(user_settings_file):
                    with open(user_settings_file, 'r', encoding='utf-8') as f:
                        user_settings = json.load(f)
                    
                    user_settings["first_run_reminder"] = False
                    
                    with open(user_settings_file, 'w', encoding='utf-8') as f:
                        json.dump(user_settings, f, ensure_ascii=False, indent=4)
                    
            except Exception as e:
                print(f"保存用户设置失败: {e}")
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            # 修复弃用警告，使用globalPosition()代替globalPos()
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.LeftButton and self.dragging:
            # 修复弃用警告，使用globalPosition()代替globalPos()
            self.move(event.globalPosition().toPoint() - self.drag_position)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = False
