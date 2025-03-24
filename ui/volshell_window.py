from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                               QPushButton, QTextEdit, QLabel, QComboBox,
                               QMessageBox, QApplication, QSplitter, QFrame, QSizeGrip)
from PySide6.QtCore import Qt, QProcess, Signal, QObject, QTimer, QEvent, QPoint
from PySide6.QtGui import QFont, QTextCursor, QColor, QIcon
import os
import yaml
import sys
import time
import re

# 导入样式相关变量
from ui.styles import (
    background_color, text_color, button_bg_color, button_text_color, 
    button_hover_color, border_color, group_title_bg_color, cmd_output_bg_color,
    cmd_output_text_color, current_font_family, minimize_button_color, close_button_color
)

class VolshellProcess(QObject):
    outputReady = Signal(str)
    errorReady = Signal(str)
    finished = Signal(int, QProcess.ExitStatus)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = QProcess(self)
        
        # 使用信号连接捕获输出
        self.process.readyReadStandardOutput.connect(self._read_stdout)
        self.process.readyReadStandardError.connect(self._read_stderr)
        self.process.finished.connect(self._process_finished)
        
        # 强制不缓冲标准输出
        self.process.setProcessChannelMode(QProcess.SeparateChannels)
        
        # 输出处理变量
        self.output_buffer = ""
        self.is_running = False
        
        # 每次发送命令后，确保能及时读取输出的定时器
        self.flush_timer = QTimer(self)
        self.flush_timer.timeout.connect(self._flush_output)
        self.flush_timer.setSingleShot(True)
        
    def _read_stdout(self):
        """立即读取标准输出"""
        if self.process and self.process.state() == QProcess.Running:
            data = self.process.readAllStandardOutput().data().decode('utf-8', errors='replace')
            if data:
                self.outputReady.emit(data)
                QApplication.processEvents()  # 立即处理事件，确保UI更新
                
    def _read_stderr(self):
        """立即读取标准错误"""
        if self.process and self.process.state() == QProcess.Running:
            data = self.process.readAllStandardError().data().decode('utf-8', errors='replace')
            if data:
                self.errorReady.emit(data)
                QApplication.processEvents()  # 立即处理事件，确保UI更新
                
    def _flush_output(self):
        """强制刷新任何可能的输出"""
        if self.process and self.process.state() == QProcess.Running:
            if self.process.bytesAvailable() > 0:
                self._read_stdout()
            # 修复方法名错误，PySide6没有bytesAvailableFromStandardError方法
            # 错误写法: if self.process.bytesAvailableFromStandardError() > 0:
            # 注意：在SeparateChannels模式下，bytesAvailable()只读取标准输出，所以需要专门处理标准错误
            try:
                # 尝试直接读取错误流，如果有数据会触发_read_stderr
                self.process.readAllStandardError()
            except:
                pass
                
    def _process_finished(self, exit_code, exit_status):
        """处理进程结束事件"""
        self.is_running = False
        self.flush_timer.stop()
        
        # 确保读取所有剩余输出
        self._flush_output()
        
        # 发出完成信号
        self.finished.emit(exit_code, exit_status)
        
    def start(self, program, arguments=[]):
        """启动进程"""
        try:
            # 设置环境变量强制Python不缓冲
            env = QProcess.systemEnvironment()
            env.append("PYTHONUNBUFFERED=1")
            env.append("PYTHONIOENCODING=utf-8")
            self.process.setEnvironment(env)
            
            # 设置工作目录
            self.process.setWorkingDirectory(os.getcwd())
            
            # 启动进程
            self.process.start(program, arguments)
            success = self.process.waitForStarted(5000)
            
            if success:
                self.is_running = True
            
            return success
        except Exception as e:
            self.errorReady.emit(f"启动失败: {str(e)}")
            return False
            
    def write(self, data):
        """向进程写入数据"""
        if not self.is_running or not self.process:
            return False
            
        try:
            # 确保命令以换行符结束
            if not data.endswith('\n'):
                data += '\n'
                
            # 将命令转换为字节并写入进程
            bytes_data = data.encode('utf-8')
            self.process.write(bytes_data)
            self.process.waitForBytesWritten(1000)  # 等待数据写入完成
            
            # 设置定时器执行多次刷新，确保能读取到命令的响应
            # 这里采用多次尝试的策略，因为响应可能会延迟
            for delay in [50, 100, 200, 500]:
                QTimer.singleShot(delay, self._flush_output)
                
            return True
        except Exception as e:
            self.errorReady.emit(f"写入命令失败: {str(e)}")
            return False
            
    def terminate(self):
        """终止进程"""
        if not self.is_running or not self.process:
            return
            
        try:
            # 停止刷新定时器
            self.flush_timer.stop()
            
            # 尝试先发送exit()命令
            try:
                self.write("exit()")
                # 给一点时间让进程退出
                self.process.waitForFinished(2000)
            except:
                pass
                
            # 如果进程仍在运行，强制终止
            if self.process.state() == QProcess.Running:
                self.process.terminate()
                if not self.process.waitForFinished(2000):
                    self.process.kill()
        except Exception as e:
            self.errorReady.emit(f"终止进程时出错: {str(e)}")
        finally:
            self.is_running = False


class VolshellWindow(QWidget):
    def __init__(self, mem_path, profile, parent=None):
        super().__init__(parent, Qt.Window)  # 使用Qt.Window标志创建顶级窗口
        self.mem_path = mem_path
        self.profile = profile
        self.volshell_process = None
        self.command_history = []
        self.history_index = -1
        self.current_command = ""
        self._destroyed = False
        
        self.setAttribute(Qt.WA_DeleteOnClose, True)  # 确保窗口关闭时被删除
        self.setWindowTitle("Volshell 交互终端")
        self.setWindowFlags(Qt.FramelessWindowHint)  # 移除原生标题栏
        self.setAttribute(Qt.WA_TranslucentBackground)  # 启用窗口背景透明
        self.resize(800, 600)
        
        # 用于移动窗口的变量
        self.dragging = False
        self.drag_position = QPoint()
        
        self.setup_ui()
        self.load_config()
        
        # 应用样式
        self.apply_style()
        
        # 设置字体
        self.apply_font()
        
        # 监听主题变化
        QApplication.instance().paletteChanged.connect(self.on_theme_changed)

    def load_config(self):
        try:
            with open('config/base_config.yaml', 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            self.python27 = os.path.abspath(config['base_tools']['python27']['path'])
            self.volatility2 = os.path.abspath(config['tools']['volatility2_python']['path'])
            self.volatility2_plugin = os.path.abspath(config['tools']['volatility2_plugin']['path'])
        except Exception as e:
            self.append_output(f"加载配置失败: {str(e)}", error=True)
            self.python27 = ""
            self.volatility2 = ""
            self.volatility2_plugin = ""

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)  # 设置边距，为圆角留出空间
        main_layout.setSpacing(0)
        
        # 创建内容容器（带圆角的主窗口）
        self.content_container = QWidget()
        self.content_container.setObjectName("contentContainer")
        container_layout = QVBoxLayout(self.content_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # 创建自定义标题栏
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(30)
        self.title_bar.setObjectName("titleBar")
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        
        # 添加图标
        icon_label = QLabel()
        icon_label.setPixmap(QIcon('res/logo.ico').pixmap(20, 20))
        title_layout.addWidget(icon_label)
        
        # 添加标题
        title_label = QLabel("Volshell 交互终端")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 添加最小化按钮
        self.min_button = self.create_circle_button(minimize_button_color)
        self.min_button.clicked.connect(self.showMinimized)
        self.min_button.setToolTip("最小化")
        
        # 添加关闭按钮
        self.close_button = self.create_circle_button(close_button_color)
        self.close_button.clicked.connect(self.close)
        self.close_button.setToolTip("关闭")
        
        title_layout.addWidget(self.min_button)
        title_layout.addWidget(self.close_button)
        
        container_layout.addWidget(self.title_bar)
        
        # 创建内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # 顶部控制区域
        control_layout = QHBoxLayout()
        
        # 进程选择
        self.pid_label = QLabel("进程 PID:")
        self.pid_input = QLineEdit()
        self.pid_input.setPlaceholderText("输入PID (可选)")
        control_layout.addWidget(self.pid_label)
        control_layout.addWidget(self.pid_input)
        
        # 启动按钮
        self.start_button = QPushButton("启动 Volshell")
        self.start_button.clicked.connect(self.start_volshell)
        control_layout.addWidget(self.start_button)
        
        # 停止按钮
        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self.stop_volshell)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)
        
        content_layout.addLayout(control_layout)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 输出区域
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 10))
        splitter.addWidget(self.output_text)
        
        # 底部区域包含输入框和快捷命令
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        # 输入区域
        input_layout = QHBoxLayout()
        self.prompt_label = QLabel(">>>")
        self.prompt_label.setFont(QFont("Consolas", 10))
        
        self.input_line = QLineEdit()
        self.input_line.setFont(QFont("Consolas", 10))
        self.input_line.setPlaceholderText("输入 volshell 命令...")
        self.input_line.returnPressed.connect(self.send_command)
        self.input_line.setEnabled(False)
        
        # 添加上下键历史记录导航
        self.input_line.installEventFilter(self)
        
        input_layout.addWidget(self.prompt_label)
        input_layout.addWidget(self.input_line)
        
        bottom_layout.addLayout(input_layout)
        
        # 添加常用命令按钮区域
        cmd_buttons_frame = QFrame()
        cmd_buttons_frame.setObjectName("cmdButtonsFrame")
        cmd_buttons_layout = QVBoxLayout(cmd_buttons_frame)
        cmd_buttons_layout.setContentsMargins(0, 5, 0, 5)
        
        # 添加标题
        cmd_buttons_title = QLabel("常用命令按钮:")
        cmd_buttons_title.setObjectName("cmdButtonsTitle")
        cmd_buttons_layout.addWidget(cmd_buttons_title)
        
        # 创建按钮网格布局
        from PySide6.QtWidgets import QGridLayout
        cmd_grid = QGridLayout()
        cmd_grid.setSpacing(5)
        
        # 定义命令按钮
        command_buttons = [
            ("addrspace()", "获取内核/虚拟地址空间"),
            ("addrspace().base", "获取物理地址空间"),
            ("proc()", "获取当前进程对象"),
            ("proc().get_process_address_space()", "获取当前进程地址空间"),
            ("proc().get_load_modules()", "获取当前进程DLL"),
            ("cc()", "切换当前上下文"),
            ("db(addr)", "以十六进制打印字节"),
            ("dd(addr)", "打印dwords"),
            ("dq(addr)", "打印qwords"),
            ("dt(\"_EPROCESS\")", "显示对象或类型信息"),
            ("dis(addr)", "反汇编代码"),
            ("ps()", "显示活动进程"),
            ("modules()", "显示加载的模块"),
            ("getprocs()", "获取进程对象生成器"),
            ("getmods()", "获取内核模块生成器"),
            ("sc()", "显示当前上下文"),
            ("hh()", "获取命令帮助"),
            ("list_entry()", "遍历_LIST_ENTRY")
        ]
        
        # 创建按钮并添加到网格
        self.cmd_buttons = []
        row, col = 0, 0
        max_cols = 3  # 每行最多3个按钮
        
        for cmd, tooltip in command_buttons:
            btn = QPushButton(cmd)
            btn.setToolTip(tooltip)
            btn.setProperty("command", cmd)
            btn.clicked.connect(self.insert_command_from_button)
            btn.setEnabled(False)
            self.cmd_buttons.append(btn)
            
            cmd_grid.addWidget(btn, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        cmd_buttons_layout.addLayout(cmd_grid)
        bottom_layout.addWidget(cmd_buttons_frame)
        
        splitter.addWidget(bottom_widget)
        
        # 设置分割器初始大小
        splitter.setSizes([400, 200])
        
        content_layout.addWidget(splitter)
        
        container_layout.addWidget(content_widget)
        
        # 添加大小调整手柄
        size_grip = QSizeGrip(self.content_container)
        size_grip.setFixedSize(16, 16)
        
        # 创建一个布局来放置大小调整手柄在右下角
        grip_layout = QHBoxLayout()
        grip_layout.setContentsMargins(0, 0, 0, 0)
        grip_layout.addStretch()
        grip_layout.addWidget(size_grip)
        
        container_layout.addLayout(grip_layout)
        
        # 添加内容容器到主布局
        main_layout.addWidget(self.content_container)
    
    def create_circle_button(self, color):
        """创建圆形按钮"""
        button = QPushButton()
        button.setFixedSize(16, 16)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {self.lighten_color(color)};
            }}
        """)
        return button
    
    def lighten_color(self, color, amount=20):
        """使颜色变亮"""
        if color.startswith("rgba("):
            parts = color.strip("rgba()").split(",")
            r = min(255, int(parts[0]) + amount)
            g = min(255, int(parts[1]) + amount)
            b = min(255, int(parts[2]) + amount)
            a = parts[3]
            return f"rgba({r}, {g}, {b}, {a})"
        elif color.startswith("#"):
            r = min(255, int(color[1:3], 16) + amount)
            g = min(255, int(color[3:5], 16) + amount)
            b = min(255, int(color[5:7], 16) + amount)
            return f"#{r:02x}{g:02x}{b:02x}"
        return color
    
    def apply_style(self):
        """应用样式"""
        # 从ui.styles重新导入最新的颜色变量，确保获取到最新的主题颜色
        from ui.styles import (
            background_color, text_color, button_bg_color, button_text_color, 
            button_hover_color, border_color, group_title_bg_color, cmd_output_bg_color,
            cmd_output_text_color
        )
        
        # 设置全局样式
        self.setStyleSheet(f"""
            QWidget {{
                color: {text_color};
            }}
            
            #contentContainer {{
                background-color: {background_color};
                border-radius: 10px;
                border: 1px solid {border_color};
            }}
            
            #titleBar {{
                background-color: {group_title_bg_color};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom: 1px solid {border_color};
            }}
            
            #cmdButtonsFrame {{
                background-color: {background_color};
                border: 1px solid {border_color};
                border-radius: 5px;
                padding: 5px;
            }}
            
            #cmdButtonsTitle {{
                color: {text_color};
                font-weight: bold;
                background-color: transparent;
            }}
            
            QLabel {{
                color: {text_color};
                background-color: transparent;
            }}
            
            QPushButton {{
                background-color: {button_bg_color};
                color: {button_text_color};
                border: 1px solid {border_color};
                border-radius: 3px;
                padding: 5px;
            }}
            
            QPushButton:hover {{
                background-color: {button_hover_color};
            }}
            
            QPushButton:disabled {{
                background-color: {button_bg_color};
                color: rgba(200, 200, 200, 100);
                border: 1px solid rgba(100, 100, 100, 100);
            }}
            
            QLineEdit {{
                background-color: {cmd_output_bg_color};
                color: {cmd_output_text_color};
                border: 1px solid {border_color};
                border-radius: 3px;
                padding: 3px;
            }}
            
            QLineEdit:disabled {{
                background-color: rgba(50, 50, 50, 100);
                color: rgba(200, 200, 200, 100);
            }}
            
            QTextEdit {{
                background-color: {cmd_output_bg_color};
                color: {cmd_output_text_color};
                border: 1px solid {border_color};
                border-radius: 3px;
            }}
            
            QComboBox {{
                background-color: {button_bg_color};
                color: {button_text_color};
                border: 1px solid {border_color};
                border-radius: 3px;
                padding: 3px;
            }}
            
            QComboBox:disabled {{
                background-color: rgba(50, 50, 50, 100);
                color: rgba(200, 200, 200, 100);
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {cmd_output_bg_color};
                color: {cmd_output_text_color};
                selection-background-color: {button_hover_color};
                selection-color: {button_text_color};
            }}
            
            QSplitter::handle {{
                background-color: {border_color};
            }}
            
            QSplitter::handle:horizontal {{
                width: 1px;
            }}
            
            QSplitter::handle:vertical {{
                height: 1px;
            }}
            
            QSizeGrip {{
                background-color: transparent;
            }}
        """)
        
        # 为提示符设置特殊样式
        self.prompt_label.setStyleSheet(f"color: #569CD6; background-color: transparent;")
        
        # 更新最小化和关闭按钮的样式
        if hasattr(self, 'min_button') and hasattr(self, 'close_button'):
            self.min_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {minimize_button_color};
                    border-radius: 8px;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {self.lighten_color(minimize_button_color)};
                }}
            """)
            
            self.close_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {close_button_color};
                    border-radius: 8px;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {self.lighten_color(close_button_color)};
                }}
            """)
    
    def apply_font(self):
        """应用字体"""
        # 从ui.styles重新导入最新的字体变量
        from ui.styles import current_font_family
        
        # 使用等宽字体作为终端显示
        term_font = QFont("Consolas", 10)
        self.output_text.setFont(term_font)
        self.input_line.setFont(term_font)
        self.prompt_label.setFont(term_font)
        
        # 使用系统默认字体作为界面字体
        ui_font = QFont(current_font_family, 9)
        self.pid_label.setFont(ui_font)
        self.start_button.setFont(ui_font)
        self.stop_button.setFont(ui_font)
    
    def on_theme_changed(self):
        """主题变化时更新样式"""
        # 更新样式
        self.apply_style()
        
        # 更新字体
        self.apply_font()
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件，用于移动窗口"""
        if event.button() == Qt.LeftButton and self.title_bar.geometry().contains(event.position().toPoint()):
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件，用于移动窗口"""
        if event.buttons() & Qt.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件，结束窗口移动"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def eventFilter(self, obj, event):
        if obj is self.input_line and event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Up:
                self.navigate_history(-1)  # 向上导航历史
                return True
            elif key == Qt.Key_Down:
                self.navigate_history(1)  # 向下导航历史
                return True
        return super().eventFilter(obj, event)
    
    def navigate_history(self, direction):
        if not self.command_history:
            return
            
        if direction < 0:  # 向上
            if self.history_index == -1:
                # 保存当前输入
                self.current_command = self.input_line.text()
                self.history_index = len(self.command_history) - 1
            else:
                self.history_index = max(0, self.history_index - 1)
            self.input_line.setText(self.command_history[self.history_index])
        else:  # 向下
            if self.history_index == -1:
                return
            self.history_index += 1
            if self.history_index >= len(self.command_history):
                self.history_index = -1
                self.input_line.setText(self.current_command)
            else:
                self.input_line.setText(self.command_history[self.history_index])
    
    def start_volshell(self):
        try:
            if self.volshell_process is not None:
                self.stop_volshell()
                
            self.output_text.clear()
            self.append_output("正在启动 volshell...\n")
            
            # 构建volshell命令
            # 添加-u参数禁用Python输出缓冲
            python_cmd = [self.python27, "-u"]
            cmd = [self.volatility2]
            cmd.extend([f'--plugin={self.volatility2_plugin}'])
            cmd.extend(['-f', self.mem_path])
            cmd.extend([f'--profile={self.profile}'])
            cmd.append('volshell')
            
            # 如果指定了PID，添加-p参数
            pid = self.pid_input.text().strip()
            if pid:
                cmd.extend(['-p', pid])
            
            # 将完整命令行用于显示目的
            display_cmd = python_cmd + cmd
            self.append_output(f"执行命令: {' '.join(display_cmd)}\n")
            
            # 创建进程
            self.volshell_process = VolshellProcess(self)
            self.volshell_process.outputReady.connect(self.handle_output)
            self.volshell_process.errorReady.connect(lambda text: self.handle_output(text, error=True))
            self.volshell_process.finished.connect(self.handle_finished)
            
            # 启动进程
            success = self.volshell_process.start(python_cmd[0], python_cmd[1:] + cmd)
            
            # 更新UI状态
            if success:
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.input_line.setEnabled(True)
                
                # 启用所有命令按钮
                for btn in self.cmd_buttons:
                    btn.setEnabled(True)
                    
                self.input_line.setFocus()
            else:
                self.append_output("启动volshell失败\n", error=True)
            
        except Exception as e:
            self.append_output(f"启动volshell失败: {str(e)}", error=True)
    
    def stop_volshell(self):
        if self.volshell_process:
            self.append_output("\n正在停止 volshell...\n")
            self.volshell_process.terminate()
            self.volshell_process = None
        
        # 更新UI状态
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.input_line.setEnabled(False)
        
        # 禁用所有命令按钮
        for btn in self.cmd_buttons:
            btn.setEnabled(False)
    
    def send_command(self):
        if not self.volshell_process:
            return
            
        command = self.input_line.text().strip()
        if not command:
            return
            
        # 添加到历史记录
        if not self.command_history or self.command_history[-1] != command:
            self.command_history.append(command)
        self.history_index = -1
        
        # 在输出区域显示命令（手动显示，因为QProcess不会自动回显）
        self.append_output(f">>> {command}\n", command=True)
        
        # 发送命令到进程
        self.volshell_process.write(command)
        
        # 清空输入框
        self.input_line.clear()
    
    def handle_output(self, text, error=False):
        self.append_output(text, error=error)
    
    def handle_finished(self, exit_code, exit_status):
        if exit_code != 0:
            self.append_output(f"\nVolshell进程异常退出，退出代码: {exit_code}\n", error=True)
        else:
            self.append_output("\nVolshell进程已正常退出\n")
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.input_line.setEnabled(False)
        
        # 禁用所有命令按钮
        for btn in self.cmd_buttons:
            btn.setEnabled(False)
        
        self.volshell_process = None
    
    def append_output(self, text, error=False, command=False):
        if self._destroyed:
            return
            
        # 保存当前滚动位置
        scrollbar = self.output_text.verticalScrollBar()
        was_at_bottom = scrollbar.value() == scrollbar.maximum()
        
        # 获取当前光标
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # 根据是否为错误设置颜色
        format = cursor.charFormat()
        if error:
            format.setForeground(QColor("#FF6B68"))  # 红色
        elif command:
            format.setForeground(QColor("#569CD6"))  # 蓝色
        else:
            # 使用来自样式的颜色
            from ui.styles import cmd_output_text_color
            format.setForeground(QColor(cmd_output_text_color))
        
        cursor.setCharFormat(format)
        cursor.insertText(text)
        
        # 如果之前在底部，保持在底部
        if was_at_bottom:
            scrollbar.setValue(scrollbar.maximum())
    
    def isDestroyed(self):
        """检查窗口是否已销毁"""
        return self._destroyed
    
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # 当窗口关闭时，确保进程也被终止
        self._destroyed = True
        if self.volshell_process:
            self.volshell_process.terminate()
            self.volshell_process = None
            
        super().closeEvent(event)

    def insert_command_from_button(self):
        """从按钮插入命令"""
        if not self.input_line.isEnabled():
            return
            
        sender = self.sender()
        if sender:
            command = sender.property("command")
            if command:
                # 获取当前光标位置
                cursor_pos = self.input_line.cursorPosition()
                current_text = self.input_line.text()
                
                # 在光标位置插入命令
                new_text = current_text[:cursor_pos] + command + current_text[cursor_pos:]
                self.input_line.setText(new_text)
                
                # 将光标移动到插入的命令后面
                self.input_line.setCursorPosition(cursor_pos + len(command))
                
                # 设置焦点回到输入框
                self.input_line.setFocus()
