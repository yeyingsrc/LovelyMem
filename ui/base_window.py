"""
基础无边框窗口类

封装自定义标题栏、圆形按钮、窗口拖拽等共通功能，
消除 main_window.py、launcher.py、file_slot.py、topic_analysis_dialog.py 等
文件中重复实现相同代码的问题。
"""
import logging
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QIcon, QMouseEvent
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QDialog
)

from core.paths import LOGO_ICO

logger = logging.getLogger(__name__)


def create_circle_button(base_color, size=14):
    """
    创建圆形按钮（统一实现）。
    
    之前在 main_window.py, launcher.py, file_slot.py, 
    topic_analysis_dialog.py 等文件中各自实现。
    """
    button = QPushButton()
    button.setFixedSize(size, size)
    button.setCursor(Qt.PointingHandCursor)
    return button


def update_circle_button_style(button, base_color, hover_color=None):
    """
    更新圆形按钮样式（统一实现）。
    
    之前在 main_window.py, topic_analysis_dialog.py 中重复定义。
    """
    if hover_color is None:
        hover_color = base_color
    
    radius = button.width() // 2
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {base_color};
            border-radius: {radius}px;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
    """)


class TitleBarMixin:
    """
    自定义标题栏混入类。
    
    提供标题栏创建和窗口拖拽功能。
    需要子类具有 setWindowFlags(Qt.FramelessWindowHint) 的窗口。
    """
    
    # 标题栏按钮颜色常量
    THEME_BUTTON_COLOR = "rgba(255, 223, 186, 0.9)"
    MINIMIZE_BUTTON_COLOR = "rgba(198, 255, 198, 0.9)"
    MAXIMIZE_BUTTON_COLOR = "rgba(186, 225, 255, 0.9)"
    CLOSE_BUTTON_COLOR = "rgba(255, 204, 204, 0.9)"
    
    def _init_drag_state(self):
        """初始化拖拽状态变量"""
        self._dragging = False
        self._drag_position = QPoint()
    
    def create_title_bar(self, title="LovelyMem", show_theme=False, 
                         show_minimize=True, show_maximize=False, show_close=True):
        """
        创建自定义标题栏。
        
        Args:
            title: 标题文本
            show_theme: 是否显示主题切换按钮
            show_minimize: 是否显示最小化按钮
            show_maximize: 是否显示最大化按钮
            show_close: 是否显示关闭按钮
        
        Returns:
            title_bar: QFrame 标题栏控件
        """
        self._init_drag_state()
        
        title_bar = QFrame()
        title_bar.setFixedHeight(30)
        title_bar.setObjectName("titleBar")
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        
        # 添加图标
        icon_label = QLabel()
        icon_path = str(LOGO_ICO)
        icon_label.setPixmap(QIcon(icon_path).pixmap(20, 20))
        title_layout.addWidget(icon_label)
        
        # 添加标题
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 创建按钮
        if show_theme:
            self.theme_button = create_circle_button(self.THEME_BUTTON_COLOR)
            self.theme_button.setToolTip("切换主题")
            title_layout.addWidget(self.theme_button)
        
        if show_minimize:
            self.min_button = create_circle_button(self.MINIMIZE_BUTTON_COLOR)
            self.min_button.clicked.connect(self.showMinimized)
            self.min_button.setToolTip("最小化")
            title_layout.addWidget(self.min_button)
        
        if show_maximize:
            self.max_button = create_circle_button(self.MAXIMIZE_BUTTON_COLOR)
            self.max_button.clicked.connect(self._toggle_maximize)
            self.max_button.setToolTip("最大化")
            title_layout.addWidget(self.max_button)
        
        if show_close:
            self.close_button = create_circle_button(self.CLOSE_BUTTON_COLOR)
            self.close_button.clicked.connect(self.close)
            self.close_button.setToolTip("关闭")
            title_layout.addWidget(self.close_button)
        
        self._title_bar = title_bar
        return title_bar
    
    def _toggle_maximize(self):
        """切换最大化/还原状态"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def handle_title_bar_mouse_press(self, event: QMouseEvent):
        """处理标题栏鼠标按下事件（用于拖拽）"""
        if event.button() == Qt.LeftButton:
            if hasattr(self, '_title_bar') and self._title_bar.geometry().contains(event.position().toPoint()):
                # 确保点击的不是按钮
                child_widget = self.childAt(event.position().toPoint())
                if isinstance(child_widget, QPushButton):
                    return False  # 让事件继续传播给按钮
                
                self._dragging = True
                self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
                return True
        return False
    
    def handle_title_bar_mouse_move(self, event: QMouseEvent):
        """处理标题栏鼠标移动事件（用于拖拽）"""
        if self._dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
            return True
        return False
    
    def handle_title_bar_mouse_release(self, event: QMouseEvent):
        """处理标题栏鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self._dragging = False
            return True
        return False
    
    def update_title_bar_buttons(self, hover_color=None):
        """更新标题栏所有圆形按钮的样式"""
        buttons_and_colors = []
        
        if hasattr(self, 'theme_button'):
            buttons_and_colors.append((self.theme_button, self.THEME_BUTTON_COLOR))
        if hasattr(self, 'min_button'):
            buttons_and_colors.append((self.min_button, self.MINIMIZE_BUTTON_COLOR))
        if hasattr(self, 'max_button'):
            buttons_and_colors.append((self.max_button, self.MAXIMIZE_BUTTON_COLOR))
        if hasattr(self, 'close_button'):
            buttons_and_colors.append((self.close_button, self.CLOSE_BUTTON_COLOR))
        
        for button, color in buttons_and_colors:
            update_circle_button_style(button, color, hover_color)
