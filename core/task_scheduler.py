from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QInputDialog, QMessageBox, QSplitter,
                              QComboBox, QGroupBox, QMenu, QApplication)
from PySide6.QtCore import Qt, Signal
import json
import os
import sys

# 导入自定义模块
from core.flow_graph.flow_scene import FlowScene
from core.flow_graph.flow_view import FlowView
from core.task_ui.task_panel import TaskPanel
from core.utils.file_io import save_flow, load_flow


class TaskSchedulerDialog(QDialog):
    """
    任务编排对话框 - 主界面类
    实现了流程图形式的任务编排器，支持拖拽和连线
    """
    task_execute = Signal(list)  # 发送任务列表信号
    DEFAULT_FLOW_FILE = 'config/task_flows/default_flow.json'  # 默认配置文件路径

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("任务编排")
        self.resize(1200, 800)  # 扩大窗口尺寸以适应流程图
        self.parent = parent
        
        # 设置窗口标志，不强制置顶
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        
        # 设置UI组件
        self.setup_ui()
        
        # 创建场景和视图
        self.flow_scene = FlowScene(self)
        self.flow_view.setScene(self.flow_scene)
        
        # 加载默认配置
        self.load_default_flow()
        
        # 更新可用任务列表
        self.task_panel.update_available_tasks()

    def setup_ui(self):
        """设置UI布局"""
        main_layout = QVBoxLayout(self)
        
        # 创建分割器，左侧放置任务列表，右侧放置流程图
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧任务面板
        self.task_panel = TaskPanel(self)
        splitter.addWidget(self.task_panel)
        
        # 右侧流程图视图
        self.flow_view = FlowView(self)
        splitter.addWidget(self.flow_view)
        
        # 设置分割器的初始大小
        splitter.setSizes([300, 900])  
        
        # 添加分割器到主布局
        main_layout.addWidget(splitter, 1)
        
        # 底部按钮区域
        bottom_layout = QHBoxLayout()
        
        save_button = QPushButton("保存任务流程")
        save_button.clicked.connect(self.save_task_flow)
        
        load_button = QPushButton("加载任务流程")
        load_button.clicked.connect(self.load_task_flow)
        
        execute_button = QPushButton("执行")
        execute_button.clicked.connect(self.execute_tasks)
        
        bottom_layout.addWidget(save_button)
        bottom_layout.addWidget(load_button)
        bottom_layout.addStretch(1)  # 添加弹性空间
        bottom_layout.addWidget(execute_button)
        
        main_layout.addLayout(bottom_layout)

    def save_task_flow(self):
        """保存当前任务流程"""
        name, ok = QInputDialog.getText(self, "保存任务流程", "请输入任务流程名称:")
        if ok and name:
            try:
                os.makedirs('config/task_flows', exist_ok=True)
                filename = f'config/task_flows/{name}.json'
                save_flow(filename, self.flow_scene)
                QMessageBox.information(self, "成功", "任务流程保存成功！")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"保存任务流程失败：{str(e)}")

    def load_task_flow(self):
        """加载任务流程"""
        flows_dir = 'config/task_flows'
        if not os.path.exists(flows_dir):
            QMessageBox.warning(self, "错误", "没有找到已保存的任务流程！")
            return

        flows = [f[:-5] for f in os.listdir(flows_dir) if f.endswith('.json')]
        if not flows:
            QMessageBox.warning(self, "错误", "没有找到已保存的任务流程！")
            return

        name, ok = QInputDialog.getItem(self, "加载任务流程", 
                                      "选择要加载的任务流程:", flows, 0, False)
        if ok and name:
            try:
                filename = f'config/task_flows/{name}.json'
                load_flow(filename, self.flow_scene)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"加载任务流程失败：{str(e)}")

    def load_default_flow(self):
        """加载默认配置"""
        try:
            if os.path.exists(self.DEFAULT_FLOW_FILE):
                load_flow(self.DEFAULT_FLOW_FILE, self.flow_scene)
            else:
                # 如果默认配置不存在，创建一个空白场景
                self.flow_scene.clear()
        except Exception as e:
            print(f"Error loading default flow: {str(e)}")
            import traceback
            traceback.print_exc()

    def execute_tasks(self):
        """执行当前任务流程"""
        try:
            tasks = self.flow_scene.get_execution_sequence()
            if not tasks:
                QMessageBox.warning(self, "警告", "当前流程图中没有可执行的任务或任务连接不完整！")
                return
            
            # 显示任务列表
            task_list = "\n".join([f"{i+1}. {task['area']} - {task['task']}" for i, task in enumerate(tasks)])
            
            reply = QMessageBox.question(self, "确认", 
                                       f"是否确定要执行以下任务流程？\n\n{task_list}",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                # 发送任务列表信号
                self.task_execute.emit(tasks)
                # 不再隐藏对话框
        except Exception as e:
            QMessageBox.warning(self, "错误", f"执行任务失败：{str(e)}")

    def closeEvent(self, event):
        """关闭前保存默认配置"""
        try:
            os.makedirs(os.path.dirname(self.DEFAULT_FLOW_FILE), exist_ok=True)
            save_flow(self.DEFAULT_FLOW_FILE, self.flow_scene)
        except Exception as e:
            print(f"Error saving default flow: {str(e)}")
        event.accept()


# 测试代码（仅在直接运行此文件时执行）
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = TaskSchedulerDialog()
    dialog.show()
    sys.exit(app.exec())