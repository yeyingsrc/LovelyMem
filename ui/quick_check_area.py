from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, QHBoxLayout, QMessageBox
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

class CollapsibleButtonGroup(QWidget):
    def __init__(self, title, buttons, favorite_manager):
        super().__init__()
        self.title = title
        self.buttons = buttons
        self.favorite_manager = favorite_manager
        self.is_expanded = True
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.title_button = QPushButton(self.title)
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

        for button in self.buttons:
            button.setContextMenuPolicy(Qt.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda pos, btn=button: self.show_context_menu(pos, btn))

    def show_context_menu(self, pos, button):
        context_menu = self.favorite_manager.create_context_menu(button, source_area="QuickCheck")
        context_menu.exec_(button.mapToGlobal(pos))

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)

class QuickCheckArea(QWidget):
    def __init__(self, favorite_manager, main_window):
        super().__init__()
        self.favorite_manager = favorite_manager
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
        self.advanced_group = CollapsibleButtonGroup("高级功能", advanced_buttons, self.favorite_manager)
        layout.addWidget(self.advanced_group)
        # 其他功能组
        
        other_buttons = [
            QPushButton("常备知识"),
            QPushButton("强制重置VOL3缓存"),
        ]

        other_buttons[0].clicked.connect(self.show_knowledge_base)
        other_buttons[1].clicked.connect(self.update_vol3_cache)
        self.other_group = CollapsibleButtonGroup("其他功能", other_buttons, self.favorite_manager)
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

    def avatar_clicked(self, event):
        self.click_count += 1
        if self.click_count == random.randint(30, 100):
            QMessageBox.information(self, "恭喜", "恭喜获得离线授权5折券！")
            self.click_count = 0

    def update_vol3_cache(self):
        reply = QMessageBox.question(self, "提示", "一般来说如果没有更换路径位置不需要点击这里\n强制重置VOL3缓存会删除本地已经有的vol3缓存\n强制构建默认镜像索引，是否继续？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            update_identifier_cache()

    # 添加这个新方法
    def show_knowledge_base(self):
        dialog = KnowledgeBaseDialog(self)
        dialog.exec_()

    def show_task_scheduler(self):
        dialog = TaskSchedulerDialog(self)
        dialog.task_execute.connect(self.execute_task_flow)
        dialog.exec_()

    def execute_task_flow(self, stages):
        dialog = TaskSchedulerDialog(self)  # 保持对话框的引用
        
        for stage in stages:
            stage_name = stage["stage"]
            tasks = stage["tasks"]
            
            # 显示当前执行的阶段
            self.main_window.cmd_output.append(f"\n=== 执行{stage_name} ===\n")
            
            for task in tasks:
                try:
                    area, function = task.split(" - ", 1)
                    self.main_window.cmd_output.append(f"正在执行: {function}")
                    
                    if area == "MemProcFS":
                        self.main_window.execute_memprocfs_function(function)
                    elif area == "Volatility 2":
                        self.main_window.execute_vol2_function(function)
                    elif area == "Volatility 3":
                        self.main_window.execute_vol3_function(function)
                    elif area == "快速检查":
                        self.main_window.execute_quick_check_function(function)
                    
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"执行任务 '{task}' 时发生错误：{str(e)}")
                
            # 每个阶段执行完后暂停，等待用户确认
            reply = QMessageBox.question(self, f"{stage_name}完成", 
                                       f"{stage_name}已执行完成，是否继续执行下一阶段？",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                dialog.show()  # 重新显示任务编排窗口
                return  # 仅退出执行，不关闭窗口

    def show_report_editor(self):
        self.report_editor = ReportEditor()
        self.report_editor.setWindowTitle("报告编辑器")
        self.report_editor.resize(1000, 600)
        self.report_editor.show()
    def start_AI_assistant(self):
        import subprocess,os
        # 检测一下OfflineLicense文件是否存在
        print("正在启动AI助手")
        subprocess.Popen(["../Tools/python3/python.exe", "AItools\gradio_ui.py"])
        
    def show_config_dialog(self):
        """显示配置对话框"""
        dialog = ConfigDialog(self)
        dialog.exec_()
