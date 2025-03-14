from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, QHBoxLayout, QMessageBox, QMenu
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from ui.styles import quick_check_style
import random
from plugin.knowledge_base import KnowledgeBaseDialog
from plugin.quickcheck import QuickCheck
from db.updatevol3cache import update_identifier_cache
from core.task_scheduler import TaskSchedulerDialog
from plugin.report_editor import ReportEditor
from ui.config_dialog import ConfigDialog
from PySide6.QtWidgets import QApplication

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
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setStyleSheet(quick_check_style)
        layout = QVBoxLayout(self)
        
        
        # 新增高级功能组
        advanced_buttons = [
            QPushButton("任务编排"),
            QPushButton("报告编辑器"),
            QPushButton("AIlovelymem"),
            QPushButton("设置"),
        ]
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
        advanced_buttons[2].clicked.connect(self.start_AI_assistant)
        advanced_buttons[3].clicked.connect(self.show_config_dialog)
        # 为其他高级功能按钮添加连接
        


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
    def start_AI_assistant(self):
        import subprocess,os
        # 检测一下OfflineLicense文件是否存在
        print("正在启动AI助手")
        subprocess.Popen([r"../Tools/python3/python.exe", r"AItools\gradio_ui.py"])
        
    def show_config_dialog(self):
        """显示配置对话框"""
        dialog = ConfigDialog(self)
        dialog.exec()
