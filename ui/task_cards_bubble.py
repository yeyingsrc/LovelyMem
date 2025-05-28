from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property, QPoint
from PySide6.QtGui import QPainter, QPainterPath, QColor, QFont, QPalette, QPen

class TaskCard(QWidget):
    """
    单个任务卡片组件
    """
    
    def __init__(self, task_name, parent=None):
        super().__init__(parent)
        self.task_name = task_name
        self.border_radius = 8
        self.padding = 12
        
        # 设置固定大小
        self.setFixedSize(200, 60)
        
        # 设置布局
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(self.padding, self.padding, 
                                     self.padding, self.padding)
        
        # 状态指示器
        self.status_indicator = QLabel("🔸")
        self.status_indicator.setFixedSize(16, 16)
        self.status_indicator.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_indicator)
        
        # 任务名称标签
        self.task_label = QLabel(task_name)
        self.task_label.setWordWrap(True)
        self.task_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                font-size: 12px;
                font-weight: 500;
                padding: 2px;
            }
        """)
        self.layout.addWidget(self.task_label, 1)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
    
    def paintEvent(self, event):
        """绘制卡片样式"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        
        # 卡片背景色
        bg_color = QColor(255, 255, 255, 250)  # 白色背景
        border_color = QColor(40, 167, 69, 180)  # 绿色边框
        
        # 绘制卡片背景
        path = QPainterPath()
        path.addRoundedRect(rect, self.border_radius, self.border_radius)
        painter.fillPath(path, bg_color)
        
        # 绘制边框
        painter.setPen(QPen(border_color, 1.5))
        painter.drawPath(path)
        
        # 绘制左侧装饰条
        accent_rect = rect.adjusted(4, 4, -rect.width() + 8, -4)
        accent_path = QPainterPath()
        accent_path.addRoundedRect(accent_rect, 2, 2)
        painter.fillPath(accent_path, QColor(40, 167, 69, 120))

class TaskCardsBubble(QWidget):
    """
    多卡片任务气泡组件
    每个任务显示为一个独立的小卡片
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
        # 气泡属性
        self._opacity = 0.0
        self._scale = 0.8
        self.border_radius = 12
        self.padding = 16
        self.card_spacing = 8
        
        # 设置布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(self.padding, self.padding, 
                                     self.padding, self.padding)
        self.layout.setSpacing(self.card_spacing)
        
        # 标题标签
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                font-size: 14px;
                font-weight: bold;
                padding: 4px;
                margin-bottom: 8px;
            }
        """)
        self.layout.addWidget(self.title_label)
        
        # 卡片容器
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(self.card_spacing)
        self.layout.addWidget(self.cards_container)
        
        # 添加整体阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        # 动画
        self.fade_animation = QPropertyAnimation(self, b"opacity")
        self.fade_animation.setDuration(250)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.scale_animation = QPropertyAnimation(self, b"scale")
        self.scale_animation.setDuration(250)
        self.scale_animation.setEasingCurve(QEasingCurve.OutBack)
        
        # 自动隐藏定时器
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_animated)
    
    @Property(float)
    def opacity(self):
        return self._opacity
    
    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.update()
    
    @Property(float)
    def scale(self):
        return self._scale
    
    @scale.setter
    def scale(self, value):
        self._scale = value
        self.update()
    
    def set_tasks(self, tasks):
        """设置任务列表并创建对应的卡片"""
        # 清除现有卡片
        self.clear_cards()
        
        task_count = len(tasks)
        
        if task_count == 0:
            # 无任务时显示提示
            self.title_label.setText("📋 当前没有正在执行的任务")
            self.title_label.setStyleSheet("""
                QLabel {
                    color: #6c757d;
                    background: transparent;
                    font-size: 14px;
                    font-weight: 500;
                    padding: 16px;
                }
            """)
        else:
            # 设置标题
            self.title_label.setText(f"⚡ 正在执行 {task_count} 个任务")
            self.title_label.setStyleSheet("""
                QLabel {
                    color: #2c3e50;
                    background: transparent;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 4px;
                    margin-bottom: 8px;
                }
            """)
            
            # 为每个任务创建卡片
            for task in tasks:
                card = TaskCard(task)
                self.cards_layout.addWidget(card)
        
        # 调整大小
        self.adjustSize()
    
    def clear_cards(self):
        """清除所有任务卡片"""
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def show_at_position(self, global_pos, auto_hide_delay=4000):
        """在指定位置显示气泡"""
        # 调整位置，确保气泡在屏幕内
        screen_geometry = self.screen().geometry()
        bubble_size = self.sizeHint()
        
        x = global_pos.x() - bubble_size.width() // 2
        y = global_pos.y() - bubble_size.height() - 15
        
        # 边界检查
        if x < screen_geometry.left():
            x = screen_geometry.left() + 10
        elif x + bubble_size.width() > screen_geometry.right():
            x = screen_geometry.right() - bubble_size.width() - 10
        
        if y < screen_geometry.top():
            y = global_pos.y() + 35  # 显示在下方
        
        self.move(x, y)
        self.show_animated()
        
        # 设置自动隐藏
        if auto_hide_delay > 0:
            self.hide_timer.start(auto_hide_delay)
    
    def show_animated(self):
        """显示动画"""
        self.show()
        
        # 透明度动画
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        
        # 缩放动画
        self.scale_animation.setStartValue(0.8)
        self.scale_animation.setEndValue(1.0)
        self.scale_animation.start()
    
    def hide_animated(self):
        """隐藏动画"""
        # 透明度动画
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.hide)
        self.fade_animation.start()
        
        # 缩放动画
        self.scale_animation.setStartValue(1.0)
        self.scale_animation.setEndValue(0.8)
        self.scale_animation.start()
    
    def paintEvent(self, event):
        """绘制整体容器背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 应用透明度和缩放
        painter.setOpacity(self._opacity)
        
        # 计算缩放后的矩形
        rect = self.rect()
        scaled_width = int(rect.width() * self._scale)
        scaled_height = int(rect.height() * self._scale)
        scaled_rect = rect.adjusted(
            (rect.width() - scaled_width) // 2,
            (rect.height() - scaled_height) // 2,
            -(rect.width() - scaled_width) // 2,
            -(rect.height() - scaled_height) // 2
        )
        
        # 绘制整体背景
        bg_color = QColor(248, 249, 250, 240)  # 浅灰色半透明背景
        border_color = QColor(220, 220, 220, 200)  # 浅灰色边框
        
        path = QPainterPath()
        path.addRoundedRect(scaled_rect, self.border_radius, self.border_radius)
        painter.fillPath(path, bg_color)
        
        # 绘制边框
        painter.setPen(QPen(border_color, 1))
        painter.drawPath(path)

class TaskCardsTooltipManager:
    """
    多卡片任务提示管理器
    管理多卡片气泡的显示和隐藏
    """
    
    def __init__(self):
        self.current_bubble = None
    
    def show_task_tooltip(self, widget, task_manager, global_pos=None):
        """显示任务提示气泡"""
        # 隐藏当前气泡
        self.hide_current_bubble()
        
        # 创建新气泡
        self.current_bubble = TaskCardsBubble()
        
        # 获取任务列表
        tasks = task_manager.get_tasks()
        
        self.current_bubble.set_tasks(tasks)
        
        # 确定显示位置
        if global_pos is None:
            global_pos = widget.mapToGlobal(QPoint(widget.width() // 2, 0))
        
        self.current_bubble.show_at_position(global_pos)
    
    def hide_current_bubble(self):
        """隐藏当前气泡"""
        if self.current_bubble:
            self.current_bubble.hide_animated()
            self.current_bubble = None

# 全局实例
task_cards_tooltip_manager = TaskCardsTooltipManager()