from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QMenu, QPushButton, QMessageBox, QScrollArea, QLineEdit, QGroupBox, QComboBox, QLabel, QDialog, QDialogButtonBox, QFormLayout, QFileDialog
from PySide6.QtCore import Qt
from ui.styles import vol2_style, button_style
import ui.styles
from plugin.vol2linux import Vol2LinuxPlugin
import os

class Vol2LinuxButton(QPushButton):
    """Linux命令按钮"""
    def __init__(self, text, function=None):
        super().__init__(text)
        if function:
            self.clicked.connect(function)
        # 调小字体
        font = self.font()
        font.setPointSize(font.pointSize() - 4)
        self.setFont(font)
        self.update_style()
        # 移除固定大小设置，使按钮大小自适应
    
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

        self.title_button = QPushButton(self.title)
        self.title_button.clicked.connect(self.toggle_expand)
        self.title_button.setStyleSheet(ui.styles.button_style)
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
        
        # 添加"添加到预设"菜单项
        if hasattr(self.main_window, 'preset_manager'):
            # 获取预设菜单的动作
            preset_actions = self.main_window.preset_manager.create_preset_actions(button, source_area="Vol2Linux")
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
        param_input.setPlaceholderText("输入参数 (例如: -p 1234 或 -v)")
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
                # 查找Vol2LinuxArea实例
                vol2linux_area = self.find_vol2linux_area()
                if vol2linux_area:
                    # 执行带参数的命令
                    vol2linux_area.execute_with_params(button, params)
                else:
                    QMessageBox.warning(self, "错误", "无法找到Vol2LinuxArea实例")
    
    def find_vol2linux_area(self):
        # 向上查找Vol2LinuxArea实例
        parent = self.parent()
        while parent:
            if isinstance(parent, Vol2LinuxArea):
                return parent
            parent = parent.parent()
        return None

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)
    
    def update_styles(self):
        self.title_button.setStyleSheet(ui.styles.button_style)
        for button in self.buttons:
            if isinstance(button, Vol2LinuxButton):
                button.update_style()

class Vol2LinuxArea(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.setStyleSheet(vol2_style)

        self.main_window = main_window
        self.vol2linux_plugin = Vol2LinuxPlugin('')
        self.button_groups = []  # 存储所有按钮组
        self.all_buttons = []    # 存储所有按钮
        
        # 初始化时调用一次样式更新
        self.current_button_style = button_style
        
        # 保存导入线程的引用，防止被垃圾回收
        self.import_thread = None
        
        self.setup_ui()
        self.update_styles()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # 创建设置组
        self.profile_group = QGroupBox("设置")
        profile_layout = QVBoxLayout()
        
        # Profile 下拉框和按钮（水平布局）
        profile_row = QHBoxLayout()
        profile_label = QLabel("Linux Profile:")
        self.profile_combo = QComboBox()
        self.profile_combo.setStyleSheet(ui.styles.button_style)
        self.profile_combo.setMinimumWidth(200)  # 增加下拉框的最小宽度，使其显示更完整
        
        # 添加导入Profile按钮
        self.import_profile_button = Vol2LinuxButton("导入Profile")
        self.import_profile_button.clicked.connect(self.import_profile)
        
        # 添加profile选择变化事件
        self.profile_combo.currentIndexChanged.connect(self.on_profile_changed)
        
        profile_row.addWidget(profile_label)
        profile_row.addWidget(self.profile_combo)
        profile_row.addWidget(self.import_profile_button)
        profile_row.addStretch()
        
        # 搜索框（水平布局）
        search_row = QHBoxLayout()
        search_label = QLabel("搜索按钮:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词搜索按钮...")
        self.search_input.textChanged.connect(self.filter_buttons)
        search_row.addWidget(search_label)
        search_row.addWidget(self.search_input)
        search_row.addStretch()
        
        # 将行添加到垂直布局
        profile_layout.addLayout(profile_row)
        profile_layout.addLayout(search_row)
        
        self.profile_group.setLayout(profile_layout)
        main_layout.addWidget(self.profile_group)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)

        content_layout = QVBoxLayout(scroll_content)
        content_layout.setSpacing(2)
        content_layout.setAlignment(Qt.AlignTop)

        # 添加自定义命令区域
        self.create_custom_command_area(content_layout)

        # 创建功能组
        self.create_function_groups(content_layout)

        content_layout.addStretch()
        main_layout.addWidget(scroll_area)

    def filter_buttons(self, search_text):
        """根据搜索文本过滤按钮"""
        if not search_text:
            # 如果搜索框为空，恢复所有按钮组的可见性
            for group in self.button_groups:
                group.setVisible(True)
                group.content_widget.setVisible(group.is_expanded)
            # 恢复所有按钮的样式
            self.update_button_styles()
            return
            
        search_text = search_text.lower()
        search_terms = [term.strip() for term in search_text.split() if term.strip()]
        
        # 遍历所有按钮组
        for group in self.button_groups:
            # 检查组内是否有匹配的按钮
            has_match = False
            for button in group.buttons:
                button_text = button.text().lower()
                # 检查是否所有搜索词都匹配
                if all(term in button_text for term in search_terms):
                    has_match = True
                    button.setStyleSheet(ui.styles.button_style + "background-color: #4CAF50;")  # 高亮匹配的按钮
                else:
                    button.setStyleSheet(ui.styles.button_style)  # 恢复正常样式
            
            # 根据是否有匹配来设置组的可见性
            group.setVisible(has_match)
            if has_match:
                group.content_widget.setVisible(True)  # 展开有匹配的组

    def update_button_styles(self):
        """更新所有按钮的样式"""
        for button in self.all_buttons:
            if isinstance(button, Vol2LinuxButton):
                button.update_style()

    def create_custom_command_area(self, layout):
        """创建自定义命令区域"""
        custom_group = QGroupBox("自定义命令")
        custom_layout = QVBoxLayout(custom_group)
        
        input_layout = QHBoxLayout()
        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("输入Volatility 2 Linux命令...")
        self.custom_button = Vol2LinuxButton("执行")
        self.custom_button.clicked.connect(self.execute_custom_command)
        
        input_layout.addWidget(self.custom_input)
        input_layout.addWidget(self.custom_button)
        
        custom_layout.addLayout(input_layout)
        layout.addWidget(custom_group)

    def execute_custom_command(self):
        """执行自定义命令"""
        command = self.custom_input.text().strip()
        if not command:
            QMessageBox.warning(self, "错误", "请输入命令")
            return
            
        if not self.vol2linux_plugin.profile:
            QMessageBox.warning(self, "错误", "请先设置Linux Profile")
            return
            
        # 解析命令
        parts = command.split()
        if not parts:
            return
            
        plugin_name = parts[0]
        params = ' '.join(parts[1:])
        
        # 执行命令
        self.vol2linux_plugin.run_plugin_with_params(plugin_name, f"自定义命令: {plugin_name}", params)

    def create_function_groups(self, layout):
        """创建功能组"""
        # 定义Linux命令及其中文翻译和描述
        linux_commands = {
            "进程信息": [
                {"cmd": "linux_pslist", "zh": "进程列表", "desc": "Gather active tasks by walking the task_struct->task list"},
                {"cmd": "linux_psaux", "zh": "进程详情", "desc": "Gathers processes along with full command line and start time"},
                {"cmd": "linux_pstree", "zh": "进程树", "desc": "Shows the parent/child relationship between processes"},
                {"cmd": "linux_psxview", "zh": "隐藏进程检测", "desc": "Find hidden processes with various process listings"},
                {"cmd": "linux_psscan", "zh": "进程扫描", "desc": "Scan physical memory for processes"},
                {"cmd": "linux_pidhashtable", "zh": "PID哈希表", "desc": "Enumerates processes through the PID hash table"},
                {"cmd": "linux_pslist_cache", "zh": "进程缓存", "desc": "Gather tasks from the kmem_cache"},
                {"cmd": "linux_threads", "zh": "线程信息", "desc": "Prints threads of processes"},
                {"cmd": "linux_ldrmodules", "zh": "加载模块比较", "desc": "Compares the output of proc maps with the list of libraries from libdl"},
                {"cmd": "linux_bash", "zh": "Bash历史", "desc": "Recover bash history from bash process memory"},
                {"cmd": "linux_bash_env", "zh": "Bash环境变量", "desc": "Recover a process' dynamic environment variables"},
                {"cmd": "linux_dynamic_env", "zh": "动态环境变量", "desc": "Recover a process' dynamic environment variables"},
                {"cmd": "linux_bash_hash", "zh": "Bash哈希表", "desc": "Recover bash hash table from bash process memory"},
                {"cmd": "linux_process_hollow", "zh": "进程空心检测", "desc": "Checks for signs of process hollowing"}
            ],
            "内存分析": [
                {"cmd": "linux_memmap", "zh": "内存映射", "desc": "Dumps the memory map for linux tasks"},
                {"cmd": "linux_proc_maps", "zh": "进程内存映射", "desc": "Gathers process memory maps"},
                {"cmd": "linux_proc_maps_rb", "zh": "进程内存映射RB树", "desc": "Gathers process maps for linux through the mappings red-black tree"},
                {"cmd": "linux_dump_map", "zh": "内存映射转储", "desc": "Writes selected memory mappings to disk"},
                {"cmd": "linux_vma_cache", "zh": "VMA缓存", "desc": "Gather VMAs from the vm_area_struct cache"}
            ],
            "文件系统": [
                {"cmd": "linux_enumerate_files", "zh": "文件枚举", "desc": "Lists files referenced by the filesystem cache"},
                {"cmd": "linux_find_file", "zh": "文件查找", "desc": "Lists and recovers files from memory"},
                {"cmd": "linux_dentry_cache", "zh": "目录项缓存", "desc": "Gather files from the dentry cache"},
                {"cmd": "linux_recover_filesystem", "zh": "文件系统恢复", "desc": "Recovers the entire cached file system from memory"},
                {"cmd": "linux_tmpfs", "zh": "临时文件系统", "desc": "Recovers tmpfs filesystems from memory"},
                {"cmd": "linux_getcwd", "zh": "当前工作目录", "desc": "Lists current working directory of each process"},
                {"cmd": "linux_lsof", "zh": "打开文件列表", "desc": "Lists file descriptors and their path"},
                {"cmd": "linux_kernel_opened_files", "zh": "内核打开文件", "desc": "Lists files that are opened from within the kernel"}
            ],
            "网络分析": [
                {"cmd": "linux_netstat", "zh": "网络连接", "desc": "Lists open sockets"},
                {"cmd": "linux_arp", "zh": "ARP表", "desc": "Print the ARP table"},
                {"cmd": "linux_ifconfig", "zh": "网络接口", "desc": "Gathers active interfaces"},
                {"cmd": "linux_route_cache", "zh": "路由缓存", "desc": "Recovers the routing cache from memory"},
                {"cmd": "linux_netscan", "zh": "网络扫描", "desc": "Carves for network connection structures"},
                {"cmd": "linux_list_raw", "zh": "原始套接字", "desc": "List applications with promiscuous sockets"},
                {"cmd": "linux_netfilter", "zh": "网络过滤器", "desc": "Lists Netfilter hooks"},
                {"cmd": "linux_pkt_queues", "zh": "数据包队列", "desc": "Writes per-process packet queues out to disk"},
                {"cmd": "linux_sk_buff_cache", "zh": "套接字缓冲区", "desc": "Recovers packets from the sk_buff kmem_cache"}
            ],
            "内核分析": [
                {"cmd": "linux_check_syscall", "zh": "系统调用检查", "desc": "Checks if the system call table has been altered"},
                {"cmd": "linux_check_modules", "zh": "模块检查", "desc": "Compares module list to sysfs info, if available"},
                {"cmd": "linux_check_afinfo", "zh": "网络协议检查", "desc": "Verifies the operation function pointers of network protocols"},
                {"cmd": "linux_check_fop", "zh": "文件操作检查", "desc": "Check file operation structures for rootkit modifications"},
                {"cmd": "linux_check_idt", "zh": "IDT检查", "desc": "Checks if the IDT has been altered"},
                {"cmd": "linux_check_inline_kernel", "zh": "内联内核钩子检查", "desc": "Check for inline kernel hooks"},
                {"cmd": "linux_check_creds", "zh": "凭证结构检查", "desc": "Checks if any processes are sharing credential structures"},
                {"cmd": "linux_check_tty", "zh": "TTY设备检查", "desc": "Checks tty devices for hooks"},
                {"cmd": "linux_check_syscall_arm", "zh": "ARM系统调用检查", "desc": "Checks if the system call table has been altered"},
                {"cmd": "linux_check_evt_arm", "zh": "ARM异常向量表检查", "desc": "Checks the Exception Vector Table to look for syscall table hooking"},
                {"cmd": "linux_hidden_modules", "zh": "隐藏模块检测", "desc": "Carves memory to find hidden kernel modules"},
                {"cmd": "linux_keyboard_notifiers", "zh": "键盘通知链检查", "desc": "Parses the keyboard notifier call chain"},
                {"cmd": "linux_apihooks", "zh": "用户态API钩子检查", "desc": "Checks for userland apihooks"}
            ],
            "系统信息": [
                {"cmd": "linux_banner", "zh": "系统标识", "desc": "Prints the Linux banner information"},
                {"cmd": "linux_cpuinfo", "zh": "CPU信息", "desc": "Prints info about each active processor"},
                {"cmd": "linux_dmesg", "zh": "内核日志", "desc": "Gather dmesg buffer"},
                {"cmd": "linux_iomem", "zh": "IO内存映射", "desc": "Provides output similar to /proc/iomem"},
                {"cmd": "linux_mount", "zh": "挂载点", "desc": "Gather mounted fs/devices"},
                {"cmd": "linux_mount_cache", "zh": "挂载点缓存", "desc": "Gather mounted fs/devices from kmem_cache"},
                {"cmd": "linux_slabinfo", "zh": "Slab信息", "desc": "Mimics /proc/slabinfo on a running machine"},
                {"cmd": "linux_lsmod", "zh": "加载模块列表", "desc": "Gather loaded kernel modules"},
                {"cmd": "linux_aslr_shift", "zh": "ASLR偏移检测", "desc": "Automatically detect the Linux ASLR shift"},
                {"cmd": "linux_info_regs", "zh": "寄存器信息", "desc": "It's like 'info registers' in GDB. It prints out all the"}
            ],
            "可执行文件分析": [
                {"cmd": "linux_elfs", "zh": "ELF文件扫描", "desc": "Find ELF binaries in process mappings"},
                {"cmd": "linux_malfind", "zh": "恶意代码查找", "desc": "Looks for suspicious process mappings"},
                {"cmd": "linux_library_list", "zh": "库文件列表", "desc": "Lists libraries loaded into a process"},
                {"cmd": "linux_librarydump", "zh": "库文件转储", "desc": "Dumps shared libraries in process memory to disk"},
                {"cmd": "linux_procdump", "zh": "进程转储", "desc": "Dumps a process's executable image to disk"},
                {"cmd": "linux_moddump", "zh": "内核模块转储", "desc": "Extract loaded kernel modules"},
                {"cmd": "linux_plthook", "zh": "PLT钩子扫描", "desc": "Scan ELF binaries' PLT for hooks to non-NEEDED images"}
            ],
            "其他功能": [
                {"cmd": "linux_yarascan", "zh": "Yara扫描", "desc": "A shell in the Linux memory image"},
                {"cmd": "linux_strings", "zh": "字符串提取", "desc": "Match physical offsets to virtual addresses (may take a while, VERY verbose)"},
                {"cmd": "linux_volshell", "zh": "内存交互Shell", "desc": "Shell in the memory image"},
                {"cmd": "linux_truecrypt_passphrase", "zh": "TrueCrypt密码恢复", "desc": "Recovers cached Truecrypt passphrases"}
            ]
        }
        
        # 为每个分组创建按钮和按钮组
        for group_name, commands in linux_commands.items():
            buttons = []
            for cmd_info in commands:
                cmd = cmd_info["cmd"]
                zh_name = cmd_info["zh"]
                desc = cmd_info["desc"]
                
                button = Vol2LinuxButton(zh_name)
                button.setToolTip(f"{cmd}: {desc}")  # 设置气泡提示，显示原始英文命令和描述
                button.clicked.connect(lambda checked=False, cmd=cmd: self.vol2linux_plugin.run_plugin(cmd, cmd))
                buttons.append(button)
                self.all_buttons.append(button)
                
            # 创建按钮组
            button_group = CollapsibleButtonGroup(group_name, buttons, self.main_window)
            layout.addWidget(button_group)
            self.button_groups.append(button_group)

    def load_profile(self):
        """加载Linux Profile"""
        # 获取当前选择的profile
        selected_profile = self.profile_combo.currentText()
        if not selected_profile:
            QMessageBox.warning(self, "错误", "请选择一个Linux Profile")
            return
            
        # 设置profile
        self.vol2linux_plugin.set_profile(selected_profile)
        QMessageBox.information(self, "成功", f"已设置Linux Profile: {selected_profile}")
        
    def import_profile(self):
        """导入Linux Profile"""
        # 打开文件对话框，选择zip文件
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("ZIP文件 (*.zip)")
        file_dialog.setWindowTitle("选择Linux Profile ZIP文件")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                zip_file_path = selected_files[0]
                
                # 打印开始导入的消息
                print(f"[*] 开始导入Linux Profile: {os.path.basename(zip_file_path)}")
                
                # 创建并启动导入线程
                self.import_thread = self.vol2linux_plugin.import_linux_profile(zip_file_path)
                self.import_thread.import_completed.connect(self.on_import_completed)
                self.import_thread.start()
                
                # 禁用导入按钮，防止重复点击
                self.import_profile_button.setEnabled(False)
                self.import_profile_button.setText("导入中...")
    
    def on_import_completed(self, success, message, new_profile):
        """导入完成后的回调函数"""
        # 重新启用导入按钮
        self.import_profile_button.setEnabled(True)
        self.import_profile_button.setText("导入Profile")
        
        if success:
            # 重新加载profiles列表
            self.populate_linux_profiles()
            
            # 如果有新的profile，选择它
            if new_profile:
                index = self.profile_combo.findText(new_profile)
                if index >= 0:
                    self.profile_combo.setCurrentIndex(index)
                    # 自动加载新导入的profile
                    self.vol2linux_plugin.set_profile(new_profile)
            
            # 使用打印而不是消息框
            print(f"[+] {message}")
        else:
            # 错误信息仍然使用消息框，因为这需要用户注意
            QMessageBox.warning(self, "错误", message)
            
        # 不要在这里删除线程引用，让它自然结束

    def update_styles(self):
        """更新所有样式"""
        for group in self.button_groups:
            group.update_styles()
        self.import_profile_button.update_style()
        self.custom_button.update_style()

    def set_memory_image(self, mem_path):
        """设置内存镜像路径"""
        if mem_path:
            self.vol2linux_plugin = Vol2LinuxPlugin(mem_path)
            # 获取并填充Linux profiles
            self.populate_linux_profiles()
            print(f"[+] Vol2Linux: 已设置内存镜像路径 {mem_path}")
        else:
            print("[-] Vol2Linux: 内存镜像路径为空")

    def populate_linux_profiles(self):
        """填充Linux profiles下拉框"""
        self.profile_combo.clear()
        profiles = self.vol2linux_plugin.get_linux_profiles()
        if profiles:
            self.profile_combo.addItems(profiles)
            print(f"[+] 已加载 {len(profiles)} 个Linux profiles")
            
            # 自动选择第一个profile
            if self.profile_combo.count() > 0:
                selected_profile = self.profile_combo.itemText(0)
                self.profile_combo.setCurrentIndex(0)
                self.vol2linux_plugin.set_profile(selected_profile)
                print(f"[+] 已自动选择Linux Profile: {selected_profile}")
        else:
            print("[-] 未找到Linux profiles")
            
    def execute_with_params(self, button, params):
        """执行带参数的命令"""
        cmd = button.text()
        self.vol2linux_plugin.run_plugin_with_params(cmd, f"{cmd} {params}", params)

    def on_profile_changed(self, index):
        """处理profile选择变化"""
        if index >= 0:
            selected_profile = self.profile_combo.itemText(index)
            self.vol2linux_plugin.set_profile(selected_profile)
            print(f"[+] 已选择Linux Profile: {selected_profile}")

    def closeEvent(self, event):
        """窗口关闭时的处理"""
        # 等待所有导入线程完成
        if hasattr(self.vol2linux_plugin, 'wait_for_import_threads'):
            self.vol2linux_plugin.wait_for_import_threads()
        
        # 调用父类的closeEvent
        super().closeEvent(event)
