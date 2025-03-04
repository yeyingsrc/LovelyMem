from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QMessageBox, QMenu, QGroupBox, QComboBox, QDialog, QCheckBox, QDialogButtonBox, QLabel, QLineEdit, QToolButton
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon
import re
import csv
import os
import sqlite3
from ui.styles import background_color,text_color,button_bg_color,button_text_color

class NewRegexDialog(QDialog):
    def __init__(self, file_tree):
        super().__init__()
        self.setWindowTitle("添加正则表达式")
        self.setLayout(QVBoxLayout())
        self.setWindowIcon(QIcon(r"res\logo.ico"))

        self.regex_input = QLineEdit()
        self.regex_input.setPlaceholderText("输入正则表达式")
        self.layout().addWidget(QLabel("正则表达式:"))
        self.layout().addWidget(self.regex_input)

        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("输入添加理由")
        self.layout().addWidget(QLabel("添加理由:"))
        self.layout().addWidget(self.reason_input)

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.MultiSelection)
        self.populate_file_list(file_tree)
        self.layout().addWidget(QLabel("选择匹配文件:"))
        self.layout().addWidget(self.file_list)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout().addWidget(button_box)

    def populate_file_list(self, file_tree):
        def traverse_tree(item):
            for i in range(item.childCount()):
                child = item.child(i)
                if child.childCount() == 0:  # 这是一个文件
                    file_name = child.text(0)
                    if not file_name.lower().endswith('.json'):
                        self.file_list.addItem(file_name)
                else:  # 这是一个文件夹
                    traverse_tree(child)

        root = file_tree.invisibleRootItem()
        traverse_tree(root)

    def get_regex(self):
        return self.regex_input.text()

    def get_reason(self):
        return self.reason_input.text()

    def get_selected_files(self):
        if not self.file_list.selectedItems():
            return False
        else:
            return [item.text() for item in self.file_list.selectedItems()]

class NewRegexGroupDialog(QDialog):
    def __init__(self, file_tree):
        super().__init__()
        self.setWindowTitle("新增/编辑正则组")
        self.setLayout(QVBoxLayout())
        self.setWindowIcon(QIcon(r"res\logo.ico"))

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入正则组名称")
        self.layout().addWidget(self.name_input)

        self.file_combo = QComboBox()
        self.file_combo.addItem("所有文件")
        self.populate_file_combo(file_tree)
        self.layout().addWidget(QLabel("选择指定文件:"))
        self.layout().addWidget(self.file_combo)

        self.db_choice = QComboBox()
        self.db_choice.addItems(["用户数据库", "默认数据库"])
        self.layout().addWidget(QLabel("选择数据库:"))
        self.layout().addWidget(self.db_choice)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout().addWidget(button_box)

    def populate_file_combo(self, file_tree):
        def traverse_tree(item):
            for i in range(item.childCount()):
                child = item.child(i)
                if child.childCount() == 0:  # 这是一个文件
                    file_name = child.text(0)
                    if not file_name.lower().endswith('.json'):
                        self.file_combo.addItem(file_name)
                else:  # 这是一个文件夹
                    traverse_tree(child)

        root = file_tree.invisibleRootItem()
        traverse_tree(root)

    def get_group_name(self):
        return self.name_input.text()

    def get_selected_file(self):
        return self.file_combo.currentText()

    def get_selected_db(self):
        return "user" if self.db_choice.currentText() == "用户数据库" else "default"

class DeleteRegexGroupDialog(QDialog):
    def __init__(self, groups):
        super().__init__()
        self.setWindowTitle("删除正则组")
        self.setLayout(QVBoxLayout())
        self.setWindowIcon(QIcon(r"res\logo.ico"))

        self.checkboxes = []
        for group, file in groups:
            checkbox = QCheckBox(f"{group} ({file})")
            self.checkboxes.append(checkbox)
            self.layout().addWidget(checkbox)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout().addWidget(button_box)

    def get_selected_groups(self):
        return [cb.text().split(" (")[0] for cb in self.checkboxes if cb.isChecked()]

class RegexSlot(QGroupBox):
    regex_check_signal = Signal(list)  # 发送匹配结果的信号

    def __init__(self, file_tree):
        super().__init__("正则槽")
        self.file_tree = file_tree  # 保存 file_tree 作为类的属性
        self.init_databases()  # 首先初始化数据库
        self.setup_ui()
        self.load_regex_groups()  # 然后加载正则组
        self.load_regex_from_db()  # 加载当前选中组的正则表达式

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 10)  # 为标题留出空间

        # 正则组下拉框和操作按钮的水平布局
        group_layout = QHBoxLayout()

        # 正则组下拉框
        self.regex_group_combo = QComboBox()
        self.regex_group_combo.addItem("选择正则组")
        self.regex_group_combo.currentIndexChanged.connect(self.handle_group_selection)
        group_layout.addWidget(self.regex_group_combo, 1)  # 设置拉伸因子为1

        # 操作按钮
        self.group_action_button = QToolButton()
        self.group_action_button.setText("操作")
        self.group_action_button.setPopupMode(QToolButton.InstantPopup)
        self.setup_group_action_menu()
        group_layout.addWidget(self.group_action_button)

        layout.addLayout(group_layout)

        # 正则表达式列表
        self.regex_list = QListWidget()
        self.regex_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.regex_list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.regex_list)

        # 按钮布局
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("添加")
        self.check_button = QPushButton("快速检查")

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.check_button)

        # 将按钮布局添加到主布局
        layout.addLayout(button_layout)

        # 连接信号和槽
        self.add_button.clicked.connect(self.show_add_regex_dialog)
        self.check_button.clicked.connect(self.quick_check)


    def setup_group_action_menu(self):
        #按钮名称 操作
        menu = QMenu(self)
        menu.addAction("新增正则组", self.add_new_regex_group)
        menu.addAction("编辑正则组", self.edit_regex_group)
        menu.addAction("删除正则组", self.show_delete_groups_dialog)
        self.group_action_button.setMenu(menu)
        self.group_action_button.setText("操作")

    def load_regex_groups(self):
        current_group = self.regex_group_combo.currentText().split(" (")[0]
        self.regex_group_combo.clear()
        self.regex_group_combo.addItem("选择正则组")
        
        groups = []
        for db, db_type in [(self.default_db, "默认"), (self.user_db, "用户")]:
            c = db.cursor()
            c.execute("SELECT name, file FROM regex_groups")
            groups.extend([(name, file, db_type) for name, file in c.fetchall()])
        
        for group, file, db_type in groups:
            display_text = f"{group} ({file}) - {db_type}"
            self.regex_group_combo.addItem(display_text, (group, db_type))
        
        if groups:
            if current_group != "选择正则组":
                index = self.regex_group_combo.findText(current_group, Qt.MatchStartsWith)
                if index != -1:
                    self.regex_group_combo.setCurrentIndex(index)
                else:
                    self.regex_group_combo.setCurrentIndex(1)  # 选择第一个正则组
            else:
                self.regex_group_combo.setCurrentIndex(1)  # 选择第一个正则组
        
        self.load_regex_from_db()  # 加载当前选中组的正则表达式

    def get_regex_groups_from_db(self):
        groups = set()
        for db in [self.user_db, self.default_db]:
            c = db.cursor()
            c.execute("SELECT name, file FROM regex_groups")
            groups.update(c.fetchall())
        return list(groups)

    def handle_group_selection(self, index):
        if index > 0:  # 确保选择的不是 "选择正则组"
            self.load_regex_from_db()
        else:
            self.regex_list.clear()

    def get_group_file(self, group_name, db):
        c = db.cursor()
        c.execute("SELECT file FROM regex_groups WHERE name = ?", (group_name,))
        result = c.fetchone()
        if result:
            return result[0]
        return "所有文件"

    def edit_regex_group(self):
        current_index = self.regex_group_combo.currentIndex()
        if current_index > 0:
            current_group, current_db_type = self.regex_group_combo.itemData(current_index)
            db = self.user_db if current_db_type == "用户" else self.default_db
            current_file = self.get_group_file(current_group, db)
            dialog = NewRegexGroupDialog(self.file_tree)
            dialog.name_input.setText(current_group)
            dialog.file_combo.setCurrentText(current_file)
            dialog.db_choice.setCurrentText("用户数据库" if current_db_type == "用户" else "默认数据库")
            
            if dialog.exec_():
                new_name = dialog.get_group_name()
                new_file = dialog.get_selected_file()
                new_db_type = dialog.get_selected_db()
                if new_name:
                    if new_name != current_group or new_file != current_file or new_db_type != current_db_type:
                        self.update_regex_group(current_group, new_name, new_file, current_db_type, new_db_type)
                        self.load_regex_groups()
                        # 更新后，重新选择编辑后的组
                        index = self.regex_group_combo.findText(f"{new_name} ({new_file})", Qt.MatchStartsWith)
                        if index != -1:
                            self.regex_group_combo.setCurrentIndex(index)
                else:
                    QMessageBox.warning(self, "警告", "正则组名称不能为空")
        else:
            QMessageBox.warning(self, "警告", "请先选择一个正则组")

    def update_regex_group(self, old_name, new_name, new_file, old_db_type, new_db_type):
        old_db = self.user_db if old_db_type == "用户" else self.default_db
        new_db = self.user_db if new_db_type == "user" else self.default_db

        # 从旧数据库删除
        c = old_db.cursor()
        c.execute("DELETE FROM regex_groups WHERE name = ?", (old_name,))
        c.execute("DELETE FROM regex WHERE group_name = ?", (old_name,))
        old_db.commit()

        # 添加到新数据库
        c = new_db.cursor()
        c.execute("INSERT INTO regex_groups (name, file) VALUES (?, ?)", (new_name, new_file))
        c.execute("UPDATE regex SET group_name = ? WHERE group_name = ?", (new_name, old_name))
        new_db.commit()

    def add_new_regex_group(self):
        dialog = NewRegexGroupDialog(self.file_tree)
        if dialog.exec_():
            group_name = dialog.get_group_name()
            selected_file = dialog.get_selected_file()
            selected_db = dialog.get_selected_db()
            if group_name:
                if group_name not in [self.regex_group_combo.itemData(i)[0] for i in range(self.regex_group_combo.count()) if self.regex_group_combo.itemData(i)]:
                    display_text = f"{group_name} ({selected_file}) - {'用户' if selected_db == 'user' else '默认'}"
                    self.regex_group_combo.addItem(display_text, (group_name, selected_db))
                    self.regex_group_combo.setCurrentText(display_text)
                    self.save_regex_group(group_name, selected_file, selected_db)
                    self.load_regex_from_db()
                else:
                    QMessageBox.warning(self, "警告", "该正则组名称已存在")
            else:
                QMessageBox.warning(self, "警告", "正则组名称不能为空")

    def save_regex_group(self, group_name, file, db_choice):
        db = self.user_db if db_choice == "user" else self.default_db
        c = db.cursor()
        c.execute("INSERT OR REPLACE INTO regex_groups (name, file) VALUES (?, ?)", (group_name, file))
        db.commit()

    def show_delete_groups_dialog(self):
        groups = self.get_regex_groups_from_db()
        if not groups:
            QMessageBox.information(self, "提示", "没有可删除的正则组")
            return
        dialog = DeleteRegexGroupDialog(groups)
        
        # 添加数据库选择
        dialog.db_choice = QComboBox()
        dialog.db_choice.addItems(["用户数据库", "默认数据库"])
        dialog.layout().insertWidget(dialog.layout().count() - 1, QLabel("选择数据库:"))
        dialog.layout().insertWidget(dialog.layout().count() - 1, dialog.db_choice)
        
        if dialog.exec_():
            selected_groups = dialog.get_selected_groups()
            selected_db = "user" if dialog.db_choice.currentText() == "用户数据库" else "default"
            for group in selected_groups:
                self.delete_regex_group(group, selected_db)
            self.load_regex_groups()

    def delete_regex_group(self, group_name, db_type):
        db = self.user_db if db_type == "用户" else self.default_db
        c = db.cursor()
        c.execute("DELETE FROM regex_groups WHERE name = ?", (group_name,))
        c.execute("DELETE FROM regex WHERE group_name = ?", (group_name,))
        db.commit()

        # 从下拉框中移除该组
        self.regex_group_combo.blockSignals(True)  # 阻止信号触发
        for i in range(self.regex_group_combo.count()):
            if self.regex_group_combo.itemData(i) == group_name:
                self.regex_group_combo.removeItem(i)
                break
        if self.regex_group_combo.currentData() == group_name:
            self.regex_group_combo.setCurrentIndex(0)
        self.regex_group_combo.blockSignals(False)  # 恢复信号

        # 清空正则表达式列表
        self.regex_list.clear()

    def show_add_regex_dialog(self):
        current_group = self.regex_group_combo.currentData()
        if current_group is None:
            QMessageBox.warning(self, "警告", "请先选择一个正则组")
            return

        dialog = NewRegexDialog(self.file_tree)  # 传入 file_tree 而不是 file_list
        if dialog.exec_():
            regex = dialog.get_regex()
            reason = dialog.get_reason()
            selected_files = dialog.get_selected_files()
            if regex and selected_files != False:
                self.regex_list.addItem(f"{regex} ({', '.join(selected_files)}) - {reason}")
                db = self.user_db if current_group[1] == "用户" else self.default_db
                self.save_regex_to_db(regex, selected_files, reason, db, current_group[0])
            else:
                QMessageBox.warning(self, "警告", "正则表达式不能为空或未选择文件")

    def add_regex(self):
        regex = self.regex_input.text()
        if regex:
            self.regex_list.addItem(regex)
            self.regex_input.clear()
            self.save_regex_to_db(regex)

    def delete_regex(self):
        current_item = self.regex_list.currentItem()
        if current_item:
            regex_text = current_item.text()
            regex, _ = regex_text.split(" (", 1)  # 提取正则表达式部分
            current_group = self.regex_group_combo.currentData()
            if current_group:
                group_name, db_type = current_group
                db = self.user_db if db_type == "用户" else self.default_db
                if self.delete_regex_from_db(regex, group_name, db):
                    self.regex_list.takeItem(self.regex_list.row(current_item))
                    QMessageBox.information(self, "成功", "正则表达式已成功删除")
                else:
                    QMessageBox.warning(self, "错误", "删除正则表达式时出现问题")
            else:
                QMessageBox.warning(self, "警告", "请先选择一个正则组")

    def save_regex_to_db(self, regex, files, reason, db, group_name):
        c = db.cursor()
        c.execute("INSERT OR REPLACE INTO regex (group_name, pattern, files, reason) VALUES (?, ?, ?, ?)", 
                  (group_name, regex, ','.join(files), reason))
        db.commit()
        print(f"保存正则表达式到数据库: {regex}")  # 添加调试信息

    def delete_regex_from_db(self, regex, group_name, db):
        try:
            c = db.cursor()
            c.execute("DELETE FROM regex WHERE group_name = ? AND pattern = ?", (group_name, regex))
            db.commit()
            print(f"从数据库删除正则表达式: {regex}")  # 添加调试信息
            return True
        except sqlite3.Error as e:
            print(f"删除正则表达式时出错: {e}")
            return False

    def load_regex_from_db(self):
        current_group = self.regex_group_combo.currentData()
        if current_group is None or current_group[0] == "选择正则组":
            return

        self.regex_list.clear()
        group_name, db_type = current_group
        db = self.user_db if db_type == "用户" else self.default_db
        c = db.cursor()
        c.execute("SELECT pattern, files, reason FROM regex WHERE group_name = ?", (group_name,))
        patterns = c.fetchall()
        for pattern, files, reason in patterns:
            item_text = f"{pattern} ({files}) - {reason}"
            self.regex_list.addItem(item_text)
            #print(f"从数据库加载正则表达式: {pattern}")  # 添加调试信息

    def quick_check(self):
        regex_items = [self.regex_list.item(i).text() for i in range(self.regex_list.count())]
        if not regex_items:
            QMessageBox.warning(self, "警告", "请先添加正则表达式")
            return

        results = []
        for regex_item in regex_items:
            pattern, files_str = regex_item.split(" (", 1)
            files_and_reason = files_str.rsplit(") - ", 1)
            files = [f.strip() for f in files_and_reason[0].split(",")]  # 使用逗号分割文件名并去除空格
            reason = files_and_reason[1] if len(files_and_reason) > 1 else ""
            
            print(f"正在使用正则表达式: {pattern}")
            try:
                compiled_pattern = re.compile(pattern)
            except re.error as e:
                print(f"正则表达式编译错误: {pattern}, 错误: {str(e)}")
                continue

            for file_name in files:
                file_name = file_name.strip()  # 移除可能的前后空格
                file_path = os.path.join("output", file_name)
                print(f"正在查询文件: {file_path}")
                if os.path.exists(file_path):
                    if file_name.lower().endswith('.json'):
                        print(f"跳过JSON文件: {file_name}")
                        continue
                    is_csv = file_name.lower().endswith('.csv')
                    if is_csv:
                        print(f"正在处理CSV文件: {file_name}")
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as csvfile:
                            csv_reader = csv.reader(csvfile)
                            headers = next(csv_reader)  # 读取表头
                            for line_number, row in enumerate(csv_reader, 2):  # 从2开始，因为第1行是表头
                                line = ','.join(row)
                                match = compiled_pattern.search(line)
                                if match:
                                    results.append([file_name, line_number, ','.join(headers), line.strip(), pattern, reason])
                    else:
                        print(f"正在处理普通文本文件: {file_name}")
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                            for line_number, line in enumerate(file, 1):
                                match = compiled_pattern.search(line)
                                if match:
                                    results.append([file_name, line_number, '', match.group(), pattern, reason])
                else:
                    print(f"文件不存在: {file_path}")

        if results:
            self.save_results_to_csv(results)
            self.regex_check_signal.emit(results)
        else:
            QMessageBox.information(self, "结果", "没有找到匹配的内容")

    def save_results_to_csv(self, results):
        output_file = "output/regex_check_results.csv"
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["文件名", "行号", "表头", "匹配内容", "匹配的正则", "理由"])
            writer.writerows(results)
        QMessageBox.information(self, "保存成功", f"结果已保存到 {output_file}")

    # 添加这个新方法
    def show_context_menu(self, position):
        context_menu = QMenu(self)
        delete_action = context_menu.addAction("删除")
        edit_action = context_menu.addAction("编辑")
        
        action = context_menu.exec_(self.regex_list.mapToGlobal(position))
        
        if action == delete_action:
            self.delete_regex()
        elif action == edit_action:
            self.edit_regex()

    def edit_regex(self):
        current_item = self.regex_list.currentItem()
        if current_item:
            current_text = current_item.text()
            regex, rest = current_text.split(" (", 1)
            files_and_reason = rest.rsplit(") - ", 1)
            files = files_and_reason[0].split(", ")
            reason = files_and_reason[1] if len(files_and_reason) > 1 else ""

            dialog = NewRegexDialog(self.file_tree)  # 使用 self.file_tree 而不是 self.file_list
            dialog.regex_input.setText(regex)
            dialog.reason_input.setText(reason)
            
            # 选中之前选择的文件
            for i in range(dialog.file_list.count()):
                if dialog.file_list.item(i).text() in files:
                    dialog.file_list.item(i).setSelected(True)
            
            if dialog.exec_():
                new_regex = dialog.get_regex()
                new_files = dialog.get_selected_files()
                new_reason = dialog.get_reason()
                if new_regex and new_files != False:
                    current_group = self.regex_group_combo.currentData()
                    if current_group:
                        db = self.user_db if current_group[1] == "用户" else self.default_db
                        self.delete_regex_from_db(regex, current_group[0], db)
                        self.save_regex_to_db(new_regex, new_files, new_reason, db, current_group[0])
                        current_item.setText(f"{new_regex} ({', '.join(new_files)}) - {new_reason}")
                    else:
                        QMessageBox.warning(self, "警告", "请先选择一个正则组")
                else:
                    QMessageBox.warning(self, "警告", "正则表达式不能为空或未选择文件")

    def init_databases(self):
        self.user_db = sqlite3.connect('db/user_regex.db')
        self.default_db = sqlite3.connect('db/default_regex.db')
        self.create_tables(self.user_db)
        self.create_tables(self.default_db)

    def create_tables(self, db):
        c = db.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS regex_groups
                     (name TEXT PRIMARY KEY, file TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS regex
                     (group_name TEXT, pattern TEXT, files TEXT, reason TEXT, 
                      PRIMARY KEY (group_name, pattern))''')
        db.commit()

    def closeEvent(self, event):
        self.user_db.close()
        self.default_db.close()
        super().closeEvent(event)