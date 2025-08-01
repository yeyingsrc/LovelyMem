from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTableWidget,
                               QTableWidgetItem, QHeaderView, QApplication, QProgressDialog, QListWidget, QSplitter,QListWidgetItem, QGroupBox, QMessageBox)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject
from PySide6 import QtGui
import os,re
import subprocess
import shutil
from PIL import Image
from plugin.QuicklyView import QuicklyView
from plugin.config import config
import hexdump
from plugin.csv_rules import get_rule
from plugin.CsvLoader import CsvLoader
import ui.styles

from core.config_manager import get_saved_theme  # 修改这行



class NewtableWidget(QWidget):
    style_updated_signal = Signal()

    def __init__(self, path=None, title=None, parent=None):
        super().__init__(parent)
        self.setup_ui(title)
        self.path = path
        self.loader_thread = None
        self.progress_dialog = None
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.image_path, self.profile = self.read_temp_file()

        self.customContextMenuRequested.connect(self.show_context_menu)

        self.process_rule, self.menu_rule = get_rule(os.path.basename(path)) if path else (None, None)
        if path:
            QTimer.singleShot(0, self.load_csv)

        self.setStyleSheet(ui.styles.newtable_widget_style)
        self.csv_loader = None
    def setup_ui(self, title):
        self.setWindowTitle(title)
        self.setWindowIcon(QtGui.QIcon('res/logo.ico'))
        self.setGeometry(100, 100, 1200, 800)

        

        main_layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        self.lineEdit_str = QLineEdit()
        search_button = QPushButton('搜索')
        search_button.clicked.connect(self.findrow)
        search_layout.addWidget(self.lineEdit_str)
        search_layout.addWidget(search_button)
        main_layout.addLayout(search_layout)

        # 创建一个垂直分割器
        splitter = QSplitter(Qt.Vertical)

        # 添加表格到分割器
        self.tableWidget_find = QTableWidget()
        splitter.addWidget(self.tableWidget_find)

        # 创建一个 QGroupBox 来包含搜索结果列表
        search_results_group = QGroupBox("搜索结果")
        search_results_layout = QVBoxLayout()
        self.search_results_list = QListWidget()
        self.search_results_list.itemDoubleClicked.connect(self.go_to_row)
        search_results_layout.addWidget(self.search_results_list)
        search_results_group.setLayout(search_results_layout)

        # 将 QGroupBox 添加到分割器
        splitter.addWidget(search_results_group)

        # 设置分割器的初始大小比例
        splitter.setStretchFactor(0, 3)  # 表格占3份
        splitter.setStretchFactor(1, 1)  # 搜索结果列表占1份

        # 默认隐藏搜索结果组
        search_results_group.hide()

        main_layout.addWidget(splitter)

        self.setLayout(main_layout)



    def load_csv(self):
        #标题是 正在加载中
        self.progress_dialog = QProgressDialog("加载中...", "取消", 0, 100, self)
        self.progress_dialog.setWindowTitle("正在加载")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.show()

        self.loader_thread = QThread(self)
        self.csv_loader = CsvLoader(self.path)
        self.csv_loader.moveToThread(self.loader_thread)

        self.loader_thread.started.connect(self.csv_loader.load_csv)
        self.csv_loader.data_loaded.connect(self.update_table)
        self.csv_loader.progress_updated.connect(self.progress_dialog.setValue)
        self.csv_loader.finished.connect(self.loading_finished)

        self.loader_thread.start()

    def update_table(self, df):
        if self.tableWidget_find.columnCount() == 0:
            # 设置表头
            self.tableWidget_find.setColumnCount(len(df.columns))
            self.tableWidget_find.setHorizontalHeaderLabels(df.columns)

        # 添加新数据
        current_row_count = self.tableWidget_find.rowCount()
        self.tableWidget_find.setRowCount(current_row_count + len(df))

        for i, (_, row) in enumerate(df.iterrows(), start=current_row_count):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.tableWidget_find.setItem(i, j, item)

    def loading_finished(self):
        self.loader_thread.quit()
        self.loader_thread.wait()
        self.progress_dialog.close()
        self.setup_table_properties()

    def setup_table_properties(self):
        header = self.tableWidget_find.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        header.setSectionsMovable(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.tableWidget_find.setSortingEnabled(True)

        # 添加以下代码来自动调整列宽
        self.tableWidget_find.resizeColumnsToContents()

        # 设置最小和最大列宽
        for column in range(self.tableWidget_find.columnCount()):
            current_width = self.tableWidget_find.columnWidth(column)
            min_width = 50  # 最小宽度
            max_width = 300  # 最大宽度
            new_width = max(min_width, min(current_width, max_width))
            self.tableWidget_find.setColumnWidth(column, new_width)

    def show_context_menu(self, pos):
        if self.menu_rule:
            context_menu = self.menu_rule(self)
            if context_menu:  # 添加这个检查
                context_menu.exec(self.mapToGlobal(pos))  # 注意：在 PySide6 中是 exec，不是 exec
            else:
                print("警告：菜单规则没有返回有效的上下文菜单")
        else:
            print("警告：没有为此表格设置菜单规则")

    def get_truepath(self, selectstr):
        ntfsroot = r'M:\forensic\ntfs'
        memfilepath = r'M:/forensic/files/ROOT'

        if selectstr.split('\\')[1] in ['0', '1', '2']:
            print('[*] 识别为ntfs目录' + selectstr)
            truepath = ntfsroot + selectstr.replace('\\', '/')
        elif 'HarddiskVolume' in selectstr or ':\\' in selectstr or '\\' in selectstr:
            print('[*] 使用ntfs目录' + selectstr)
            selectstr = '/'.join(selectstr.split('\\')[3:]) if 'HarddiskVolume' in selectstr else '/'.join(selectstr.split('\\')[1:])
            truepath = ntfsroot + '\\0\\' + selectstr.replace('\\', '/')
        else:
            print('[*] 使用正常目录' + selectstr)
            truepath = memfilepath + selectstr.replace('\\', '/')
        return truepath.replace('/', '\\')

    def get_selected_item_text(self):
        table = self.sender().parent() if isinstance(self.sender().parent(), QTableWidget) else self.tableWidget_find
        selected_items = table.selectedItems()
        if selected_items:
            return selected_items[0].text().strip('"')
        else:
            return None

    def delete_column(self):
        table = self.sender().parent() if isinstance(self.sender().parent(), QTableWidget) else self.tableWidget_find
        current_column = table.currentColumn()
        if current_column >= 0:
            table.removeColumn(current_column)
            print('[+] 删除成功！')
        else:
            print('[×] 未选择任何列！')

    def delete_row(self):
        table = self.sender().parent() if isinstance(self.sender().parent(), QTableWidget) else self.tableWidget_find
        current_row = table.currentRow()
        if current_row >= 0:
            table.removeRow(current_row)
            print('[+] 删除成功！')
        else:
            print('[×] 未选择任何行！')

    def copy_to_search(self):
        selectstr = self.get_selected_item_text()
        if selectstr:
            self.lineEdit_str.setText(selectstr)
            QApplication.clipboard().setText(selectstr)
            print(f'[+] 发送成功！内容为：{selectstr}')
        else:
            print('[×] 未选择任何内容！')

    def open_directory(self):
        selectstr = self.get_selected_item_text()
        if selectstr:
            print("所选单元格内容：", selectstr)
            print(r'[*] 若跳转不成功或文件大小为0，请使用vol2或vol3 filescan功能搜索指定文件，或前往M:\forensic\files\ROOT\路径下查找文件')
            truepath = self.get_truepath(selectstr).replace('\\\\', '\\')
            if os.path.isdir(truepath):
                print('[*] 正在打开目录：' + truepath)
                subprocess.run(["explorer", truepath])
            else:
                print('[*] 正在打开目录：' + os.path.dirname(truepath))
                subprocess.run(["explorer", "/select,", truepath])
        else:
            print('[×] 未选择任何内容！')

    def quickly_view(self):
        selectstr = self.get_selected_item_text()
        if selectstr:
            print("所选单元格内容：", selectstr)
            truepath = self.get_truepath(selectstr)
            if os.path.isdir(truepath):
                print('[×] 该路径为文件夹！')
                return
            try:
                self.quicklyviewwindow = QuicklyView(f'文件内容,文件路径：{truepath}', size=(800, 600))
                with open(truepath, 'r', encoding='utf-8') as f:
                    self.quicklyviewwindow.textEdit.setPlainText(f.read(500))
                self.quicklyviewwindow.show()
            except Exception as e:
                print('[×] ' + str(e))
                print('[×] 该文件无法快速读取,即将使用hexdump打印至控制台')
                print('[*] 正在使用hexdump打印文件内容：' + truepath)
                with open(truepath, 'rb') as f:
                    hexdump.hexdump(f.read(500))
        else:
            print('[×] 未选择任何内容！')

    def quickly_view_img(self):
        selectstr = self.get_selected_item_text()
        if selectstr:
            print("所选单元格内容：", selectstr)
            truepath = self.get_truepath(selectstr)
            try:
                Image.open(truepath).show()
            except:
                print('[×] 该文件不是图片！')
        else:
            print('[×] 未选择任何内容！')

    def hex_to_str(self):
        selectstr = self.get_selected_item_text()
        if selectstr:
            try:
                decoded_str = bytes.fromhex(selectstr).decode()
                print(f"[+] 转换成功！原始结果为：{decoded_str}")
            except:
                print('[×] 转换失败！')
        else:
            print('[×] 未选择任何内容！')

    def export_file_vol2(self):
        from plugin.vol2 import Vol2Plugin
        selectstr = self.get_selected_item_text()
        if selectstr and ('0x' in selectstr or selectstr.isdigit()):
            Vol2Plugin(self.image_path).vol2_dumpfiles(selectstr)
        else:
            print('[×] 请选择offset列！')

    def export_file_vol3(self):
        from plugin.vol3 import Vol3Plugin
        selectstr = self.get_selected_item_text()
        if selectstr and ('0x' in selectstr or selectstr.isdigit()):
            Vol3Plugin(self.image_path).vol3dumpfiles(selectstr)
        else:
            print('[×] 请选择offset列！')

    def proc_to_lovelypixelweaver_memprocfs(self):
        selectstr = self.get_selected_item_text()
        if selectstr and selectstr.isdigit():
            procmemfile = rf'M:/pid/{selectstr}/minidump/minidump.dmp'
            os.makedirs('tmp', exist_ok=True)
            newpath = r'tmp/minidump.data'
            if os.path.exists(newpath):
                os.remove(newpath)
            shutil.copy(procmemfile, newpath)

            cmd2 = rf'"{config.lovelypixelweaver}" tmp/minidump.data'
            print('[*] 正在调用lovelypixelweaver执行命令：' + cmd2)
            subprocess.Popen(cmd2, shell=True)
            print('[+] 执行成功！')
        else:
            print('[×] 请选择程序的PID！')

    def proc_to_lovelypixelweaver_vol2(self):
        from plugin.vol2 import Vol2Plugin
        selectstr = self.get_selected_item_text()
        if selectstr and selectstr.isdigit():
            Vol2Plugin(self.image_path).vol2_memdump(selectstr)
            procmemfile = rf'output/{selectstr}.dmp'
            os.makedirs('tmp', exist_ok=True)
            newpath = rf'tmp/{selectstr}.data'
            if os.path.exists(newpath):
                os.remove(newpath)
            shutil.copy(procmemfile, newpath)

            cmd2 = rf'"{config.lovelypixelweaver}" tmp/{selectstr}.data'
            print('[*] 正在调用lovelypixelweaver执行命令：' + cmd2)
            subprocess.Popen(cmd2, shell=True)
            print('[+] 执行成功！')
        else:
            print('[×] 请选择程序的PID！')
    
    def proc_to_lovelypixelweaver_vol3(self):
        from plugin.vol3 import Vol3Plugin
        from PySide6.QtCore import QTimer
        selectstr = self.get_selected_item_text()
        image_path = open('output/image_info.txt', 'r').read().split(',')[0]
        if selectstr and selectstr.isdigit():
            vol3_plugin = Vol3Plugin(image_path)
            vol3_plugin.vol3memmap(selectstr)
            
            # 使用QTimer定期检查文件是否存在
            self.check_timer = QTimer()
            self.check_timer.timeout.connect(lambda: self.check_file_exists(selectstr))
            self.check_timer.start(1000)  # 每秒检查一次
        else:
            print('[×] 请选择程序的PID！')

    def check_file_exists(self, selectstr):
        if os.path.exists(f'output/memmap_{selectstr}.dmp'):
            self.check_timer.stop()
            self.process_dmp_file(selectstr)

    def process_dmp_file(self, selectstr):
        procmemfile = rf'output/memmap_{selectstr}.dmp'
        os.makedirs('tmp', exist_ok=True)
        newpath = rf'tmp/{selectstr}.data'
        if os.path.exists(newpath):
            os.remove(newpath)
        shutil.copy(procmemfile, newpath)

        cmd2 = rf'"{config.lovelypixelweaver}" tmp/{selectstr}.data'
        print('[*] 正在调用lovelypixelweaver执行命令：' + cmd2)
        subprocess.Popen(cmd2, shell=True)
        print('[+] 执行成功！')


    def proc_to_strings(self):
        selectstr = self.get_selected_item_text()
        if selectstr and selectstr.isdigit():
            procmemfile = rf'M:/pid/{selectstr}/minidump/minidump.dmp'
            os.makedirs('tmp', exist_ok=True)
            newpath = r'tmp/minidump.data'
            if os.path.exists(newpath):
                os.remove(newpath)
            shutil.copy(procmemfile, newpath)

            outputname = rf'output/strings_pid_{selectstr}.txt'
            cmd2 = rf'"{config.strings}" -n 5 -a -nobanner tmp/minidump.data > {outputname}'
            print('[*] 正在调用strings执行命令：' + cmd2)
            subprocess.run(cmd2, shell=True, check=True)

            try:
                self.stringswindows = QuicklyView(f'文件内容,文件路径：{outputname}', size=(500, 900))
                with open(outputname, 'r', encoding='utf-8') as f:
                    self.stringswindows.textEdit.setPlainText(f.read())
                self.stringswindows.show()
            except Exception as e:
                print('[×] ' + str(e))
        else:
            print('[×] 请选择程序的PID！')
    # 句柄信息M:\pid\{pid}\handles\handles.txt
    def proc_to_handle(self):
        selectstr = self.get_selected_item_text()
        if selectstr and selectstr.isdigit():
            handlefile = rf'M:/pid/{selectstr}/handles/handles.txt'
            if os.path.exists(handlefile):
                with open(handlefile, 'r', encoding='utf-8') as f:
                    self.handlewindows = QuicklyView(f'文件内容,文件路径：{handlefile}', size=(500, 900))
                    self.handlewindows.textEdit.setPlainText(f.read())
                self.handlewindows.show()
            else:
                print('[×] 该文件不存在！')
        # 复制一份
        shutil.copy(handlefile, f'output/handles_{selectstr}.txt')
    # 权限标识M:\pid\{pid}\token\privileges.txt     
    def proc_to_flags(self):
        selectstr = self.get_selected_item_text()
        if selectstr and selectstr.isdigit():
            flagsfile = rf'M:/pid/{selectstr}/token/privileges.txt'

            if os.path.exists(flagsfile):
                with open(flagsfile, 'r', encoding='utf-8') as f:
                    #加载前插入字符串‘‘123’’
                    content = f.read()

                    content = '''
                    e 代表进程特权已启用。
                    p 代表进程特权存在。
                    d 代表进程特权默认已启用。\n

                    ''' + content
                    self.flagswindows = QuicklyView(f'权限标识,文件路径：{flagsfile}', size=(500, 900))
                    self.flagswindows.textEdit.setPlainText(content)
                self.flagswindows.show()
            else:
                print('[×] 该文件不存在！')
        # 复制一份
        shutil.copy(flagsfile, f'output/privileges_flags_{selectstr}.txt')
    # "M:\pid\5784\modules\modules-versioninfo.txt"
    def proc_to_verinfo(self):
        selectstr = self.get_selected_item_text()
        if selectstr and selectstr.isdigit():
            verinfofile = rf'M:/pid/{selectstr}/modules/modules-versioninfo.txt'
            # QuicklyView
            try:
                self.verinfowindows = QuicklyView(f'模块版本信息,文件路径：{verinfofile}', size=(500, 900))
                with open(verinfofile, 'r', encoding='utf-8') as f:
                    self.verinfowindows.textEdit.setPlainText(f.read())
                self.verinfowindows.show()
            except Exception as e:
                print('[×] ' + str(e))
            if os.path.exists(verinfofile):
                shutil.copy(verinfofile, f'output/verinfo_{selectstr}.txt')
                print(f'[+] 已把该程序的版本信息复制到output/verinfo_{selectstr}.txt文件')
            else:
                print('[×] 该文件不存在！')


    # 复制该程序所需的所有文件M:\pid\5784\files\vads 到output文件夹
    def proc_to_files(self):
        selectstr = self.get_selected_item_text()
        if selectstr and selectstr.isdigit():
            filespath = rf'M:/pid/{selectstr}/files/vads/'
            if os.path.exists(filespath):
                shutil.copytree(filespath, f'output/files_{selectstr}')

                print(f'[+] 已把该程序所使用的所有文件复制到output/files_{selectstr}文件夹，请注意不要运行任何文件！！！！！！')
            else:
                print('[×] 该文件夹不存在！')

    def procdump_vol2(self):
        from plugin.vol2 import Vol2Plugin
        selectstr = self.get_selected_item_text()
        if selectstr and selectstr.isdigit():
            Vol2Plugin(self.image_path).vol2_procdump(selectstr)
        else:
            print('[×] 请选择程序的PID！')

    def procdump_vol3(self):
        from plugin.vol3 import Vol3Plugin
        selectstr = self.get_selected_item_text()
        image_path = open('output/image_info.txt', 'r').read().split(',')[0]
        if selectstr and selectstr.isdigit():
            Vol3Plugin(image_path).vol3procdump(selectstr)
        else:
            print('[×] 请选择程序的PID！')

    def handle_error(self, error_message):
        print(f"Error: {error_message}")

    def thread_finished(self):
        self.load_thread = None
        self.setup_table_properties()  # 在数据加载完成后调整列宽

    def findrow(self):
        str_to_find = self.lineEdit_str.text().lower()
        found_rows = []
        for row in range(self.tableWidget_find.rowCount()):
            for column in range(self.tableWidget_find.columnCount()):
                item = self.tableWidget_find.item(row, column)
                if item:
                    item_text = item.text().lower()
                    if '*' in str_to_find:
                        keywords = str_to_find.split('*')
                        if all(keyword.strip() in item_text for keyword in keywords if keyword.strip()):
                            found_rows.append((row, item.text()))
                            break
                    elif str_to_find in item_text:
                        found_rows.append((row, item.text()))
                        break

        self.search_results_list.clear()
        if found_rows:
            for row, text in found_rows:
                item = QListWidgetItem(f"行 {row + 1}: {text}")
                item.setData(Qt.UserRole, row)
                self.search_results_list.addItem(item)
            print('[+] 搜索成功！')
            self.search_results_list.parent().show()  # 显示搜索结果组
        else:
            QMessageBox.warning(self, "搜索结果", "未找到匹配项！")
            self.search_results_list.parent().hide()  # 隐藏搜索结果组

    def go_to_row(self, item):
        row = item.data(Qt.UserRole)
        self.tableWidget_find.clearSelection()
        for column in range(self.tableWidget_find.columnCount()):
            cell_item = self.tableWidget_find.item(row, column)
            if cell_item:
                cell_item.setSelected(True)
                cell_item.setBackground(QtGui.QColor('#FFB3BA'))  # 使用较柔和的浅粉红色
        self.tableWidget_find.setFocus()
        self.tableWidget_find.scrollToItem(self.tableWidget_find.item(row, 0))

    def read_temp_file(self):
        try:
            with open('output/image_info.txt', 'r') as f:
                mem, profile = f.read().split(',')[:2]
            return mem, profile
        except Exception as e:
            #print('[×] 无法读取temp.txt文件: ' + str(e))
            return None, None
    # 将当前单元格内容转为新的表格打开
    def open_new_table(self):
        selectstr = self.get_selected_item_text()
        if selectstr:
            # 创建新窗口
            new_window = QWidget()
            new_window.setWindowTitle("表中表")
            new_window.setGeometry(100, 100, 600, 400)
            
            # 创建新的表格控件
            new_table = QTableWidget(new_window)
            
            # 创建布局并将表格添加到布局中
            layout = QVBoxLayout(new_window)
            layout.addWidget(new_table)
            new_window.setLayout(layout)
            
            # 使用逗号分割选中的文本
            items = selectstr.split(',')
            
            # 设置列数为分割后的项目数
            new_table.setColumnCount(len(items))
            
            # 获取当前选择的单元格
            current_item = self.tableWidget_find.currentItem()
            if current_item:
                current_row = current_item.row()
                current_column = current_item.column()
                
                # 获取左边单元格的内容作为表头
                if current_column > 0:
                    header_item = self.tableWidget_find.item(current_row, current_column - 1)
                    if header_item:
                        header = header_item.text()
                    else:
                        header = f'列1'
                else:
                    header = f'列1'
                
                # 使用逗号分割表头
                headers = header.split(',')
                if len(headers) < len(items):
                    headers.extend([f'列{i+1}' for i in range(len(headers), len(items))])
                new_table.setHorizontalHeaderLabels(headers[:len(items)])
            else:
                # 如果没有选中的单元格，使用默认表头
                new_table.setHorizontalHeaderLabels([f'列{i+1}' for i in range(len(items))])
            
            # 插入新行并填充数据
            new_table.insertRow(0)
            for i, item in enumerate(items):
                new_table.setItem(0, i, QTableWidgetItem(item.strip()))
            
            # 为新表格添加右键菜单
            new_table.setContextMenuPolicy(Qt.CustomContextMenu)
            new_table.customContextMenuRequested.connect(lambda pos: self.show_context_menu_newtable(new_table, pos))
            
            # 显示新窗口
            new_window.show()
            
            # 保持新窗口的引用，防止被垃圾回收
            self.new_window = new_window
    
    def show_context_menu_newtable(self, table, pos):
        from plugin.csv_rules import regax_context_menu
        
        # 获取点击位置的项目
        item = table.itemAt(pos)
        
        if item:
            # 如果点击了一个项目，选中它
            item.setSelected(True)
        
        # 获取选中的项目
        selected_items = table.selectedItems()
        
        if selected_items:
            # 创建一个新的 NewtableWidget 实例，用于处理上下文菜单操作
            temp_widget = NewtableWidget()
            temp_widget.tableWidget_find = table  # 将新表格设置为 tableWidget_find
            
            menu = regax_context_menu(temp_widget)
            if menu:
                # 执行菜单并传递正确的全局位置
                menu.exec(table.viewport().mapToGlobal(pos))
            else:
                print("警告：菜单规则没有返回有效的上下文菜单")
        else:
            print("警告：未选择任何项目")

    def closeEvent(self, event):
        if self.loader_thread and self.loader_thread.isRunning():
            self.loader_thread.quit()
            self.loader_thread.wait()
        super().closeEvent(event)

    def task_to_regedit(self):
        selectstr = self.get_selected_item_text()
        if selectstr:
            # M:\sys\tasks\by-name
            taskspath = rf'M:/sys/tasks/by-name/{selectstr}'
            if os.path.exists(taskspath):
                shutil.copytree(taskspath, f'output/tasks_{selectstr}')
                print(f'[+] 已把该任务注册表相关信息复制到output/tasks_{selectstr}文件夹，')
            else:
                print('[×] 该文件夹不存在！')
            # quicklyview "M:\sys\tasks\by-name\{}\taskinfo.txt"
            taskinfopath = rf'M:/sys/tasks/by-name/{selectstr}/taskinfo.txt'
            self.new_window_tasks_taskinfo = QuicklyView(f'{selectstr}简要信息,文件路径：{taskinfopath}', size=(500, 900))
            self.new_window_tasks_taskinfo.load_file_content(taskinfopath)
            self.new_window_tasks_taskinfo.show()

    def server_to_regedit(self):
        selectstr = self.get_selected_item_text()
        # M:\sys\services\by-id
        if selectstr:
            servicespath = rf'M:/sys/services/by-id/{selectstr}'
            if os.path.exists(servicespath):
                shutil.copytree(servicespath, f'output/services_{selectstr}')
                print(f'[+] 已把该服务注册表相关信息复制到output/services_{selectstr}文件夹，')
            else:
                print('[×] 该文件夹不存在！')
            # quicklyview "M:\sys\services\by-id\{}\svcinfo.txt"
            svcinfopath = rf'M:/sys/services/by-id/{selectstr}/svcinfo.txt'
            self.new_window_services_svcinfo = QuicklyView(f'该服务简要信息,文件路径：{svcinfopath}', size=(500, 900))
            self.new_window_services_svcinfo.load_file_content(svcinfopath)
            self.new_window_services_svcinfo.show()
            

