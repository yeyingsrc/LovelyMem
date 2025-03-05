from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QMenu, QPushButton, QMessageBox, QScrollArea, QLineEdit, QGroupBox, QComboBox
from PySide6.QtCore import Qt
from ui.styles import vol2_style, button_style
from plugin.vol2 import Vol2Plugin

class Vol2Button(QPushButton):
    def __init__(self, text, function=None):
        super().__init__(text)
        if function:
            self.clicked.connect(function)
        # 调小字体
        font = self.font()
        font.setPointSize(font.pointSize() - 4)
        self.setFont(font)

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

        self.title_button = Vol2Button(self.title)
        self.title_button.clicked.connect(self.toggle_expand)
        layout.addWidget(self.title_button)

        self.content_widget = QWidget()
        self.content_layout = QGridLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setHorizontalSpacing(5)
        self.content_layout.setVerticalSpacing(5)
        for i, button in enumerate(self.buttons):
            row = i // 3  # 每行3个按钮
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
            context_menu = self.main_window.preset_manager.create_context_menu(button, source_area="Vol2")
            context_menu.exec_(button.mapToGlobal(pos))

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)

class Vol2Area(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.setStyleSheet(vol2_style)

        self.main_window = main_window
        self.vol2_plugin = Vol2Plugin('')

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)

        layout = QVBoxLayout(scroll_content)

        # 添加 Profile 下拉框
        self.profile_group = QGroupBox("Profile")
        profile_layout = QVBoxLayout(self.profile_group)
        self.profile_combo = QComboBox()
        self.profile_combo.setStyleSheet(button_style)
        profile_layout.addWidget(self.profile_combo)
        layout.addWidget(self.profile_group)

        # 添加自定义命令区域
        self.create_custom_command_area(layout)

        # 重新组织功能组
        self.create_function_groups(layout)

        layout.addStretch()

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    def create_function_groups(self, layout):
        # 基本功能组（保持不变）
        basic_functions = [
            ("文件扫描(filescan)", lambda: self.button_clicked(self.vol2_plugin.vol2_filescan)),
            ("进程列表(pslist)", lambda: self.button_clicked(self.vol2_plugin.vol2_pslist)),
            ("网络扫描(netscan)", lambda: self.button_clicked(self.vol2_plugin.vol2_netscan)),
            ("命令行(cmdline)", lambda: self.button_clicked(self.vol2_plugin.vol2_cmdline)),
            ("环境变量(envars)", lambda: self.button_clicked(self.vol2_plugin.vol2_envars)),
            ("服务扫描(svcscan)", lambda: self.button_clicked(self.vol2_plugin.vol2_svcscan)),
            ("驱动扫描(driverscan)", lambda: self.button_clicked(self.vol2_plugin.vol2_driverscan)),
            ("注册表键值(printkey)", lambda: self.button_clicked(self.vol2_plugin.vol2_printkey)),
            ("时间线(timeliner)", lambda: self.button_clicked(self.vol2_plugin.vol2_timeliner)),
            ("剪贴板(clipboard)", lambda: self.button_clicked(self.vol2_plugin.vol2_clipboard)),
            ("编辑框(editbox)", lambda: self.button_clicked(self.vol2_plugin.vol2_editbox)),
            ("命令扫描(cmdscan)", lambda: self.button_clicked(self.vol2_plugin.vol2_cmdscan)),
            ("控制台(consoles)", lambda: self.button_clicked(self.vol2_plugin.vol2_consoles)),
        ]
        basic_buttons = [self.create_button(text, func) for text, func in basic_functions]
        self.basic_group = CollapsibleButtonGroup("基本功能", basic_buttons, self.main_window)
        layout.addWidget(self.basic_group)

        # 进程分析组
        process_functions = [
            ("进程列表(pslist)", lambda: self.button_clicked(self.vol2_plugin.vol2_pslist)),
            ("隐藏进程检测(psxview)", lambda: self.button_clicked(self.vol2_plugin.vol2_psxview)),
            ("进程句柄(handles)", lambda: self.button_clicked(self.vol2_plugin.vol2_handles)),
            ("进程权限(privs)", lambda: self.button_clicked(self.vol2_plugin.vol2_privs)),
            ("命令行(cmdline)", lambda: self.button_clicked(self.vol2_plugin.vol2_cmdline)),
            ("命令扫描(cmdscan)", lambda: self.button_clicked(self.vol2_plugin.vol2_cmdscan)),
            ("控制台(consoles)", lambda: self.button_clicked(self.vol2_plugin.vol2_consoles)),
            ("环境变量(envars)", lambda: self.button_clicked(self.vol2_plugin.vol2_envars)),
            ("DLL列表(dlllist)", lambda: self.button_clicked(self.vol2_plugin.vol2_dlllist)),
        ]
        process_buttons = [self.create_button(text, func) for text, func in process_functions]
        self.process_group = CollapsibleButtonGroup("进程分析", process_buttons, self.main_window)
        layout.addWidget(self.process_group)

        # 内存和模块分析组
        memory_functions = [
            ("VAD信息(vadinfo)", lambda: self.button_clicked(self.vol2_plugin.vol2_vadinfo)),
            ("加载模块(modules)", lambda: self.button_clicked(self.vol2_plugin.vol2_modules)),
            ("已卸载模块(unloadedmodules)", lambda: self.button_clicked(self.vol2_plugin.vol2_unloadedmodules)),
            ("SSDT表(ssdt)", lambda: self.button_clicked(self.vol2_plugin.vol2_ssdt)),
            ("内核定时器(timers)", lambda: self.button_clicked(self.vol2_plugin.vol2_timers)),
            ("GDI定时器(gditimers)", lambda: self.button_clicked(self.vol2_plugin.vol2_gditimers)),
            ("驱动扫描(driverscan)", lambda: self.button_clicked(self.vol2_plugin.vol2_driverscan)),
            ("驱动IRP钩子检测(driverirp)", lambda: self.button_clicked(self.vol2_plugin.vol2_driverirp)),
        ]
        memory_buttons = [self.create_button(text, func) for text, func in memory_functions]
        self.memory_group = CollapsibleButtonGroup("内存和模块分析", memory_buttons, self.main_window)
        layout.addWidget(self.memory_group)

        # 文件系统和注册表分析组
        file_registry_functions = [
            ("文件扫描(filescan)", lambda: self.button_clicked(self.vol2_plugin.vol2_filescan)),
            ("MFT解析(mftparser)", lambda: self.button_clicked(self.vol2_plugin.vol2_mftparser)),
            ("文件夹访问记录(shellbags)", lambda: self.button_clicked(self.vol2_plugin.vol2_shellbags)),
            ("注册表键值(printkey)", lambda: self.button_clicked(self.vol2_plugin.vol2_printkey)),
            ("导出注册表(dumpregistry)", lambda: self.button_clicked(self.vol2_plugin.vol2_dumpregistry)),
            ("应用程序兼容性缓存(shimcache)", lambda: self.button_clicked(self.vol2_plugin.vol2_shimcache)),
            ("审计策略(auditpol)", lambda: self.button_clicked(self.vol2_plugin.vol2_auditpol)),
        ]
        file_registry_buttons = [self.create_button(text, func) for text, func in file_registry_functions]
        self.file_registry_group = CollapsibleButtonGroup("文件和注册表分析", file_registry_buttons, self.main_window)
        layout.addWidget(self.file_registry_group)

        # 网络分析组
        network_functions = [
            ("网络扫描(netscan)", lambda: self.button_clicked(self.vol2_plugin.vol2_netscan)),


        ]
        network_buttons = [self.create_button(text, func) for text, func in network_functions]
        self.network_group = CollapsibleButtonGroup("网络分析", network_buttons, self.main_window)
        layout.addWidget(self.network_group)

        # 用户活动组
        user_activity_functions = [
            ("用户助手(userassist)", lambda: self.button_clicked(self.vol2_plugin.vol2_userassist)),
            ("IE历史记录(iehistory)", lambda: self.button_clicked(self.vol2_plugin.vol2_iehistory)),
            ("Chrome历史(chromehistory)", lambda: self.button_clicked(self.vol2_plugin.vol2_chromehistory)),
            ("Firefox历史(firefoxhistory)", lambda: self.button_clicked(self.vol2_plugin.vol2_firefoxhistory)),
            ("TrueCrypt摘要(truecryptsummary)", lambda: self.button_clicked(self.vol2_plugin.vol2_truecryptsummary)),
            ("窗口信息(windows)", lambda: self.button_clicked(self.vol2_plugin.vol2_windows)),
            ("窗口结构(wintree)", lambda: self.button_clicked(self.vol2_plugin.vol2_wintree)),
            ("桌面扫描(deskscan)", lambda: self.button_clicked(self.vol2_plugin.vol2_deskscan)),
            ("会话信息(session)", lambda: self.button_clicked(self.vol2_plugin.vol2_session)),
            ("剪贴板(clipboard)", lambda: self.button_clicked(self.vol2_plugin.vol2_clipboard)),
            ("编辑框(editbox)", lambda: self.button_clicked(self.vol2_plugin.vol2_editbox)),
        ]
        user_activity_buttons = [self.create_button(text, func) for text, func in user_activity_functions]
        self.user_activity_group = CollapsibleButtonGroup("用户活动", user_activity_buttons, self.main_window)
        layout.addWidget(self.user_activity_group)

        # 系统信息组
        system_info_functions = [
            ("镜像信息(imageinfo)", lambda: self.button_clicked(self.vol2_plugin.vol2_imageinfo)),
            ("版本信息(verinfo)", lambda: self.button_clicked(self.vol2_plugin.vol2_verinfo)),
            ("关机时间(shutdowntime)", lambda: self.button_clicked(self.vol2_plugin.vol2_shutdowntime)),
            ("原子表(atoms)", lambda: self.button_clicked(self.vol2_plugin.vol2_atoms)),
            ("原子表扫描(atomscan)", lambda: self.button_clicked(self.vol2_plugin.vol2_atomscan)),
            ("系统回调(callbacks)", lambda: self.button_clicked(self.vol2_plugin.vol2_callbacks)),  
        ]
        system_info_buttons = [self.create_button(text, func) for text, func in system_info_functions]
        self.system_info_group = CollapsibleButtonGroup("系统信息", system_info_buttons, self.main_window)
        layout.addWidget(self.system_info_group)

        # 恶意代码和钩子检测组
        malware_functions = [
            ("恶意代码检测(malfind)", lambda: self.button_clicked(self.vol2_plugin.vol2_malfind)),
            ("API钩子检测(apihooks)", lambda: self.button_clicked(self.vol2_plugin.vol2_apihooks)),
            ("互斥对象扫描(mutantscan)", lambda: self.button_clicked(self.vol2_plugin.vol2_mutantscan)),
            ("事件钩子(eventhooks)", lambda: self.button_clicked(self.vol2_plugin.vol2_eventhooks)),
            ("消息钩子(messagehooks)", lambda: self.button_clicked(self.vol2_plugin.vol2_messagehooks)),
            ("符号链接扫描(symlinkscan)", lambda: self.button_clicked(self.vol2_plugin.vol2_symlinkscan)),
        ]
        malware_buttons = [self.create_button(text, func) for text, func in malware_functions]
        self.malware_group = CollapsibleButtonGroup("恶意代码和钩子检测", malware_buttons, self.main_window)
        layout.addWidget(self.malware_group)

        # 文件导出组
        export_functions = [
            ("导出注册表(dumpregistry)", lambda: self.button_clicked(self.vol2_plugin.vol2_dumpregistry)),
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

        self.export_group = CollapsibleButtonGroup("文件导出", [export_widget], self.main_window)
        layout.addWidget(self.export_group)

        # 扩展功能组
        extended_functions = [
            ("Mimikatz(mimikatz)", lambda: self.button_clicked(self.vol2_plugin.vol2_mimikatz)),
            ("BitLocker(bitlocker)", lambda: self.button_clicked(self.vol2_plugin.vol2_bitlocker)),
            ("信任记录(trustrecords)", lambda: self.button_clicked(self.vol2_plugin.vol2_trustrecords)),
            ("卸载信息(uninstallinfo)", lambda: self.button_clicked(self.vol2_plugin.vol2_uninstallinfo)),
            ("截图(screenshot)", lambda: self.button_clicked(self.vol2_plugin.vol2_screenshot)),
        ]
        extended_buttons = [self.create_button(text, func) for text, func in extended_functions]
        self.extended_group = CollapsibleButtonGroup("扩展功能", extended_buttons, self.main_window)
        layout.addWidget(self.extended_group)

    def update_mem_path(self):
        new_mem_path = self.main_window.get_current_mem_path()
        if new_mem_path != self.vol2_plugin.mem_path:
            self.vol2_plugin = Vol2Plugin(new_mem_path)
        return new_mem_path

    def create_button(self, text, func):
        # 检查文本是否包含括号
        if '(' in text and ')' in text:
            # 分离按钮文本和tooltip内容
            button_text, tooltip = text.split('(', 1)
            tooltip = tooltip.rstrip(')')
            button = Vol2Button(button_text.strip())
            button.setToolTip(tooltip)
        else:
            # 如果没有括号，整个文本作为按钮文本，不设置tooltip
            button = Vol2Button(text.strip())
        
        button.clicked.connect(func)
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
        # 创建 output/image_info.txt 内容 imagepath,profile[0]
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
        self.update()  # 强制更新界���

    # 在 create_function_groups 方法之前添加自定义命令区域
    def create_custom_command_area(self, layout):
        # 创建自定义命令组
        custom_command_group = QGroupBox("自定义命令")
        custom_command_layout = QHBoxLayout(custom_command_group)
        
        # 创建命令输入框
        self.custom_command_input = QLineEdit()
        self.custom_command_input.setPlaceholderText("输入Vol2命令 (例如: pslist)")
        
        # 创建执行按钮
        execute_button = QPushButton("执行")
        #execute_button.setStyleSheet(button_style)
        execute_button.clicked.connect(self.execute_custom_command)
        
        # 添加到布局
        custom_command_layout.addWidget(self.custom_command_input)
        custom_command_layout.addWidget(execute_button)
        
        layout.addWidget(custom_command_group)

    # 添加执行自定义命令的方法
    def execute_custom_command(self):
        command = self.custom_command_input.text().strip()
        if not command:
            QMessageBox.warning(self, "警告", "请输入命令！")
            return
        
        self.update_mem_path()
        if not self.vol2_plugin.mem_path:
            QMessageBox.warning(self, "警告", "请先载入内存镜像文件！")
            return
        
        # 构造并执行命令
        try:
            # 构造完整的命令
            cmd = [
                self.vol2_plugin.python27,
                self.vol2_plugin.volatility2,
                f'--plugin={self.vol2_plugin.volatility2_plugin}',
                '-f',
                self.vol2_plugin.mem_path,
                f'--profile={self.vol2_plugin.profile}',
                command,
                '--output=text',  # 使用text格式输出以便查看完整结果
                f'--output-file=output/output_vol2_custom_{command.replace(" ", "_")}.txt'
            ]
            
            # 使用 run_plugin_with_custom_command 执行命令
            self.vol2_plugin.run_plugin_with_custom_command(
                cmd, 
                f'自定义命令({command})'
            )
        except Exception as e:
            QMessageBox.warning(self, "错误", f"执行命令时出错：{str(e)}")
