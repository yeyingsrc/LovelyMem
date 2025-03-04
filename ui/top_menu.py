from PySide6.QtWidgets import QMenuBar, QMenu
from PySide6.QtGui import QAction

class TopMenu(QMenuBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 创建"文件"菜单
        file_menu = QMenu("文件", self)
        self.addMenu(file_menu)
        
        # 创建"加载镜像"动作
        load_image_action = QAction("加载镜像", self)
        file_menu.addAction(load_image_action)
        
        # 创建"卸载镜像"动作
        unload_image_action = QAction("卸载镜像", self)
        file_menu.addAction(unload_image_action)
        
        # 连接动作到槽函数(这些函数需要在主窗口中实现)
        load_image_action.triggered.connect(parent.load_image)
        unload_image_action.triggered.connect(parent.unload_image)