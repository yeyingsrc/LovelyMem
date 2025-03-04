from PySide6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QGroupBox, 
                             QProgressDialog, QMessageBox, QDialog, QVBoxLayout,
                             QLineEdit, QLabel)
from PySide6.QtCore import Signal, QThread, Qt, QTimer
from plugin.quickcheck import QuickCheck, QuickCheckWorker

class RegexInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("输入搜索正则表达式")
        layout = QVBoxLayout(self)
        
        # 添加说明标签
        label = QLabel("请输入正则表达式，留空则使用默认表达式：\nflag{.+}|666c6167\\w+|ZmxhZ[\\w=]+|&#102.+")
        layout.addWidget(label)
        
        # 添加输入框
        self.regex_input = QLineEdit()
        self.regex_input.setPlaceholderText("输入正则表达式")
        layout.addWidget(self.regex_input)
        
        # 添加确定和取消按钮
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)

    def get_regex(self):
        return self.regex_input.text()

class FileMenuArea(QWidget):
    load_image_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_path = None
        self.quick_check_thread = None
        self.quick_check_worker = None
        self.quick_check_button = None
        self.is_searching = False
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group_box = QGroupBox("文件操作")
        group_layout = QHBoxLayout(group_box)
        
        load_image_button = QPushButton("加载镜像")
        unload_image_button = QPushButton("卸载镜像")
        self.quick_check_button = QPushButton("搜索镜像字符串")
        self.quick_check_button.setMinimumWidth(120)  # 设置最小宽度确保进度条显示效果
        
        group_layout.addWidget(load_image_button)
        group_layout.addWidget(unload_image_button)
        group_layout.addWidget(self.quick_check_button)
        
        layout.addWidget(group_box)
        
        load_image_button.clicked.connect(self.load_image_signal.emit)
        unload_image_button.clicked.connect(self.parent().unload_image)
        self.quick_check_button.clicked.connect(self.show_quick_check)

    def show_quick_check(self):
        if self.is_searching:
            if QMessageBox.question(self, "取消搜索", "是否要取消当前搜索？") == QMessageBox.Yes:
                self.cancel_quick_check()
            return

        if self.image_path is None:
            QMessageBox.warning(self, "错误", "未加载镜像文件")
            return

        dialog = RegexInputDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            regex = dialog.get_regex()
            self.start_search(regex)

    def start_search(self, regex):
        self.is_searching = True
        self.quick_check_button.setEnabled(False)
        self.set_button_progress(0)
        
        self.quick_check_thread = QThread()
        self.quick_check_worker = QuickCheckWorker(self.image_path, regex)
        self.quick_check_worker.moveToThread(self.quick_check_thread)

        self.quick_check_thread.started.connect(self.quick_check_worker.run)
        self.quick_check_worker.finished.connect(self.on_quick_check_finished)
        self.quick_check_worker.finished.connect(self.quick_check_thread.quit)
        self.quick_check_worker.progress.connect(self.update_search_progress)
        self.quick_check_worker.error.connect(self.show_error)

        self.quick_check_thread.start()

    def set_button_progress(self, value):
        style = f"""
        QPushButton {{
            text-align: center;
            padding: 4px;
            position: relative;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                      stop: 0 #007bff,
                                      stop: {value/100} #007bff,
                                      stop: {value/100} #f8f9fa,
                                      stop: 1 #f8f9fa);
            border: 1px solid #ced4da;
            border-radius: 4px;
        }}
        QPushButton:disabled {{
            color: #212529;
        }}
        """
        self.quick_check_button.setStyleSheet(style)
        self.quick_check_button.setText(f"搜索中... {int(value)}%")

    def update_search_progress(self, value):
        if self.is_searching:
            self.set_button_progress(value)

    def on_quick_check_finished(self):
        self.is_searching = False
        self.quick_check_button.setEnabled(True)
        self.quick_check_button.setStyleSheet("")
        self.quick_check_button.setText("搜索镜像字符串")
        
        if self.quick_check_worker:
            self.quick_check_worker.deleteLater()
        if self.quick_check_thread:
            self.quick_check_thread.deleteLater()
        self.quick_check_worker = None
        self.quick_check_thread = None

    def show_error(self, error_msg):
        self.is_searching = False
        self.quick_check_button.setEnabled(True)
        self.quick_check_button.setStyleSheet("")
        self.quick_check_button.setText("搜索镜像字符串")
        QMessageBox.critical(self, "错误", f"搜索过程中发生错误：{error_msg}")

    def cancel_quick_check(self):
        if self.quick_check_worker and self.is_searching:
            self.quick_check_worker.requestInterruption()
            self.quick_check_button.setText("正在取消...")
            self.is_searching = False

    def set_image_path(self, path):
        self.image_path = path

    def trigger_load_image(self):
        self.load_image_signal.emit()
