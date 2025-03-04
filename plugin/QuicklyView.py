from PySide6.QtWidgets import (QMessageBox, QWidget, QListWidget, QVBoxLayout, QDialog, QHBoxLayout, 
                               QLineEdit, QPushButton, QTextEdit, QInputDialog, QGroupBox, QSplitter, QListWidgetItem)
from PySide6.QtCore import Qt, QRect
from PySide6 import QtGui, QtWidgets
from PySide6.QtWidgets import QApplication
import chardet
import ui.styles
import sys
import traceback

class QuicklyView(QDialog):  # 改为继承 QDialog
    def __init__(self, title, size=(800, 600)):
        try:
            super().__init__()
            self.setStyleSheet(ui.styles.newtable_widget_style)
            self.resize(*size)
            self.setWindowTitle(title)
            self.setWindowIcon(QtGui.QIcon('res/logo.ico'))

            self.layout = QVBoxLayout(self)

            # 创建一个垂直分割器
            splitter = QSplitter(Qt.Vertical)

            # 添加文本编辑器到分割器
            self.textEdit = QTextEdit(self)
            self.textEdit.setReadOnly(True)
            self.textEdit.setTextInteractionFlags(Qt.TextSelectableByMouse)
            splitter.addWidget(self.textEdit)

            # 创建一个 QGroupBox 来包含搜索结果列表
            search_results_group = QGroupBox("搜索结果")
            search_results_layout = QVBoxLayout()
            self.search_results_list = QListWidget()
            self.search_results_list.itemDoubleClicked.connect(self.jump_to_result)
            search_results_layout.addWidget(self.search_results_list)
            search_results_group.setLayout(search_results_layout)

            # 将 QGroupBox 添加到分割器
            splitter.addWidget(search_results_group)

            # 设置分割器的初始大小比例
            splitter.setStretchFactor(0, 3)  # 文本编辑器占3份
            splitter.setStretchFactor(1, 1)  # 搜索结果列表占1份

            # 默认隐藏搜索结果组
            search_results_group.hide()

            self.layout.addWidget(splitter)

            # 搜索框和按钮放在底部
            search_layout = QHBoxLayout()
            self.lineEdit_str = QLineEdit()
            self.search_button = QPushButton('搜索')
            self.search_button.clicked.connect(self.findstr)
            search_layout.addWidget(self.lineEdit_str)
            search_layout.addWidget(self.search_button)

            self.reload_button = QPushButton('重新加载')
            self.reload_button.clicked.connect(self.show_encoding_dialog)
            search_layout.addWidget(self.reload_button)

            self.layout.addLayout(search_layout)

            self.setLayout(self.layout)
            
            self.file_path = None

        except Exception as e:
            self.show_error_message(f"初始化 QuicklyView 时发生错误：{str(e)}")
            raise

    def show_error_message(self, message):
        print(f"错误：{message}")
        print("错误详情：")
        traceback.print_exc()
        QMessageBox.critical(None, "错误", message)

    def load_file_content(self, file):
        try:
            self.file_path = file
            encodings = ['utf-8', 'gbk', 'gb2312', 'iso-8859-1', 'utf-16', 'ascii']
            content = None

            # 首先尝试自动检测编码
            with open(file, 'rb') as f:
                raw_data = f.read()
            detected = chardet.detect(raw_data)
            detected_encoding = detected['encoding']

            if detected_encoding:
                encodings.insert(0, detected_encoding)

            for encoding in encodings:
                try:
                    with open(file, 'r', encoding=encoding) as f:
                        content = f.read()
                    print(f"成功使用 {encoding} 编码读取文件")
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                try:
                    # 尝试以二进制模式读取文件
                    content = raw_data.decode('utf-8', errors='replace')
                    print("文件可能包含二进制数据，已尝试强制解码")
                except Exception as e:
                    error_message = f"无法读取文件 {file}。错误: {str(e)}"
                    print(error_message)
                    content = error_message

            self.textEdit.setPlainText(content)

        except Exception as e:
            self.show_error_message(f"加载文件内容时发生错误：{str(e)}")

    def show_encoding_dialog(self):
        if not self.file_path:
            QMessageBox.warning(self, "错误", "没有加载文件")
            return
        
        encodings = ['utf-8', 'gbk', 'gb2312', 'iso-8859-1', 'utf-16', 'ascii', 'binary']
        encoding, ok = QInputDialog.getItem(self, "选择编码", "选择文件编码:", encodings, 0, False)
        if ok and encoding:
            self.reload_with_encoding(encoding)

    def reload_with_encoding(self, encoding):
        try:
            if encoding == 'binary':
                with open(self.file_path, 'rb') as file:
                    content = file.read()
                content = content.decode('utf-8', errors='replace')
            else:
                with open(self.file_path, 'r', encoding=encoding) as file:
                    content = file.read()
            self.textEdit.setPlainText(content)
            print(f"成功使用 {encoding} 编码重新加载文件")
        except Exception as e:
            error_message = f"使用 {encoding} 编码重新加载文件失败: {str(e)}"
            print(error_message)
            self.textEdit.setPlainText(error_message)

    def findstr(self):
        search_text = self.lineEdit_str.text()
        if search_text:
            self.textEdit.moveCursor(QtGui.QTextCursor.Start)
            cursor = self.textEdit.textCursor()
            document = self.textEdit.document()
            matches = []
            format = QtGui.QTextCharFormat()
            format.setBackground(QtGui.QBrush(QtGui.QColor("#faeaea")))

            # 清除之前的高亮
            cursor.setPosition(0)
            cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.KeepAnchor)
            cursor.setCharFormat(QtGui.QTextCharFormat())

            # 搜索并高亮新的匹配项
            cursor.setPosition(0)
            while True:
                cursor = document.find(search_text, cursor)
                if cursor.isNull():
                    break
                cursor.mergeCharFormat(format)
                matches.append(cursor.selectionStart())

            self.search_results_list.clear()
            if matches:
                for i, match in enumerate(matches):
                    cursor = self.textEdit.textCursor()
                    cursor.setPosition(match)
                    cursor.movePosition(QtGui.QTextCursor.EndOfWord, QtGui.QTextCursor.KeepAnchor)
                    item = QListWidgetItem(f"结果 {i+1}: {cursor.selectedText()}")
                    item.setData(Qt.UserRole, match)  # 存储匹配位置
                    self.search_results_list.addItem(item)
                self.search_results_list.parent().show()  # 显示搜索结果组
                print(f"找到 {len(matches)} 个匹配项")
            else:
                self.search_results_list.parent().hide()  # 隐藏搜索结果组
                print("没有找到匹配项")

    def jump_to_result(self, item):
        position = item.data(Qt.UserRole)
        cursor = self.textEdit.textCursor()
        cursor.setPosition(position)
        self.textEdit.setTextCursor(cursor)
        self.textEdit.ensureCursorVisible()
        self.textEdit.setFocus()

    def show_search_results(self, matches):
        dialog = QDialog(self)
        dialog.setWindowTitle("搜索结果")
        dialog.resize(400, 300)
        layout = QVBoxLayout(dialog)
        listWidget = QListWidget(dialog)
        for match in matches:
            cursor = self.textEdit.textCursor()
            cursor.setPosition(match)
            cursor.movePosition(QtGui.QTextCursor.EndOfWord, QtGui.QTextCursor.KeepAnchor)
            listWidget.addItem(cursor.selectedText())
        listWidget.itemDoubleClicked.connect(lambda item: self.jump_to_result(matches[listWidget.row(item)]))
        layout.addWidget(listWidget)
        dialog.setLayout(layout)
        dialog.show()

    def show_and_exec(self):
        try:
            self.show()
            QApplication.instance().processEvents()
            return self.exec_()
        except Exception as e:
            self.show_error_message(f"显示 QuicklyView 窗口时发生错误：{str(e)}")
