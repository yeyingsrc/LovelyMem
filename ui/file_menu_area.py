import multiprocessing
from PySide6.QtCore import QThread, Signal, QTimer
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
)

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

        group_layout.addWidget(load_image_button)
        group_layout.addWidget(unload_image_button)
        group_layout.addWidget(self.quick_check_button)

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
        if dialog.exec_() == QDialog.Accepted:
            regex = dialog.get_regex()
            thread_count = dialog.get_thread_count()
            use_mmap = dialog.get_use_mmap()
            self.start_search(regex, thread_count, use_mmap)

    def start_search(self, regex, thread_count=None, use_mmap=True):
        self.is_searching = True
        self.quick_check_button.setEnabled(False)
        self.set_button_progress(0)

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
        self.quick_check_button.setText("搜索字符串")
        
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
        QMessageBox.critical(self, "错误", f"搜索过程中发生错误：{error_msg}")

    def cancel_quick_check(self):
        if self.quick_check_worker and self.is_searching:
            self.quick_check_worker.requestInterruption()
            self.quick_check_button.setText("正在取消...")
            self.is_searching = False

    def set_image_path(self, path):
        self.image_path = path

    def trigger_load_image(self):
        self.load_image_signal.emit()
