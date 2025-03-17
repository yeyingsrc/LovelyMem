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

class CmdOutputWindow(QWidget):
    """命令输出独立窗口"""
    # 定义关闭信号，用于在窗口关闭时通知主窗口
    closed = Signal(QTextEdit)
    
    def __init__(self, cmd_output):
        super().__init__(None, Qt.Window)  # 使用Qt.Window标志创建顶级窗口
        self.setWindowTitle("命令输出")
        self.setWindowFlags(Qt.FramelessWindowHint)  # 移除原生标题栏
        self.setAttribute(Qt.WA_TranslucentBackground)  # 启用窗口背景透明
        self.resize(600, 400)  # 设置合适的默认大小
        
        self.cmd_output = cmd_output
        
        # 先设置父控件，确保控件可见
        self.cmd_output.setParent(self)
        
        self.setup_ui()
        
        # 确保文本编辑器可见
        self.cmd_output.setVisible(True)
        
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
        QApplication.processEvents()
    
    def lighten_color(self, color, amount=20):
        """使颜色变亮"""
        if color.startswith("rgba("):
            parts = color.strip("rgba()").split(",")
            r = min(255, int(parts[0]) + amount)
            g = min(255, int(parts[1]) + amount)
            b = min(255, int(parts[2]) + amount)
            a = parts[3]
            return f"rgba({r}, {g}, {b}, {a})"
        elif color.startswith("#"):
            r = min(255, int(color[1:3], 16) + amount)
            g = min(255, int(color[3:5], 16) + amount)
            b = min(255, int(color[5:7], 16) + amount)
            return f"#{r:02x}{g:02x}{b:02x}"
        return color
    
    def apply_style(self):
        """应用样式"""
        # 从ui.styles重新导入最新的颜色变量，确保获取到最新的主题颜色
        from ui.styles import (
            background_color, text_color, button_bg_color, button_text_color, 
            button_hover_color, border_color, group_title_bg_color, cmd_output_bg_color,
            cmd_output_text_color, minimize_button_color, close_button_color
        )
        
        self.setStyleSheet(f"""
            QWidget {{
                color: {text_color};
            }}
            
            #contentContainer {{
                background-color: {background_color};
                border-radius: 10px;
                border: 1px solid {border_color};
            }}
            
            #titleBar {{
                background-color: {group_title_bg_color};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom: 1px solid {border_color};
            }}
            
            QLabel {{
                color: {text_color};
            }}
            
            QTextEdit {{
                background-color: {cmd_output_bg_color};
                color: {cmd_output_text_color};
                border: 1px solid {border_color};
                border-radius: 3px;
            }}
            
            QPushButton {{
                background-color: {button_bg_color};
                color: {button_text_color};
                border: none;
                border-radius: 3px;
                padding: 5px;
            }}
            
            QPushButton:hover {{
                background-color: {button_hover_color};
            }}
            
            QSizeGrip {{
                background-color: transparent;
            }}
        """)
    
    def create_circle_button(self, color):
        """创建圆形按钮"""
        # 从ui.styles重新导入最新的颜色变量
        from ui.styles import (
            minimize_button_color, close_button_color
        )
        
        # 使用最新的颜色
        if color == minimize_button_color or color == close_button_color:
            color = minimize_button_color if color == minimize_button_color else close_button_color
        
        button = QPushButton()
        button.setFixedSize(16, 16)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {self.lighten_color(color)};
            }}
        """)
        return button
    
    def apply_font(self):
        """应用字体"""
        # 从ui.styles重新导入最新的字体变量
        from ui.styles import current_font_family
        
        font = QFont(current_font_family, 9)  # 使用与主窗口相同的字体
        self.setFont(font)
        
        # 为所有子控件设置字体
        for widget in self.findChildren(QWidget):
            widget.setFont(font)
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)  # 设置边距，为圆角留出空间
        main_layout.setSpacing(0)
        
        # 创建内容容器（带圆角的主窗口）
        self.content_container = QWidget()
        self.content_container.setObjectName("contentContainer")
        container_layout = QVBoxLayout(self.content_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # 创建自定义标题栏
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(30)
        self.title_bar.setObjectName("titleBar")
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        
        # 添加图标
        icon_label = QLabel()
        icon_label.setPixmap(QIcon('res/logo.ico').pixmap(20, 20))
        title_layout.addWidget(icon_label)
        
        # 添加标题
        title_label = QLabel("命令输出")
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
        
        container_layout.addWidget(self.title_bar)
        
        # 创建内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)
        
        # 添加命令输出到内容区域
        content_layout.addWidget(self.cmd_output)
        
        container_layout.addWidget(content_widget)
        
        # 添加大小调整手柄
        size_grip = QSizeGrip(self.content_container)
        size_grip.setFixedSize(16, 16)
        
        # 创建一个布局来放置大小调整手柄在右下角
        grip_layout = QHBoxLayout()
        grip_layout.setContentsMargins(0, 0, 0, 0)
        grip_layout.addStretch()
        grip_layout.addWidget(size_grip)
        
        container_layout.addLayout(grip_layout)
        
        # 添加内容容器到主布局
        main_layout.addWidget(self.content_container)
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件，用于移动窗口"""
        if event.button() == Qt.LeftButton and self.title_bar.geometry().contains(event.position().toPoint()):
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件，用于移动窗口"""
        if event.buttons() & Qt.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件，结束窗口移动"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def closeEvent(self, event):
        """窗口关闭时发出信号"""
        self.closed.emit(self.cmd_output)
        super().closeEvent(event)
    
    def on_theme_changed(self):
        """主题变化时更新样式"""
        # 更新最小化和关闭按钮的样式
        from ui.styles import minimize_button_color, close_button_color
        
        self.min_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {minimize_button_color};
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {self.lighten_color(minimize_button_color)};
            }}
        """)
        
        self.close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {close_button_color};
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {self.lighten_color(close_button_color)};
            }}
        """)
        
        # 应用整体样式
        self.apply_style()
        self.apply_font()
