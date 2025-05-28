from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                              QGroupBox, QLineEdit, QTextEdit, QLabel, QListWidget, QPushButton,
                              QSplitter, QPlainTextEdit, QFileDialog, QMenu, QMessageBox, QFrame, QToolButton, QListView, QTabBar)
from PySide6.QtGui import (QIcon, QTextCursor, QColor, QMouseEvent, QPainter, QCloseEvent,
                          QPalette, QGuiApplication, QFont, QTransform)
from PySide6.QtCore import Qt, Slot, QTimer, QPoint, Signal, QThread, QSettings, QSize

from ui.styles import (main_window_style, candy_background, common_font_style, 
                       splitter_style, tab_style, left_group_style,  
                       right_panel_style, memprocfs_style, vol2_style, vol3_style, 
                       quick_check_style, cmd_output_style, current_font_family,
                       background_color, text_color, button_bg_color, button_text_color,
                       button_hover_color, border_color, group_title_bg_color,
                       color_schemes, apply_color_scheme, is_dark_mode, 
                       cmd_output_text_color,
                       theme_button_color, minimize_button_color, maximize_button_color, close_button_color)
# 添加毛玻璃效果覆盖层类
class GlassOverlay(QWidget):
    """实现毛玻璃效果的覆盖层，在拖放文件时显示"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置无边框透明背景
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # 隐藏覆盖层（初始状态）
        self.hide()
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建内容容器
        self.content_container = QWidget(self)
        self.content_container.setObjectName("dropContainer")
        self.content_container.setStyleSheet("""
            #dropContainer {
                background-color: rgba(255, 255, 255, 0.85);
                border: 5px dashed #808080;
                border-radius: 10px;
            }
        """)
        
        # 创建内容布局
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(40, 30, 40, 30)
        
        # 创建提示标签
        self.hint_label = QLabel("释放鼠标加载内存镜像", self.content_container)
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setFont(QFont(common_font_style, 18, QFont.Bold))
        self.hint_label.setStyleSheet(f"""
            color: #3498db;
            font-size: 18px;
            font-weight: bold;
        """)
        
        # 添加内存图标
        self.mem_icon = QLabel(self.content_container)
        self.mem_icon.setPixmap(QIcon('res/mem.svg').pixmap(64, 64))
        self.mem_icon.setAlignment(Qt.AlignCenter)
        
        # 将控件添加到内容布局
        content_layout.addWidget(self.hint_label)
        content_layout.addSpacing(15)
        content_layout.addWidget(self.mem_icon)
        
        # 将内容容器添加到主布局
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.content_container, 0, Qt.AlignCenter)
        self.main_layout.addStretch(1)
    
    def showEvent(self, event):
        """显示时调整大小并居中显示提示标签"""
        super().showEvent(event)
        # 调整覆盖层大小为父窗口大小
        if self.parent():
            self.setGeometry(0, 0, self.parent().width(), self.parent().height())
    
    def paintEvent(self, event):
        """绘制毛玻璃效果背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 创建半透明背景
        painter.fillRect(self.rect(), QColor(255, 255, 255, 150))
        
        # 添加模糊效果（这里使用半透明渐变来模拟）
        gradient = QColor(41, 128, 185, 40)
        painter.fillRect(self.rect(), gradient)
        
        # 添加微妙的网格图案，增强毛玻璃效果
        pen = painter.pen()
        pen.setWidth(1)
        pen.setColor(QColor(255, 255, 255, 20))
        painter.setPen(pen)
        
        # 绘制水平和垂直线条，形成网格
        step = 20
        for i in range(0, self.width(), step):
            painter.drawLine(i, 0, i, self.height())
        for i in range(0, self.height(), step):
            painter.drawLine(0, i, self.width(), i)
