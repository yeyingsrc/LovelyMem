#from plugin.NewtableWidget import NewtableWidget
from plugin.QuicklyView import QuicklyView
from lovelyform import show_csv_viewer
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread, Signal
import os
import csv
import chardet
import traceback

class FileProcessThread(QThread):
    finished = Signal(str, str, str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        file_size = os.path.getsize(self.file_path)
        file_extension = os.path.splitext(self.file_path)[1]
        
        try:
            with open(self.file_path, 'rb') as file:
                raw_content = file.read(1000)
            encoding = chardet.detect(raw_content)['encoding']
            content = raw_content.decode(encoding or 'utf-8', errors='replace')
        except Exception as e:
            content = f"无法读取文件内容: {str(e)}"
        
        self.finished.emit(str(file_size), file_extension, content)

class OpenFile:
    def __init__(self):
        self.table_widget = None
        self.thread = None

    def run(self, file_path):
        print(f"文件分析器正在处理文件: {file_path}")
        
        self.thread = FileProcessThread(file_path)
        self.thread.finished.connect(self.on_file_processed)
        self.thread.start()

    def on_file_processed(self, file_size, file_extension, content):
        if file_extension.lower() == '.csv':
            try:
                filepath = self.thread.file_path
                show_csv_viewer(filepath)
                # #csv_viewer = NewtableWidget(filepath, f"CSV 查看器 - {os.path.basename(filepath)}")
                # #csv_viewer.show()
                # #self.viewers.append(csv_viewer)
                # self.table_widget = NewtableWidget(self.thread.file_path, f"CSV内容 - {os.path.basename(self.thread.file_path)}")
                # self.table_widget.show()
                # print("CSV文件内容已在表格中显示")
            except Exception as e:
                print(f"无法解析CSV文件: {str(e)}")
                traceback.print_exc()
        else:
            try:
                quick_view = QuicklyView(f"文件内容预览 - {os.path.basename(self.thread.file_path)}")
                quick_view.load_file_content(self.thread.file_path)
                QApplication.instance().processEvents()
                quick_view.show_and_exec()
                print("文件内容预览已在新窗口中打开")
            except Exception as e:
                print(f"显示 QuicklyView 时发生错误：{str(e)}")
                traceback.print_exc()
        
        print(f"文件大小: {file_size} 字节")
        print(f"文件扩展名: {file_extension}")
        print("文件分析器执行完毕")

        self.thread.quit()
        self.thread.wait()