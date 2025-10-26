from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, QHBoxLayout, QMessageBox, QMenu, QDialog
from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QPixmap
from ui.styles import quick_check_style
import random
import os
from plugin.knowledge_base import KnowledgeBaseDialog
from plugin.quickcheck import QuickCheck, QuickCheckWorker
from db.updatevol3cache import update_identifier_cache
from core.task_scheduler import TaskSchedulerDialog
from plugin.report_editor import ReportEditor
from ui.config_dialog import ConfigDialog
from ui.topic_analysis_dialog import TopicAnalysisDialog
from PySide6.QtWidgets import QApplication
import multiprocessing
from PySide6.QtWidgets import QFormLayout, QLineEdit, QSpinBox, QCheckBox, QGroupBox

class RegexInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("输入搜索正则表达式")
        layout = QVBoxLayout(self)

        # 添加说明标签
        label = QLabel("请输入正则表达式，留空则使用默认表达式：\nflag{.+}|666c6167\w+|ZmxhZ[\w=]+|&#102.+")
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

class QuickCheckButton(QPushButton):
    def __init__(self, text, function=None):
        super().__init__(text)
        if function:
            self.clicked.connect(function)

class CollapsibleButtonGroup(QWidget):
    def __init__(self, title, buttons, main_window):
        super().__init__()
        self.title = title
        self.buttons = buttons
        self.main_window = main_window
        self.is_expanded = True
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.title_button = QuickCheckButton(self.title)
        self.title_button.clicked.connect(self.toggle_expand)
        layout.addWidget(self.title_button)

        self.content_widget = QWidget()
        self.content_layout = QGridLayout(self.content_widget)
        for i, button in enumerate(self.buttons):
            row = i // 2
            col = i % 2
            self.content_layout.addWidget(button, row, col)
        self.content_widget.setVisible(True)
        layout.addWidget(self.content_widget)
        
        # 添加右键菜单功能
        for button in self.buttons:
            button.setContextMenuPolicy(Qt.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda pos, btn=button: self.show_context_menu(pos, btn))

    def show_context_menu(self, pos, button):
        if hasattr(self.main_window, 'preset_manager'):
            context_menu = self.main_window.preset_manager.create_context_menu(button, source_area="QuickCheck")
            context_menu.exec(button.mapToGlobal(pos))

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)

class QuickCheckArea(QWidget):
    add_tab_signal = Signal(QWidget, str)  # 添加标签页的信号
    
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setStyleSheet(quick_check_style)
        layout = QVBoxLayout(self)
        
        
        # 新增高级功能组
        advanced_buttons = [
            QPushButton("任务编排"),
            QPushButton("报告编辑器"),
            QPushButton("字典管理"),
            QPushButton("题意分析"),
            QPushButton("设置"),
            QPushButton("高亮设置"),
            QPushButton("搜索镜像字符串"),
        ]
        
        # 初始化搜索相关属性
        self.is_searching = False
        self.quick_check_worker = None
        self.quick_check_thread = None
        self.search_results = None
        self.current_smooth_progress = 0
        self.target_progress = 0
        self.image_path = None
        self.advanced_group = CollapsibleButtonGroup("高级功能", advanced_buttons, self.main_window)
        layout.addWidget(self.advanced_group)
        # 其他功能组
        
        other_buttons = [
            QPushButton("常备知识"),
            QPushButton("强制重置VOL3缓存"),
        ]

        other_buttons[0].clicked.connect(self.show_knowledge_base)
        other_buttons[1].clicked.connect(self.update_vol3_cache)
        self.other_group = CollapsibleButtonGroup("其他功能", other_buttons, self.main_window)
        layout.addWidget(self.other_group)



        advanced_buttons[0].clicked.connect(self.show_task_scheduler)
        advanced_buttons[1].clicked.connect(self.show_report_editor)
        advanced_buttons[2].clicked.connect(self.show_dictionary_manager)
        advanced_buttons[3].clicked.connect(self.show_topic_analysis)
        advanced_buttons[4].clicked.connect(self.show_config_dialog)
        advanced_buttons[5].clicked.connect(self.show_highlight_settings)
        advanced_buttons[6].clicked.connect(self.show_quick_check)
        # 为其他高级功能按钮添加连接

        # 保存搜索按钮的引用以便后续操作
        self.quick_check_button = advanced_buttons[6]
        


        layout.addStretch()

    def update_user_info(self, avatar_path, user_info):
        self.user_avatar.setPixmap(QPixmap(avatar_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.user_info_label.setText(user_info)

    def update_vol3_cache(self):
        reply = QMessageBox.question(self, "提示", "一般来说如果没有更换路径位置不需要点击这里\n强制重置VOL3缓存会删除本地已经有的vol3缓存\n强制构建默认镜像索引，是否继续？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            update_identifier_cache()

    # 添加这个新方法
    def show_knowledge_base(self):
        dialog = KnowledgeBaseDialog(self)
        dialog.exec()

    def show_task_scheduler(self):
        dialog = TaskSchedulerDialog(self)
        dialog.task_execute.connect(self.execute_task_flow)
        # 使用非模态方式显示对话框
        dialog.show()

    def execute_task_flow(self, tasks):
        """执行任务流程
        
        参数:
            tasks: 从流程图获取的任务序列，每个任务是一个包含 area 和 task 键的字典
        """
        # 显示当前执行的任务流程
        self.main_window.cmd_output.append("\n=== 开始执行任务流程 ===\n")
        
        for i, task in enumerate(tasks):
            try:
                area = task["area"]
                function = task["task"]
                
                # 添加任务到任务管理器
                task_name = f"任务流程 - {area} - {function}"
                if hasattr(self.main_window, 'task_manager'):
                    self.main_window.task_manager.add_task(task_name)
                
                try:
                    # 显示当前执行的任务
                    self.main_window.cmd_output.append(f"正在执行 [{i+1}/{len(tasks)}]: {area} - {function}")
                    
                    # 根据任务区域执行相应的功能
                    if area == "MemProcFS":
                        self.main_window.execute_memprocfs_function(function)
                    elif area == "Volatility 2":
                        self.main_window.execute_vol2_function(function)
                    elif area == "Volatility 3":
                        self.main_window.execute_vol3_function(function)
                    elif area == "快速检查":
                        self.main_window.execute_quick_check_function(function)
                    
                    # 每个任务执行后短暂暂停，让用户有时间查看输出
                    QApplication.processEvents()
                finally:
                    # 任务完成后从任务管理器中移除
                    if hasattr(self.main_window, 'task_manager'):
                        self.main_window.task_manager.remove_task(task_name)
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"执行任务 '{area} - {function}' 时发生错误：{str(e)}")
                break
        
        # 任务流程执行完成
        self.main_window.cmd_output.append("\n=== 任务流程执行完成 ===\n")

    def show_report_editor(self):
        self.report_editor = ReportEditor()
        self.report_editor.setWindowTitle("报告编辑器")
        self.report_editor.resize(1000, 600)
        self.report_editor.show()
        
    def show_config_dialog(self):
        """显示配置对话框"""
        dialog = ConfigDialog(self)
        dialog.exec()
        
    def show_dictionary_manager(self):
        """显示字典管理器"""
        from ui.dictionary_manager_dialog import DictionaryManagerDialog
        dialog = DictionaryManagerDialog(self)
        dialog.exec()
        
    def show_highlight_settings(self):
        """显示按钮高亮设置对话框"""
        from ui.highlight_settings_dialog import HighlightSettingsDialog
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'highlight_buttons.json')
        highlight_manager = self.main_window.highlight_manager if hasattr(self.main_window, 'highlight_manager') else None
        dialog = HighlightSettingsDialog(self, config_path, highlight_manager)
        dialog.exec()

    def show_topic_analysis(self):
        """显示题意分析对话框"""
        # 获取主窗口的高亮管理器
        highlight_manager = getattr(self.main_window, 'highlight_manager', None)

        # 创建并显示题意分析对话框
        dialog = TopicAnalysisDialog(self.main_window, highlight_manager)
        dialog.show()

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
        if hasattr(self.main_window, 'task_manager'):
            self.main_window.task_manager.add_task("搜索镜像字符串")

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
        if hasattr(self.main_window, 'task_manager'):
            self.main_window.task_manager.remove_task("搜索镜像字符串")
        
        # 停止进度定时器
        if hasattr(self, 'progress_timer') and self.progress_timer.isActive():
            self.progress_timer.stop()
            
        # 处理搜索结果
        if hasattr(self, 'search_results'):
            self.process_search_results(self.search_results)
            
    def process_search_results(self, results):
        # 处理搜索结果的逻辑 - 根据用户要求，不展示结果也不添加tab
        # 只进行搜索，不显示结果
        
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
        if hasattr(self.main_window, 'task_manager'):
            self.main_window.task_manager.remove_task("搜索镜像字符串")
        
        QMessageBox.critical(self, "错误", f"搜索过程中发生错误：{error_msg}")

    def cancel_quick_check(self):
        if self.quick_check_worker and self.is_searching:
            self.quick_check_worker.requestInterruption()
            self.quick_check_button.setText("正在取消...")
            self.is_searching = False
            
            # 从任务管理器中移除任务
            if hasattr(self.main_window, 'task_manager'):
                self.main_window.task_manager.remove_task("搜索镜像字符串")

    def set_image_path(self, path):
        self.image_path = path
