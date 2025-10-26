import multiprocessing
from PySide6.QtCore import QThread, Signal, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QObject, Property
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QToolTip,
    QFrame,
)
from PySide6.QtGui import QPainter, QBrush, QColor, QPen
from PySide6.QtCore import Qt
from .task_cards_bubble import task_cards_tooltip_manager

from plugin.quickcheck import QuickCheckWorker
from core.i18n import t



class RegexInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("输入搜索正则表达式")
        layout = QVBoxLayout(self)

        # 添加说明标签
        label = QLabel("请输入正则表达式，留空则使用默认表达式：\nflag{.+}|666c6167\\w+|ZmxhZ[\\w=]+|&#102.+")
        layout.addWidget(label)

        # 添加输入框
        self.regex_input = QLineEdit()
        self.regex_input.setPlaceholderText("输入正则表达式")
        layout.addWidget(self.regex_input)

        # 添加高级选项
        self.advanced_group = QGroupBox("高级选项")
        advanced_layout = QFormLayout(self.advanced_group)

        # 线程数选择
        self.thread_count = QSpinBox()
        self.thread_count.setMinimum(1)
        self.thread_count.setMaximum(32)
        self.thread_count.setValue(multiprocessing.cpu_count() * 2)  # 默认为CPU核心数的2倍
        advanced_layout.addRow("线程数:", self.thread_count)

        # 内存映射选项
        self.use_mmap = QCheckBox("使用内存映射")
        self.use_mmap.setChecked(True)
        self.use_mmap.setToolTip("使用内存映射通常能提高性能，但对于非常大的文件可能会失败")
        advanced_layout.addRow("", self.use_mmap)

        layout.addWidget(self.advanced_group)

        # 添加确定和取消按钮
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)

    def get_regex(self):
        return self.regex_input.text()

    def get_thread_count(self):
        return self.thread_count.value()

    def get_use_mmap(self):
        return self.use_mmap.isChecked()


class TaskStatusManager(QObject):
    """任务状态管理器，用于跟踪当前正在执行的任务"""
    task_added = Signal(str)  # 任务添加信号
    task_removed = Signal(str)  # 任务移除信号
    tasks_updated = Signal(list)  # 任务列表更新信号
    
    def __init__(self):
        super().__init__()
        self.current_tasks = []  # 当前正在执行的任务列表
    
    def add_task(self, task_name):
        """添加任务"""
        if task_name not in self.current_tasks:
            self.current_tasks.append(task_name)
            self.task_added.emit(task_name)
            self.tasks_updated.emit(self.current_tasks.copy())
    
    def remove_task(self, task_name):
        """移除任务"""
        if task_name in self.current_tasks:
            self.current_tasks.remove(task_name)
            self.task_removed.emit(task_name)
            self.tasks_updated.emit(self.current_tasks.copy())
    
    def get_tasks(self):
        """获取当前任务列表"""
        return self.current_tasks.copy()
    
    def clear_tasks(self):
        """清空所有任务"""
        self.current_tasks.clear()
        self.tasks_updated.emit([])


class TaskStatusButton(QPushButton):
    """任务状态显示按钮"""
    
    def __init__(self, task_manager, parent=None):
        super().__init__(parent)
        self.task_manager = task_manager
        self.setFixedSize(24, 24)
        
        # 动画属性
        self._rotation = 0
        self._pulse_scale = 1.0
        self.is_loading = False
        
        # 旋转动画（加载效果）
        self.rotation_animation = QPropertyAnimation(self, b"rotation")
        self.rotation_animation.setDuration(1000)
        self.rotation_animation.setLoopCount(-1)  # 无限循环
        self.rotation_animation.setStartValue(0)
        self.rotation_animation.setEndValue(360)
        
        # 脉冲动画（有任务时的效果）
        self.pulse_animation = QPropertyAnimation(self, b"pulse_scale")
        self.pulse_animation.setDuration(1500)
        self.pulse_animation.setLoopCount(-1)
        self.pulse_animation.setEasingCurve(QEasingCurve.InOutSine)
        self.pulse_animation.setStartValue(1.0)
        self.pulse_animation.setEndValue(1.1)
        
        # 连接任务管理器信号
        self.task_manager.tasks_updated.connect(self.update_display)
        self.task_manager.task_removed.connect(self.on_task_completed)
        
        # 初始化时隐藏按钮
        self.hide()
        self.has_ever_had_tasks = False  # 标记是否曾经有过任务
        
        # 设置鼠标悬停事件
        self.setMouseTracking(True)
    
    @Property(float)
    def rotation(self):
        return self._rotation
    
    @rotation.setter
    def rotation(self, value):
        self._rotation = value
        self.update()
    
    @Property(float)
    def pulse_scale(self):
        return self._pulse_scale
    
    @pulse_scale.setter
    def pulse_scale(self, value):
        self._pulse_scale = value
        self.update()
    
    def update_display(self, tasks):
        """更新按钮显示"""
        task_count = len(tasks)
        
        # 停止所有动画
        self.rotation_animation.stop()
        self.pulse_animation.stop()
        
        if task_count == 0:
            # 无任务状态 - 直接隐藏按钮
            self.hide()
            self.is_loading = False
            self._pulse_scale = 1.0
        else:
            # 有任务状态
            self.has_ever_had_tasks = True  # 标记曾经有过任务
            self.show()  # 确保按钮可见
            self.setText(str(task_count))
            self.is_loading = True
            self.setStyleSheet("""
                QPushButton {
                    border: 2px solid #28a745;
                    border-radius: 12px;
                    background-color: #d4edda;
                    color: #155724;
                    font-weight: bold;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #c3e6cb;
                    border-color: #1e7e34;
                }
            """)
            
            # 启动脉冲动画
            self.pulse_animation.start()
        
        self.update()  # 触发重绘
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        # 使用新的气泡组件显示任务信息
        global_pos = self.mapToGlobal(QPoint(self.width() // 2, 0))
        task_cards_tooltip_manager.show_task_tooltip(self, self.task_manager, global_pos)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        # 隐藏气泡
        task_cards_tooltip_manager.hide_current_bubble()
        super().leaveEvent(event)
    
    def on_task_completed(self, task_name):
        """任务完成时的处理"""
        # 如果当前显示的气泡存在，更新其状态为完成状态
        if hasattr(task_cards_tooltip_manager, 'current_bubble') and task_cards_tooltip_manager.current_bubble:
            # 触发气泡重新渲染，显示任务完成后的灰色状态
            task_cards_tooltip_manager.current_bubble.update()
            # 延迟隐藏气泡，让用户看到状态变化
            QTimer.singleShot(1500, task_cards_tooltip_manager.hide_current_bubble)
    
    def paintEvent(self, event):
        """自定义绘制事件"""
        super().paintEvent(event)
        
        if self.is_loading and self._pulse_scale != 1.0:
            # 绘制脉冲效果
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 计算脉冲圆环
            center = self.rect().center()
            base_radius = min(self.width(), self.height()) // 2 - 2
            pulse_radius = base_radius * self._pulse_scale
            
            # 绘制脉冲圆环
            pulse_color = QColor(40, 167, 69, int(100 * (2.0 - self._pulse_scale)))
            painter.setPen(QPen(pulse_color, 2))
            painter.drawEllipse(center, int(pulse_radius), int(pulse_radius))
            
            painter.end()


class FileMenuArea(QWidget):
    load_image_signal = Signal()
    add_tab_signal = Signal(QWidget, str)  # 添加标签页的信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_path = None
        
        # 创建任务状态管理器
        self.task_manager = TaskStatusManager()
        
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group_box = QGroupBox(t("file_operations.title"))
        group_layout = QHBoxLayout(group_box)

        load_image_button = QPushButton(t("file_operations.load_image"))
        unload_image_button = QPushButton(t("file_operations.unload_image"))

        # 创建任务状态按钮
        self.task_status_button = TaskStatusButton(self.task_manager, self)
        self.task_status_button.setToolTip(t("file_operations.task_status"))

        group_layout.addWidget(load_image_button)
        group_layout.addWidget(unload_image_button)
        group_layout.addWidget(self.task_status_button)  # 添加任务状态按钮

        layout.addWidget(group_box)

        load_image_button.clicked.connect(self.load_image_signal.emit)
        unload_image_button.clicked.connect(self.parent().unload_image)


    def set_image_path(self, path):
        self.image_path = path

    def trigger_load_image(self):
        self.load_image_signal.emit()
