from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QPushButton, QMessageBox, QLineEdit, QHBoxLayout, QScrollArea, QGroupBox, QCheckBox, QMenu, QLabel, QDialog, QDialogButtonBox, QFormLayout
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

        self.title_button = Vol3Button(self.title)
        self.title_button.clicked.connect(self.toggle_expand)
        layout.addWidget(self.title_button)

        self.content_widget = QWidget()
        self.content_layout = QGridLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setHorizontalSpacing(2)
        self.content_layout.setVerticalSpacing(2)
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
        context_menu = QMenu(self)
        
        # 添加"添加到预设"菜单项 - 直接添加到菜单，而不是子菜单
        if hasattr(self.main_window, 'preset_manager'):
            # 获取预设菜单的动作，而不是子菜单
            preset_actions = self.main_window.preset_manager.create_preset_actions(button, source_area="Vol3")
            for action in preset_actions:
                context_menu.addAction(action)
        
        # 添加"参数执行"菜单项
        param_action = context_menu.addAction("参数执行")
        param_action.triggered.connect(lambda: self.execute_with_params(button))
        
        context_menu.exec(button.mapToGlobal(pos))

    def execute_with_params(self, button):
        # 获取按钮对应的功能名称
        button_text = button.text()
        
        # 创建参数输入对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(f"为 {button_text} 输入参数")
        dialog.resize(400, 150)
        
        layout = QFormLayout(dialog)
        
        # 创建参数输入框
        param_input = QLineEdit()
        param_input.setPlaceholderText("输入参数 (例如: --pid=1234 或 --dump)")
        layout.addRow("参数:", param_input)
        
        # 创建按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # 显示对话框并获取结果
        if dialog.exec() == QDialog.Accepted:
            params = param_input.text().strip()
            if params:
                # 查找Vol3Area实例
                vol3_area = self.find_vol3_area()
                if vol3_area:
                    # 执行带参数的命令
                    vol3_area.execute_with_params(button, params)
                else:
                    QMessageBox.warning(self, "错误", "无法找到Vol3Area实例")
    
    def find_vol3_area(self):
        # 向上查找Vol3Area实例
        parent = self.parent()
        while parent:
            if isinstance(parent, Vol3Area):
                return parent
            parent = parent.parent()
        return None

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)

    def update_styles(self):
        self.title_button.update_style()
        for button in self.buttons:
            if isinstance(button, Vol3Button):
                button.update_style()



class Vol3Area(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.vol3_plugin = None
        self.button_groups = []  # 存储所有按钮组
        self.all_buttons = []    # 存储所有按钮
        
        # 连接任务完成信号
        if self.vol3_plugin:
            self.vol3_plugin.task_completed_signal.connect(self.on_task_completed)
        
        self.setup_ui()
        self.update_styles()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Create settings group box for offline mode
        settings_group = QGroupBox("设置")
        settings_layout = QHBoxLayout()
        
        # 添加离线模式复选框
        self.offline_checkbox = QCheckBox("离线模式")
        self.offline_checkbox.setToolTip("启用离线模式 (--offline)")
        self.offline_checkbox.setChecked(False)  # Set checked by default
        settings_layout.addWidget(self.offline_checkbox)
        
        # 添加搜索框
        search_label = QLabel("搜索按钮:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词搜索按钮...")
        self.search_input.textChanged.connect(self.filter_buttons)
        settings_layout.addWidget(search_label)
        settings_layout.addWidget(self.search_input)
        
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
                ("空心进程检测(hollowprocesses)", "vol3_hollowprocesses"),
                ("进程虚假化检测(processghosting)", "vol3_processghosting"),
                ("隐藏进程检测(psxview)", "vol3_psxview"),
                ("线程信息(threads)", "vol3_threads"),
                ("可疑线程检测(suspicious_threads)", "vol3_suspicious_threads"),
                ("挂起线程检测(suspended_threads)", "vol3_suspended_threads"),
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
                ("KPCR信息(kpcrs)", "vol3_kpcrs"),
                ("定时器信息(timers)", "vol3_timers"),
                ("导入地址表(IAT)", "vol3_iat"),
                ("桌面扫描(deskscan)", "vol3_deskscan"),
                ("桌面信息(desktops)", "vol3_desktops"),
                ("直接系统调用(direct_system_calls)", "vol3_direct_system_calls"),
                ("间接系统调用(indirect_system_calls)", "vol3_indirect_system_calls"),
                ("VAD正则扫描(vadregexscan)", "vol3_vadregexscan"),
                ("Windows信息(windows)", "vol3_windows"),
                ("窗口站(windowstations)", "vol3_windowstations"),
            ],
            "文件和网络": [
                ("文件对象扫描(filescan)", "vol3_filescan"), 
                ("互斥体对象扫描(mutantscan)", "vol3_mutantscan"), 
                ("网络连接扫描(netscan)", "vol3_netscan"),
                ("网络连接状态(netstat)", "vol3_netstat"),
                ("Shim缓存内存分析(shimcachemem)", "vol3_shimcachemem"),
            ],
            "注册表": [
                ("注册表证书信息(certificates)", "vol3_registry.certificates"), 
                ("注册表Hive列表(hivelist)", "vol3_registry.hivelist"),
                ("注册表Hive扫描(hivescan)", "vol3_registry.hivescan"), 
                ("注册表键值查看(printkey)", "vol3_registry.printkey"),
                ("用户操作记录(userassist)", "vol3_registry.userassist"),
                ("注册表单元格获取(registry.getcellroutine)", "vol3_registry.getcellroutine"),
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
                ("服务差异分析(svcdiff)", "vol3_svcdiff"),
                ("服务列表(svclist)", "vol3_svclist"),
            ],
        }

        for group_name, functions in function_groups.items():
            buttons = [Vol3Button(text, partial(self.button_clicked, func)) for text, func in functions]
            group = CollapsibleButtonGroup(group_name, buttons, self.main_window)
            content_layout.addWidget(group)
            self.button_groups.append(group)
            self.all_buttons.extend([(button, group, text) for button, (text, _) in zip(buttons, functions)])

        content_layout.addStretch(1)
        main_layout.addWidget(scroll_area)

    def filter_buttons(self, search_text):
        """根据搜索文本过滤按钮"""
        if not search_text:
            # 如果搜索框为空，恢复所有按钮组的可见性
            for group in self.button_groups:
                group.setVisible(True)
                group.content_widget.setVisible(group.is_expanded)
            # 恢复所有按钮的可见性和样式
            for button, _, _ in self.all_buttons:
                button.setVisible(True)
                button.setStyleSheet(ui.styles.button_style)
            return
            
        search_text = search_text.lower()
        search_terms = [term.strip() for term in search_text.split() if term.strip()]
        
        # 隐藏所有按钮组
        for group in self.button_groups:
            group.setVisible(False)
            
        # 显示包含匹配按钮的组，并展开这些组
        for button, group, button_text in self.all_buttons:
            # 检查按钮文本是否匹配所有搜索词（AND逻辑）
            button_text_lower = button_text.lower()
            is_match = all(term in button_text_lower for term in search_terms)
            
            if is_match:
                # 显示匹配的按钮和它所在的组
                group.setVisible(True)
                group.content_widget.setVisible(True)  # 展开包含匹配按钮的组
                button.setVisible(True)
                # 高亮匹配的按钮
                button.setStyleSheet(ui.styles.button_style + "background-color: rgba(0, 150, 255, 0.3);")
            else:
                # 隐藏不匹配的按钮
                button.setVisible(False)
                # 恢复未匹配按钮的样式
                button.setStyleSheet(ui.styles.button_style)

    def update_mem_path(self):
        new_mem_path = self.main_window.get_current_mem_path()
        if new_mem_path:
            self.vol3_plugin = self.main_window.vol3_plugin
            # 重新连接任务完成信号
            if self.vol3_plugin and hasattr(self.vol3_plugin, 'task_completed_signal'):
                self.vol3_plugin.task_completed_signal.connect(self.on_task_completed)
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
                # 添加任务到任务管理器
                task_name = f"Volatility 3 - {func_name.replace('vol3_', '')}"
                if hasattr(self.main_window, 'task_manager'):
                    self.main_window.task_manager.add_task(task_name)
                
                # 保存任务名称，以便在任务完成时移除
                if not hasattr(self, 'active_tasks'):
                    self.active_tasks = {}
                self.active_tasks[func_name.replace('vol3_', '')] = task_name
                
                offline_mode = self.offline_checkbox.isChecked()
                func(offline=offline_mode)
            else:
                QMessageBox.warning(self, "警告", f"Vol3Plugin 中没有 {func_name} 方法！")
        else:
            QMessageBox.warning(self, "警告", "Vol3Plugin 未正确初始化！")
    
    def on_task_completed(self, plugin_name):
        """任务完成时的回调函数"""
        if hasattr(self, 'active_tasks') and plugin_name in self.active_tasks:
            task_name = self.active_tasks[plugin_name]
            if hasattr(self.main_window, 'task_manager'):
                self.main_window.task_manager.remove_task(task_name)
            # 从活动任务列表中移除
            del self.active_tasks[plugin_name]
    
    # 添加新方法：带参数执行命令
    def execute_with_params(self, button, params):
        new_mem_path = self.update_mem_path()
        if not new_mem_path:
            QMessageBox.warning(self, "警告", "请先载入内存镜像文件！")
            return
        
        # 获取按钮文本和对应的命令
        button_text = button.text()
        plugin_name = button.toolTip() if button.toolTip() else button_text
        
        # 解析参数
        param_list = params.split()
        
        # 构造并执行命令
        try:
            # 确定输出类型
            output_type = 'quick' if plugin_name in self.vol3_plugin.txt_plugins else 'csv'
            
            # 构造基本命令
            cmd = [
                f'"{self.vol3_plugin.pythonpath}"',
                f'"{self.vol3_plugin.volatility3}"',
                '-f',
                f'"{new_mem_path}"'
            ]
            
            # 添加离线模式参数（如果启用）
            if self.offline_checkbox.isChecked():
                cmd.append('--offline')
            
            # 添加输出类型
            cmd.extend([
                '-r',
                output_type
            ])
            
            # 添加插件名称（确保以windows.开头）
            plugin_cmd = plugin_name
            if not plugin_cmd.startswith("windows."):
                plugin_cmd = f"windows.{plugin_cmd}"
            
            # 添加用户输入的参数
            full_cmd = f"{plugin_cmd} {' '.join(param_list)}"
            cmd.append(full_cmd)
            str_params = '_'.join(param_list)
            # 输出文件名
            clean_plugin_name = plugin_name.replace("windows.", "")
            output_file = f'output/output_vol3_{clean_plugin_name}_{str_params}.{"txt" if clean_plugin_name in self.vol3_plugin.txt_plugins else "csv"}'
            
            print(f"[*] 正在执行命令：{' '.join(cmd)}")
            
            # 创建工作线程并执行
            worker = WorkerThread(cmd)
            
            def on_task_complete(success, msg, output):
                if success:
                    print(f"[+] 命令执行成功：{full_cmd}")
                    self.vol3_plugin.on_task_completed(success, msg, output, output_file, f'{clean_plugin_name}(带参数)')
                else:
                    print(f"[×] 命令执行失败：{full_cmd}")
                    print(f"错误信息：{msg}")
                    QMessageBox.warning(self, "执行失败", f"命令执行失败：{msg}")
            
            worker.task_completed.connect(on_task_complete)
            worker.start()
            self.vol3_plugin.workers.append(worker)
            
        except Exception as e:
            error_msg = f"执行命令时出错：{str(e)}"
            print(f"[×] {error_msg}")
            QMessageBox.warning(self, "错误", error_msg)

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
