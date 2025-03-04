import os
import hashlib
import json
import urllib.request
from tqdm import tqdm
from urllib.parse import urljoin, quote
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QProgressBar, QLabel, QMessageBox, QTextEdit, QPushButton, QDialog, QHBoxLayout, QFrame
from PySide6.QtCore import Qt, Signal, QObject, QThread, QProcess, QPoint
from PySide6.QtGui import QIcon, QMouseEvent, QColor
import subprocess

class UpdateSignals(QObject):
    total_progress = Signal(int, str)
    file_progress = Signal(int, str)
    finished = Signal(bool, str)
    execute_command = Signal(str)
    command_output = Signal(str)
    command_finished = Signal()
    show_command_confirmation = Signal(list)  # 新增信号

class UpdateWorker(QThread):
    def __init__(self, update_url, download_base_url, update_directory, post_update_commands_url):
        super().__init__()
        self.update_url = update_url
        self.download_base_url = download_base_url
        self.update_directory = update_directory
        self.post_update_commands_url = post_update_commands_url
        self.signals = UpdateSignals()
        self.command_confirmed = False

    def run(self):
        has_updates = update_components(self.update_url, self.download_base_url, self.update_directory, self.post_update_commands_url, self.signals)
        self.signals.finished.emit(has_updates, "更新完成" if has_updates else "没有发现新的更新内容")

class UpdateWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)  # 移除原生标题栏
        self.setAttribute(Qt.WA_TranslucentBackground, False)  # 启用窗口背景透明
        self.setFixedSize(500, 400)
        self.setup_ui()
        
        # 用于移动窗口的变量
        self.dragging = False
        self.drag_position = QPoint()


    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建自定义标题栏
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(30)
        # 修改标题栏的样式
        self.title_bar.setStyleSheet("""
            background-color: #FFFFFF;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        """)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        
        # 添加图标
        icon_label = QLabel()
        icon_label.setPixmap(QIcon('res/logo.ico').pixmap(20, 20))
        title_layout.addWidget(icon_label)
        
        # 添加标题，并设置样式为黑色
        title_label = QLabel("LovelyMem 更新程序")
        title_label.setStyleSheet("color: black; font-weight: bold;")  # 设置标题文字为黑色和粗体
        title_layout.addWidget(title_label)

        title_layout.addStretch()
        
        # 添加关闭按钮
        close_button = self.create_circle_button("rgba(255, 235, 238, 0.9)")
        close_button.clicked.connect(self.close)
        
        title_layout.addWidget(close_button)
        
        layout.addWidget(self.title_bar)

        # 添加原有的UI组件
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)

        self.total_status_label = QLabel("总体更新进度", self)
        content_layout.addWidget(self.total_status_label)

        self.total_progress_bar = QProgressBar(self)
        self.total_progress_bar.setRange(0, 100)
        self.total_progress_bar.setTextVisible(True)
        content_layout.addWidget(self.total_progress_bar)

        self.file_status_label = QLabel("当前文件进度", self)
        content_layout.addWidget(self.file_status_label)

        self.file_progress_bar = QProgressBar(self)
        self.file_progress_bar.setRange(0, 100)
        self.file_progress_bar.setTextVisible(True)
        content_layout.addWidget(self.file_progress_bar)

        self.command_output = QTextEdit(self)
        self.command_output.setReadOnly(True)
        self.command_output.setMinimumHeight(200)
        content_layout.addWidget(self.command_output)

        layout.addWidget(content_widget)

    def create_circle_button(self, base_color):
        button = QPushButton()
        button.setFixedSize(12, 12)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {base_color};
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: rgba{QColor(base_color).darker(110).getRgb()};
            }}
        """)
        return button

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if self.title_bar.geometry().contains(event.position().toPoint()):  # 使用 position() 替代 pos()
                self.dragging = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()  # 使用 globalPosition() 替代 globalPos()
                event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)  # 使用 globalPosition() 替代 globalPos()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.dragging = False
        super().mouseReleaseEvent(event)

    def update_total_progress(self, value, status):
        self.total_progress_bar.setValue(value)
        self.total_status_label.setText(status)

    def update_file_progress(self, value, status):
        self.file_progress_bar.setValue(value)
        self.file_status_label.setText(status)

    def append_command_output(self, output):
        self.command_output.append(output)
        self.command_output.verticalScrollBar().setValue(self.command_output.verticalScrollBar().maximum())

    def show_result(self, has_updates, message):
        QMessageBox.information(self, "更新结果", message)
        self.close()

class CommandExecutionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(300, 200)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 230, 240, 0.8);
                border-radius: 10px;
            }
            QLabel, QTextEdit {
                color: #333333;
                font-family: '幼圆', 'YouYuan', 'Microsoft YaHei', 'SimHei', sans-serif;
                font-size: 12px;
            }
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid #ffb3c6;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: rgba(255, 200, 210, 0.9);
                border-radius: 5px;
            }
        """)

        self.status_label = QLabel("正在执行命令", self)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)  # 设置为循环进度条
        layout.addWidget(self.progress_bar)

        self.output_text = QTextEdit(self)
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

    def update_status(self, status):
        self.status_label.setText(status)

    def append_output(self, output):
        self.output_text.append(output)
        self.output_text.verticalScrollBar().setValue(self.output_text.verticalScrollBar().maximum())

class CommandConfirmationDialog(QDialog):
    def __init__(self, commands):
        super().__init__()
        self.setWindowTitle("确认执行命令")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        label = QLabel("以下命令将被执行，是否继续？")
        layout.addWidget(label)
        
        command_list = QTextEdit()
        command_list.setReadOnly(True)
        command_list.setText("\n".join(commands))
        layout.addWidget(command_list)
        
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_file(url, destination, signals):
    with urllib.request.urlopen(url) as response, open(destination, 'wb') as out_file:
        file_size = int(response.getheader('Content-Length').strip())
        chunk_size = 4096
        downloaded = 0
        for chunk in iter(lambda: response.read(chunk_size), b''):
            out_file.write(chunk)
            downloaded += len(chunk)
            progress = int((downloaded / file_size) * 100)
            signals.file_progress.emit(progress, f"正在下载: {os.path.basename(destination)}")

def update_components(update_url, download_base_url, update_directory, post_update_commands_url, signals):
    with urllib.request.urlopen(update_url) as response:
        update_list = json.load(response)
    
    total_files = len(update_list)
    has_updates = False
    for index, item in enumerate(update_list, 1):
        file_path = os.path.join(update_directory, item['file'])
        file_md5 = item['md5']
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        if os.path.exists(file_path):
            local_md5 = calculate_md5(file_path)
            if local_md5 == file_md5:
                signals.total_progress.emit(int((index / total_files) * 100), f"总进度: {index}/{total_files}")
                signals.file_progress.emit(100, f"文件 {os.path.basename(file_path)} 已是最新")
                continue
        
        has_updates = True
        file_url = urljoin(download_base_url, quote(item['file'].replace('\\', '/')))
        download_file(file_url, file_path, signals)
        
        downloaded_md5 = calculate_md5(file_path)
        if downloaded_md5 != file_md5:
            signals.file_progress.emit(100, f"文件 {os.path.basename(file_path)} MD5校验失败")
        else:
            signals.file_progress.emit(100, f"文件 {os.path.basename(file_path)} 更新成功")
        
        signals.total_progress.emit(int((index / total_files) * 100), f"总进度: {index}/{total_files}")
    
    if post_update_commands_url:
        signals.file_progress.emit(0, "正在获取更新后命令")
        try:
            with urllib.request.urlopen(post_update_commands_url) as response:
                commands = json.load(response)
            
            if commands:
                signals.show_command_confirmation.emit(commands)
                # 等待用户确认
                while not hasattr(signals, 'command_confirmed'):
                    QThread.msleep(100)
                
                if signals.command_confirmed:
                    for i, command in enumerate(commands, 1):
                        signals.execute_command.emit(f"正在执行命令 {i}/{len(commands)}: {command}")
                        try:
                            process = subprocess.Popen(
                                command,
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True,
                                bufsize=1,
                                universal_newlines=True
                            )
                            
                            while True:
                                output = process.stdout.readline()
                                if output == '' and process.poll() is not None:
                                    break
                                if output:
                                    signals.command_output.emit(output.strip())
                            
                            rc = process.poll()
                            if rc == 0:
                                signals.command_output.emit(f"命令 {i}/{len(commands)} 执行成功")
                            else:
                                signals.command_output.emit(f"命令 {i}/{len(commands)} 执行失败，返回码: {rc}")
                        except Exception as e:
                            signals.command_output.emit(f"命令 {i}/{len(commands)} 执行出错: {str(e)}")
                    
                    signals.command_output.emit("所有命令执行完毕")
                    signals.command_finished.emit()
                    has_updates = True
                else:
                    signals.command_output.emit("用户取消了命令执行")
            else:
                signals.file_progress.emit(100, "没有需要执行的命令")
            
        except Exception as e:
            signals.file_progress.emit(100, f"获取或执行更新后命令失败: {str(e)}")
    
    return has_updates

def start_update(url):
    app = QApplication([])
    update_window = UpdateWindow()
    update_window.setWindowTitle("LovelyMem 更新程序")
    update_window.show()
    update_json_url = url + 'lovelymem/update_list_new.json'
    base_download_url = url + 'lovelymem/update_new/'
    update_directory_path = '.'
    post_update_commands_url = url + 'lovelymem/post_update_commands.json'

    worker = UpdateWorker(update_json_url, base_download_url, update_directory_path, post_update_commands_url)
    worker.signals.total_progress.connect(update_window.update_total_progress)
    worker.signals.file_progress.connect(update_window.update_file_progress)
    worker.signals.finished.connect(update_window.show_result)
    worker.signals.execute_command.connect(lambda cmd: update_window.update_file_progress(0, cmd))
    worker.signals.command_output.connect(update_window.append_command_output)
    
    def show_command_confirmation(commands):
        dialog = CommandConfirmationDialog(commands)
        if dialog.exec() == QDialog.Accepted:
            worker.signals.command_confirmed = True
        else:
            worker.signals.command_confirmed = False
    
    worker.signals.show_command_confirmation.connect(show_command_confirmation)

    # kill task lovelymem.exe
    worker.signals.command_finished.connect(lambda: os.system('taskkill /im lovelymem.exe /f'))
    
    
    worker.start()

    app.exec()

if __name__ == "__main__":
    url = open('updateurl.txt', 'r').read()
    start_update(url)
