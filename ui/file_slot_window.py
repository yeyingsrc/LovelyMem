import sys
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QGroupBox, QSizeGrip, QFrame
)
from PySide6.QtGui import QFont, QIcon, QPixmap

from ui.styles import (
    background_color, text_color, button_bg_color, button_text_color, 
    button_hover_color, border_color, group_title_bg_color, cmd_output_bg_color,
    cmd_output_text_color, current_font_family, minimize_button_color, close_button_color
)

class FileSlotWindow(QWidget):
    """文件槽独立窗口"""
    # 定义关闭信号，用于在窗口关闭时通知主窗口，并传递文件槽引用
    closed = Signal(object)
    
    def __init__(self, file_slot):
        super().__init__(None, Qt.Window)  # 使用Qt.Window标志创建顶级窗口
        self.setWindowTitle("文件槽")
        self.setWindowFlags(Qt.FramelessWindowHint)  # 移除原生标题栏
        self.setAttribute(Qt.WA_TranslucentBackground)  # 启用窗口背景透明
        self.resize(600, 500)  # 设置合适的默认大小
        
        self.file_slot = file_slot
        
        # 先设置父控件，确保控件可见
        self.file_slot.setParent(self)
        
        self.setup_ui()
        
        # 确保文件槽可见
        self.file_slot.setVisible(True)
        
        # 用于移动窗口的变量
        self.dragging = False
        self.drag_position = QPoint()
        
        # 应用样式
        self.apply_style()
        
        # 设置字体
        self.apply_font()
        
        # 监听主题变化
        QApplication.instance().paletteChanged.connect(self.on_theme_changed)
        
        # 显示窗口
        self.show()
    
    def setup_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建自定义标题栏
        title_bar = QFrame()
        title_bar.setFixedHeight(30)
        title_bar.setObjectName("title_bar")
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        
        # 添加图标
        icon_label = QLabel()
        icon_label.setPixmap(QIcon('res/logo.ico').pixmap(20, 20))
        title_layout.addWidget(icon_label)
        
        # 添加标题
        title_label = QLabel("文件槽")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 添加最小化按钮
        self.min_button = self.create_circle_button(minimize_button_color)
        self.min_button.clicked.connect(self.showMinimized)
        self.min_button.setToolTip("最小化")
        
        # 添加关闭按钮
        self.close_button = self.create_circle_button(close_button_color)
        self.close_button.clicked.connect(self.close)
        self.close_button.setToolTip("关闭")
        
        title_layout.addWidget(self.min_button)
        title_layout.addWidget(self.close_button)
        
        main_layout.addWidget(title_bar)
        
        # 创建内容区域
        content_frame = QFrame()
        content_frame.setObjectName("content_frame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(5, 5, 5, 5)
        
        # 添加文件槽到内容区域
        content_layout.addWidget(self.file_slot)
        
        main_layout.addWidget(content_frame)
        
        # 添加大小调整手柄
        size_grip = QSizeGrip(self)
        main_layout.addWidget(size_grip, 0, Qt.AlignBottom | Qt.AlignRight)
    
    def create_circle_button(self, base_color):
        """创建圆形按钮"""
        button = QPushButton()
        button.setFixedSize(12, 12)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {base_color};
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {button_hover_color};
            }}
        """)
        return button
    
    def apply_style(self):
        """应用样式"""
        # 设置窗口整体样式
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {background_color};
                color: {text_color};
                font-family: {current_font_family};
            }}
            
            #title_bar {{
                background-color: {group_title_bg_color};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom: 1px solid {border_color};
            }}
            
            #content_frame {{
                background-color: {background_color};
                border: 1px solid {border_color};
                border-top: none;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }}
            
            QLabel {{
                color: {text_color};
            }}
            
            QPushButton {{
                background-color: {button_bg_color};
                color: {button_text_color};
                border: 1px solid {border_color};
                border-radius: 3px;
                padding: 5px;
            }}
            
            QPushButton:hover {{
                background-color: {button_hover_color};
            }}
        """)
    
    def apply_font(self):
        """应用字体"""
        font = QFont(current_font_family)
        self.setFont(font)
    
    def on_theme_changed(self):
        """主题变化时更新样式"""
        self.apply_style()
    
    def mousePressEvent(self, event):
        """鼠标按下事件，用于实现窗口拖动"""
        if event.button() == Qt.LeftButton:
            # 检查是否在标题栏区域
            if event.position().y() <= 30:
                self.dragging = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件，用于实现窗口拖动"""
        if event.buttons() & Qt.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件，用于实现窗口拖动"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
    
    def closeEvent(self, event):
        """窗口关闭事件，发送关闭信号"""
        # 将文件槽从当前窗口移除，避免被销毁
        self.file_slot.setParent(None)
        # 发送关闭信号，并传递文件槽引用
        self.closed.emit(self.file_slot)
        # 接受关闭事件
        event.accept()
