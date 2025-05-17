from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QPushButton, QMessageBox, QLineEdit, QHBoxLayout, QScrollArea, QGroupBox, QCheckBox, QMenu, QLabel, QDialog, QDialogButtonBox, QFormLayout
from PySide6.QtCore import Qt
from ui.styles import memprocfs_style, get_current_theme, apply_color_scheme, is_dark_mode
import ui.styles
from plugin.vol3linux import Vol3LinuxPlugin, WorkerThread
from functools import partial
import json

class Vol3LinuxButton(QPushButton):
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
        # 针对Linux区域的按钮设置一个类似但稍微特殊的样式
        button_style = ui.styles.button_style
        # 添加轻微的绿色边框作为Linux特色
        linux_button_style = f"{button_style} QPushButton:hover {{ border: 1px solid rgba(84, 160, 84, 0.8); }}" 
        self.setStyleSheet(linux_button_style)

class LinuxCollapsibleButtonGroup(QWidget):
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

        # 自定义标题按钮样式
        self.title_button = Vol3LinuxButton(self.title)
        self.title_button.clicked.connect(self.toggle_expand)
        # Linux主题颜色
        linux_color = "rgba(84, 160, 84, 0.8)"
        self.title_button.setStyleSheet(f"{ui.styles.button_style} QPushButton {{ background-color: {linux_color}; color: white; font-weight: bold; text-align: left; padding-left: 10px; }}")
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
        
        # 添加"添加到预设"菜单项
        if hasattr(self.main_window, 'preset_manager'):
            preset_actions = self.main_window.preset_manager.create_preset_actions(button, source_area="Vol3Linux")
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
        
        # 执行对话框
        if dialog.exec() == QDialog.Accepted:
            params = param_input.text().strip()
            if params:
                vol3_linux_area = self.find_vol3_linux_area()
                if vol3_linux_area:
                    vol3_linux_area.execute_with_params(button, params)
            else:
                QMessageBox.information(self, "提示", "没有输入参数，将使用默认参数执行。")
                button.click()  # 如果没有参数，直接触发按钮点击

    def find_vol3_linux_area(self):
        # 查找父级的Vol3LinuxArea实例
        parent = self.parent()
        while parent:
            if isinstance(parent, Vol3LinuxArea):
                return parent
            parent = parent.parent()
        return None

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)

    def update_styles(self):
        # 添加Linux风格的特殊标题样式
        linux_color = "rgba(84, 160, 84, 0.8)"  # Linux绿色调
        self.title_button.setStyleSheet(f"{ui.styles.button_style} QPushButton {{ background-color: {linux_color}; color: white; font-weight: bold; text-align: left; padding-left: 10px; }}")
        
        # 更新其他所有按钮
        for button in self.buttons:
            if isinstance(button, Vol3LinuxButton):
                button.update_style()

class Vol3LinuxArea(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.vol3_plugin = None  # 在需要时初始化
        self.button_groups = []  # 存储所有按钮组
        self.all_buttons = []    # 存储所有按钮
        
        # 定义功能分组 - 根据lin_func.md更新
        self.function_groups = {
            "系统基础信息": [
                ("Banner识别(Banners)", "vol3linux_banners_Banners"),
                ("引导时间(Boottime)", "vol3linux_boottime_Boottime"),
                ("IOMEM映射(IOMem)", "vol3linux_iomem_IOMem"),
                ("VMCore信息(VMCoreInfo)", "vol3linux_vmcoreinfo_VMCoreInfo"),
                ("内核消息(Kmsg)", "vol3linux_kmsg_Kmsg"),
                ("内核符号(Kallsyms)", "vol3linux_kallsyms_Kallsyms")
            ],
            "进程信息": [
                ("进程列表(PsList)", "vol3linux_pslist_PsList"), 
                ("进程扫描(PsScan)", "vol3linux_psscan_PsScan"), 
                ("进程树(PsTree)", "vol3linux_pstree_PsTree"),
                ("命令行参数(PsAux)", "vol3linux_psaux_PsAux"),
                ("进程内存映射(proc.Maps)", "vol3linux_proc_Maps"),
                ("进程调用栈(PsCallStack)", "vol3linux_pscallstack_PsCallStack"),
                ("PID哈希表(PIDHashTable)", "vol3linux_pidhashtable_PIDHashTable"),
                ("权限和能力(Capabilities)", "vol3linux_capabilities_Capabilities"),
                ("Ptrace跟踪(Ptrace)", "vol3linux_ptrace_Ptrace")
            ],
            "用户与环境": [
                ("Bash命令(Bash)", "vol3linux_bash_Bash"), 
                ("环境变量(Envars)", "vol3linux_envars_Envars")
            ],
            "网络与通信": [
                ("IP地址(ip.Addr)", "vol3linux_ip_Addr"),
                ("网络接口(ip.Link)", "vol3linux_ip_Link"),
                ("Socket统计(Sockstat)", "vol3linux_sockstat_Sockstat"),
                ("网络过滤器(Netfilter)", "vol3linux_netfilter_Netfilter")
            ],
            "文件系统": [
                ("挂载信息(MountInfo)", "vol3linux_mountinfo_MountInfo"),
                ("文件句柄(Lsof)", "vol3linux_lsof_Lsof"),
                ("缓存文件(pagecache.Files)", "vol3linux_pagecache_Files"),
                ("缓存节点(pagecache.InodePages)", "vol3linux_pagecache_InodePages"),
                ("恢复文件系统(pagecache.RecoverFs)", "vol3linux_pagecache_RecoverFs")
            ],
            "内核与模块": [
                ("ELF文件分析(Elfs)", "vol3linux_elfs_Elfs"), 
                ("加载模块(Lsmod)", "vol3linux_lsmod_Lsmod"), 
                ("内核线程(Kthreads)", "vol3linux_kthreads_Kthreads"),
                ("模块提取(ModuleExtract)", "vol3linux_module_extract_ModuleExtract"),
                ("模块视图(Modxview)", "vol3linux_modxview_Modxview"),
                ("隐藏模块(Hidden_modules)", "vol3linux_hidden_modules_Hidden_modules"),
                ("已加载库(LibraryList)", "vol3linux_library_list_LibraryList")
            ],
            "图形和输入": [
                ("帧缓冲设备(Fbdev)", "vol3linux_graphics_fbdev_Fbdev"),
                ("键盘监听器(Keyboard_notifiers)", "vol3linux_keyboard_notifiers_Keyboard_notifiers"),
                ("TTY检查(tty_check)", "vol3linux_tty_check_tty_check")
            ],
            "跟踪与性能": [
                ("eBPF程序(EBPF)", "vol3linux_ebpf_EBPF"),
                ("FTrace检查(CheckFtrace)", "vol3linux_tracing_ftrace_CheckFtrace"),
                ("性能事件(PerfEvents)", "vol3linux_tracing_perf_events_PerfEvents"),
                ("跟踪点检查(CheckTracepoints)", "vol3linux_tracing_tracepoints_CheckTracepoints")
            ],
            "安全检查": [
                ("AF信息检查(Check_afinfo)", "vol3linux_check_afinfo_Check_afinfo"), 
                ("凭证检查(Check_creds)", "vol3linux_check_creds_Check_creds"), 
                ("IDT检查(Check_idt)", "vol3linux_check_idt_Check_idt"),
                ("系统调用检查(Check_syscall)", "vol3linux_check_syscall_Check_syscall"), 
                ("模块检查(Check_modules)", "vol3linux_check_modules_Check_modules"), 
                ("恶意代码检测(Malfind)", "vol3linux_malfind_Malfind"),
                ("内存正则扫描(VmaRegExScan)", "vol3linux_vmaregexscan_VmaRegExScan")
            ]
        }
        
        self.setup_ui()
        self.update_styles()

    def setup_ui(self):
        # 设置整体布局
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)
        
        # 创建设置组合框，将搜索和离线模式选项放在这里
        settings_group = QGroupBox("设置")
        settings_layout = QVBoxLayout()  # 改为垂直布局以容纳更多选项
        
        # 搜索和离线模式行
        top_settings_layout = QHBoxLayout()
        
        # 搜索框
        search_label = QLabel("搜索按钮:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索关键词")
        self.search_input.textChanged.connect(self.filter_buttons)
        top_settings_layout.addWidget(search_label)
        top_settings_layout.addWidget(self.search_input)
        
        # 离线模式复选框
        self.offline_checkbox = QCheckBox("离线模式")
        self.offline_checkbox.setToolTip("启用离线模式 (--offline)")
        top_settings_layout.addWidget(self.offline_checkbox)
        
        # 添加伸缩空间以保持布局平衡
        top_settings_layout.addStretch()
        
        # 代理设置行
        proxy_settings_layout = QHBoxLayout()
        
        # 代理复选框 - 默认勾选
        self.proxy_checkbox = QCheckBox("使用代理")
        self.proxy_checkbox.setToolTip("启用代理连接访问远程符号服务器")
        self.proxy_checkbox.setChecked(True)  # 默认选中
        proxy_settings_layout.addWidget(self.proxy_checkbox)
        
        # 代理URL输入框 - 默认值
        proxy_url_label = QLabel("代理地址:")
        self.proxy_url_input = QLineEdit()
        self.proxy_url_input.setPlaceholderText("例如: http://127.0.0.1:7890")
        self.proxy_url_input.setText("http://127.0.0.1:1090")  # 设置默认值
        proxy_settings_layout.addWidget(proxy_url_label)
        proxy_settings_layout.addWidget(self.proxy_url_input)
        
        # 新增远程符号URL设置行
        remote_url_layout = QHBoxLayout()
        
        # 远程符号URL标签和输入框
        remote_url_label = QLabel("远程符号URL:")
        self.remote_url_input = QLineEdit()
        self.remote_url_input.setPlaceholderText("https://github.com/Abyss-W4tcher/volatility3-symbols/raw/master/banners/banners.json")
        remote_url_layout.addWidget(remote_url_label)
        remote_url_layout.addWidget(self.remote_url_input)
        
        # 添加到设置布局
        settings_layout.addLayout(top_settings_layout)
        settings_layout.addLayout(proxy_settings_layout)
        settings_layout.addLayout(remote_url_layout)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)

        content_layout = QVBoxLayout(scroll_content)
        content_layout.setSpacing(2)
        content_layout.setAlignment(Qt.AlignTop)

        # 添加自定义命令区域
        self.create_custom_command_area(content_layout)

        # 为每个功能分组创建按钮组
        for group_name, functions in self.function_groups.items():
            buttons = []
            for button_label, func_name in functions:
                button = Vol3LinuxButton(button_label)
                button.clicked.connect(partial(self.button_clicked, func_name))
                buttons.append(button)
                self.all_buttons.append(button)
            
            # 创建按钮组
            button_group = LinuxCollapsibleButtonGroup(group_name, buttons, self.main_window)
            self.button_groups.append(button_group)
            content_layout.addWidget(button_group)

        main_layout.addWidget(scroll_area)

    # 根据搜索文本过滤按钮
    def filter_buttons(self, search_text):
        search_text = search_text.lower()
        
        # 没有搜索文本，显示所有按钮组
        if not search_text:
            for group in self.button_groups:
                group.setVisible(True)
                
                # 重置按钮可见性
                for button in group.buttons:
                    button.setVisible(True)
                    
                # 更新网格布局
                visible_buttons = [b for b in group.buttons if b.isVisible()]
                for i, button in enumerate(visible_buttons):
                    row = i // 3
                    col = i % 3
                    group.content_layout.addWidget(button, row, col)
                    
            return
            
        # 搜索匹配
        for group in self.button_groups:
            visible_buttons = []
            
            # 检查每个按钮是否匹配
            for button in group.buttons:
                if search_text in button.text().lower() or search_text in button.toolTip().lower():
                    button.setVisible(True)
                    visible_buttons.append(button)
                else:
                    button.setVisible(False)
                    
            # 如果组内有可见按钮，则显示组
            group.setVisible(len(visible_buttons) > 0)
            
            # 如果组可见，更新按钮布局
            if group.isVisible():
                # 重排按钮
                for i, button in enumerate(visible_buttons):
                    row = i // 3
                    col = i % 3
                    group.content_layout.addWidget(button, row, col)
                
                # 如果有可见的按钮，则展开组
                if visible_buttons and not group.is_expanded:
                    group.toggle_expand()

    def update_mem_path(self):
        """更新内存路径并确保Vol3LinuxPlugin正确初始化"""
        # 参照Vol3Area的实现方式，使用main_window的get_current_mem_path方法
        new_mem_path = self.main_window.get_current_mem_path()
        if new_mem_path:
            try:
                # 如果main_window上有vol3_linux_plugin，使用它
                if hasattr(self.main_window, 'vol3_linux_plugin') and self.main_window.vol3_linux_plugin:
                    self.vol3_plugin = self.main_window.vol3_linux_plugin
                    print(f"[信息] 使用主窗口上的Vol3LinuxPlugin实例")
                # 否则创建新的Vol3LinuxPlugin实例
                elif not self.vol3_plugin or self.vol3_plugin.mem_path != new_mem_path:
                    print(f"[信息] 初始化Vol3LinuxPlugin: {new_mem_path}")
                    self.vol3_plugin = Vol3LinuxPlugin(new_mem_path)
                    # 将实例保存到main_window上，便于共享
                    self.main_window.vol3_linux_plugin = self.vol3_plugin
            except Exception as e:
                print(f"[错误] 初始化Vol3LinuxPlugin失败: {str(e)}")
                return None
            return new_mem_path
        else:
            print("[提示] 未找到内存镜像路径，请先载入镜像")
            return None

    def button_clicked(self, func_name, checked=False):
        """处理按钮点击事件"""
        # 首先更新内存路径
        new_mem_path = self.update_mem_path()
        if not new_mem_path:
            QMessageBox.warning(self, "警告", "请先载入内存镜像文件！")
            return
        
        # 检查vol3_plugin是否已初始化
        if not self.vol3_plugin:
            QMessageBox.warning(self, "警告", "内存分析插件未初始化，请确保已载入内存镜像！")
            return
        
        # 检查设置选项
        use_offline = self.offline_checkbox.isChecked()
        use_proxy = self.proxy_checkbox.isChecked()
        proxy_url = self.proxy_url_input.text().strip() if use_proxy else None
        
        # 验证代理URL格式
        if use_proxy and not proxy_url:
            QMessageBox.warning(self, "警告", "启用代理时需要提供代理地址！")
            return
        
        # 处理func_name格式，去掉"linux."前缀（如果有）
        plugin_name = func_name
        if func_name.startswith("linux."):
            plugin_name = func_name.replace("linux.", "")
        
        # 组装方法名
        method_name = f'vol3linux_{plugin_name}'
        print(f"[DEBUG] 尝试调用方法: {method_name}")
        
        if hasattr(self.vol3_plugin, method_name):
            try:
                # 调用相应的方法，传递离线参数和代理参数
                getattr(self.vol3_plugin, method_name)(offline=use_offline, use_proxy=use_proxy, proxy_url=proxy_url)
                print(f"[*] 执行 {plugin_name} 命令")
                if use_proxy:
                    print(f"[*] 使用代理: {proxy_url}")
            except Exception as e:
                error_msg = f"执行 {plugin_name} 时出错：{str(e)}"
                print(f"[×] {error_msg}")
                QMessageBox.warning(self, "错误", error_msg)
        else:
            print(f"[DEBUG] 无法找到方法: {method_name}, 可用方法: {dir(self.vol3_plugin)}")
            QMessageBox.warning(self, "错误", f"未找到命令: {plugin_name}")

    def execute_with_params(self, button, params):
        # 获取按钮文本
        button_text = button.text()
        
        # 找到对应的功能名称
        function_name = None
        for group_name, functions in self.function_groups.items():
            for btn_label, func_name in functions:
                if btn_label == button_text:
                    function_name = func_name
                    break
            if function_name:
                break
        
        if not function_name:
            QMessageBox.warning(self, "错误", f"找不到与按钮 '{button_text}' 对应的功能名称")
            return
        
        print(f"[DEBUG] 参数执行命令: {function_name} 使用参数: {params}")
        
        # 执行命令并传递参数
        new_mem_path = self.update_mem_path()
        if not new_mem_path:
            QMessageBox.warning(self, "警告", "请先载入内存镜像文件！")
            return
            
        # 检查vol3_plugin是否已初始化
        if not self.vol3_plugin:
            QMessageBox.warning(self, "警告", "内存分析插件未初始化，请确保已载入内存镜像！")
            return
        
        # 检查设置选项
        use_offline = self.offline_checkbox.isChecked()
        use_proxy = self.proxy_checkbox.isChecked()
        proxy_url = self.proxy_url_input.text().strip() if use_proxy else None
        
        # 验证代理URL格式
        if use_proxy and not proxy_url:
            QMessageBox.warning(self, "警告", "启用代理时需要提供代理地址！")
            return
        
        # 如果使用代理，生成代理环境变量
        proxy_env = ""
        if use_proxy and proxy_url:
            print(f"[*] 使用代理: {proxy_url}")
            # 用于Windows系统的代理设置
            proxy_env = f"set HTTPS_PROXY={proxy_url} && set HTTP_PROXY={proxy_url} && "
        
        # 处理插件名称
        plugin_name = function_name
        if function_name.startswith("linux."):
            plugin_name = function_name.replace("linux.", "")
        
        # 确定输出类型
        output_type = 'quick' if plugin_name in self.vol3_plugin.txt_plugins else 'csv'
        
        # 构造命令
        cmd = [
            f'{proxy_env}"{self.vol3_plugin.pythonpath}"' if use_proxy else f'"{self.vol3_plugin.pythonpath}"',
            f'"{self.vol3_plugin.volatility3}"',
            '-f',
            f'"{new_mem_path}"'
        ]
        
        # 添加离线模式或远程ISF URL参数
        if use_offline:
            cmd.append('--offline')
        elif use_proxy and proxy_url:
            # 如果使用代理，使用远程ISF URL
            cmd.append("--remote-isf-url")
            # 使用用户自定义URL或默认URL
            remote_url = self.remote_url_input.text().strip()
            if remote_url:
                cmd.append(f'"{remote_url}"')
            else:
                cmd.append('"https://github.com/Abyss-W4tcher/volatility3-symbols/raw/master/banners/banners.json"')
        else:
            # 否则使用本地符号表
            cmd.append("--single-location")
            cmd.append(f'"{os.path.join(os.path.dirname(self.vol3_plugin.volatility3), "symbols")}"')
        
        # 添加输出格式
        cmd.extend([
            '-r',
            output_type
        ])
        
        # 构造带参数的命令
        full_command = f"linux.{plugin_name}"
        if params:
            for param_name, param_value in params.items():
                full_command += f" --{param_name}={param_value}"
        
        cmd.append(full_command)
        
        print(f"[*] 正在执行命令：{' '.join(cmd)}")
        
        # 创建工作线程并执行
        try:
            worker = WorkerThread(cmd)
            output_file = f'output/output_vol3_linux_{plugin_name}_params.{"txt" if plugin_name in self.vol3_plugin.txt_plugins else "csv"}'
            
            def on_task_complete(success, msg, output):
                if success:
                    print(f"[+] 命令执行成功：{function_name} {params}")
                    self.vol3_plugin.on_task_completed(success, msg, output, output_file, f'linux_{plugin_name}')
                else:
                    print(f"[×] 命令执行失败：{function_name} {params}")
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
        # 获取当前主题信息
        current_theme = get_current_theme()
        is_dark = is_dark_mode()
        
        # Linux特色绿色调
        linux_color = "rgba(84, 160, 84, 0.8)" 
        
        try:
            # 从样式配置中读取当前主题的颜色方案
            with open("config/style.json", "r", encoding="utf-8") as f:
                color_schemes = json.load(f)
            
            scheme = color_schemes[current_theme]["dark" if is_dark else "light"]
            # 获取背景色和文本色
            bg_color = scheme["background_color"]
            text_color = scheme["text_color"]
            
            # 设置整个区域的基础样式
            base_style = f"""
            QWidget {{ 
                background-color: {bg_color}; 
                color: {text_color}; 
            }}
            QLineEdit, QPushButton, QComboBox, QCheckBox {{ 
                background-color: {bg_color}; 
                color: {text_color}; 
            }}
            """
            
            # 应用基础样式到所有控件
            self.setStyleSheet(base_style + ui.styles.memprocfs_style)
            
            # 为分组标题添加Linux风格，但保持与主题变化一致
            for group_box in self.findChildren(QGroupBox):
                group_box.setStyleSheet(f"""
                    QGroupBox {{background-color: {bg_color}; border: 1px solid {linux_color};}}
                    QGroupBox::title {{background-color: {linux_color}; color: white; padding: 2px;}}
                """)
                
            # 应用样式到滚动区域和其内容
            scroll_area = self.findChild(QScrollArea)
            if scroll_area:
                scroll_area.setStyleSheet(base_style + ui.styles.memprocfs_style)
                content_widget = scroll_area.widget()
                if content_widget:
                    content_widget.setStyleSheet(base_style)
                    
            # 更新所有按钮和按钮组
            for button in self.findChildren(QPushButton):
                if isinstance(button, Vol3LinuxButton):
                    button.update_style()
            
            # 更新所有按钮组样式
            for group in self.findChildren(LinuxCollapsibleButtonGroup):
                group.update_styles()
                
        except Exception as e:
            print(f"[错误] 读取主题信息失败: {str(e)}")
            # 如果读取主题失败，至少应用基本样式
            self.setStyleSheet(ui.styles.memprocfs_style)
        
        self.update()

    def update_button_styles(self):
        # 直接调用update_styles来更新所有按钮样式
        # 这与vol3_area的实现保持一致
        self.update_styles()

    def create_custom_command_area(self, layout):
        # 创建自定义命令组
        custom_command_group = QGroupBox("自定义命令")
        custom_command_layout = QHBoxLayout(custom_command_group)
        
        # 创建命令输入框
        self.custom_command_input = QLineEdit()
        self.custom_command_input.setPlaceholderText("输入Vol3 Linux命令 (例如: linux.pslist)")
        
        # 创建执行按钮
        execute_button = QPushButton("执行")
        execute_button.clicked.connect(self.execute_custom_command)
        
        # 添加到布局
        custom_command_layout.addWidget(self.custom_command_input)
        custom_command_layout.addWidget(execute_button)
        
        layout.addWidget(custom_command_group)

    def execute_custom_command(self):
        command = self.custom_command_input.text().strip()
        if not command:
            QMessageBox.warning(self, "警告", "请输入命令！")
            return
        
        # 确保命令以linux.开头
        if not command.startswith("linux."):
            command = "linux." + command
        
        new_mem_path = self.update_mem_path()
        if not new_mem_path:
            QMessageBox.warning(self, "警告", "请先载入内存镜像文件！")
            return
        
        # 检查设置选项
        use_offline = self.offline_checkbox.isChecked()
        use_proxy = self.proxy_checkbox.isChecked()
        proxy_url = self.proxy_url_input.text().strip() if use_proxy else None
        
        # 验证代理URL格式
        if use_proxy and not proxy_url:
            QMessageBox.warning(self, "警告", "启用代理时需要提供代理地址！")
            return
        
        # 构造并执行命令
        try:
            # 从命令中提取插件名称用于输出文件命名
            plugin_name = command.replace("linux.", "").replace(" ", "_")
            
            # 确保vol3_plugin已初始化
            if not self.vol3_plugin:
                QMessageBox.warning(self, "警告", "内存分析插件未初始化，请确保已载入内存镜像！")
                return
            
            # 如果使用代理，生成代理环境变量
            proxy_env = ""
            if use_proxy and proxy_url:
                print(f"[*] 使用代理: {proxy_url}")
                # 用于Windows系统的代理设置
                proxy_env = f"set HTTPS_PROXY={proxy_url} && set HTTP_PROXY={proxy_url} && "
            
            # 确定输出类型
            output_type = 'quick' if plugin_name in self.vol3_plugin.txt_plugins else 'csv'
            
            # 构造命令
            cmd = [
                f'{proxy_env}"{self.vol3_plugin.pythonpath}"' if use_proxy else f'"{self.vol3_plugin.pythonpath}"',
                f'"{self.vol3_plugin.volatility3}"',
                '-f',
                f'"{new_mem_path}"'
            ]
            
            # 添加离线模式或远程ISF URL参数
            if use_offline:
                cmd.append('--offline')
            elif use_proxy and proxy_url:
                # 如果使用代理，使用远程ISF URL
                cmd.append("--remote-isf-url")
                # 使用用户自定义URL或默认URL
                remote_url = self.remote_url_input.text().strip()
                if remote_url:
                    cmd.append(f'"{remote_url}"')
                else:
                    cmd.append('"https://github.com/Abyss-W4tcher/volatility3-symbols/raw/master/banners/banners.json"')
            else:
                # 否则使用本地符号表
                cmd.append("--single-location")
                cmd.append(f'"{os.path.join(os.path.dirname(self.vol3_plugin.volatility3), "symbols")}"')
            
            cmd.extend([
                '-r',
                output_type,
                command
            ])
            
            print(f"[*] 正在执行命令：{' '.join(cmd)}")
            
            # 创建工作线程并执行
            worker = WorkerThread(cmd)
            output_file = f'output/output_vol3_linux_custom_{plugin_name}.{"txt" if plugin_name in self.vol3_plugin.txt_plugins else "csv"}'
            
            def on_task_complete(success, msg, output):
                if success:
                    print(f"[+] 命令执行成功：{command}")
                    self.vol3_plugin.on_task_completed(success, msg, output, output_file, f'linux_custom_{plugin_name}')
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
