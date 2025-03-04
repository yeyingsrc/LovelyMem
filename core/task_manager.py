import json
import os
from PySide6.QtCore import QObject, Signal, Slot


class TaskManager(QObject):
    """
    任务管理器：负责任务的执行和管理
    """
    # 信号
    task_started = Signal(str, str)  # 参数：stage_name, task_name
    task_completed = Signal(str, str)  # 参数：stage_name, task_name
    all_tasks_completed = Signal()
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.current_tasks = []
    
    def execute_tasks(self, tasks):
        """
        执行一系列任务
        
        Args:
            tasks: 任务列表，格式为 [{"area": area_name, "task": task_name}, ...]
        """
        self.current_tasks = tasks
        
        # 按顺序执行每个任务
        for i, task_data in enumerate(tasks):
            area = task_data["area"]
            task_name = task_data["task"]
            
            # 构造阶段名称
            stage_name = f"任务 {i+1}/{len(tasks)}"
            
            # 构造完整任务名称
            task_full_name = f"{area} - {task_name}"
            
            # 通知任务开始
            self.task_started.emit(stage_name, task_full_name)
            
            # 执行任务
            self._execute_task(area, task_name)
            
            # 通知任务完成
            self.task_completed.emit(stage_name, task_full_name)
        
        # 通知所有任务完成
        self.all_tasks_completed.emit()
    
    def _execute_task(self, area, task_name):
        """
        执行单个任务
        
        Args:
            area: 任务所属区域（MemProcFS、Volatility 2等）
            task_name: 任务名称
        """
        if not self.main_window:
            print(f"无法执行任务：{area} - {task_name}（未连接到主窗口）")
            return
        
        try:
            # 根据区域执行对应的任务
            if area == "MemProcFS":
                self._execute_memprocfs_task(task_name)
            elif area == "Volatility 2":
                self._execute_vol2_task(task_name)
            elif area == "Volatility 3":
                self._execute_vol3_task(task_name)
            elif area == "快速检查":
                self._execute_quick_check_task(task_name)
            else:
                print(f"未知区域：{area}")
        except Exception as e:
            print(f"执行任务时出错：{area} - {task_name}")
            print(f"错误详情：{str(e)}")
            import traceback
            traceback.print_exc()
    
    def _execute_memprocfs_task(self, task_name):
        """执行MemProcFS区域的任务"""
        memprocfs_area = self.main_window.memprocfs_area
        
        # 遍历所有按钮组
        from ui.memprocfs_area import CollapsibleButtonGroup
        for group in memprocfs_area.findChildren(CollapsibleButtonGroup):
            for i in range(group.content_layout.count()):
                widget = group.content_layout.itemAt(i).widget()
                if hasattr(widget, 'text') and widget.text() == task_name:
                    # 找到匹配的按钮，触发点击事件
                    widget.click()
                    return
    
    def _execute_vol2_task(self, task_name):
        """执行Volatility 2区域的任务"""
        vol2_area = self.main_window.vol2_area
        
        # 遍历所有按钮组
        from ui.vol2_area import CollapsibleButtonGroup
        for group in vol2_area.findChildren(CollapsibleButtonGroup):
            for i in range(group.content_layout.count()):
                widget = group.content_layout.itemAt(i).widget()
                if hasattr(widget, 'text') and widget.text() == task_name:
                    # 找到匹配的按钮，触发点击事件
                    widget.click()
                    return
    
    def _execute_vol3_task(self, task_name):
        """执行Volatility 3区域的任务"""
        vol3_area = self.main_window.vol3_area
        
        # 遍历所有按钮组
        from ui.vol3_area import CollapsibleButtonGroup
        for group in vol3_area.findChildren(CollapsibleButtonGroup):
            for button in group.buttons:
                if hasattr(button, 'text') and button.text() == task_name:
                    # 找到匹配的按钮，触发点击事件
                    button.click()
                    return
    
    def _execute_quick_check_task(self, task_name):
        """执行快速检查区域的任务"""
        # 根据任务名称执行对应的操作
        if task_name == "常备知识":
            if hasattr(self.main_window, "show_knowledge"):
                self.main_window.show_knowledge()
        elif task_name == "强制重置VOL3缓存":
            if hasattr(self.main_window, "reset_vol3_cache"):
                self.main_window.reset_vol3_cache()
        elif task_name == "任务编排":
            # 避免递归调用
            pass
