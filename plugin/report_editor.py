from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                              QPushButton, QComboBox, QLineEdit, QLabel, 
                              QMessageBox, QFileDialog, QSplitter, QListWidget,
                              QDialog, QDialogButtonBox, QFormLayout)
from PySide6.QtCore import Qt,QUrl
import re
import os
import json
import markdown
from ui.styles import (get_color_scheme, is_dark_mode, report_editor_style,
                      button_style, cmd_output_style)
from core.config_manager import get_saved_theme

class ExtractRule:
    def __init__(self, name="", file_pattern="", regex_pattern="", template_text=""):
        self.name = name
        self.file_pattern = file_pattern  # 文件名模式,支持通配符
        self.regex_pattern = regex_pattern
        self.template_text = template_text  # 模板文本,包含占位符

class RuleEditDialog(QDialog):
    def __init__(self, parent=None, rule=None):
        super().__init__(parent)
        self.setWindowTitle("编辑提取规则")
        self.setup_ui(rule)
        self.update_theme()

    def setup_ui(self, rule):
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        
        # 创建文件选择组合控件
        file_widget = QWidget()
        file_layout = QHBoxLayout(file_widget)
        file_layout.setContentsMargins(0, 0, 0, 0)
        
        self.file_pattern_edit = QLineEdit()
        self.file_pattern_edit.setPlaceholderText("输入文件模式或选择文件(如 *.txt)")
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_file)
        
        file_layout.addWidget(self.file_pattern_edit)
        file_layout.addWidget(browse_btn)
        
        # 正则表达式部分
        regex_widget = QWidget()
        regex_layout = QHBoxLayout(regex_widget)
        regex_layout.setContentsMargins(0, 0, 0, 0)
        
        self.regex_pattern_edit = QLineEdit()
        test_regex_btn = QPushButton("测试")
        test_regex_btn.clicked.connect(self.test_regex)
        
        regex_layout.addWidget(self.regex_pattern_edit)
        regex_layout.addWidget(test_regex_btn)
        
        self.template_edit = QTextEdit()

        if rule:
            self.name_edit.setText(rule.name)
            self.file_pattern_edit.setText(rule.file_pattern)
            self.regex_pattern_edit.setText(rule.regex_pattern)
            self.template_edit.setText(rule.template_text)

        layout.addRow("规则名称:", self.name_edit)
        layout.addRow("文件选择:", file_widget)
        layout.addRow("正则表达式:", regex_widget)
        layout.addRow("模板文本:", self.template_edit)

        # 添加示例说明
        example_label = QLabel(
            "示例说明:\n"
            "1. 文件选择支持:\n"
            "   - 直接选择文件\n"
            "   - 输入通配符模式(如 *.txt)\n"
            "   - 输入相对路径(如 output/*.txt)\n"
            "2. 正则表达式示例:\n"
            "   - Computer Name:\\s*(.+)  # 提取计算机名\n"
            "   - LSA Key:\\s*([a-f0-9]+)  # 提取LSA密钥\n"
            "3. 模板文本中使用占位符:\n"
            "   - {match} 表示完整匹配\n"
            "   - {match1}, {match2} 表示捕获组\n"
            "4. 支持多行模板文本"
        )
        layout.addRow(example_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def browse_file(self):
        """打开文件选择对话框"""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setViewMode(QFileDialog.Detail)
        
        # 设置初始目录为output
        file_dialog.setDirectory("output")
        
        # 添加快捷方式
        file_dialog.setSidebarUrls([
            QUrl.fromLocalFile("output"),
            QUrl.fromLocalFile("logs"),
            QUrl.fromLocalFile("config")
        ])
        
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                # 获取相对路径
                abs_path = selected_files[0]
                try:
                    rel_path = os.path.relpath(abs_path)
                    self.file_pattern_edit.setText(rel_path)
                except ValueError:
                    # 如果无法获取相对路径，使用绝对路径
                    self.file_pattern_edit.setText(abs_path)

    def test_regex(self):
        """测试正则表达式"""
        pattern = self.regex_pattern_edit.text()
        if not pattern:
            QMessageBox.warning(self, "警告", "请输入正则表达式")
            return
            
        file_pattern = self.file_pattern_edit.text()
        if not file_pattern:
            QMessageBox.warning(self, "警告", "请选择或输入文件模式")
            return
            
        try:
            # 编译正则表达式以验证语法
            regex = re.compile(pattern)
            
            # 查找匹配的文件
            matches = []
            # 获取文件路径
            if os.path.isfile(file_pattern):
                # 如果是具体文件
                files_to_check = [file_pattern]
            else:
                # 如果是通配符模式
                base_dir = os.path.dirname(file_pattern) or "."
                file_pattern_name = os.path.basename(file_pattern)
                if os.path.exists(base_dir):
                    files_to_check = [
                        os.path.join(base_dir, f) 
                        for f in os.listdir(base_dir)
                        if re.match(file_pattern_name.replace("*", ".*"), f)
                    ]
                else:
                    files_to_check = []
            
            # 检查文件内容
            for file_path in files_to_check:
                if os.path.isfile(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 查找所有匹配
                        for match in regex.finditer(content):
                            if match.groups():
                                matches.append(f"捕获组: {match.groups()}")
                            matches.append(f"完整匹配: {match.group(0)}")
            
            if matches:
                QMessageBox.information(self, "测试结果", 
                                      f"找到 {len(matches)} 个匹配:\n\n" + 
                                      "\n".join(matches[:10]) +
                                      ("\n..." if len(matches) > 10 else ""))
            else:
                QMessageBox.warning(self, "测试结果", "未找到匹配")
                
        except re.error as e:
            QMessageBox.critical(self, "正则表达式错误", f"正则表达式语法错误: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"测试时发生错误: {str(e)}")

    def get_rule(self):
        return ExtractRule(
            name=self.name_edit.text(),
            file_pattern=self.file_pattern_edit.text(),
            regex_pattern=self.regex_pattern_edit.text(),
            template_text=self.template_edit.toPlainText()
        )

    def update_theme(self):
        # 获取当前主题
        theme_name = get_saved_theme()
        is_dark = is_dark_mode()
        colors = get_color_scheme(theme_name, is_dark)
        
        # 应用对话框样式
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['background_color']};
                color: {colors['text_color']};
            }}
            QLabel {{
                color: {colors['text_color']};
            }}
            QLineEdit, QTextEdit {{
                background-color: {colors['cmd_output_bg_color']};
                color: {colors['cmd_output_text_color']};
                border: 1px solid {colors['border_color']};
                border-radius: 3px;
                padding: 3px;
            }}
            QPushButton {{
                background-color: {colors['button_bg_color']};
                color: {colors['button_text_color']};
                border: none;
                border-radius: 3px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {colors['button_hover_color']};
            }}
        """)

class ReportEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = []
        self.template_vars = {}  # 存储模板变量的实际值
        self.setup_ui()  # 先创建界面
        self.load_rules()  # 再加载规则
        self.update_theme()  # 最后更新主题
        
        # 监听主题变化
        if parent:
            parent.theme_changed.connect(self.update_theme)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建顶部工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(5)  # 减小按钮间距
        
        # 左侧规则管理区域
        rule_group = QHBoxLayout()
        
        # 规则列表改用下拉框
        self.rule_combo = QComboBox()
        self.rule_combo.setMinimumWidth(150)  # 设置最小宽度
        self.update_rule_list()
        
        # 规则管理按钮
        add_rule_btn = QPushButton("添加")
        edit_rule_btn = QPushButton("编辑")
        delete_rule_btn = QPushButton("删除")
        apply_rule_btn = QPushButton("应用")
        apply_all_btn = QPushButton("应用全部")
        
        # 设置按钮最小宽度
        for btn in [add_rule_btn, edit_rule_btn, delete_rule_btn, apply_rule_btn, apply_all_btn]:
            btn.setMinimumWidth(40)
            btn.setMaximumWidth(70)
        
        add_rule_btn.clicked.connect(self.add_rule)
        edit_rule_btn.clicked.connect(self.edit_rule)
        delete_rule_btn.clicked.connect(self.delete_rule)
        apply_rule_btn.clicked.connect(self.apply_rule)
        apply_all_btn.clicked.connect(self.apply_all_rules)
        
        rule_group.addWidget(QLabel("规则:"))
        rule_group.addWidget(self.rule_combo)
        for btn in [add_rule_btn, edit_rule_btn, delete_rule_btn, apply_rule_btn, apply_all_btn]:
            rule_group.addWidget(btn)
        
        # 右侧模板管理按钮
        template_group = QHBoxLayout()
        save_template_btn = QPushButton("保存模板")
        load_template_btn = QPushButton("加载模板")
        export_md_btn = QPushButton("导出MD")
        
        # 设置按钮最小宽度
        for btn in [save_template_btn, load_template_btn, export_md_btn]:
            btn.setMinimumWidth(60)
            btn.setMaximumWidth(70)
        
        save_template_btn.clicked.connect(self.save_template)
        load_template_btn.clicked.connect(self.load_template)
        export_md_btn.clicked.connect(self.export_markdown)
        
        template_group.addWidget(save_template_btn)
        template_group.addWidget(load_template_btn)
        template_group.addWidget(export_md_btn)
        
        # 添加弹性空间,使规则组靠左,模板组靠右
        toolbar.addLayout(rule_group)
        toolbar.addStretch()
        toolbar.addLayout(template_group)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 创建编辑器和预览区的容器
        editor_container = QWidget()
        editor_layout = QVBoxLayout(editor_container)
        
        # 添加模板变量工具栏
        template_vars_toolbar = QHBoxLayout()
        self.var_combo = QComboBox()
        insert_var_btn = QPushButton("插入变量")
        refresh_var_btn = QPushButton("刷新")
        
        insert_var_btn.clicked.connect(self.insert_template_var)
        refresh_var_btn.clicked.connect(self.update_var_combo)
        
        template_vars_toolbar.addWidget(QLabel("已定义规则:"))
        template_vars_toolbar.addWidget(self.var_combo)
        template_vars_toolbar.addWidget(insert_var_btn)
        template_vars_toolbar.addWidget(refresh_var_btn)
        template_vars_toolbar.addStretch()
        
        # 创建编辑器
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("在这里编写报告内容...")
        
        editor_layout.addLayout(template_vars_toolbar)
        editor_layout.addWidget(self.editor)
        
        # 创建预览区容器
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        
        # 添加预览标题
        preview_header = QHBoxLayout()
        preview_label = QLabel("预览")
        preview_header.addWidget(preview_label)
        preview_header.addStretch()
        
        # 创建预览区
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        
        preview_layout.addLayout(preview_header)
        preview_layout.addWidget(self.preview)
        
        # 将编辑器和预览区添加到分割器
        splitter.addWidget(editor_container)
        splitter.addWidget(preview_container)
        
        # 设置分割器的初始比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        # 添加到主布局
        layout.addLayout(toolbar)
        layout.addWidget(splitter)
        
        # 设置布局的边距和间距
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 连接编辑器的内容变化信号到预览更新函数
        self.editor.textChanged.connect(self.update_preview)

    def load_rules(self):
        try:
            if os.path.exists('config/report_rules.json'):
                with open('config/report_rules.json', 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)
                    self.rules = [ExtractRule(**rule) for rule in rules_data]
                    # 更新规则列表和变量下拉框
                    self.update_rule_list()
                    self.update_var_combo()
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载规则失败: {str(e)}")

    def update_var_combo(self):
        """更新变量下拉框的选项"""
        current_text = self.var_combo.currentText()  # 保存当前选中的项
        
        self.var_combo.clear()
        for rule in self.rules:
            self.var_combo.addItem(rule.name)
        
        # 恢复之前选中的项
        index = self.var_combo.findText(current_text)
        if index >= 0:
            self.var_combo.setCurrentIndex(index)
        
        # 更新预览
        self.update_preview()
        
        # 移除弹窗提示
        # QMessageBox.information(self, "提示", "变量列表已刷新")

    def save_rules(self):
        try:
            os.makedirs('config', exist_ok=True)
            with open('config/report_rules.json', 'w', encoding='utf-8') as f:
                rules_data = [vars(rule) for rule in self.rules]
                json.dump(rules_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"保存规则失败: {str(e)}")

    def update_rule_list(self):
        self.rule_combo.clear()
        for rule in self.rules:
            self.rule_combo.addItem(rule.name)

    def add_rule(self):
        dialog = RuleEditDialog(self)
        if dialog.exec_():
            rule = dialog.get_rule()
            self.rules.append(rule)
            self.update_rule_list()
            self.save_rules()

    def edit_rule(self):
        if self.rule_combo.currentIndex() == -1:
            QMessageBox.warning(self, "警告", "请选择要编辑的规则")
            return
        
        rule_index = self.rule_combo.currentIndex()
        dialog = RuleEditDialog(self, self.rules[rule_index])
        if dialog.exec_():
            self.rules[rule_index] = dialog.get_rule()
            self.update_rule_list()
            self.save_rules()

    def delete_rule(self):
        if self.rule_combo.currentIndex() == -1:
            QMessageBox.warning(self, "警告", "请选择要删除的规则")
            return
        
        rule_name = self.rule_combo.currentText()
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除规则 '{rule_name}' 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            rule_index = self.rule_combo.currentIndex()
            self.rules.pop(rule_index)
            self.update_rule_list()
            self.save_rules()

    def apply_rule(self):
        if self.rule_combo.currentIndex() == -1:
            QMessageBox.warning(self, "警告", "请选择要应用的规则")
            return
        
        rule = self.rules[self.rule_combo.currentIndex()]
        
        try:
            # 查找匹配的文件
            matches = []
            file_pattern = rule.file_pattern
            
            # 处理不同类型的路径
            search_paths = ["output", "logs", "config"]
            
            # 如果是绝对路径
            if os.path.isabs(file_pattern):
                if os.path.isfile(file_pattern):
                    matches.append(file_pattern)
            else:
                # 如果是相对路径，在所有搜索路径中查找
                for search_path in search_paths:
                    full_pattern = os.path.join(search_path, os.path.basename(file_pattern))
                    if os.path.exists(search_path):
                        for file in os.listdir(search_path):
                            full_path = os.path.join(search_path, file)
                            if os.path.isfile(full_path) and re.match(full_pattern.replace("*", ".*"), full_path):
                                matches.append(full_path)
            
            if not matches:
                QMessageBox.warning(self, "警告", f"未找到匹配的文件: {file_pattern}\n已搜索目录: {', '.join(search_paths)}")
                return
            
            # 从匹配的文件中提取内容
            all_matches = []  # 存储所有正则匹配结果
            for file_path in matches:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 查找所有匹配
                        for match in re.finditer(rule.regex_pattern, content, re.MULTILINE):
                            all_matches.append(match)
                except Exception as e:
                    print(f"处理文件 {file_path} 时出错: {str(e)}")
                    continue

            if all_matches:
                # 获取当前光标位置
                cursor = self.editor.textCursor()
                # 处理模板文本
                result = rule.template_text
                
                # 如果模板中包含 {match}，替换为所有完整匹配
                if "{match}" in result:
                    matches_text = "\n".join(m.group(0) for m in all_matches)
                    result = result.replace("{match}", matches_text)
                
                # 处理捕获组
                for i in range(1, 10):  # 支持最多9个捕获组
                    placeholder = f"{{match{i}}}"
                    if placeholder in result:
                        group_matches = []
                        for m in all_matches:
                            if m.groups() and len(m.groups()) >= i:
                                group_matches.append(m.group(i))
                        if group_matches:
                            result = result.replace(placeholder, "\n".join(group_matches))
                
                cursor.insertText(result + "\n")
            else:
                QMessageBox.warning(self, "警告", "未找到匹配内容")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"应用规则时发生错误：{str(e)}")

    def save_template(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存模板",
                "templates",
                "Template Files (*.tpl);;All Files (*)"
            )
            
            if file_path:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.editor.toPlainText())
                QMessageBox.information(self, "成功", "模板已保存！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存模板时发生错误：{str(e)}")

    def load_template(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "加载模板",
                "templates",
                "Template Files (*.tpl);;All Files (*)"
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.editor.setPlainText(f.read())
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载模板时发生错误：{str(e)}")

    def update_preview(self):
        try:
            content = self.editor.toPlainText()
            preview_content = content

            # 为每个规则变量尝试获取示例值
            for rule in self.rules:
                try:
                    # 查找匹配的文件
                    matches = []
                    file_pattern = rule.file_pattern
                    
                    # 处理不同类型的路径
                    search_paths = ["output", "logs", "config"]  # 添加所有可能的搜索路径
                    
                    # 如果是绝对路径
                    if os.path.isabs(file_pattern):
                        if os.path.isfile(file_pattern):
                            matches.append(file_pattern)
                    else:
                        # 如果是相对路径，在所有搜索路径中查找
                        for search_path in search_paths:
                            full_pattern = os.path.join(search_path, os.path.basename(file_pattern))
                            if os.path.exists(search_path):
                                for file in os.listdir(search_path):
                                    full_path = os.path.join(search_path, file)
                                    if os.path.isfile(full_path) and re.match(full_pattern.replace("*", ".*"), full_path):
                                        matches.append(full_path)

                    all_matches = []  # 存储所有匹配结果
                    for file_path in matches:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                                # 查找所有匹配
                                for match in re.finditer(rule.regex_pattern, file_content, re.MULTILINE):
                                    # 使用捕获组或完整匹配
                                    if match.groups():
                                        example_value = match.group(1)  # 使用第一个捕获组
                                    else:
                                        example_value = match.group(0)  # 使用完整匹配
                                    if example_value:  # 确保值不是None
                                        all_matches.append(example_value)
                        except Exception as e:
                            print(f"处理文件 {file_path} 时出错: {str(e)}")
                            continue

                    if all_matches:
                        # 将所有匹配结果组合成一个字符串，用换行符分隔
                        combined_value = "\n".join(all_matches)
                        # 替换模板中的变量
                        preview_content = preview_content.replace(
                            f"{{{rule.name}}}", 
                            combined_value
                        )

                except Exception as e:
                    print(f"处理规则 {rule.name} 时出错: {str(e)}")
                    continue

            # 转换为HTML
            html_content = markdown.markdown(preview_content)
            self.preview.setHtml(html_content)
        except Exception as e:
            self.preview.setPlainText(f"预览更新错误：{str(e)}")

    def export_markdown(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出Markdown",
                "output",
                "Markdown Files (*.md);;All Files (*)"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.editor.toPlainText())
                QMessageBox.information(self, "成功", "报告已成功导出！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出报告时发生错误：{str(e)}")

    def update_theme(self):
        # 获取当前主题
        theme_name = get_saved_theme()
        is_dark = is_dark_mode()
        colors = get_color_scheme(theme_name, is_dark)
        
        # 应用主题样式到整个编辑器
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['background_color']};
                color: {colors['text_color']};
            }}
            QLabel {{
                color: {colors['text_color']};
            }}
            QPushButton {{
                background-color: {colors['button_bg_color']};
                color: {colors['button_text_color']};
                border: none;
                border-radius: 3px;
                padding: 5px;
                min-width: 40px;
                max-width: 70px;
            }}
            QPushButton:hover {{
                background-color: {colors['button_hover_color']};
            }}
            QTextEdit {{
                background-color: {colors['cmd_output_bg_color']};
                color: {colors['cmd_output_text_color']};
                border: 1px solid {colors['border_color']};
                border-radius: 3px;
            }}
            QComboBox {{
                background-color: {colors['button_bg_color']};
                color: {colors['button_text_color']};
                border: 1px solid {colors['border_color']};
                border-radius: 3px;
                padding: 3px;
                min-width: 150px;
            }}
            QComboBox:hover {{
                background-color: {colors['button_hover_color']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
                margin-right: 5px;
            }}
            QSplitter::handle {{
                background-color: {colors['border_color']};
                width: 2px;
            }}
            QSplitter::handle:hover {{
                background-color: {colors['button_hover_color']};
            }}
            QLineEdit {{
                background-color: {colors['cmd_output_bg_color']};
                color: {colors['cmd_output_text_color']};
                border: 1px solid {colors['border_color']};
                border-radius: 3px;
                padding: 3px;
            }}
        """)
        
        # 为特定容器设置样式
        for container in self.findChildren(QWidget):
            if container.layout() is not None:  # 只为有布局的容器设置样式
                container.setStyleSheet(f"""
                    QWidget {{
                        background-color: {colors['background_color']};
                    }}
                """)
        
        # 设置分割器样式
        for splitter in self.findChildren(QSplitter):
            splitter.setStyleSheet(f"""
                QSplitter::handle {{
                    background-color: {colors['border_color']};
                    width: 2px;
                }}
                QSplitter::handle:hover {{
                    background-color: {colors['button_hover_color']};
                }}
            """)
        
        # 设置编辑器和预览区的占位符文本颜色
        placeholder_style = f"""
            QTextEdit {{
                background-color: {colors['cmd_output_bg_color']};
                color: {colors['cmd_output_text_color']};
            }}
            QTextEdit[placeholder]:empty {{
                color: {colors['border_color']};
            }}
        """
        self.editor.setStyleSheet(placeholder_style)
        self.preview.setStyleSheet(placeholder_style)

    def apply_all_rules(self):
        """一键应用所有规则"""
        if not self.rules:
            QMessageBox.warning(self, "警告", "没有可用的规则")
            return
        
        # 记录处理结果
        results = []
        skipped = []
        
        for rule in self.rules:
            try:
                # 查找匹配的文件
                matches = []
                file_pattern = rule.file_pattern
                
                # 处理不同类型的路径
                search_paths = ["output", "logs", "config"]
                
                # 如果是绝对路径
                if os.path.isabs(file_pattern):
                    if os.path.isfile(file_pattern):
                        matches.append(file_pattern)
                else:
                    # 如果是相对路径，在所有搜索路径中查找
                    for search_path in search_paths:
                        full_pattern = os.path.join(search_path, os.path.basename(file_pattern))
                        if os.path.exists(search_path):
                            for file in os.listdir(search_path):
                                full_path = os.path.join(search_path, file)
                                if os.path.isfile(full_path) and re.match(full_pattern.replace("*", ".*"), full_path):
                                    matches.append(full_path)
                
                if not matches:
                    skipped.append(f"规则 '{rule.name}' - 未找到匹配文件: {file_pattern}")
                    continue
                    
                # 从匹配的文件中提取内容
                all_matches = []  # 存储所有正则匹配结果
                for file_path in matches:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 查找所有匹配
                            for match in re.finditer(rule.regex_pattern, content, re.MULTILINE):
                                all_matches.append(match)
                    except Exception as e:
                        print(f"处理文件 {file_path} 时出错: {str(e)}")
                        continue

                if all_matches:
                    # 获取当前光标位置
                    cursor = self.editor.textCursor()
                    # 处理模板文本
                    result = rule.template_text
                    
                    # 如果模板中包含 {match}，替换为所有完整匹配
                    if "{match}" in result:
                        matches_text = "\n".join(m.group(0) for m in all_matches)
                        result = result.replace("{match}", matches_text)
                    
                    # 处理捕获组
                    for i in range(1, 10):  # 支持最多9个捕获组
                        placeholder = f"{{match{i}}}"
                        if placeholder in result:
                            group_matches = []
                            for m in all_matches:
                                if m.groups() and len(m.groups()) >= i:
                                    group_matches.append(m.group(i))
                                if group_matches:
                                    result = result.replace(placeholder, "\n".join(group_matches))
                    
                    cursor.insertText(result + "\n\n")
                    results.append(f"规则 '{rule.name}' 找到 {len(all_matches)} 个匹配")
                else:
                    skipped.append(f"规则 '{rule.name}' - 所有文件中均未找到匹配内容")
                    
            except Exception as e:
                skipped.append(f"规则 '{rule.name}' 处理出错: {str(e)}")
        
        # 显示处理结果
        message = "处理完成\n\n"
        if results:
            message += "成功:\n" + "\n".join(results) + "\n\n"
        if skipped:
            message += "跳过/失败:\n" + "\n".join(skipped)
            
        QMessageBox.information(self, "应用规则结果", message)

    def insert_template_var(self):
        """插入选中的规则变量"""
        if self.var_combo.currentIndex() == -1:
            QMessageBox.warning(self, "警告", "请先添加规则")
            return
        
        var_name = self.var_combo.currentText()
        var_placeholder = f"{{{var_name}}}"
        cursor = self.editor.textCursor()
        cursor.insertText(var_placeholder)
        
        # 更新预览
        self.update_preview()