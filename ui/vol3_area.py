from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QPushButton, QMessageBox, QLineEdit, QHBoxLayout, QScrollArea, QGroupBox, QCheckBox
from PySide6.QtCore import Qt
from ui.styles import memprocfs_style, get_current_theme, apply_color_scheme, is_dark_mode
import ui.styles
from plugin.vol3 import Vol3Plugin, WorkerThread
from functools import partial

class Vol3Button(QPushButton):
    def __init__(self, text, function=None):
        # 检查文本是否包含括号
        if '(' in text and ')' in text:
            # 分离按钮文本和tooltip内容
            button_text, tooltip = text.split('(', 1)
            tooltip = tooltip.rstrip(')')
            super().__init__(button_text.strip())
            self.setToolTip(tooltip)
        else:
            # 如果没有括号，整个文本作为按钮文本，不设置tooltip
            super().__init__(text.strip())
        
        if function:
            self.clicked.connect(function)
        self.update_style()

    def update_style(self):
        self.setStyleSheet(ui.styles.button_style)



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

        self.title_button = Vol3Button(self.title)
        self.title_button.clicked.connect(self.toggle_expand)
        layout.addWidget(self.title_button)

        self.content_widget = QWidget()
        self.content_layout = QGridLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setHorizontalSpacing(2)
        self.content_layout.setVerticalSpacing(2)
        for i, button in enumerate(self.buttons):
            row = i // 3
            col = i % 3
            self.content_layout.addWidget(button, row, col)
        self.content_widget.setVisible(False)
        layout.addWidget(self.content_widget)

        for button in self.buttons:
            button.setContextMenuPolicy(Qt.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda pos, btn=button: self.show_context_menu(pos, btn))

    def show_context_menu(self, pos, button):
        context_menu = self.favorite_manager.create_context_menu(button, source_area="Vol3")
        context_menu.exec_(button.mapToGlobal(pos))

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)

    def update_styles(self):
        self.title_button.update_style()
        for button in self.buttons:
            if isinstance(button, Vol3Button):
                button.update_style()



class Vol3Area(QWidget):
    def __init__(self, favorite_manager, main_window):
        super().__init__()
        self.favorite_manager = favorite_manager
        self.main_window = main_window
        self.vol3_plugin = None
        self.setup_ui()
        self.update_styles()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Create settings group box for offline mode
        settings_group = QGroupBox("设置")
        settings_layout = QHBoxLayout()
        self.offline_checkbox = QCheckBox("离线模式")
        self.offline_checkbox.setToolTip("启用离线模式 (--offline)")
        self.offline_checkbox.setChecked(True)  # Set checked by default
        settings_layout.addWidget(self.offline_checkbox)
        settings_layout.addStretch()
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)

        content_layout = QVBoxLayout(scroll_content)
        content_layout.setSpacing(2)
        content_layout.setAlignment(Qt.AlignTop)

        # Add custom command area
        self.create_custom_command_area(content_layout)

        function_groups = {
            "进程信息": [
                ("进程列表(pslist)", "vol3_pslist"), 
                ("进程扫描(psscan)", "vol3_psscan"), 
                ("进程树(pstree)", "vol3_pstree"),
                ("DLL列表(dlllist)", "vol3_dlllist"), 
                ("进程句柄(handles)", "vol3_handles"), 
                ("进程SID(getsids)", "vol3_getsids"),
                ("命令行参数(cmdline)", "vol3_cmdline"), 
                ("进程加载模块(ldrmodules)", "vol3_ldrmodules"), 
                ("进程权限(privileges)", "vol3_privileges"),
                
            ],
            "系统信息": [
                ("系统基本信息(info)", "vol3_info"),
                ("内核模块列表(modules)", "vol3_modules"), 
                ("内核模块扫描(modscan)", "vol3_modscan"), 
                ("驱动程序扫描(driverscan)", "vol3_driverscan"),
                ("驱动程序IRP(driverirp)", "vol3_driverirp"), 
                ("驱动程序模块(drivermodule)", "vol3_drivermodule"), 
                ("系统服务描述符表(ssdt)", "vol3_ssdt"),
                ("系统回调函数(callbacks)", "vol3_callbacks"), 
                ("大页内存池(bigpools)", "vol3_bigpools"), 
                ("设备对象树(devicetree)", "vol3_devicetree"),
                ("导入地址表(iat)", "vol3_iat"), 
                ("作业对象链接(joblinks)", "vol3_joblinks"),
                ("主引导记录扫描(mbrscan)", "vol3_mbrscan"), 
                ("内存池扫描器(poolscanner)", "vol3_poolscanner"), 
                ("会话信息(sessions)", "vol3_sessions"),
                ("系统统计信息(statistics)", "vol3_statistics"), 
                ("符号链接扫描(symlinkscan)", "vol3_symlinkscan"), 
                ("线程扫描(thrdscan)", "vol3_thrdscan"),
                ("虚拟地址描述符(vadinfo)", "vol3_vadinfo"), 
                ("VAD树遍历(vadwalk)", "vol3_vadwalk"), 
                ("Windows版本信息(verinfo)", "vol3_verinfo"),
                ("虚拟内存映射表(virtmap)", "vol3_virtmap"),
                ("已卸载模块(unloadedmodules)", "vol3_unloadedmodules"),
            ],
            "文件和网络": [
                ("文件对象扫描(filescan)", "vol3_filescan"), 
                ("互斥体对象扫描(mutantscan)", "vol3_mutantscan"), 
                ("网络连接扫描(netscan)", "vol3_netscan"),
                ("网络连接状态(netstat)", "vol3_netstat"),
            ],
            "注册表": [
                ("注册表证书信息(certificates)", "vol3_registry.certificates"), 
                ("注册表Hive列表(hivelist)", "vol3_registry.hivelist"),
                ("注册表Hive扫描(hivescan)", "vol3_registry.hivescan"), 
                ("注册表键值查看(printkey)", "vol3_registry.printkey"),
                ("用户操作记录(userassist)", "vol3_registry.userassist"),
            ],
            "恶意代码检测": [
                ("内存注入检测(malfind)", "vol3_malfind"), 
                ("域控密钥检查(skeleton_key_check)", "vol3_skeleton_key_check"),
                ("TrueCrypt加密信息(truecrypt)", "vol3_truecrypt"),
            ],
            "其他功能": [
                ("环境变量信息(envars)", "vol3_envars"), 
                ("系统崩溃信息(crashinfo)", "vol3_crashinfo"), 
                ("缓存密码转储(cachedump)", "vol3_cachedump"),
                ("密码哈希转储(hashdump)", "vol3_hashdump"), 
                ("LSA密钥转储(lsadump)", "vol3_lsadump"), 
                ("服务SID查询(getservicesids)", "vol3_getservicesids"),
            ],
            
            "新版本新增功能": [
                ("已卸载模块(unloadedmodules)", "vol3_unloadedmodules"),
                ("空心进程检测(hollowprocesses)", "vol3_hollowprocesses"),
                ("KPCR信息(kpcrs)", "vol3_kpcrs"),
                ("进程虚假化检测(processghosting)", "vol3_processghosting"),
                ("隐藏进程检测(psxview)", "vol3_psxview"),
                ("注册表单元格获取(registry.getcellroutine)", "vol3_registry.getcellroutine"),
                ("Shim缓存内存分析(shimcachemem)", "vol3_shimcachemem"),
                ("可疑线程检测(suspicious_threads)", "vol3_suspicious_threads"),
                ("服务差异分析(svcdiff)", "vol3_svcdiff"),
                ("服务列表(svclist)", "vol3_svclist"),
                ("线程信息(threads)", "vol3_threads"),
                ("定时器信息(timers)", "vol3_timers"),
                ("导入地址表(IAT)", "vol3_iat"),
            ],
        }

        for group_name, functions in function_groups.items():
            buttons = [Vol3Button(text, partial(self.button_clicked, func)) for text, func in functions]
            group = CollapsibleButtonGroup(group_name, buttons, self.favorite_manager)
            content_layout.addWidget(group)

        content_layout.addStretch(1)
        main_layout.addWidget(scroll_area)

    def update_mem_path(self):
        new_mem_path = self.main_window.get_current_mem_path()
        if new_mem_path:
            self.vol3_plugin = self.main_window.vol3_plugin
            return new_mem_path
        return None

    def button_clicked(self, func_name, checked=False):
        new_mem_path = self.update_mem_path()
        if not new_mem_path:
            QMessageBox.warning(self, "警告", "请先载入内存镜像文件！")
            return
        if self.vol3_plugin:
            if isinstance(func_name, str):
                pass
            elif callable(func_name):
                func_name = func_name.__name__
            else:
                QMessageBox.warning(self, "警告", f"无效的函数名: {func_name}")
                return

            if not func_name.startswith("vol3_"):
                func_name = f"vol3_{func_name}"

            func = getattr(self.vol3_plugin, func_name, None)
            if func:
                offline_mode = self.offline_checkbox.isChecked()
                func(offline=offline_mode)
            else:
                QMessageBox.warning(self, "警告", f"Vol3Plugin 中没有 {func_name} 方法！")
        else:
            QMessageBox.warning(self, "警告", "Vol3Plugin 未正确初始化！")

    def update_styles(self):
       
        self.setStyleSheet(ui.styles.memprocfs_style)
        for group in self.findChildren(CollapsibleButtonGroup):
            group.update_styles()
        
        scroll_area = self.findChild(QScrollArea)
        if scroll_area:
            scroll_area.setStyleSheet(ui.styles.memprocfs_style)
            scroll_content = scroll_area.widget()
            if scroll_content:
                scroll_content.setStyleSheet(ui.styles.memprocfs_style)
        
        self.update()

    def update_button_styles(self):
        self.update_styles()

    def create_custom_command_area(self, layout):
        # Create custom command group
        custom_command_group = QGroupBox("自定义命令")
        custom_command_layout = QHBoxLayout(custom_command_group)
        
        # Create command input box
        self.custom_command_input = QLineEdit()
        self.custom_command_input.setPlaceholderText("输入Vol3命令 (例如: windows.pslist)")
        
        # Create execute button
        execute_button = QPushButton("执行")
        execute_button.clicked.connect(self.execute_custom_command)
        
        # Add to layout
        custom_command_layout.addWidget(self.custom_command_input)
        custom_command_layout.addWidget(execute_button)
        
        layout.addWidget(custom_command_group)

    def execute_custom_command(self):
        command = self.custom_command_input.text().strip()
        if not command:
            QMessageBox.warning(self, "警告", "请输入命令！")
            return
        
        new_mem_path = self.update_mem_path()
        if not new_mem_path:
            QMessageBox.warning(self, "警告", "请先载入内存镜像文件！")
            return
        
        # Construct and execute command
        try:
            # Extract plugin name from command for output file naming
            plugin_name = command.replace("windows.", "").replace(" ", "_")
            
            # Determine output type based on plugin
            output_type = 'quick' if plugin_name in self.vol3_plugin.txt_plugins else 'csv'
            
            # Construct command
            cmd = [
                f'"{self.vol3_plugin.pythonpath}"',
                f'"{self.vol3_plugin.volatility3}"',
                '-f',
                f'"{new_mem_path}"'
            ]
            
            # Add offline flag if checkbox is checked
            if self.offline_checkbox.isChecked():
                cmd.append('--offline')
            
            cmd.extend([
                '-r',
                output_type,
                command
            ])
            
            print(f"[*] 正在执行命令：{' '.join(cmd)}")  # Add command execution feedback
            
            # Create worker thread and execute
            worker = WorkerThread(cmd)
            output_file = f'output/output_vol3_custom_{plugin_name}.{"txt" if plugin_name in self.vol3_plugin.txt_plugins else "csv"}'
            
            def on_task_complete(success, msg, output):
                if success:
                    print(f"[+] 命令执行成功：{command}")
                    self.vol3_plugin.on_task_completed(success, msg, output, output_file, f'custom_{plugin_name}')
                else:
                    print(f"[×] 命令执行失败：{command}")
                    print(f"错误信息：{msg}")
                    QMessageBox.warning(self, "执行失败", f"命令执行失败：{msg}")
            
            worker.task_completed.connect(on_task_complete)
            worker.start()
            self.vol3_plugin.workers.append(worker)
            
        except Exception as e:
            error_msg = f"执行命令时出错：{str(e)}"
            print(f"[×] {error_msg}")
            QMessageBox.warning(self, "错误", error_msg)
