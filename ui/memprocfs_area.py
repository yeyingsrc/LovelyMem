from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QGroupBox, QScrollArea
from PySide6.QtCore import Qt
from ui.styles import memprocfs_style, button_style, right_panel_style
from plugin.memprocfs import memprocfsplugin
from lovelyform import show_csv_viewer

class MemProcFSButton(QPushButton):
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
        self.is_expanded = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.title_button = MemProcFSButton(self.title)
        self.title_button.clicked.connect(self.toggle_expand)
        layout.addWidget(self.title_button)

        self.content_widget = QWidget()
        self.content_layout = QGridLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setHorizontalSpacing(5)
        self.content_layout.setVerticalSpacing(5)
        for i, button in enumerate(self.buttons):
            row = i // 3  # 每行5个按钮
            col = i % 3
            self.content_layout.addWidget(button, row, col)
        self.content_widget.setVisible(False)
        layout.addWidget(self.content_widget)
        
        # 添加右键菜单功能
        for button in self.buttons:
            button.setContextMenuPolicy(Qt.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda pos, btn=button: self.show_context_menu(pos, btn))

    def show_context_menu(self, pos, button):
        if hasattr(self.main_window, 'preset_manager'):
            context_menu = self.main_window.preset_manager.create_context_menu(button, source_area="MemProcFS")
            context_menu.exec(button.mapToGlobal(pos))

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)

class MemProcFSArea(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.setStyleSheet(memprocfs_style)
        self.main_window = main_window
        self.memprocfs_plugin = memprocfsplugin(self)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)

        layout = QVBoxLayout(scroll_content)

        self.create_function_groups(layout)

        layout.addStretch()

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    def create_function_groups(self, layout):
        basic_functions = [
            ("系统信息", self.memprocfs_plugin.systeminfo),
            ("进程信息", self.memprocfs_plugin.loadproc),
            ("网络信息", self.memprocfs_plugin.load_netstat),
            ("任务列表", self.memprocfs_plugin.loadtasks),
            ("驱动程序", self.memprocfs_plugin.loaddrivers),
            ("句柄信息", self.memprocfs_plugin.load_handles),
            ("服务列表", self.memprocfs_plugin.loadservices),
            ("所有文件", self.memprocfs_plugin.loadallfiles),
            ("Yara扫描", self.memprocfs_plugin.yara_scan),
            ("Yara详情", self.memprocfs_plugin.yara_detail),
            ("恶意软件检测", self.memprocfs_plugin.loadfindevil),
            ("导出全部Eventlog", self.memprocfs_plugin.copy_alleventlog2output),
            ("导出全部注册表", self.memprocfs_plugin.copy_all_registry2output),
            ("导出全部证书", self.memprocfs_plugin.copy_all_certificates2output),
            ("获取产品id", self.memprocfs_plugin.get_product_id),
            ("获取DTB", self.memprocfs_plugin.get_dtb),
            ("driver_irp", self.memprocfs_plugin.convert_driver_to_csv),
            ("bigpools", self.memprocfs_plugin.memprocfs_bigpools),
            ("allpools", self.memprocfs_plugin.memprocfs_allpools),
        ]
        basic_buttons = [self.create_button(text, func) for text, func in basic_functions]
        self.basic_group = CollapsibleButtonGroup("基本功能", basic_buttons, self.main_window)
        layout.addWidget(self.basic_group)

        advanced_functions = [
            ("网络时间线", self.memprocfs_plugin.loadnetstat_timeline),
            ("NTFS文件时间线", self.memprocfs_plugin.loadntfs_timeline),
            ("进程时间线", self.memprocfs_plugin.loadproc_timeline),
            ("Web时间线", self.memprocfs_plugin.loadweb_timeline),
            ("任务时间线", self.memprocfs_plugin.loadtasks_timeline),
            ("注册表时间线", self.memprocfs_plugin.loadtimeline_registry),
            ("Prefetch时间线", self.memprocfs_plugin.timeline_prefetch),
            ("所有时间线", self.memprocfs_plugin.alltimeline),
        ]
        advanced_buttons = [self.create_button(text, func) for text, func in advanced_functions]
        self.advanced_group = CollapsibleButtonGroup("时间线功能", advanced_buttons, self.main_window)
        layout.addWidget(self.advanced_group)

        # lovelymem_functions = [
        #     ("开机自启检测", self.memprocfs_plugin.lovelymem_checkRun),
        #     ("默认浏览器检测", self.memprocfs_plugin.lovelymem_defaultbrowser),
        #     ("IFEO劫持检测", self.memprocfs_plugin.lovelymem_ifeodebug),
        # ]
        # lovelymem_buttons = [self.create_button(text, func) for text, func in lovelymem_functions]
        # self.lovelymem_group = CollapsibleButtonGroup("快速检测", lovelymem_buttons, self.main_window)
        # layout.addWidget(self.lovelymem_group)

    def create_button(self, text, func):
        button = MemProcFSButton(text)
        
        def wrapped_func():
            # 添加任务到任务管理器
            task_name = f"MemProcFS - {text}"
            if hasattr(self.main_window, 'task_manager'):
                self.main_window.task_manager.add_task(task_name)
            
            try:
                func()
            finally:
                # 任务完成后从任务管理器中移除
                if hasattr(self.main_window, 'task_manager'):
                    self.main_window.task_manager.remove_task(task_name)
        
        button.clicked.connect(wrapped_func)
        return button

    def update_button_styles(self):
        for group in self.findChildren(CollapsibleButtonGroup):
            group.title_button.setStyleSheet(button_style)
            for button in group.buttons:
                if isinstance(button, QPushButton):
                    button.setStyleSheet(button_style)
        
        for groupbox in self.findChildren(QGroupBox):
            groupbox.setStyleSheet(right_panel_style)
        
        self.update()  # 强制更新界面