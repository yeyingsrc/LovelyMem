from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                               QListWidget, QPushButton, QSplitter, QMenu, QMessageBox, 
                               QComboBox, QInputDialog, QDialog, QCheckBox, QDialogButtonBox, 
                               QToolButton, QTreeWidget, QTreeWidgetItem, QHeaderView,QApplication)
from PySide6.QtCore import Qt, Signal, QDir,QFileInfo, QMimeData, QPoint, QTimer
from PySide6.QtGui import QCursor, QIcon, QAction, QDrag
import os, subprocess
import shutil
from plugin.NewtableWidget import NewtableWidget
from plugin.QuicklyView import QuicklyView
import ui.styles
import importlib.util
import importlib
import sys
import traceback
import logging
from datetime import datetime
import sqlite3
from ui.regex_slot import RegexSlot
from ui.file_slot import FileSlot

class CustomTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setExpandsOnDoubleClick(False)  # 禁用双击展开
        self.last_clicked_item = None

    def mouseReleaseEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        if item:
            if self.last_clicked_item and self.last_clicked_item == item:
                # 如果是同一个项目被点击两次，切换展开状态
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

class MemoryWorkbench(QWidget):
    """
    内存工作台类，用于显示和管理内存分析工具
    """
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

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建一个垂直分割器
        main_splitter = QSplitter(Qt.Vertical)
        #main_splitter.setStyleSheet(ui.styles.splitter_style)

        # 文件槽
        self.file_slot = FileSlot(self.file_manager)
        self.file_slot.pack_files_signal.connect(self.pack_files)
        self.file_slot.clear_files_signal.connect(self.clear_files)
        
        # 为文件槽添加双击事件
        self.file_slot.mouseDoubleClickEvent = lambda event: self.window().on_file_slot_double_click(event)
        
        # 创建文件槽容器
        self.file_slot_container = QWidget()
        file_slot_layout = QVBoxLayout(self.file_slot_container)
        file_slot_layout.setContentsMargins(0, 0, 0, 0)
        file_slot_layout.addWidget(self.file_slot)
        
        # 将文件槽容器添加到主分割器
        main_splitter.addWidget(self.file_slot_container)
        
        # 创建正则槽
        self.regex_slot = RegexSlot(self.file_slot.file_tree)
        self.regex_slot.regex_check_signal.connect(self.handle_regex_check_results)
        # 为正则槽添加双击事件
        self.regex_slot.mouseDoubleClickEvent = lambda event: self.on_regex_slot_double_click(event)
        
        # 创建预设组
        self.setup_preset_group()

        # 创建一个水平分割器用于正则槽和预设
        bottom_splitter = QSplitter(Qt.Horizontal)
        
        # 添加正则槽和预设组到底部分割器
        bottom_splitter.addWidget(self.regex_slot)
        bottom_splitter.addWidget(self.preset_group)
        
        # 设置预设槽和正则槽的比例
        bottom_splitter.setStretchFactor(0, 3)  # 正则槽
        bottom_splitter.setStretchFactor(1, 1)  # 预设槽

        # 将底部分割器添加到主分割器
        main_splitter.addWidget(bottom_splitter)
        
        # 设置主分割器的初始大小比例
        main_splitter.setStretchFactor(0, 2)  # 文件槽
        main_splitter.setStretchFactor(1, 1)  # 底部分割器

        # 将主分割器添加到主布局
        layout.addWidget(main_splitter)

        # 修改下拉框的连接
        self.preset_combo.currentIndexChanged.connect(self.on_preset_changed)

    def pack_files(self):
        # 转发信号
        self.pack_files_signal.emit()

    def clear_files(self):
        # 转发信号
        self.clear_files_signal.emit()

    def update_file_list(self):
        # 调用文件槽的更新方法
        self.file_slot.update_file_list()

    def add_file(self, file_path, file_size, mod_time):
        # 直接调用文件槽的方法
        self.file_slot.add_file(file_path, file_size, mod_time)

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
            
            # 首先确保表存在
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
        self.file_slot.show_file_context_menu(position)

    def show_preset_item_context_menu(self, position):
        item = self.preset_list.itemAt(position)
        if item is not None:
            context_menu = QMenu()
            edit_action = context_menu.addAction("编辑")
            delete_action = context_menu.addAction("删除")
            
            action = context_menu.exec(self.preset_list.mapToGlobal(position))
            
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
        """处理正则检查结果"""
        # 创建CSV文件并保存结果
        self.regex_slot.save_results_to_csv(results)
        
        # 这里可以添加代码来显示结果或进行其他操作
        print(f"找到 {len(results)} 个配配项")
        # 例如，可以打开生成CSV 文件
        self.open_csv_file("output/regex_check_results.csv")

    def on_regex_slot_double_click(self, event):
        """处理正则槽的双击事件"""
        #print("正则槽双击事件触发")
        # 如果已经有正则槽窗口，则不创建新窗口
        if hasattr(self, 'regex_slot_window') and self.regex_slot_window is not None:
            self.regex_slot_window.activateWindow()  # 激活已有窗口
            #print("激活已有正则槽窗口")
            return
            
        # 隐藏主界面的正则槽区域
        #print("隐藏主界面正则槽")
        self.hide_regex_slot()
        
        # 创建独立的正则槽窗口
        #print(f"创建新正则槽窗口，原始正则槽ID: {id(self.regex_slot)}")
        from ui.regex_slot_window import RegexSlotWindow
        self.regex_slot_window = RegexSlotWindow(self.regex_slot)
        # 连接关闭信号
        self.regex_slot_window.closed.connect(self.on_regex_window_closed)
        
        # 调整布局
        QTimer.singleShot(100, self.adjust_layout_visibility)

    def on_regex_window_closed(self, regex_slot):
        """处理正则槽窗口关闭事件"""
        #print(f"正则槽窗口关闭事件触发，接收到的正则槽ID: {id(regex_slot)}")
        # 重置正则槽窗口引用
        self.regex_slot_window = None
        
        # 将右键菜单传递给主窗口处理
        self.window().on_regex_slot_window_closed(regex_slot)
        
        # 显示正则槽
        self.show_regex_slot()

    def hide_regex_slot(self):
        """隐藏正则槽"""
        if hasattr(self, 'regex_slot'):
            self.regex_slot.setVisible(False)
            # 使用定时器延迟调整布局，确保UI状态已完全更新
            QTimer.singleShot(100, self.adjust_layout_visibility)
    
    def show_regex_slot(self):
        """显示正则槽"""
        if hasattr(self, 'regex_slot'):
            self.regex_slot.setVisible(True)
            # 使用定时器延迟调整布局，确保UI状态已完全更新
            QTimer.singleShot(100, self.adjust_layout_visibility)
            
    def add_regex_slot_back(self, regex_slot):
        """将正则槽控件重新添加到主窗口"""
        # 确保正则槽没有父控件
        if regex_slot.parent():
            regex_slot.setParent(None)
            
        # 更新正则槽引用
        self.regex_slot = regex_slot
        
        # 确保正则槽可见
        self.regex_slot.setVisible(True)
        
        # 重新设置底部分割器
        bottom_splitter = self.setup_bottom_splitter()
            
        # 重新连接信号
        try:
            self.regex_slot.regex_check_signal.disconnect()  # 先断开可能的旧连接
        except:
            pass
        self.regex_slot.regex_check_signal.connect(self.handle_regex_check_results)
        
        # 重新设置双击事件
        self.regex_slot.mouseDoubleClickEvent = lambda event: self.on_regex_slot_double_click(event)
        
        # 调整布局
        QTimer.singleShot(100, self.adjust_layout_visibility)
        
        # 确保正则槽显示内容
        if hasattr(self.regex_slot, 'load_regex_groups'):
            self.regex_slot.load_regex_groups()

    def setup_bottom_splitter(self):
        """设置底部分割器"""
        # 移除旧的底部分割器（如果存在）
        main_splitter = None
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item.widget() and isinstance(item.widget(), QSplitter) and item.widget().orientation() == Qt.Vertical:
                main_splitter = item.widget()
                break
                
        if main_splitter is None:
            return None
            
        # 移除旧的底部分割器
        if main_splitter.count() > 1:
            old_widget = main_splitter.widget(1)
            if old_widget:
                old_widget.setParent(None)
                
        # 创建新的底部分割器
        bottom_splitter = QSplitter(Qt.Horizontal)
        
        # 创建正则槽（如果尚未创建）
        if not hasattr(self, 'regex_slot') or self.regex_slot is None:
            self.regex_slot = RegexSlot(self.file_slot.file_tree)
            self.regex_slot.regex_check_signal.connect(self.handle_regex_check_results)
            # 为正则槽添加双击事件
            self.regex_slot.mouseDoubleClickEvent = lambda event: self.on_regex_slot_double_click(event)
            
        # 创建预设组（如果尚未创建）
        if not hasattr(self, 'preset_group') or self.preset_group is None:
            self.setup_preset_group()
            
        # 添加正则槽到分割器
        bottom_splitter.addWidget(self.regex_slot)
            
        # 添加预设组到分割器
        bottom_splitter.addWidget(self.preset_group)
        
        # 设置预设槽和正则槽的比例
        bottom_splitter.setStretchFactor(0, 3)  # 正则槽
        bottom_splitter.setStretchFactor(1, 1)  # 预设槽
        
        # 将底部分割器添加到主分割器
        main_splitter.addWidget(bottom_splitter)
        
        # 设置主分割器的初始大小比例
        main_splitter.setStretchFactor(0, 2)  # 文件槽
        main_splitter.setStretchFactor(1, 1)  # 底部分割器
        
        return bottom_splitter
        
    def setup_preset_group(self):
        """设置预设组"""
        self.preset_group = QGroupBox("预设")
        preset_layout = QVBoxLayout(self.preset_group)
        preset_layout.setContentsMargins(5, 5, 5, 5)

        # 预设组下拉框和操作按钮的水平布局
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
        
        # 为预设槽添加双击事件处理
        self.preset_group.mouseDoubleClickEvent = lambda event: self.on_preset_slot_double_click(event)

    def on_preset_slot_double_click(self, event):
        """处理预设槽的双击事件"""
        # 创建独立的预设槽窗口
        from ui.preset_slot_window import PresetSlotWindow
        
        # 获取预设组合框和列表
        preset_combo = self.preset_combo
        preset_list = self.preset_list
        preset_action_button = self.preset_action_button
        execute_preset_button = self.execute_preset_button
        
        # 创建一个临时的预设槽控件
        preset_widget = QWidget()
        preset_layout = QVBoxLayout(preset_widget)
        preset_layout.setContentsMargins(5, 5, 5, 5)
        
        # 将控件添加到临时控件中
        group_layout = QHBoxLayout()
        group_layout.addWidget(preset_combo, 1)
        group_layout.addWidget(preset_action_button)
        preset_layout.addLayout(group_layout)
        preset_layout.addWidget(preset_list)
        button_layout = QHBoxLayout()
        button_layout.addWidget(execute_preset_button)
        preset_layout.addLayout(button_layout)
        
        # 创建独立窗口
        self.preset_window = PresetSlotWindow(preset_widget)
        # 连接关闭信号
        self.preset_window.closed.connect(self.on_preset_window_closed)
        
        # 隐藏主界面的预设槽区域
        self.preset_group.setVisible(False)
        # 调整主窗口大小
        self.window().adjust_window_size()

    def on_preset_window_closed(self, preset_widget):
        """处理预设槽窗口关闭事件"""
        # 将预设槽控件重新添加到主窗口
        if hasattr(self, 'preset_group'):
            # 获取临时控件中的组件
            temp_layout = preset_widget.layout()
            
            # 获取预设组合框和列表
            group_layout = temp_layout.itemAt(0).layout()
            preset_combo = group_layout.itemAt(0).widget()
            preset_action_button = group_layout.itemAt(1).widget()
            preset_list = temp_layout.itemAt(1).widget()
            button_layout = temp_layout.itemAt(2).layout()
            execute_preset_button = button_layout.itemAt(0).widget()
            
            # 更新主窗口中的引用
            self.preset_combo = preset_combo
            self.preset_action_button = preset_action_button
            self.preset_list = preset_list
            self.execute_preset_button = execute_preset_button
            
            # 清除现有的控件
            preset_layout = self.preset_group.layout()
            while preset_layout.count():
                item = preset_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            
            # 重新添加控件
            new_group_layout = QHBoxLayout()
            new_group_layout.addWidget(preset_combo, 1)
            new_group_layout.addWidget(preset_action_button)
            preset_layout.addLayout(new_group_layout)
            preset_layout.addWidget(preset_list)
            new_button_layout = QHBoxLayout()
            new_button_layout.addWidget(execute_preset_button)
            preset_layout.addLayout(new_button_layout)
            
            # 显示预设槽区域
            self.preset_group.setVisible(True)
            # 调整主窗口大小
            self.window().adjust_window_size()

    def show_delete_preset_dialog(self):
        presets = self.get_preset_names_from_db()
        if not presets:
            QMessageBox.information(self, "提示", "没有可删除的预设")
            return

        dialog = DeletePresetDialog(presets)
        if dialog.exec():
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
        # 如果找不到对应的扩展名不返回
        return mime_to_ext.get(mime_type, '')

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
        # 直接调用文件槽的方法
        return self.file_slot.get_full_path(item)

    def quick_open_file(self, file_path):
        # 直接调用文件槽的方法
        self.file_slot.quick_open_file(file_path)

    def open_csv_file(self, file_path):
        # 直接调用文件槽的方法
        self.file_slot.open_csv_file(file_path)

    def open_file_dir(self, file_path):
        # 直接调用文件槽的方法
        self.file_slot.open_file_dir(file_path)

    def open_text_file(self, file_path):
        # 直接调用文件槽的方法
        self.file_slot.open_text_file(file_path)

    def open_image_file(self, file_path):
        # 直接调用文件槽的方法
        self.file_slot.open_image_file(file_path)

    def open_other_file(self, file_path):
        # 直接调用文件槽的方法
        self.file_slot.open_other_file(file_path)

    def delete_selected_file(self, file_path):
        # 直接调用文件槽的方法
        self.file_slot.delete_selected_file(file_path)

    def show_sort_menu(self):
        menu = QMenu(self)
        menu.addAction("按名称排序", lambda: self.file_slot.file_tree.sortItems(0, Qt.AscendingOrder))
        menu.addAction("按大小排序", lambda: self.file_slot.file_tree.sortItems(1, Qt.AscendingOrder))
        menu.addAction("按修改日期排序", lambda: self.file_slot.file_tree.sortItems(2, Qt.AscendingOrder))
        menu.exec(QCursor.position().toPoint())

    def hide_file_slot(self):
        """隐藏文件槽"""
        if hasattr(self, 'file_slot_container'):
            self.file_slot_container.setVisible(False)
            # 使用定时器延迟调整布局，确保UI状态已完全更新
            QTimer.singleShot(100, self.adjust_layout_visibility)
    
    def show_file_slot(self):
        """显示文件槽"""
        if hasattr(self, 'file_slot_container'):
            self.file_slot_container.setVisible(True)
            # 使用定时器延迟调整布局，确保UI状态已完全更新
            QTimer.singleShot(100, self.adjust_layout_visibility)
            
    def add_file_slot_back(self, file_slot):
        """将文件槽控件重新添加到主窗口"""
        #print(f"开始添加文件槽回主窗口，ID: {id(file_slot)}")
        
        # 确保文件槽没有父控件
        if file_slot.parent():
            #print(f"文件槽有父控件: {file_slot.parent()}")
            file_slot.setParent(None)
            
        # 更新文件槽引用
        self.file_slot = file_slot
        
        # 找到文件槽容器
        if hasattr(self, 'file_slot_container'):
            # 清除现有的控件
            file_slot_layout = self.file_slot_container.layout()
            while file_slot_layout.count():
                item = file_slot_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            
            # 添加回文件槽控件
            file_slot_layout.addWidget(file_slot)
            
            # 重新连接信号
            self.file_slot.pack_files_signal.connect(self.pack_files)
            self.file_slot.clear_files_signal.connect(self.clear_files)
            
            # 为文件槽添加双击事件
            self.file_slot.mouseDoubleClickEvent = lambda event: self.window().on_file_slot_double_click(event)
            
            # 显示文件槽容器
            self.file_slot_container.setVisible(True)
            
            # 调整布局
            QTimer.singleShot(100, self.adjust_layout_visibility)
        else:
            print("错误：找不到文件槽容器")

    def adjust_layout_visibility(self):
        """根据当前可见组件调整布局空间"""
        # 获取主分割器
        main_splitter = None
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item.widget() and isinstance(item.widget(), QSplitter) and item.widget().orientation() == Qt.Vertical:
                main_splitter = item.widget()
                break
                
        if not main_splitter:
            return
            
        # 检查文件槽可见性
        file_slot_visible = hasattr(self, 'file_slot_container') and self.file_slot_container.isVisible()
        
        # 检查底部分割器中组件的可见性
        bottom_visible = False
        if main_splitter.count() > 1:
            bottom_splitter = main_splitter.widget(1)
            # 检查底部分割器中是否有可见组件
            for i in range(bottom_splitter.count()):
                if bottom_splitter.widget(i) and bottom_splitter.widget(i).isVisible():
                    bottom_visible = True
                    break
        # 新增：根据底部组件可见性隐藏或显示底部分割器及其手柄
        if main_splitter.count() > 1:
            bottom_splitter = main_splitter.widget(1)
            bottom_splitter.setVisible(bottom_visible)
            handle = main_splitter.handle(1)
            handle.setVisible(bottom_visible)
        
        # 设置分割器比例
        if file_slot_visible and bottom_visible:
            # 文件槽和底部组件都可见 - 使用默认比例
            main_splitter.setStretchFactor(0, 2)  # 文件槽
            main_splitter.setStretchFactor(1, 1)  # 底部分割器
        elif file_slot_visible and not bottom_visible:
            # 只有文件槽可见 - 文件槽占用全部空间
            main_splitter.setStretchFactor(0, 1)  # 文件槽
            main_splitter.setStretchFactor(1, 0)  # 底部分割器
        elif not file_slot_visible and bottom_visible:
            # 只有底部组件可见 - 底部组件占用全部空间
            main_splitter.setStretchFactor(0, 0)  # 文件槽
            main_splitter.setStretchFactor(1, 1)  # 底部分割器
        else:
            # 两者都不可见 - 默认比例
            main_splitter.setStretchFactor(0, 1)
            main_splitter.setStretchFactor(1, 1)
        
        # 刷新UI
        QApplication.processEvents()

    def closeEvent(self, event):
        for viewer in self.viewers:
            viewer.close()
        self.viewers.clear()
        super().closeEvent(event)

    def load_preset_names(self):
        conn = sqlite3.connect('db/presets.db')
        c = conn.cursor()
        
        # 确保表存在
        c.execute('''CREATE TABLE IF NOT EXISTS presets
                     (name TEXT, button_text TEXT)''')
        
        c.execute("SELECT DISTINCT name FROM presets")
        preset_names = c.fetchall()
        conn.close()

        self.preset_combo.clear()
        self.preset_combo.addItem("选择预设")
        for name in preset_names:
            self.preset_combo.addItem(name[0])
        
        # 如果有预设，默认选择第一个
        if preset_names:
            self.preset_combo.setCurrentIndex(1)  # 对应第一个预设
            self.load_preset()  # 加载选中预设的内容

    def set_regex_slot_visibility(self, visible):
        """设置正则槽的可见性"""
        if hasattr(self, 'regex_slot'):
            self.regex_slot.setVisible(visible)
            # 调整布局
            QTimer.singleShot(100, self.adjust_layout_visibility)
    
    def set_preset_slot_visibility(self, visible):
        """设置预设的可见性"""
        if hasattr(self, 'preset_group'):
            self.preset_group.setVisible(visible)
            # 调整布局
            QTimer.singleShot(100, self.adjust_layout_visibility)

class DeletePresetDialog(QDialog):
    def __init__(self, presets):
        super().__init__()
        self.setWindowTitle("删除预设")
        self.setLayout(QVBoxLayout())
        self.setWindowIcon(QIcon(r"res\logo.ico"))

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
