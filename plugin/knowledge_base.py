from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout, QTabWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

class KnowledgeBaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Lovelymem - Volatility 2 常备知识")
        self.setGeometry(100, 100, 900, 600)
        self.setWindowIcon(QIcon('res/logo.ico'))
        
        layout = QVBoxLayout(self)
        
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        self.create_tabs()
        
        button_layout = QHBoxLayout()
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)

    def create_tabs(self):
        self.add_tab("基本功能", self.load_basic_knowledge())
        self.add_tab("高级功能", self.load_advanced_knowledge())
        self.add_tab("系统信息", self.load_system_knowledge())
        self.add_tab("用户信息", self.load_user_knowledge())
        self.add_tab("文件导出", self.load_export_knowledge())
        self.add_tab("扩展功能", self.load_extend_knowledge())

    def add_tab(self, name, content):
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml(content)
        self.tab_widget.addTab(text_browser, name)

    def load_basic_knowledge(self):
        return """
        <h2>基本功能插件及其作用</h2>
        <ul>
            <li><b>filescan</b>: 使用池扫描技术查找内存中的文件对象 (<i>FILE_OBJECT</i>)，可以发现隐藏或已删除的文件句柄。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 filescan</pre>
            </li>
            <li><b>pslist</b>: 列出系统中的进程，包括PID、进程名、创建时间等信息，基于遍历活动进程的双向链表。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 pslist</pre>
            </li>
            <li><b>netscan</b>: 使用池扫描技术查找内存中的网络连接和套接字信息，可发现隐藏的网络活动。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 netscan</pre>
            </li>
            <li><b>cmdline</b>: 显示每个进程的命令行参数，帮助理解进程的启动方式和目的。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 cmdline</pre>
            </li>
            <li><b>envars</b>: 显示每个进程的环境变量，可能包含路径、用户名等敏感信息。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 envars</pre>
            </li>
            <li><b>svcscan</b>: 扫描系统服务，列出服务名称、显示名称、状态等信息，可发现异常或恶意服务。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 svcscan</pre>
            </li>
            <li><b>driverscan</b>: 使用池扫描技术查找内存中的驱动程序对象 (<i>DRIVER_OBJECT</i>)，可发现隐藏的驱动程序。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 driverscan</pre>
            </li>
            <li><b>printkey</b>: 打印指定的注册表项及其子项的内容，用于分析系统配置和应用程序设置。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 printkey -K "Software\\Microsoft\\Windows\\CurrentVersion\\Run"</pre>
            </li>
            <li><b>timeliner</b>: 从内存中提取各种带有时间戳的活动，生成系统事件的时间线，有助于理解事件发生的顺序。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 timeliner</pre>
            </li>
            <li><b>clipboard</b>: 提取剪贴板内容，可能包含用户复制的密码、URL等敏感信息。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 clipboard</pre>
            </li>
        </ul>
        """

    def load_advanced_knowledge(self):
        return """
        <h2>高级功能插件及其作用</h2>
        <ul>
            <li><b>apihooks</b>: 检测进程和内核中的API钩子，发现潜在的恶意代码注入和Rootkit活动。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 apihooks</pre>
            </li>
            <li><b>callbacks</b>: 显示系统注册的回调函数，可能被恶意软件用于持久化或监控系统活动。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 callbacks</pre>
            </li>
            <li><b>driverirp</b>: 检查驱动程序的IRP（I/O请求包）挂钩，发现Rootkit等恶意驱动程序。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 driverirp</pre>
            </li>
            <li><b>gditimers</b>: 显示GDI子系统的计时器，恶意软件可能利用这些计时器执行代码。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 gditimers</pre>
            </li>
            <li><b>handles</b>: 列出进程打开的句柄，包括文件、注册表键、互斥体等，有助于理解进程的行为。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 handles</pre>
            </li>
            <li><b>malfind</b>: 检测进程内存中可疑的代码注入或隐藏的恶意代码，扫描没有关联到磁盘文件的可执行内存区域。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 malfind</pre>
            </li>
            <li><b>modules</b>: 列出加载的内核模块（驱动程序），可发现隐藏的或未经签名的驱动程序。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 modules</pre>
            </li>
            <li><b>mutantscan</b>: 扫描互斥体对象（Mutex），恶意软件常用其进行进程间通信或防止重复感染。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 mutantscan</pre>
            </li>
            <li><b>privs</b>: 显示进程的权限，识别具有高权限的进程，可能存在权限提升。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 privs</pre>
            </li>
            <li><b>psxview</b>: 使用多种方法列出进程，比较结果以发现隐藏的进程或Rootkit。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 psxview</pre>
            </li>
            <li><b>ssdt</b>: 显示系统服务描述表（SSDT），检测系统调用被挂钩的情况，发现Rootkit。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 ssdt</pre>
            </li>
            <li><b>timers</b>: 列出内核中的计时器对象，恶意软件可能利用计时器进行代码执行或持久化。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 timers</pre>
            </li>
            <li><b>unloadedmodules</b>: 显示已卸载的内核模块，可能包含短暂加载的恶意驱动程序的痕迹。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 unloadedmodules</pre>
            </li>
            <li><b>vadinfo</b>: 显示进程的虚拟地址描述符（VAD）信息，有助于发现代码注入和隐藏的内存区域。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 vadinfo</pre>
            </li>
        </ul>
        """

    def load_system_knowledge(self):
        return """
        <h2>系统信息插件及其作用</h2>
        <ul>
            <li><b>imageinfo</b>: 获取内存映像的基本信息，包括操作系统版本、服务包、内核调试符号以及建议的profile。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp imageinfo</pre>
            </li>
            <li><b>kdbgscan</b>: 扫描内存中的KDDEBUGGER_DATA块，用于确定正确的profile，尤其在自动检测失败时。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp kdbgscan</pre>
            </li>
            <li><b>shutdowntime</b>: 显示系统的最后关机时间，有助于建立事件时间线。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp --profile=Win7SP1x64 shutdowntime</pre>
            </li>
            <li><b>verinfo</b>: 显示操作系统的版本信息，辅助验证所使用的profile是否正确。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp verinfo</pre>
            </li>
            <li><b>auditpol</b>: 显示系统的审计策略，了解哪些活动会被记录，评估日志完整性。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp auditpol</pre>
            </li>
            <li><b>shimcache</b>: 分析应用程序兼容性缓存，发现曾经执行过的程序，即使已被删除。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp shimcache</pre>
            </li>
        </ul>
        """

    def load_user_knowledge(self):
        return """
        <h2>用户信息插件及其作用</h2>
        <ul>
            <li><b>userassist</b>: 分析UserAssist注册表项，显示用户最近运行的程序列表。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp userassist</pre>
            </li>
            <li><b>hashdump</b>: 提取系统中用户的密码哈希，可用于离线破解密码。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp hashdump</pre>
            </li>
            <li><b>lsadump</b>: 提取本地安全机构（LSA）的秘密数据，可能包含密码和密钥。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp lsadump</pre>
            </li>
            <li><b>iehistory</b>: 提取Internet Explorer的浏览历史记录，了解用户的上网行为。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp iehistory</pre>
            </li>
            <li><b>chromehistory</b>: 提取Chrome浏览器的历史记录和下载记录。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp chromehistory</pre>
            </li>
            <li><b>firefoxhistory</b>: 提取Firefox浏览器的历史记录，分析用户的浏览活动。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp firefoxhistory</pre>
            </li>
        </ul>
        """

    def load_export_knowledge(self):
        return """
        <h2>文件导出插件及其作用</h2>
        <ul>
            <li><b>dumpfiles</b>: 从内存中提取文件，根据特定的筛选条件（如文件名、类型等）。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp dumpfiles -r ".*\\.docx$" -D output/</pre>
            </li>
            <li><b>procdump</b>: 导出指定进程的可执行映像，用于后续的恶意软件分析。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp procdump -p 1234 -D output/</pre>
            </li>
            <li><b>moddump</b>: 导出内核模块（驱动程序），用于分析可疑的驱动程序。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp moddump -m ntoskrnl.exe -D output/</pre>
            </li>
            <li><b>memdump</b>: 导出进程的所有内存空间，有助于深入分析进程的行为。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp memdump -p 1234 -D output/</pre>
            </li>
        </ul>
        <p>这些插件可以帮助取证分析人员快速提取内存中的重要文件和数据，以进行进一步的分析和取证。</p>
        """

    def load_extend_knowledge(self):
        return """
        <h2>扩展功能插件及其作用</h2>
        <ul>
            <li><b>mimikatz</b>: 集成了Mimikatz功能，从内存中提取明文密码、哈希和Kerberos票据等敏感信息。<br>
            <b>注意：</b>需要额外安装并配置相关插件。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp mimikatz</pre>
            </li>
            <li><b>malprocfind</b>: 高级的恶意进程检测插件，结合多种技术指标识别可疑进程。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp malprocfind</pre>
            </li>
            <li><b>yarascan</b>: 使用YARA规则扫描内存，发现符合特定模式的恶意代码或数据。<br>
            <b>示例用法：</b><pre>volatility -f memory.dmp yarascan -Y "rule malware {strings: $a = {6D 65 74 61 73 70 6C 6F 69 74} condition: $a}"</pre>
            </li>
        </ul>
        <p>这些扩展插件提供了更强大的分析能力，帮助取证分析人员深入挖掘内存中的潜在威胁和证据。</p>
        """
