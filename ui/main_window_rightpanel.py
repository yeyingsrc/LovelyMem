from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                               QListWidget, QPushButton, QSplitter, QMenu, QMessageBox, 
                               QComboBox, QInputDialog, QDialog, QCheckBox, QDialogButtonBox, 
                               QToolButton, QTreeWidget, QTreeWidgetItem, QHeaderView,QApplication)
from PySide6.QtCore import Qt, Signal, QDir,QFileInfo, QMimeData, QPoint
from PySide6.QtGui import QCursor, QIcon, QAction, QDrag
import os, subprocess
import shutil
from plugin.NewtableWidget import NewtableWidget
from plugin.QuicklyView import QuicklyView
import sqlite3
from ui.regex_slot import RegexSlot
import ui.styles
import importlib.util
import importlib
import sys
import traceback
import logging
from datetime import datetime

class CustomTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setExpandsOnDoubleClick(False)  # 禁用双击展开
        self.last_clicked_item = None

    def mouseReleaseEvent(self, event):
        item = self.itemAt(event.pos())
        if item:
            if self.last_clicked_item and self.last_clicked_item == item:
                # 如果是同一个项目被点击两次，切换展开状
                item.setExpanded(not item.isExpanded())
            else:
                # 如果是新的项目被点击，只选中它，不展开
                self.setCurrentItem(item)
            self.last_clicked_item = item
        else:
            self.last_clicked_item = None
        super().mouseReleaseEvent(event)

    def clear(self):
        self.last_clicked_item = None
        super().clear()

class FileSlotWindow(QWidget):
    closed = Signal(QTreeWidget)

    def __init__(self, file_tree):
        super().__init__()
        self.setWindowTitle("文件槽")
        self.setWindowFlags(Qt.Window)
        layout = QVBoxLayout(self)
        layout.addWidget(file_tree)
        self.file_tree = file_tree

    def closeEvent(self, event):
        self.closed.emit(self.file_tree)
        super().closeEvent(event)

class RightPanel(QWidget):
    pack_files_signal = Signal()
    clear_files_signal = Signal()
    execute_preset_signal = Signal(str)  # 新增信号用于执行预设

    def __init__(self, file_manager):
        super().__init__()
        self.file_manager = file_manager
        self.setup_ui()
        self.csv_viewers = []
        self.viewers = []
        self.load_preset_names()
        self.setStyleSheet(ui.styles.right_panel_style)  # 应用整体样式
        self.plugins = self.load_plugins()  # 加载插件
        self.file_slot_window = None

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建一个垂直分割器
        main_splitter = QSplitter(Qt.Vertical)
        #main_splitter.setStyleSheet(ui.styles.splitter_style)

        # 文件
        self.file_group = QGroupBox("文件槽")
        file_layout = QVBoxLayout(self.file_group)
        file_layout.setContentsMargins(5, 5, 5, 5)
        self.file_tree = CustomTreeWidget()
        self.file_tree.setHeaderLabels(["文件名", "大小", "修改日期"])
        self.file_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.file_tree.setSortingEnabled(True)
        file_layout.addWidget(self.file_tree)

        # 设置文件槽可拖动
        self.file_group.setMouseTracking(True)
        self.file_group.mousePressEvent = self.fileslot_mouse_press_event
        self.file_group.mouseMoveEvent = self.fileslot_mouse_move_event

        # 添加打包、清空和排序按钮
        button_layout = QHBoxLayout()
        self.pack_button = QPushButton("打包")
        self.clear_button = QPushButton("清空")
        #sort_button = QPushButton("排序")
        button_layout.addWidget(self.pack_button)
        button_layout.addWidget(self.clear_button)
        #button_layout.addWidget(sort_button)
        file_layout.addLayout(button_layout)

        # 连接按钮信号
        self.pack_button.clicked.connect(self.pack_files_signal.emit)
        self.clear_button.clicked.connect(self.clear_files_signal.emit)
        #sort_button.clicked.connect(self.show_sort_menu)

        # 为文件列表添加右键菜
        self.file_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self.show_file_context_menu)

        # 创建一个水平分割器用于正则槽和预设
        bottom_splitter = QSplitter(Qt.Horizontal)

        # 正槽
        self.regex_slot = RegexSlot(self.file_tree)
        self.regex_slot.regex_check_signal.connect(self.handle_regex_check_results)
        bottom_splitter.addWidget(self.regex_slot)

        # 预设
        preset_group = QGroupBox("预设")
        preset_layout = QVBoxLayout(preset_group)
        preset_layout.setContentsMargins(5, 5, 5, 5)

        # 预设组下拉框和操作按钮的水平
        preset_group_layout = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("选择预设")
        preset_group_layout.addWidget(self.preset_combo, 1)  # 设置拉伸因子

        # 操作按钮
        self.preset_action_button = QToolButton()
        self.preset_action_button.setText("操作")
        self.preset_action_button.setPopupMode(QToolButton.InstantPopup)
        self.setup_preset_action_menu()
        preset_group_layout.addWidget(self.preset_action_button)

        preset_layout.addLayout(preset_group_layout)

        self.preset_list = QListWidget()
        self.preset_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.preset_list.customContextMenuRequested.connect(self.show_preset_item_context_menu)
        preset_layout.addWidget(self.preset_list)

        button_layout = QHBoxLayout()
        self.execute_preset_button = QPushButton("执行预设")
        self.execute_preset_button.clicked.connect(self.execute_preset)
        button_layout.addWidget(self.execute_preset_button)
        preset_layout.addLayout(button_layout)

        bottom_splitter.addWidget(preset_group)

        # 设置预设槽和正则槽的比例:1
        bottom_splitter.setStretchFactor(0, 3)  # 正则
        bottom_splitter.setStretchFactor(1, 1)  # 

        # 将文件槽和底部分割器添加到主分割
        main_splitter.addWidget(self.file_group)
        main_splitter.addWidget(bottom_splitter)

        # 设置主分割器的初始大小比
        main_splitter.setStretchFactor(0, 2)  # 文件
        main_splitter.setStretchFactor(1, 1)  # 底部分割

        layout.addWidget(main_splitter)

        # 修改下拉框的连接
        self.preset_combo.currentIndexChanged.connect(self.on_preset_changed)

    def add_file(self, file_path, file_size, mod_time):
        if not file_path.lower().endswith('.json'):
            parts = file_path.split(os.sep)
            current_item = self.file_tree.invisibleRootItem()
            for i, part in enumerate(parts):
                found = False
                for j in range(current_item.childCount()):
                    if current_item.child(j).text(0) == part:
                        current_item = current_item.child(j)
                        found = True
                        break
                if not found:
                    new_item = QTreeWidgetItem(current_item)
                    new_item.setText(0, part)
                    if i == len(parts) - 1:  # 如果是最后一部分，即文件
                        new_item.setText(1, self.format_size(file_size))
                        new_item.setText(2, mod_time.strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        # 如果不是最后一部分，说明是文件夹，设置展开指示
                        new_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
                    current_item = new_item
                
                # 不自动展开项目
                if i < len(parts) - 1:
                    current_item.setExpanded(False)

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0

    def add_regex(self):
        regex = self.regex_input.text()
        if regex:
            self.regex_list.addItem(regex)
            self.regex_input.clear()

    def add_preset(self):
        input_dialog = QInputDialog(self)
        input_dialog.setWindowIcon(QIcon("res/logo.ico"))
        preset_name, ok = input_dialog.getText(self, "新增预设", "请输入预设名")
        if ok and preset_name:
            if preset_name not in [self.preset_combo.itemText(i) for i in range(self.preset_combo.count())]:
                self.preset_combo.addItem(preset_name)
                self.preset_combo.setCurrentText(preset_name)
                self.save_preset(preset_name)
                self.preset_list.clear()  # 清空预设列表,因为这是一个新的预
            else:
                QMessageBox.warning(self, "警告", "该预设名称已存在")

    def save_preset(self, preset_name):
        conn = sqlite3.connect('db/presets.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS preset_names
                     (name TEXT PRIMARY KEY)''')
        c.execute("INSERT OR REPLACE INTO preset_names (name) VALUES (?)", (preset_name,))
        
        # 创建一个新的空预设
        c.execute('''CREATE TABLE IF NOT EXISTS presets
                     (name TEXT, button_text TEXT)''')
        
        conn.commit()
        conn.close()

    def load_preset(self):
        preset_name = self.preset_combo.currentText()
        if preset_name != "选择预设":
            conn = sqlite3.connect('db/presets.db')
            c = conn.cursor()
            
            # 首先确保表存
            c.execute('''CREATE TABLE IF NOT EXISTS presets
                         (name TEXT, button_text TEXT)''')
            
            c.execute("SELECT button_text FROM presets WHERE name = ?", (preset_name,))
            buttons = c.fetchall()
            conn.close()

            self.preset_list.clear()
            for button in buttons:
                self.preset_list.addItem(button[0])

    def get_current_preset(self):
        return self.preset_combo.currentText() if self.preset_combo.currentText() != "选择预设" else None

    def add_button_to_preset(self, preset_name, button_text):
        self.preset_list.addItem(button_text)

    def show_file_context_menu(self, position):
        item = self.file_tree.itemAt(position)
        if item and item.childCount() == 0:  # 确保选中的是文件而不是文件夹
            file_path = self.get_full_path(item)

            menu = QMenu()
            open_action = menu.addAction("快速打开")
            open_file_dir_action = menu.addAction("打开文件目录")
            
            # 添加扩展菜单
            reload_plugins_action = menu.addAction("重新加载插件")
            extensions_menu = menu.addMenu("扩展")
            for category, category_plugins in self.plugins.items():
                category_menu = extensions_menu.addMenu(category)
                for plugin_title, plugin_data in category_plugins.items():
                    plugin_action = category_menu.addAction(plugin_title)
                    plugin_action.triggered.connect(lambda checked, fp=file_path, pd=plugin_data: self.execute_plugin(fp, pd))
            
            delete_action = menu.addAction("删除")
            reload_plugins_action.triggered.connect(self.reload_plugins)
            
            action = menu.exec_(self.file_tree.mapToGlobal(position))
            
            if action == open_action:
                self.quick_open_file(file_path)
            elif action == delete_action:
                self.delete_selected_file(file_path)
                self.update_file_list()  # 在删除文件后更新文件列表
            elif action == open_file_dir_action:
                self.open_file_dir(file_path)

    def quick_open_file(self, file_path):
        print(f"尝试打开文件: {file_path}")

        if not os.path.exists(file_path):
            QMessageBox.warning(self, "文件不存在", f"文件 {os.path.basename(file_path)} 不存在")
            return

        try:
            if file_path.lower().endswith('.csv'):
                print(f"正在打开CSV文件: {file_path}")
                self.open_csv_file(file_path)
            elif file_path.lower().endswith(('.txt', '.text', '.log','.dat')):
                print(f"正在打开文本文件: {file_path}")
                self.open_text_file(file_path)
            elif file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.ico')):
                print(f"正在打开图片文件: {file_path}")
                self.open_image_file(file_path)
            else:
                print(f"不支持的文件类型: {file_path}")
                self.open_other_file(file_path)
        except Exception as e:
            print(f"打开文件时发生错误{str(e)}")
            QMessageBox.critical(self, "错误", f"打开文件时发生错误 {str(e)}")

    def open_csv_file(self, file_path):
        try:
            from lovelyform import show_csv_viewer
            show_csv_viewer(file_path)
            
            # csv_viewer = NewtableWidget(file_path, f"CSV 查看器 - {os.path.basename(file_path)}")
            # csv_viewer.show()
            # self.viewers.append(csv_viewer)
        except Exception as e:
            print(f"打开 CSV 文件时发生错误{str(e)}")
            QMessageBox.critical(self, "错误", f"打开 CSV 文件时发生错误 {str(e)}")
    def open_file_dir(self, file_path):
        if not file_path:
            QMessageBox.warning(self, "错误", "无法获取文件路径")
            return

        # 移除所有开头的 'output/'
        while file_path.startswith('output/'):
            file_path = file_path[7:]

        # 获取当前工作目录
        current_dir = os.getcwd()
        
        # 构建完整路径
        full_path = os.path.normpath(os.path.join(current_dir, 'output', file_path))
        
        print(f"尝试打开目录: {full_path}")
        if os.path.exists(full_path):
            # 在Windows上使用explorer选中文件
            subprocess.run(['explorer', '/select,', full_path])
        else:
            QMessageBox.warning(self, "文件不存在", f"文件 {file_path} 不存在")
    def open_text_file(self, file_path):
        text_viewer = QuicklyView(f"快速文本查看器 - {os.path.basename(file_path)}")
        text_viewer.load_file_content(file_path)
        text_viewer.show()
        self.viewers.append(text_viewer)
    def open_image_file(self, file_path):
        # 用PIL show
        from PIL import Image
        image = Image.open(file_path)
        image.show()
    def open_other_file(self, file_path):
        QMessageBox.information(self, "不支持的文件类型", f"暂不支持打开 {os.path.basename(file_path)} 格式的文件")

    def delete_selected_file(self, file_path):
        try:
            if self.file_manager.delete_file(file_path):
                print(f"已删除文件：{file_path}")
                self.update_file_list()
                QMessageBox.information(self, "删除成功", f"文件 {os.path.basename(file_path)} 已成功删除")
            else:
                QMessageBox.warning(self, "删除失败", f"无法删除文件 {os.path.basename(file_path)}")
        except Exception as e:
            print(f"删除文件时发生错误{str(e)}")
            QMessageBox.critical(self, "错误", f"删除文件时发生错误 {str(e)}")

    def closeEvent(self, event):
        for viewer in self.viewers:
            viewer.close()
        self.viewers.clear()
        super().closeEvent(event)

    def open_other_file(self, file_path):
        # 对于其他格式文件，可以使用系统默认程序打开
        # 或者显示一个消息说明暂不支持该格式
        print(f"暂不支持打开 {os.path.basename(file_path)} 格式的文")
        QMessageBox.information(self, "不支持的文件类型", f"暂不支持打开 {os.path.basename(file_path)} 格式的文")

    def load_preset_names(self):
        conn = sqlite3.connect('db/presets.db')
        c = conn.cursor()
        
        # 确保表存
        c.execute('''CREATE TABLE IF NOT EXISTS presets
                     (name TEXT, button_text TEXT)''')
        
        c.execute("SELECT DISTINCT name FROM presets")
        preset_names = c.fetchall()
        conn.close()

        self.preset_combo.clear()
        self.preset_combo.addItem("选择预设")
        for name in preset_names:
            self.preset_combo.addItem(name[0])
        
        # 如果有预设，默认选择第一
        if preset_names:
            self.preset_combo.setCurrentIndex(1)  # 对应第一个预
            self.load_preset()  # 加载选中预设的内

    def show_preset_item_context_menu(self, position):
        item = self.preset_list.itemAt(position)
        if item is not None:
            context_menu = QMenu()
            edit_action = context_menu.addAction("编辑")
            delete_action = context_menu.addAction("删除")
            
            action = context_menu.exec_(self.preset_list.mapToGlobal(position))
            
            if action == edit_action:
                self.edit_preset_item(item)
            elif action == delete_action:
                self.delete_preset_item(item)

    def edit_preset_item(self, item):
        current_text = item.text()
        new_text, ok = QInputDialog.getText(self, "编辑预设项", "输入新的预设:", text=current_text)
        if ok and new_text:
            item.setText(new_text)
            self.update_preset_in_db(self.preset_combo.currentText(), current_text, new_text)

    def delete_preset_item(self, item):
        reply = QMessageBox.question(self, "删除确认", 
                                     "确定要删除这个预设项吗?", 
                                     QMessageBox.Yes | QMessageBox.No, 
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            row = self.preset_list.row(item)
            self.preset_list.takeItem(row)
            self.delete_preset_from_db(self.preset_combo.currentText(), item.text())

    def update_preset_in_db(self, preset_name, old_text, new_text):
        conn = sqlite3.connect('db/presets.db')
        c = conn.cursor()
        c.execute("UPDATE presets SET button_text = ? WHERE name = ? AND button_text = ?", 
                  (new_text, preset_name, old_text))
        conn.commit()
        conn.close()

    def delete_preset_from_db(self, preset_name, button_text):
        conn = sqlite3.connect('db/presets.db')
        c = conn.cursor()
        c.execute("DELETE FROM presets WHERE name = ? AND button_text = ?", 
                  (preset_name, button_text))
        conn.commit()
        conn.close()

    def execute_preset(self):
        preset_name = self.preset_combo.currentText()
        if preset_name and preset_name != "选择预设":
            self.execute_preset_signal.emit(preset_name)
        else:
            QMessageBox.warning(self, "警告", "请先选择一个预设")

    def handle_regex_check_results(self, results):
        # 这里可以添加代码来显示结果或进行其他操作
        print(f"找到 {len(results)} 个配配项")
        # 例如，可以打开生成CSV 文件
        self.open_csv_file("output/regex_check_results.csv")

    def show_delete_preset_dialog(self):
        presets = self.get_preset_names_from_db()
        if not presets:
            QMessageBox.information(self, "提示", "没有可删除的预设")
            return

        dialog = DeletePresetDialog(presets)
        if dialog.exec_():
            selected_presets = dialog.get_selected_presets()
            for preset in selected_presets:
                self.delete_preset(preset)
            self.load_preset_names()  # 重新加载预设名称

    def get_preset_names_from_db(self):
        conn = sqlite3.connect('db/presets.db')
        c = conn.cursor()
        c.execute("SELECT DISTINCT name FROM presets")
        preset_names = [row[0] for row in c.fetchall()]
        conn.close()
        return preset_names

    def delete_preset(self, preset_name):
        conn = sqlite3.connect('db/presets.db')
        c = conn.cursor()
        c.execute("DELETE FROM presets WHERE name = ?", (preset_name,))
        conn.commit()
        conn.close()

        index = self.preset_combo.findText(preset_name)
        if index != -1:
            self.preset_combo.removeItem(index)
        if self.preset_combo.currentText() == preset_name:
            self.preset_combo.setCurrentIndex(0)

        self.preset_list.clear()

    def on_preset_changed(self, index):
        if index > 0:  # 确保选择的是 "选择预设"
            self.load_preset()

    def setup_preset_action_menu(self):
        menu = QMenu(self)
        menu.addAction("新增预设", self.add_preset)
        menu.addAction("编辑预设", self.edit_preset)
        menu.addAction("删除预设", self.show_delete_preset_dialog)
        self.preset_action_button.setMenu(menu)

    def edit_preset(self):
        current_preset = self.preset_combo.currentText()
        if current_preset != "选择预设":
            input_dialog = QInputDialog(self)
            input_dialog.setWindowIcon(QIcon("res/logo.ico"))
            new_name, ok = input_dialog.getText(self, "编辑预设", "请输入新的预设名", text=current_preset)
            if ok and new_name:
                if new_name != current_preset:
                    if new_name not in [self.preset_combo.itemText(i) for i in range(self.preset_combo.count())]:
                        self.update_preset_name(current_preset, new_name)
                        index = self.preset_combo.findText(current_preset)
                        self.preset_combo.setItemText(index, new_name)
                    else:
                        QMessageBox.warning(self, "警告", "该预设名称已存在")
        else:
            QMessageBox.warning(self, "警告", "请先选择一个预设")

    def update_preset_name(self, old_name, new_name):
        conn = sqlite3.connect('db/presets.db')
        c = conn.cursor()
        c.execute("UPDATE presets SET name = ? WHERE name = ?", (new_name, old_name))
        conn.commit()
        conn.close()

    def get_extension_from_mime(self, mime_type):
        # 这里可以根据常见MIME 类型返回对应的文件扩展名
        mime_to_ext = {
            'text/plain': '.txt',
            'text/html': '.html',
            'text/css': '.css',
            'text/javascript': '.js',
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'application/pdf': '.pdf',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.ms-excel': '.xls',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/zip': '.zip',
            'application/x-dosexec': '.exe',
            'application/x-7z-compressed': '.7z',
            'application/x-rar-compressed': '.rar',
            'application/x-tar': '.tar',
            'application/x-gzip': '.gz',
            'application/x-bzip2': '.bz2',
            'application/x-xz': '.xz',
        }
        # 如果找不到对应的扩展不修
        return mime_to_ext.get(mime_type, '')

    def update_file_list(self):
        # 记录展开状
        expanded_items = self.get_expanded_items(self.file_tree.invisibleRootItem())

        self.file_tree.clear()
        file_list = self.file_manager.get_file_list()
        for rel_path, file_size, mod_time in file_list:
            self.add_file(rel_path, file_size, mod_time)
        
        # 恢复展开状
        self.restore_expanded_items(self.file_tree.invisibleRootItem(), expanded_items)

    def get_expanded_items(self, item, path=""):
        expanded_items = {}
        for i in range(item.childCount()):
            child = item.child(i)
            child_path = os.path.join(path, child.text(0))
            if child.isExpanded():
                expanded_items[child_path] = True
            if child.childCount() > 0:
                expanded_items.update(self.get_expanded_items(child, child_path))
        return expanded_items

    def restore_expanded_items(self, item, expanded_items, path=""):
        for i in range(item.childCount()):
            child = item.child(i)
            child_path = os.path.join(path, child.text(0))
            if expanded_items.get(child_path, False):
                child.setExpanded(True)
            if child.childCount() > 0:
                self.restore_expanded_items(child, expanded_items, child_path)

    def collapse_all_items(self, item):
        for i in range(item.childCount()):
            child = item.child(i)
            child.setExpanded(False)
            if child.childCount() > 0:
                self.collapse_all_items(child)

    def load_plugins(self):
        plugins = {}
        plugin_dir = "extensions"
        
        def load_plugin_from_file(file_path):
            try:
                module_name = os.path.splitext(os.path.basename(file_path))[0]
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                if hasattr(module, "plugin_info"):
                    category = module.plugin_info.get("category", "其他")
                    if category not in plugins:
                        plugins[category] = {}
                    plugins[category][module.plugin_info["title"]] = {
                        "module": module,
                        "info": module.plugin_info,
                        "file_path": file_path
                    }
                    logging.info(f"成功加载插件: {file_path}")
                else:
                    logging.warning(f"插件文件 {file_path} 缺少 plugin_info")
            except Exception as e:
                logging.error(f"加载插件 {file_path} 时出 {str(e)}")
                logging.error(traceback.format_exc())

        for root, dirs, files in os.walk(plugin_dir):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    load_plugin_from_file(file_path)

        return plugins

    def reload_plugins(self):
        self.plugins = self.load_plugins()
        self.update_plugin_menu()
        QMessageBox.information(self, "插件重新加载", "所有插件已重新加载")

    def update_plugin_menu(self):
        # 更新右键菜单中的插件列表
        # 这个方法需要在show_file_context_menu中调
        pass

    def execute_plugin(self, file_path, plugin_data):
        print(f"执行插件，文件路径: {file_path}")  # 调试信息

        try:
            # 获取插件文件路径
            plugin_file_path = plugin_data["file_path"]
            print(f"插件文件路径: {plugin_file_path}")  # 调试信息
            
            # 使用 importlib.util.spec_from_file_location 重新加载模块
            spec = importlib.util.spec_from_file_location(plugin_data["module"].__name__, plugin_file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 更新 sys.modules
            sys.modules[plugin_data["module"].__name__] = module
            
            # 执行插件的run函数
            #print("开始执行插)  # 调试信息
            module.run(file_path)
            #print("插件执行完成")  # 调试信息
            
            logging.info(f"成功执行插件: {plugin_data['info']['title']}")
        except Exception as e:
            error_msg = f"执行插件时发生错误{str(e)}\n\n"
            error_msg += traceback.format_exc()
            logging.error(error_msg)
            print(error_msg)
            QMessageBox.warning(self, "插件执行失败", error_msg)

    def get_full_path(self, item):
        path = []
        while item is not None:
            path.insert(0, item.text(0))
            item = item.parent()
        
        # 移除路径开头的 'output' 前缀（如果存在）
        if path and path[0] == 'output':
            path.pop(0)
        
        # 构建相对'output' 目录的路
        relative_path = os.path.join(*path)
        
        # 获取当前工作目录
        current_dir = os.getcwd()
        
        # 构建完整路径
        full_path = os.path.normpath(os.path.join(current_dir, 'output', relative_path))
        
        #print(f"构建的完整路 {full_path}")  # 调试信息
        return full_path

    def show_sort_menu(self):
        menu = QMenu(self)
        menu.addAction("按名称排序", lambda: self.file_tree.sortItems(0, Qt.AscendingOrder))
        menu.addAction("按大小排序", lambda: self.file_tree.sortItems(1, Qt.AscendingOrder))
        menu.addAction("按修改日期排序", lambda: self.file_tree.sortItems(2, Qt.AscendingOrder))
        menu.exec_(QCursor.pos())

    def fileslot_mouse_press_event(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()

    def fileslot_mouse_move_event(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return

        drag = QDrag(self)
        mimedata = QMimeData()
        mimedata.setText("file_slot")
        drag.setMimeData(mimedata)

        if drag.exec_(Qt.MoveAction) == Qt.MoveAction:
            self.create_file_slot_window()

    def create_file_slot_window(self):
        if self.file_slot_window is None:
            self.file_slot_window = FileSlotWindow(self.file_tree)
            self.file_slot_window.closed.connect(self.restore_file_slot)
            self.file_slot_window.show()
            self.file_group.layout().removeWidget(self.file_tree)
            self.file_tree.setParent(None)

    def restore_file_slot(self, file_tree):
        self.file_tree = file_tree
        self.file_group.layout().addWidget(self.file_tree)
        self.file_slot_window = None

class DeletePresetDialog(QDialog):
    def __init__(self, presets):
        super().__init__()
        self.setWindowTitle("删除预设")
        self.setLayout(QVBoxLayout())
        self.setWindowIcon(QIcon("res\logo.ico"))

        self.checkboxes = []
        for preset in presets:
            checkbox = QCheckBox(preset)
            self.checkboxes.append(checkbox)
            self.layout().addWidget(checkbox)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout().addWidget(button_box)

    def get_selected_presets(self):
        return [cb.text() for cb in self.checkboxes if cb.isChecked()]
