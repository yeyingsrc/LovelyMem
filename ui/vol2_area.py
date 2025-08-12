from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QMenu, QPushButton, QMessageBox, QScrollArea, QLineEdit, QGroupBox, QComboBox, QLabel, QDialog, QDialogButtonBox, QFormLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtCore import QRegularExpression
from ui.styles import vol2_style, button_style
import ui.styles
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
        # 确保在初始化时应用当前样式
        self.update_styles()

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
        context_menu = QMenu(self)
        
        # 添加"添加到预设"菜单项 - 修改为直接添加到菜单，而不是子菜单
        if hasattr(self.main_window, 'preset_manager'):
            # 获取预设菜单的动作，而不是子菜单
            preset_actions = self.main_window.preset_manager.create_preset_actions(button, source_area="Vol2")
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
        param_input.setPlaceholderText("输入单个参数 (例如: -p1234 或 -v)")
        # 添加输入验证：只允许输入一个单词（不包含空格）
        single_word_regex = QRegularExpression(r"^[^\s]*$")
        single_word_validator = QRegularExpressionValidator(single_word_regex)
        param_input.setValidator(single_word_validator)
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
                # 查找Vol2Area实例
                vol2_area = self.find_vol2_area()
                if vol2_area:
                    # 执行带参数的命令
                    vol2_area.execute_with_params(button, params)
                else:
                    QMessageBox.warning(self, "错误", "无法找到Vol2Area实例")
    
    def find_vol2_area(self):
        # 向上查找Vol2Area实例
        parent = self.parent()
        while parent:
            if isinstance(parent, Vol2Area):
                return parent
            parent = parent.parent()
        return None

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)
    
    def update_styles(self):
        self.title_button.update_style()
        for button in self.buttons:
            if isinstance(button, Vol2Button):
                button.update_style()

class Vol2Area(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.setStyleSheet(vol2_style)

        self.main_window = main_window
        self.vol2_plugin = Vol2Plugin('')
        self.button_groups = []  # 存储所有按钮组
        self.all_buttons = []    # 存储所有按钮
        self.active_tasks = {}   # 存储活跃任务
        
        # 初始化时调用一次样式更新
        self.current_button_style = button_style
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)

        layout = QVBoxLayout(scroll_content)

        # 添加 Profile 下拉框和搜索框
        self.profile_group = QGroupBox("设置")
        profile_layout = QVBoxLayout(self.profile_group)
        
        # Profile 下拉框
        profile_label_layout = QHBoxLayout()
        profile_label = QLabel("Profile:")
        self.profile_combo = QComboBox()
        self.profile_combo.setStyleSheet(ui.styles.button_style)
        self.profile_combo.setMinimumWidth(250)  # 增加下拉框的最小宽度，使其显示更完整
        profile_label_layout.addWidget(profile_label)
        profile_label_layout.addWidget(self.profile_combo)
        profile_label_layout.addStretch()
        profile_layout.addLayout(profile_label_layout)
        
        # 添加搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索按钮:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词搜索按钮...")
        self.search_input.textChanged.connect(self.filter_buttons)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addStretch()
        profile_layout.addLayout(search_layout)
        
        layout.addWidget(self.profile_group)

        # 添加自定义命令区域
        self.create_custom_command_area(layout)

        # 重新组织功能组
        self.create_function_groups(layout)

        layout.addStretch()

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
        
        # 初始化完成后更新所有样式
        self.update_styles()
        
        # 连接profile获取完成信号
        if hasattr(self.vol2_plugin, 'profile_obtained'):
            self.vol2_plugin.profile_obtained.connect(self.on_profile_obtained)

    def filter_buttons(self, search_text):
        """根据搜索文本过滤按钮"""
        if not search_text:
            # 如果搜索框为空，恢复所有按钮组的可见性
            for group in self.button_groups:
                group.setVisible(True)
                group.content_widget.setVisible(group.is_expanded)
            # 恢复所有按钮的可见性和样式
            for button, group, button_text in self.all_buttons:
                button.setVisible(True)
                button.setStyleSheet(ui.styles.button_style)
            # 恢复所有按钮的样式
            self.update_button_styles()
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
        
        # 对所有可见组应用当前主题样式
        self.update_button_styles()

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
            ("交互式Shell(volshell)", lambda: self.button_clicked(self.vol2_plugin.vol2_volshell)),
        ]
        basic_buttons = [self.create_button(text, func) for text, func in basic_functions]
        self.basic_group = CollapsibleButtonGroup("基本功能", basic_buttons, self.main_window)
        layout.addWidget(self.basic_group)
        self.button_groups.append(self.basic_group)
        self.all_buttons.extend([(button, self.basic_group, text) for button, (text, _) in zip(basic_buttons, basic_functions)])

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
        self.button_groups.append(self.process_group)
        self.all_buttons.extend([(button, self.process_group, text) for button, (text, _) in zip(process_buttons, process_functions)])

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
            ("bigpools(bigpools)", lambda: self.button_clicked(self.vol2_plugin.vol2_bigpools)),
        ]
        memory_buttons = [self.create_button(text, func) for text, func in memory_functions]
        self.memory_group = CollapsibleButtonGroup("内存和模块分析", memory_buttons, self.main_window)
        layout.addWidget(self.memory_group)
        self.button_groups.append(self.memory_group)
        self.all_buttons.extend([(button, self.memory_group, text) for button, (text, _) in zip(memory_buttons, memory_functions)])

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
        self.button_groups.append(self.file_registry_group)
        self.all_buttons.extend([(button, self.file_registry_group, text) for button, (text, _) in zip(file_registry_buttons, file_registry_functions)])

        # 网络分析组
        network_functions = [
            ("网络扫描(netscan)", lambda: self.button_clicked(self.vol2_plugin.vol2_netscan)),
        ]
        network_buttons = [self.create_button(text, func) for text, func in network_functions]
        self.network_group = CollapsibleButtonGroup("网络分析", network_buttons, self.main_window)
        layout.addWidget(self.network_group)
        self.button_groups.append(self.network_group)
        self.all_buttons.extend([(button, self.network_group, text) for button, (text, _) in zip(network_buttons, network_functions)])

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
        self.button_groups.append(self.user_activity_group)
        self.all_buttons.extend([(button, self.user_activity_group, text) for button, (text, _) in zip(user_activity_buttons, user_activity_functions)])

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
        self.button_groups.append(self.system_info_group)
        self.all_buttons.extend([(button, self.system_info_group, text) for button, (text, _) in zip(system_info_buttons, system_info_functions)])

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
        self.button_groups.append(self.malware_group)
        self.all_buttons.extend([(button, self.malware_group, text) for button, (text, _) in zip(malware_buttons, malware_functions)])

        # # 文件导出组
        # export_functions = [
        #     ("导出注册表(dumpregistry)", lambda: self.button_clicked(self.vol2_plugin.vol2_dumpregistry)),
        #     ("导出压缩包", lambda: self.button_clicked(self.vol2_plugin.vol2_dump_all_zip)),
        #     ("导出文本文件", lambda: self.button_clicked(self.vol2_plugin.vol2_dump_all_txt)),
        #     ("导出图片文件", lambda: self.button_clicked(self.vol2_plugin.vol2_dump_all_images)),
        # ]
        # export_buttons = [self.create_button(text, func) for text, func in export_functions]

        # 添加自定义导出功能
        custom_export_layout = QHBoxLayout()
        self.custom_export_input = QLineEdit()
        self.custom_export_input.setPlaceholderText("输入单个文件扩展名(如 pdf)")
        # 添加输入验证：只允许输入一个单词（不包含空格）
        single_word_regex = QRegularExpression(r"^[^\s]*$")
        single_word_validator = QRegularExpressionValidator(single_word_regex)
        self.custom_export_input.setValidator(single_word_validator)
        custom_export_button = Vol2Button("导出指定格式")
        custom_export_button.clicked.connect(self.custom_export)
        custom_export_layout.addWidget(self.custom_export_input)
        custom_export_layout.addWidget(custom_export_button)

        export_widget = QWidget()
        export_layout = QVBoxLayout(export_widget)
        # for button in export_buttons:
        #     export_layout.addWidget(button)
        # export_layout.addLayout(custom_export_layout)

        self.export_group = CollapsibleButtonGroup("文件导出", [export_widget], self.main_window)
        layout.addWidget(self.export_group)
        self.button_groups.append(self.export_group)
        # # 由于这个组的结构特殊，我们需要单独处理
        # for button, (text, _) in zip(export_buttons, export_functions):
        #     self.all_buttons.append((button, self.export_group, text))
        # # 添加自定义导出按钮
        self.all_buttons.append((custom_export_button, self.export_group, "导出指定格式"))

        # 扩展功能组
        extended_functions = [
            ("Mimikatz(mimikatz)", lambda: self.button_clicked(self.vol2_plugin.vol2_mimikatz)),
            ("BitLocker(bitlocker)", lambda: self.button_clicked(self.vol2_plugin.vol2_bitlocker)),
            ("信任记录(trustrecords)", lambda: self.button_clicked(self.vol2_plugin.vol2_trustrecords)),
            ("卸载信息(uninstallinfo)", lambda: self.button_clicked(self.vol2_plugin.vol2_uninstallinfo)),
            ("截图(screenshot)", lambda: self.button_clicked(self.vol2_plugin.vol2_screenshot)),
            ("getprocbyaclin(getprocbyaclin)", lambda: self.button_clicked(self.vol2_plugin.vol2_getprocbyaclin)),
        ]
        extended_buttons = [self.create_button(text, func) for text, func in extended_functions]
        self.extended_group = CollapsibleButtonGroup("扩展功能", extended_buttons, self.main_window)
        layout.addWidget(self.extended_group)
        self.button_groups.append(self.extended_group)
        self.all_buttons.extend([(button, self.extended_group, text) for button, (text, _) in zip(extended_buttons, extended_functions)])

    def update_mem_path(self):
        new_mem_path = self.main_window.get_current_mem_path()
        if new_mem_path != self.vol2_plugin.mem_path:
            self.vol2_plugin = Vol2Plugin(new_mem_path)
            # 重新连接任务完成信号
            if hasattr(self.vol2_plugin, 'task_completed_signal'):
                self.vol2_plugin.task_completed_signal.connect(self.on_task_completed)
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
        # 确保按钮应用当前主题样式
        button.update_style()
        return button

    def button_clicked(self, func):
        self.update_mem_path()
        if not self.vol2_plugin.mem_path:
            QMessageBox.warning(self, "警告", "请先载入内存镜像文件！")
            return
        if callable(func):
            # 获取任务名称（通过函数名推断）
            task_name = "Volatility 2 任务"
            if hasattr(func, '__name__'):
                func_name = func.__name__
                if func_name.startswith('vol2_'):
                    # 移除前缀并格式化任务名称
                    task_name = f"Volatility 2 - {func_name[5:]}"
            
            # 添加任务到任务管理器
            if hasattr(self.main_window, 'task_manager'):
                self.main_window.task_manager.add_task(task_name)
            
            # 存储活跃任务以便后续移除
            if not hasattr(self, 'active_tasks'):
                self.active_tasks = {}
            self.active_tasks[task_name] = True
            
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
        
        # 当profile框有值时，移除获取Profile任务
        task_name = "Volatility 2 - 获取内存镜像Profile"
        if profile and hasattr(self.main_window, 'task_manager'):
            self.main_window.task_manager.remove_task(task_name)
            # 从活跃任务列表中移除
            if hasattr(self, 'active_tasks') and task_name in self.active_tasks:
                del self.active_tasks[task_name]

    def on_profile_changed(self, new_profile):
        self.profile = new_profile
        self.vol2_plugin.profile = new_profile

        # 更新 image_info.txt 文件
        with open('output/image_info.txt', 'w', encoding='utf-8') as f:
            f.write(f"{self.vol2_plugin.mem_path},{new_profile}")

        print(f"Profile 已更新为: {new_profile}")

    def update_button_styles(self):
        """向后兼容的方法，调用update_styles"""
        self.update_styles()
        
    def update_styles(self):
        """更新所有按钮和组的样式"""
        # 更新Profile下拉框
        self.profile_combo.setStyleSheet(ui.styles.button_style)
        
        # 更新所有按钮组的样式
        for group in self.button_groups:
            if isinstance(group, CollapsibleButtonGroup):
                group.update_styles()
        
        # 更新自定义命令区域的按钮样式
        if hasattr(self, 'execute_button'):
            self.execute_button.setStyleSheet(ui.styles.button_style)
        
        # 更新导出区域的自定义导出按钮
        if hasattr(self, 'custom_export_input') and hasattr(self, 'export_group'):
            for widget in self.export_group.buttons:
                if isinstance(widget, QWidget):
                    for child in widget.findChildren(QPushButton):
                        if isinstance(child, Vol2Button):
                            child.update_style()
                        else:
                            child.setStyleSheet(ui.styles.button_style)
            
        self.update()  # 强制更新界面

    # 在 create_function_groups 方法之前添加自定义命令区域
    def create_custom_command_area(self, layout):
        # 创建自定义命令组
        custom_command_group = QGroupBox("自定义命令")
        custom_command_layout = QHBoxLayout(custom_command_group)
        
        # 创建命令输入框
        self.custom_command_input = QLineEdit()
        self.custom_command_input.setPlaceholderText("输入单个Vol2命令 (例如: pslist)")
        # 添加输入验证：只允许输入一个单词（不包含空格）
        single_word_regex = QRegularExpression(r"^[^\s]*$")
        single_word_validator = QRegularExpressionValidator(single_word_regex)
        self.custom_command_input.setValidator(single_word_validator)

        # 创建执行按钮
        self.execute_button = QPushButton("执行")
        self.execute_button.setStyleSheet(ui.styles.button_style)
        self.execute_button.clicked.connect(self.execute_custom_command)
        
        # 添加到布局
        custom_command_layout.addWidget(self.custom_command_input)
        custom_command_layout.addWidget(self.execute_button)
        
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
 
    # 添加新方法：带参数执行命令
    def execute_with_params(self, button, params):
        self.update_mem_path()
        if not self.vol2_plugin.mem_path:
            QMessageBox.warning(self, "警告", "请先载入内存镜像文件！")
            return
        
        # 获取按钮文本和对应的命令
        button_text = button.text()
        command_name = button.toolTip() if button.toolTip() else button_text
        
        # 解析参数
        param_list = params.split()
        
        # 构造并执行命令
        try:
            # 构造基本命令
            cmd = [
                self.vol2_plugin.python27,
                self.vol2_plugin.volatility2,
                f'--plugin={self.vol2_plugin.volatility2_plugin}',
                '-f',
                self.vol2_plugin.mem_path,
                f'--profile={self.vol2_plugin.profile}',
                command_name
            ]
            
            # 添加用户输入的参数
            cmd.extend(param_list)
            str_params = '_'.join(param_list)
            # 添加输出参数
            output_type = 'text'  # 默认使用text格式以便查看完整结果
            output_file = f'output/output_vol2_{command_name}_{str_params}.txt'
            cmd.extend([
                f'--output={output_type}',
                f'--output-file={output_file}'
            ])
            
            # 使用run_plugin_with_custom_command执行命令
            self.vol2_plugin.run_plugin_with_custom_command(
                cmd, 
                f'{button_text}(带参数)'
            )
        except Exception as e:
            QMessageBox.warning(self, "错误", f"执行命令时出错：{str(e)}")
    
    def on_task_completed(self, task_name):
        """处理任务完成事件"""
        if hasattr(self.main_window, 'task_manager') and task_name in self.active_tasks:
            self.main_window.task_manager.remove_task(task_name)
            del self.active_tasks[task_name]
    
    def on_profile_obtained(self, profile, profilelist):
        """处理profile获取完成事件"""
        task_name = "Volatility 2 - 获取内存镜像Profile"
        # 移除profile获取任务
        if hasattr(self.main_window, 'task_manager'):
            self.main_window.task_manager.remove_task(task_name)
        
        # 从活跃任务列表中移除
        if hasattr(self, 'active_tasks') and task_name in self.active_tasks:
            del self.active_tasks[task_name]
        
        # 更新profile信息
        self.update_profile(profile, profilelist)
    
    def start_get_profile_with_task(self):
        """带任务跟踪的profile获取"""
        task_name = "Volatility 2 - 获取内存镜像Profile"
        if hasattr(self.main_window, 'task_manager'):
            self.main_window.task_manager.add_task(task_name)
        
        # 添加到活跃任务列表
        if not hasattr(self, 'active_tasks'):
            self.active_tasks = {}
        self.active_tasks[task_name] = True
        
        self.vol2_plugin.start_get_profile()
