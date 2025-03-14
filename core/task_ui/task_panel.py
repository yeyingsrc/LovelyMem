from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                              QTreeWidget, QTreeWidgetItem, QPushButton, QGroupBox)
from PySide6.QtCore import Qt, Signal, QMimeData, QPoint
from PySide6.QtGui import QDrag, QPixmap, QPainter, QColor


class TaskPanel(QWidget):
    """
    任务面板：显示可用任务并提供拖拽功能
    """
    # 信号
    task_selected = Signal(str, str)  # 参数：area, task_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI组件"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 区域选择下拉框
        area_layout = QHBoxLayout()
        area_label = QLabel("选择区域:")
        self.area_combo = QComboBox()
        self.area_combo.addItems(["MemProcFS", "Volatility 2", "Volatility 3", "快速检查"])
        self.area_combo.currentTextChanged.connect(self.update_available_tasks)
        area_layout.addWidget(area_label)
        area_layout.addWidget(self.area_combo)
        layout.addLayout(area_layout)
        
        # 任务树控件
        self.tasks_group = QGroupBox("可用任务")
        tasks_layout = QVBoxLayout(self.tasks_group)
        
        self.available_tasks = QTreeWidget()
        self.available_tasks.setHeaderLabels(["功能组"])
        self.available_tasks.setDragEnabled(True)
        self.available_tasks.setColumnWidth(0, 150)
        self.available_tasks.itemDoubleClicked.connect(self.on_task_double_clicked)
        
        # 启用拖放
        self.available_tasks.setDragDropMode(QTreeWidget.DragOnly)
        
        tasks_layout.addWidget(self.available_tasks)
        layout.addWidget(self.tasks_group, 1)
        
        # 设置外观
        self.setMinimumWidth(250)
    
    def update_available_tasks(self):
        """更新可用任务列表"""
        try:
            self.available_tasks.clear()
            area = self.area_combo.currentText()
            
            # 获取对应区域的任务
            if area == "MemProcFS":
                tasks = self.get_memprocfs_tasks()
            elif area == "Volatility 2":
                tasks = self.get_vol2_tasks()
            elif area == "Volatility 3":
                tasks = self.get_vol3_tasks()
            elif area == "快速检查":
                tasks = {"其他功能": ["常备知识", "强制重置VOL3缓存", "任务编排"]}
            
            # 添加任务到树控件
            for group_name, task_list in tasks.items():
                group_item = QTreeWidgetItem([group_name])
                for task in task_list:
                    if task:  # 确保任务名不为空
                        task_item = QTreeWidgetItem([task])
                        task_item.setFlags(task_item.flags() | Qt.ItemIsDragEnabled)
                        group_item.addChild(task_item)
                if group_item.childCount() > 0:  # 只添加非空的组
                    self.available_tasks.addTopLevelItem(group_item)
                    group_item.setExpanded(True)
        except Exception as e:
            print(f"Error updating available tasks: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def get_memprocfs_tasks(self):
        """获取MemProcFS区域的任务"""
        try:
            memprocfs_area = self.parent.parent.main_window.memprocfs_area
            tasks = {}
            
            # 遍历所有 CollapsibleButtonGroup
            from ui.memprocfs_area import CollapsibleButtonGroup
            for group in memprocfs_area.findChildren(CollapsibleButtonGroup):
                group_name = group.title
                group_buttons = []
                
                # 遍历组内的所有按钮
                for i in range(group.content_layout.count()):
                    widget = group.content_layout.itemAt(i).widget()
                    if isinstance(widget, QPushButton):
                        group_buttons.append(widget.text())
                
                if group_buttons:  # 只添加非空的组
                    tasks[group_name] = group_buttons
            
            return tasks
        except Exception as e:
            print(f"Error getting MemProcFS tasks: {str(e)}")
            # 返回一些示例任务，以防错误
            return {"内存基础信息": ["文件列表", "进程列表"], "注册表分析": ["注册表树"]}
    
    def get_vol2_tasks(self):
        """获取Volatility 2区域的任务"""
        try:
            vol2_area = self.parent.parent.main_window.vol2_area
            tasks = {}
            
            # 遍历所有 CollapsibleButtonGroup
            from ui.vol2_area import CollapsibleButtonGroup
            for group in vol2_area.findChildren(CollapsibleButtonGroup):
                group_name = group.title
                group_buttons = []
                
                # 遍历组内的所有按钮
                for i in range(group.content_layout.count()):
                    widget = group.content_layout.itemAt(i).widget()
                    if isinstance(widget, QPushButton):
                        group_buttons.append(widget.text())
                
                if group_buttons:  # 只添加非空的组
                    tasks[group_name] = group_buttons
            
            return tasks
        except Exception as e:
            print(f"Error getting Volatility 2 tasks: {str(e)}")
            # 返回一些示例任务，以防错误
            return {"进程分析": ["进程列表", "进程树"], "网络分析": ["网络连接"]}
    
    def get_vol3_tasks(self):
        """获取Volatility 3区域的任务"""
        try:
            vol3_area = self.parent.parent.main_window.vol3_area
            tasks = {}
            
            # 遍历所有 CollapsibleButtonGroup
            from ui.vol3_area import CollapsibleButtonGroup
            for group in vol3_area.findChildren(CollapsibleButtonGroup):
                group_name = group.title
                group_buttons = []
                
                # 遍历组内的所有按钮
                for button in group.buttons:
                    if isinstance(button, QPushButton):
                        group_buttons.append(button.text())
                
                if group_buttons:  # 只添加非空的组
                    tasks[group_name] = group_buttons
            
            return tasks
        except Exception as e:
            print(f"Error getting Volatility 3 tasks: {str(e)}")
            # 返回一些示例任务，以防错误
            return {"Windows进程": ["pslist", "pstree"], "Windows注册表": ["printkey"]}
    
    def on_task_double_clicked(self, item, column):
        """处理任务双击事件"""
        if not item or not item.parent():  # 如果是组标题，不处理
            return
        
        area = self.area_combo.currentText()
        task_name = item.text(0)
        
        # 在场景中心位置创建节点
        if self.parent and hasattr(self.parent, 'flow_scene'):
            scene = self.parent.flow_scene
            view = self.parent.flow_view
            
            # 计算视图中心在场景中的位置
            view_center = view.mapToScene(view.viewport().rect().center())
            
            # 创建任务节点
            scene.create_task_node(view_center, area, task_name)
    
    def startDrag(self, supportedActions):
        """自定义拖拽行为"""
        item = self.available_tasks.currentItem()
        if not item or not item.parent():  # 如果是组标题，不允许拖拽
            return
        
        # 获取任务信息
        area = self.area_combo.currentText()
        task_name = item.text(0)
        
        # 创建MIME数据
        mime_data = QMimeData()
        mime_data.setText(task_name)
        mime_data.setData("application/x-task-area", area.encode())
        mime_data.setData("application/x-task-name", task_name.encode())
        
        # 创建拖拽对象
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        
        # 创建拖拽缩略图
        pixmap = QPixmap(120, 30)
        pixmap.fill(QColor(240, 240, 255))
        painter = QPainter(pixmap)
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, task_name)
        painter.end()
        
        # 设置拖拽图像
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))
        
        # 执行拖拽
        result = drag.exec(Qt.CopyAction | Qt.MoveAction)
