from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QMenu, QPushButton, QMessageBox, QScrollArea, QLineEdit, QGroupBox, QComboBox
from PySide6.QtCore import Qt
from ui.styles import vol2_style,button_style
from plugin.vol2 import Vol2Plugin

class Vol2Button(QPushButton):
    def __init__(self, text, function=None):
        super().__init__(text)
        if function:
            self.clicked.connect(function)

class CollapsibleButtonGroup(QWidget):
    def __init__(self, title, buttons, favorite_manager):
        super().__init__()
        self.title = title
        self.buttons = buttons
        self.favorite_manager = favorite_manager
        self.is_expanded = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.title_button = Vol2Button(self.title)
        self.title_button.clicked.connect(self.toggle_expand)
        layout.addWidget(self.title_button)

        self.content_widget = QWidget()
        self.content_layout = QGridLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setHorizontalSpacing(5)
        self.content_layout.setVerticalSpacing(5)
        for i, button in enumerate(self.buttons):
            row = i // 5  # 每行5个按钮
            col = i % 5
            self.content_layout.addWidget(button, row, col)
        self.content_widget.setVisible(False)
        layout.addWidget(self.content_widget)

        for button in self.buttons:
            button.setContextMenuPolicy(Qt.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda pos, btn=button: self.show_context_menu(pos, btn))

    def show_context_menu(self, pos, button):
        context_menu = self.favorite_manager.create_context_menu(button, source_area="Vol2")
        context_menu.exec_(button.mapToGlobal(pos))

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)

class Vol2Area(QWidget):
    def __init__(self, favorite_manager, main_window):
        super().__init__()
        self.setStyleSheet(vol2_style)

        self.favorite_manager = favorite_manager
        self.main_window = main_window
        self.vol2_plugin = Vol2Plugin('')

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)

        layout = QVBoxLayout(scroll_content)

        # 添加 Profile 下拉框,支持编辑
        self.profile_group = QGroupBox("Profile")
        profile_layout = QVBoxLayout(self.profile_group)
        
        self.profile_combo = QComboBox()
        self.profile_combo.setStyleSheet(button_style)
        profile_layout.addWidget(self.profile_combo)
        layout.addWidget(self.profile_group)


        # 重新组织功能组
        self.create_function_groups(layout)

        layout.addStretch()

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    def create_function_groups(self, layout):
        # 基本功能组
        basic_functions = [
            ("文件扫描", lambda: self.button_clicked(self.vol2_plugin.vol2_filescan)),
            ("进程列表", lambda: self.button_clicked(self.vol2_plugin.vol2_pslist)),
            ("网络扫描", lambda: self.button_clicked(self.vol2_plugin.vol2_netscan)),
            ("命令行", lambda: self.button_clicked(self.vol2_plugin.vol2_cmdline)),
            ("环境变量", lambda: self.button_clicked(self.vol2_plugin.vol2_envars)),
            ("服务扫描", lambda: self.button_clicked(self.vol2_plugin.vol2_svcscan)),
            ("驱动扫描", lambda: self.button_clicked(self.vol2_plugin.vol2_driverscan)),
            ("注册表键值", lambda: self.button_clicked(self.vol2_plugin.vol2_printkey)),
            ("时间线", lambda: self.button_clicked(self.vol2_plugin.vol2_timeliner)),
            ("剪贴板", lambda: self.button_clicked(self.vol2_plugin.vol2_clipboard)),
            ("编辑框", lambda: self.button_clicked(self.vol2_plugin.vol2_editbox)),
            ("命令扫描", lambda: self.button_clicked(self.vol2_plugin.vol2_cmdscan)),
            ("控制台", lambda: self.button_clicked(self.vol2_plugin.vol2_consoles)),
        ]
        basic_buttons = [self.create_button(text, func) for text, func in basic_functions]
        self.basic_group = CollapsibleButtonGroup("基本功能", basic_buttons, self.favorite_manager)
        layout.addWidget(self.basic_group)

        # 高级功能组
        advanced_functions = [
            ("API钩子检测", lambda: self.button_clicked(self.vol2_plugin.vol2_apihooks)),
            ("系统回调", lambda: self.button_clicked(self.vol2_plugin.vol2_callbacks)),
            ("驱动IRP钩子检测", lambda: self.button_clicked(self.vol2_plugin.vol2_driverirp)),
            ("GDI定时器", lambda: self.button_clicked(self.vol2_plugin.vol2_gditimers)),
            ("进程句柄", lambda: self.button_clicked(self.vol2_plugin.vol2_handles)),
            ("原子表", lambda: self.button_clicked(self.vol2_plugin.vol2_atoms)),
            ("会话信息", lambda: self.button_clicked(self.vol2_plugin.vol2_session)),
            ("窗口扫描", lambda: self.button_clicked(self.vol2_plugin.vol2_wndscan)),
            ("恶意代码检测", lambda: self.button_clicked(self.vol2_plugin.vol2_malfind)),
            ("桌面扫描", lambda: self.button_clicked(self.vol2_plugin.vol2_deskscan)),
            ("原子表扫描", lambda: self.button_clicked(self.vol2_plugin.vol2_atomscan)),
            ("加载模块", lambda: self.button_clicked(self.vol2_plugin.vol2_modules)),
            ("事件钩子", lambda: self.button_clicked(self.vol2_plugin.vol2_eventhooks)),
            ("互斥对象扫描", lambda: self.button_clicked(self.vol2_plugin.vol2_mutantscan)),
            ("进程权限", lambda: self.button_clicked(self.vol2_plugin.vol2_privs)),
            ("隐藏进程检测", lambda: self.button_clicked(self.vol2_plugin.vol2_psxview)),
            ("SSDT表", lambda: self.button_clicked(self.vol2_plugin.vol2_ssdt)),
            ("内核定时器", lambda: self.button_clicked(self.vol2_plugin.vol2_timers)),
            ("已卸载模块", lambda: self.button_clicked(self.vol2_plugin.vol2_unloadedmodules)),
            ("VAD信息", lambda: self.button_clicked(self.vol2_plugin.vol2_vadinfo)),
            ("截图", lambda: self.button_clicked(self.vol2_plugin.vol2_screenshot)),
            ("DLL调用列表", lambda: self.button_clicked(self.vol2_plugin.vol2_dlllist)),
            ("GDI定时器", lambda: self.button_clicked(self.vol2_plugin.vol2_gditimers)),
            ("消息钩子", lambda: self.button_clicked(self.vol2_plugin.vol2_messagehooks)),
            ("用户句柄", lambda: self.button_clicked(self.vol2_plugin.vol2_userhandles)),
        ]
        advanced_buttons = [self.create_button(text, func) for text, func in advanced_functions]
        self.advanced_group = CollapsibleButtonGroup("高级功能", advanced_buttons, self.favorite_manager)
        layout.addWidget(self.advanced_group)

        # 系统信息组
        system_functions = [
            ("镜像信息", lambda: self.button_clicked(self.vol2_plugin.vol2_imageinfo)),
            ("关机时间", lambda: self.button_clicked(self.vol2_plugin.vol2_shutdowntime)),
            ("版本信息", lambda: self.button_clicked(self.vol2_plugin.vol2_verinfo)),
            ("审计策略", lambda: self.button_clicked(self.vol2_plugin.vol2_auditpol)),
            ("应用程序兼容性缓存", lambda: self.button_clicked(self.vol2_plugin.vol2_shimcache)),
        ]
        system_buttons = [self.create_button(text, func) for text, func in system_functions]
        self.system_group = CollapsibleButtonGroup("系统信息", system_buttons, self.favorite_manager)
        layout.addWidget(self.system_group)

        # 用户相关组
        user_functions = [
            ("记录行为", lambda: self.button_clicked(self.vol2_plugin.vol2_userassist)),
            ("文件夹访问记录", lambda: self.button_clicked(self.vol2_plugin.vol2_shellbags)),
            ("窗口结构", lambda: self.button_clicked(self.vol2_plugin.vol2_wintree)),
            ("MFT解析", lambda: self.button_clicked(self.vol2_plugin.vol2_mftparser)),
            ("窗口信息", lambda: self.button_clicked(self.vol2_plugin.vol2_windows)),
            ("哈希转储", lambda: self.button_clicked(self.vol2_plugin.vol2_hashdump)),
            ("LSA转储", lambda: self.button_clicked(self.vol2_plugin.vol2_lsadump)),
            ("IE历史记录", lambda: self.button_clicked(self.vol2_plugin.vol2_iehistory)),
            ("Chrome历史", lambda: self.button_clicked(self.vol2_plugin.vol2_chromehistory)),
            ("Firefox历史", lambda: self.button_clicked(self.vol2_plugin.vol2_firefoxhistory)),
            ("TrueCrypt摘要", lambda: self.button_clicked(self.vol2_plugin.vol2_truecryptsummary)),
        ]
        user_buttons = [self.create_button(text, func) for text, func in user_functions]
        self.user_group = CollapsibleButtonGroup("用户信息", user_buttons, self.favorite_manager)
        layout.addWidget(self.user_group)

        # 文件导出组
        export_functions = [
            ("导出注册表", lambda: self.button_clicked(self.vol2_plugin.vol2_dumpregistry)),
            ("导出压缩包", lambda: self.button_clicked(self.vol2_plugin.vol2_dump_all_zip)),
            ("导出文本文件", lambda: self.button_clicked(self.vol2_plugin.vol2_dump_all_txt)),
            ("导出图片文件", lambda: self.button_clicked(self.vol2_plugin.vol2_dump_all_images)),
        ]
        export_buttons = [self.create_button(text, func) for text, func in export_functions]
        
        # 添加自定义导出功能
        custom_export_layout = QHBoxLayout()
        self.custom_export_input = QLineEdit()
        self.custom_export_input.setPlaceholderText("输入文件扩展名(如 pdf)")
        custom_export_button = QPushButton("导出指定格式")
        custom_export_button.clicked.connect(self.custom_export)
        custom_export_layout.addWidget(self.custom_export_input)
        custom_export_layout.addWidget(custom_export_button)
        
        export_widget = QWidget()
        export_layout = QVBoxLayout(export_widget)
        for button in export_buttons:
            export_layout.addWidget(button)
        export_layout.addLayout(custom_export_layout)
        
        self.export_group = CollapsibleButtonGroup("文件导出(不可靠)", [export_widget], self.favorite_manager)
        layout.addWidget(self.export_group)

        # 扩展功能组
        extend_functions = [
            ("Mimikatz", lambda: self.button_clicked(self.vol2_plugin.vol2_mimikatz)),
            ("BitLocker", lambda: self.button_clicked(self.vol2_plugin.vol2_bitlocker)),
            ("信任记录", lambda: self.button_clicked(self.vol2_plugin.vol2_trustrecords)),
            ("卸载信息", lambda: self.button_clicked(self.vol2_plugin.vol2_uninstallinfo)),
        ]
        extend_buttons = [self.create_button(text, func) for text, func in extend_functions]
        self.extend_group = CollapsibleButtonGroup("扩展功能", extend_buttons, self.favorite_manager)
        layout.addWidget(self.extend_group)

    def update_mem_path(self):
        new_mem_path = self.main_window.get_current_mem_path()
        if new_mem_path != self.vol2_plugin.mem_path:
            self.vol2_plugin = Vol2Plugin(new_mem_path)
        return new_mem_path

    def create_button(self, text, func):
        button = Vol2Button(text)
        button.clicked.connect(lambda: self.button_clicked(func))
        return button

    def button_clicked(self, func):
        self.update_mem_path()
        if not self.vol2_plugin.mem_path:
            QMessageBox.warning(self, "警告", "请先载入内存镜像文件！")
            return
        if callable(func):
            func()
        else:
            print(f"无效的函数: {func}")

    def custom_export(self):
        extension = self.custom_export_input.text().strip().lower()
        if not extension:
            QMessageBox.warning(self, "警告", "请输入文件扩展名！")
            return
        self.update_mem_path()
        if not self.vol2_plugin.mem_path:
            QMessageBox.warning(self, "警告", "请先载入内存镜像文件！")
            return
        self.vol2_plugin.dump_files_by_extension([extension])

    def update_profile(self, profile, profilelist):
        self.profile = profile
        self.profile_combo.clear()
        #创建output/image_info.txt 内容imagepath,profile[0]
        with open('output/image_info.txt', 'w', encoding='utf-8') as f:
            f.write(f"{self.vol2_plugin.mem_path},{profile}")
        self.profile_combo.addItems(profilelist)
        self.profile_combo.setCurrentText(profile)
        self.profile_combo.currentTextChanged.connect(self.on_profile_changed)

    def on_profile_changed(self, new_profile):
        self.profile = new_profile
        self.vol2_plugin.profile = new_profile

        
        # 更新 image_info.txt 文件
        with open('output/image_info.txt', 'w', encoding='utf-8') as f:
            f.write(f"{self.vol2_plugin.mem_path},{new_profile}")

        print(f"Profile 已更新为: {new_profile}")


    def update_button_styles(self):
        for group in self.findChildren(CollapsibleButtonGroup):
            group.title_button.setStyleSheet(button_style)
            for button in group.buttons:
                if isinstance(button, QPushButton):
                    button.setStyleSheet(button_style)
        self.update()  # 强制更新界面