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
        self.quick_check_thread = None
        self.quick_check_worker = None
        self.quick_check_button = None
        self.is_searching = False
        self.string_search_results = None
        
        # 创建任务状态管理器
        self.task_manager = TaskStatusManager()
        
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group_box = QGroupBox("文件操作")
        group_layout = QHBoxLayout(group_box)

        load_image_button = QPushButton("加载镜像")
        unload_image_button = QPushButton("卸载镜像")
        self.quick_check_button = QPushButton("搜索镜像字符串")
        self.quick_check_button.setMinimumWidth(120)  # 设置最小宽度确保进度条显示效果
        
        # 创建任务状态按钮
        self.task_status_button = TaskStatusButton(self.task_manager, self)
        self.task_status_button.setToolTip("点击查看当前正在执行的任务")

        group_layout.addWidget(load_image_button)
        group_layout.addWidget(unload_image_button)
        group_layout.addWidget(self.quick_check_button)
        group_layout.addWidget(self.task_status_button)  # 添加任务状态按钮

        layout.addWidget(group_box)

        load_image_button.clicked.connect(self.load_image_signal.emit)
        unload_image_button.clicked.connect(self.parent().unload_image)
        self.quick_check_button.clicked.connect(self.show_quick_check)

    def show_quick_check(self):
        if self.is_searching:
            if QMessageBox.question(self, "取消搜索", "是否要取消当前搜索？") == QMessageBox.Yes:
                self.cancel_quick_check()
            return

        if self.image_path is None:
            QMessageBox.warning(self, "错误", "未加载镜像文件")
            return

        dialog = RegexInputDialog(self)
        if dialog.exec() == QDialog.Accepted:
            regex = dialog.get_regex()
            thread_count = dialog.get_thread_count()
            use_mmap = dialog.get_use_mmap()
            self.start_search(regex, thread_count, use_mmap)

    def start_search(self, regex, thread_count=None, use_mmap=True):
        self.is_searching = True
        self.quick_check_button.setEnabled(False)
        self.set_button_progress(0)
        
        # 添加任务到任务管理器
        self.task_manager.add_task("搜索镜像字符串")

        # 立即开始显示进度动画
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_smooth_progress)
        self.current_smooth_progress = 0
        self.progress_timer.start(50)  # 每50毫秒更新一次

        self.quick_check_thread = QThread()
        self.quick_check_worker = QuickCheckWorker(self.image_path, regex)
        # 配置高级选项
        if hasattr(self.quick_check_worker.quick_check, "num_threads"):
            self.quick_check_worker.quick_check.num_threads = thread_count
        if hasattr(self.quick_check_worker.quick_check, "use_mmap"):
            self.quick_check_worker.quick_check.use_mmap = use_mmap

        self.quick_check_worker.moveToThread(self.quick_check_thread)

        self.quick_check_thread.started.connect(self.quick_check_worker.run)
        self.quick_check_worker.finished.connect(self.on_quick_check_finished)
        self.quick_check_worker.finished.connect(self.quick_check_thread.quit)
        self.quick_check_worker.progress.connect(self.update_search_progress)
        self.quick_check_worker.error.connect(self.show_error)

        self.quick_check_thread.start()

    def update_smooth_progress(self):
        if self.is_searching and self.current_smooth_progress < 99:
            self.current_smooth_progress += 1
            self.set_button_progress(self.current_smooth_progress)

    def set_button_progress(self, value):
        style = f"""
        QPushButton {{
            text-align: center;
            padding: 4px;
            position: relative;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                      stop: 0 #007bff,
                                      stop: {value / 100} #007bff,
                                      stop: {value / 100} #f8f9fa,
                                      stop: 1 #f8f9fa);
            border: 1px solid #ced4da;
            border-radius: 4px;
        }}
        QPushButton:disabled {{
            color: #212529;
        }}
        """
        self.quick_check_button.setStyleSheet(style)
        self.quick_check_button.setText(f"搜索中... {int(value)}%")

    def update_search_progress(self, value):
        if self.is_searching:
            # 只更新实际进度，不直接设置按钮进度
            self.target_progress = value

    def on_quick_check_finished(self, results):
        # 确保进度条到达100%
        self.set_button_progress(100)
        
        # 延迟一小段时间后再结束搜索状态，确保用户能看到100%
        QTimer.singleShot(500, self.finish_search)
        
        # 保存结果以便延迟处理
        self.search_results = results
    
    def finish_search(self):
        self.is_searching = False
        self.quick_check_button.setEnabled(True)
        self.quick_check_button.setStyleSheet("")
        self.quick_check_button.setText("搜索镜像字符串")
        
        # 从任务管理器中移除任务
        self.task_manager.remove_task("搜索镜像字符串")
        
        # 停止进度定时器
        if hasattr(self, 'progress_timer') and self.progress_timer.isActive():
            self.progress_timer.stop()
            
        # 处理搜索结果
        if hasattr(self, 'search_results'):
            self.process_search_results(self.search_results)
            
    def process_search_results(self, results):
        # 处理搜索结果的逻辑
        if hasattr(self, 'string_search_results') and self.string_search_results:
            self.string_search_results.deleteLater()
        
        # 创建新的结果显示区域
        from ui.string_search_results import StringSearchResults
        self.string_search_results = StringSearchResults(results, self.image_path)
        self.add_tab_signal.emit(self.string_search_results, "字符串搜索结果")
        
        # 清理资源
        if self.quick_check_worker:
            self.quick_check_worker.deleteLater()
        if self.quick_check_thread:
            self.quick_check_thread.deleteLater()
        self.quick_check_worker = None
        self.quick_check_thread = None

    def show_error(self, error_msg):
        self.is_searching = False
        self.quick_check_button.setEnabled(True)
        self.quick_check_button.setStyleSheet("")
        self.quick_check_button.setText("搜索镜像字符串")
        
        # 从任务管理器中移除任务
        self.task_manager.remove_task("搜索镜像字符串")
        
        QMessageBox.critical(self, "错误", f"搜索过程中发生错误：{error_msg}")

    def cancel_quick_check(self):
        if self.quick_check_worker and self.is_searching:
            self.quick_check_worker.requestInterruption()
            self.quick_check_button.setText("正在取消...")
            self.is_searching = False
            
            # 从任务管理器中移除任务
            self.task_manager.remove_task("搜索镜像字符串")

    def set_image_path(self, path):
        self.image_path = path

    def trigger_load_image(self):
        self.load_image_signal.emit()
