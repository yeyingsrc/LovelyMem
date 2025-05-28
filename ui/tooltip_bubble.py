from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property, QPoint
from PySide6.QtGui import QPainter, QPainterPath, QColor, QFont, QPalette, QPen

class TooltipBubble(QWidget):
    """
    自定义气泡提示组件
    提供更好的视觉效果和动画
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
        
        # 设置布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(self.padding, self.padding, 
                                     self.padding, self.padding)
        
        # 内容标签
        self.content_label = QLabel()
        self.content_label.setWordWrap(True)
        self.content_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.content_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                font-size: 13px;
                font-weight: 500;
                line-height: 1.5;
                padding: 4px;
            }
        """)
        self.layout.addWidget(self.content_label)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        
        # 动画
        self.fade_animation = QPropertyAnimation(self, b"opacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.scale_animation = QPropertyAnimation(self, b"scale")
        self.scale_animation.setDuration(200)
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
    
    def set_content(self, text, task_count=0):
        """设置气泡内容"""
        if task_count == 0:
            self.content_label.setText("📋 当前没有正在执行的任务")
            self.content_label.setStyleSheet("""
                QLabel {
                    color: #6c757d;
                    background: transparent;
                    font-size: 13px;
                    font-weight: 500;
                    padding: 8px;
                }
            """)
        else:
            # 格式化任务列表，添加图标
            formatted_text = f"⚡ 正在执行 {task_count} 个任务:\n\n" + text.replace("• ", "🔸 ")
            self.content_label.setText(formatted_text)
            self.content_label.setStyleSheet("""
                QLabel {
                    color: #2c3e50;
                    background: transparent;
                    font-size: 13px;
                    font-weight: 500;
                    padding: 8px;
                }
            """)
        
        # 调整大小
        self.adjustSize()
    
    def show_at_position(self, global_pos, auto_hide_delay=3000):
        """在指定位置显示气泡"""
        # 调整位置，确保气泡在屏幕内
        screen_geometry = self.screen().geometry()
        bubble_size = self.sizeHint()
        
        x = global_pos.x() - bubble_size.width() // 2
        y = global_pos.y() - bubble_size.height() - 10  # 移除箭头高度
        
        # 边界检查
        if x < screen_geometry.left():
            x = screen_geometry.left() + 10
        elif x + bubble_size.width() > screen_geometry.right():
            x = screen_geometry.right() - bubble_size.width() - 10
        
        if y < screen_geometry.top():
            y = global_pos.y() + 30  # 显示在下方
        
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
        """绘制卡片样式"""
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
        
        # 根据任务数量选择颜色 - 保持一致的配色方案
        tasks = []
        if hasattr(self, '_task_manager'):
            tasks = self._task_manager.get_tasks()
        
        if len(tasks) == 0:
            # 无任务时的卡片样式 - 使用中性色调
            bg_color = QColor(255, 255, 255, 250)  # 白色背景
            border_color = QColor(220, 220, 220, 180)  # 浅灰色边框
            accent_color = QColor(108, 117, 125, 100)  # 灰色装饰
        else:
            # 有任务时的卡片样式 - 使用活跃色调
            bg_color = QColor(255, 255, 255, 250)  # 白色背景
            border_color = QColor(40, 167, 69, 180)  # 绿色边框
            accent_color = QColor(40, 167, 69, 100)  # 绿色装饰
        
        # 绘制卡片背景
        path = QPainterPath()
        path.addRoundedRect(scaled_rect, self.border_radius, self.border_radius)
        painter.fillPath(path, bg_color)
        
        # 绘制边框
        painter.setPen(QPen(border_color, 2))
        painter.drawPath(path)
    
    def set_task_manager(self, task_manager):
        """设置任务管理器引用"""
        self._task_manager = task_manager

class TaskTooltipManager:
    """
    任务提示管理器
    管理气泡的显示和隐藏
    """
    
    def __init__(self):
        self.current_bubble = None
    
    def show_task_tooltip(self, widget, task_manager, global_pos=None):
        """显示任务提示气泡"""
        # 隐藏当前气泡
        self.hide_current_bubble()
        
        # 创建新气泡
        self.current_bubble = TooltipBubble()
        self.current_bubble.set_task_manager(task_manager)
        
        # 获取任务列表
        tasks = task_manager.get_tasks()
        task_count = len(tasks)
        
        if task_count == 0:
            content = "当前没有正在执行的任务"
        else:
            content = "正在执行的任务：\n" + "\n".join([f"• {task}" for task in tasks])
        
        self.current_bubble.set_content(content, task_count)
        
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
tooltip_manager = TaskTooltipManager()