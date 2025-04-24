import os
import json
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QLineEdit, QTextEdit, QFileDialog,
    QSplitter, QMessageBox, QInputDialog, QGroupBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QMenu,
    QComboBox, QScrollArea, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QFont

from ui.styles import (
    button_bg_color, button_text_color, button_hover_color, border_color,
    group_title_bg_color, background_color, text_color, common_font_style
)
from plugin.dictionary_manager import DictionaryManager, DictionaryItem

logger = logging.getLogger(__name__)

class ItemEditPanel(QWidget):
    """条目编辑面板，用于编辑字典条目"""
    save_clicked = Signal(str, DictionaryItem)  # 发送旧名称和新条目信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.current_item = None
        self.old_name = ""
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 名称
        name_layout = QHBoxLayout()
        name_label = QLabel("名称:")
        self.name_edit = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # 类型
        type_layout = QHBoxLayout()
        type_label = QLabel("类型:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["通用", "命令行", "正则表达式", "SQL", "Python"])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # 标签
        tags_layout = QHBoxLayout()
        tags_label = QLabel("标签:")
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("使用逗号分隔多个标签")
        tags_layout.addWidget(tags_label)
        tags_layout.addWidget(self.tags_edit)
        layout.addLayout(tags_layout)
        
        # 描述
        desc_label = QLabel("描述:")
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(100)
        layout.addWidget(desc_label)
        layout.addWidget(self.desc_edit)
        
        # 内容
        content_label = QLabel("内容:")
        self.content_edit = QTextEdit()
        layout.addWidget(content_label)
        layout.addWidget(self.content_edit)
        
        # 文件名匹配模式
        file_pattern_layout = QHBoxLayout()
        file_pattern_label = QLabel("文件名匹配:")
        self.file_pattern_edit = QLineEdit()
        self.file_pattern_edit.setPlaceholderText("如: *.exe,*.dll (用逗号分隔多个模式，留空匹配所有文件)")
        file_pattern_layout.addWidget(file_pattern_label)
        file_pattern_layout.addWidget(self.file_pattern_edit)
        layout.addLayout(file_pattern_layout)
        
        # 精确匹配选项
        exact_match_layout = QHBoxLayout()
        self.exact_match_cb = QCheckBox("精确匹配")
        self.exact_match_cb.setToolTip("启用后只匹配完整词或数值，例如搜索\"22\"不会匹配到\"2222\"")
        exact_match_layout.addWidget(self.exact_match_cb)
        exact_match_layout.addStretch()
        layout.addLayout(exact_match_layout)
        
        # 保存按钮
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.on_save_clicked)
        layout.addWidget(self.save_button)
        
        # 应用样式
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {background_color};
                color: {text_color};
                font-family: {common_font_style.split(',')[0]};
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
            QLineEdit, QTextEdit, QComboBox {{
                background-color: {button_bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 3px;
                padding: 3px;
            }}
        """)
    
    def set_item(self, item):
        """设置当前编辑的条目"""
        self.current_item = item
        self.old_name = item.name
        
        self.name_edit.setText(item.name)
        self.type_combo.setCurrentText(item.type_name)
        self.tags_edit.setText(", ".join(item.tags))
        self.desc_edit.setText(item.description)
        self.content_edit.setText(item.content)
        self.file_pattern_edit.setText(item.file_pattern)
        self.exact_match_cb.setChecked(item.is_exact_match)
    
    def create_new_item(self):
        """创建新条目编辑状态"""
        self.current_item = DictionaryItem()
        self.old_name = ""
        
        self.name_edit.clear()
        self.type_combo.setCurrentText("通用")
        self.tags_edit.clear()
        self.desc_edit.clear()
        self.content_edit.clear()
        self.file_pattern_edit.clear()
        self.exact_match_cb.setChecked(False)
    
    def on_save_clicked(self):
        """保存按钮点击事件"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "错误", "名称不能为空")
            return
        
        # 更新条目数据
        item = DictionaryItem(
            name=self.name_edit.text().strip(),
            content=self.content_edit.toPlainText(),
            description=self.desc_edit.toPlainText(),
            tags=[tag.strip() for tag in self.tags_edit.text().split(',') if tag.strip()],
            type_name=self.type_combo.currentText(),
            file_pattern=self.file_pattern_edit.text().strip(),
            is_exact_match=self.exact_match_cb.isChecked()
        )
        
        # 发送保存信号
        self.save_clicked.emit(self.old_name, item)

class DictionaryTabWidget(QWidget):
    """字典标签页，显示一个字典的所有条目和编辑功能"""
    item_selected = Signal(DictionaryItem)
    item_saved = Signal()
    item_deleted = Signal()
    
    def __init__(self, dict_manager, dict_name, parent=None):
        super().__init__(parent)
        self.dict_manager = dict_manager
        self.dict_name = dict_name
        self.init_ui()
        self.load_items()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧创建条目列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 搜索框
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索条目...")
        self.search_edit.textChanged.connect(self.on_search_text_changed)
        search_button = QPushButton("搜索")
        search_button.clicked.connect(self.on_search_clicked)
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(search_button)
        left_layout.addLayout(search_layout)
        
        # 条目列表
        self.item_list = QListWidget()
        self.item_list.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.item_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.item_list.customContextMenuRequested.connect(self.show_item_context_menu)
        left_layout.addWidget(self.item_list)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("添加")
        self.add_button.clicked.connect(self.on_add_clicked)
        self.delete_button = QPushButton("删除")
        self.delete_button.clicked.connect(self.on_delete_clicked)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        left_layout.addLayout(button_layout)
        
        # 右侧创建编辑面板
        self.edit_panel = ItemEditPanel()
        self.edit_panel.save_clicked.connect(self.on_save_item)
        
        # 添加到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(self.edit_panel)
        splitter.setSizes([200, 400])  # 设置初始分割大小
        
        layout.addWidget(splitter)
        
        # 应用样式
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {background_color};
                color: {text_color};
                font-family: {common_font_style.split(',')[0]};
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
            QLineEdit {{
                background-color: {button_bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 3px;
                padding: 3px;
            }}
            QListWidget {{
                background-color: {button_bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 3px;
            }}
            QListWidget::item:selected {{
                background-color: {button_hover_color};
            }}
        """)
    
    def load_items(self):
        """加载所有条目"""
        self.item_list.clear()
        
        items = self.dict_manager.get_items(self.dict_name)
        for item in items:
            list_item = QListWidgetItem(item.name)
            # 设置条目数据
            list_item.setData(Qt.UserRole, item)
            self.item_list.addItem(list_item)
    
    def on_search_text_changed(self, text):
        """搜索文本变化事件"""
        if not text:
            self.load_items()
            return
        
        # 暂不实时搜索，避免卡顿
    
    def on_search_clicked(self):
        """搜索按钮点击事件"""
        query = self.search_edit.text().strip()
        if not query:
            self.load_items()
            return
        
        self.item_list.clear()
        results = self.dict_manager.search_items(query, self.dict_name)
        for dict_name, item in results:
            list_item = QListWidgetItem(item.name)
            list_item.setData(Qt.UserRole, item)
            self.item_list.addItem(list_item)
    
    def on_item_selection_changed(self):
        """条目选择变化事件"""
        selected_items = self.item_list.selectedItems()
        if not selected_items:
            return
        
        list_item = selected_items[0]
        item = list_item.data(Qt.UserRole)
        if item:
            self.edit_panel.set_item(item)
            self.item_selected.emit(item)
    
    def on_add_clicked(self):
        """添加按钮点击事件"""
        self.edit_panel.create_new_item()
    
    def on_delete_clicked(self):
        """删除按钮点击事件"""
        selected_items = self.item_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择要删除的条目")
            return
        
        list_item = selected_items[0]
        item = list_item.data(Qt.UserRole)
        if not item:
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除条目'{item.name}'吗？此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.dict_manager.delete_item(self.dict_name, item.name)
            if success:
                self.load_items()
                self.item_deleted.emit()
    
    def on_save_item(self, old_name, item):
        """保存条目"""
        success = self.dict_manager.update_item(self.dict_name, old_name, item)
        if success:
            self.load_items()
            QMessageBox.information(self, "成功", f"条目'{item.name}'已保存")
            self.item_saved.emit()
        else:
            QMessageBox.warning(self, "错误", "保存条目失败")
    
    def show_item_context_menu(self, pos):
        """显示条目上下文菜单"""
        selected_items = self.item_list.selectedItems()
        if not selected_items:
            return
        
        list_item = selected_items[0]
        item = list_item.data(Qt.UserRole)
        if not item:
            return
        
        menu = QMenu(self)
        
        copy_action = menu.addAction("复制内容")
        copy_action.triggered.connect(lambda: self.copy_item_content(item))
        
        menu.addSeparator()
        
        delete_action = menu.addAction("删除")
        delete_action.triggered.connect(self.on_delete_clicked)
        
        menu.exec_(self.item_list.mapToGlobal(pos))
    
    def copy_item_content(self, item):
        """复制条目内容到剪贴板"""
        from PySide6.QtGui import QGuiApplication
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(item.content)
        QMessageBox.information(self, "已复制", f"条目'{item.name}'的内容已复制到剪贴板")

class DictionaryManagerDialog(QDialog):
    """字典管理器对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dict_manager = DictionaryManager()
        self.init_ui()
        self.load_dictionaries()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("字典管理器")
        self.resize(900, 600)
        
        layout = QVBoxLayout(self)
        
        # 使用下拉框和操作按钮
        dict_control_layout = QHBoxLayout()
        
        # 当前选择的字典
        dict_label = QLabel("当前字典:")
        self.dict_combo = QComboBox()
        self.dict_combo.setMinimumWidth(200)
        self.dict_combo.currentIndexChanged.connect(self.on_dict_selected)
        
        # 字典操作下拉框
        operation_label = QLabel("操作:")
        self.operation_combo = QComboBox()
        self.operation_combo.addItems(["新建字典", "删除字典", "导出字典", "导入字典"])
        
        # 执行操作按钮
        self.execute_button = QPushButton("执行")
        self.execute_button.clicked.connect(self.on_execute_operation)
        
        dict_control_layout.addWidget(dict_label)
        dict_control_layout.addWidget(self.dict_combo)
        dict_control_layout.addSpacing(20)
        dict_control_layout.addWidget(operation_label)
        dict_control_layout.addWidget(self.operation_combo)
        dict_control_layout.addWidget(self.execute_button)
        dict_control_layout.addStretch()
        
        layout.addLayout(dict_control_layout)
        
        # 创建内容显示区域（替代原来的标签页）
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        layout.addWidget(self.content_area)
        
        # 字典Tab容器（不显示）
        self.dict_tabs = {}
        
        # 应用样式
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {background_color};
                color: {text_color};
                font-family: {common_font_style.split(',')[0]};
            }}
            QPushButton, QComboBox {{
                background-color: {button_bg_color};
                color: {button_text_color};
                border: 1px solid {border_color};
                border-radius: 3px;
                padding: 5px;
            }}
            QPushButton:hover, QComboBox:hover {{
                background-color: {button_hover_color};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: {border_color};
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {background_color};
                color: {text_color};
                selection-background-color: {button_hover_color};
                selection-color: {button_text_color};
                border: 1px solid {border_color};
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
        """)
    
    def load_dictionaries(self):
        """加载所有字典"""
        # 保存当前选中的字典
        current_dict = self.dict_combo.currentText() if self.dict_combo.count() > 0 else None
        
        # 清空并重新加载下拉框
        self.dict_combo.clear()
        
        # 清空内容区域
        self.clear_content_area()
        
        # 清空字典容器
        self.dict_tabs = {}
        
        # 加载所有字典
        dict_names = self.dict_manager.get_dictionary_names()
        for dict_name in dict_names:
            # 添加到下拉框
            self.dict_combo.addItem(dict_name)
            
            # 创建字典Tab但不显示
            dict_tab = DictionaryTabWidget(self.dict_manager, dict_name)
            self.dict_tabs[dict_name] = dict_tab
        
        # 如果之前有选中的字典，尝试恢复选中状态
        if current_dict and current_dict in dict_names:
            index = self.dict_combo.findText(current_dict)
            if index >= 0:
                self.dict_combo.setCurrentIndex(index)
        elif self.dict_combo.count() > 0:
            self.dict_combo.setCurrentIndex(0)
            
        # 确保显示当前选中的字典内容
        self.update_content_display()
    
    def clear_content_area(self):
        """清空内容区域"""
        # 清除内容布局中的所有小部件
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
    
    def on_dict_selected(self, index):
        """字典选择变化时切换显示的内容"""
        if index < 0 or self.dict_combo.count() == 0:
            return
            
        self.update_content_display()
    
    def update_content_display(self):
        """更新内容区域显示当前选中的字典"""
        # 获取选中的字典名称
        dict_name = self.dict_combo.currentText()
        if not dict_name:
            return
            
        # 清空内容区域
        self.clear_content_area()
        
        # 如果字典存在，显示它
        if dict_name in self.dict_tabs:
            dict_tab = self.dict_tabs[dict_name]
            self.content_layout.addWidget(dict_tab)
            dict_tab.show()
    
    def on_execute_operation(self):
        """执行所选操作"""
        operation = self.operation_combo.currentText()
        
        if operation == "新建字典":
            self.on_add_dictionary()
        elif operation == "删除字典":
            self.on_delete_dictionary()
        elif operation == "导出字典":
            self.on_export_dictionary()
        elif operation == "导入字典":
            self.on_import_dictionary()
    
    def on_add_dictionary(self):
        """添加字典按钮点击事件"""
        dict_name, ok = QInputDialog.getText(
            self, "新建字典", 
            "请输入字典名称:",
            QLineEdit.Normal, ""
        )
        
        if ok and dict_name.strip():
            dict_name = dict_name.strip()
            if dict_name in self.dict_manager.get_dictionary_names():
                QMessageBox.warning(self, "错误", f"字典'{dict_name}'已存在")
                return
            
            success = self.dict_manager.create_dictionary(dict_name)
            if success:
                self.load_dictionaries()
                # 选择新创建的字典
                for i in range(self.dict_combo.count()):
                    if self.dict_combo.itemText(i) == dict_name:
                        self.dict_combo.setCurrentIndex(i)
                        break
            else:
                QMessageBox.warning(self, "错误", f"创建字典'{dict_name}'失败")
    
    def on_delete_dictionary(self):
        """删除字典按钮点击事件"""
        current_index = self.dict_combo.currentIndex()
        if current_index < 0:
            QMessageBox.warning(self, "警告", "请先选择要删除的字典")
            return
        
        dict_name = self.dict_combo.currentText()
        
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除字典'{dict_name}'吗？此操作将删除字典中的所有条目，且不可恢复。",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.dict_manager.delete_dictionary(dict_name)
            if success:
                self.load_dictionaries()
            else:
                QMessageBox.warning(self, "错误", f"删除字典'{dict_name}'失败")
    
    def on_export_dictionary(self):
        """导出字典按钮点击事件"""
        current_index = self.dict_combo.currentIndex()
        if current_index < 0:
            QMessageBox.warning(self, "警告", "请先选择要导出的字典")
            return
        
        dict_name = self.dict_combo.currentText()
        
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出字典", 
            f"{dict_name}.json", 
            "JSON文件 (*.json)"
        )
        
        if file_path:
            try:
                # 获取字典数据
                items = self.dict_manager.get_items(dict_name)
                data = {
                    "name": dict_name,
                    "items": [item.to_dict() for item in items]
                }
                
                # 写入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                
                QMessageBox.information(self, "成功", f"字典'{dict_name}'已导出至\n{file_path}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"导出字典失败: {str(e)}")
    
    def on_import_dictionary(self):
        """导入字典按钮点击事件"""
        # 选择导入文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入字典", 
            "", 
            "JSON文件 (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            dict_name = data.get("name", "")
            if not dict_name:
                # 使用文件名作为字典名
                dict_name = os.path.basename(file_path)
                if dict_name.endswith('.json'):
                    dict_name = dict_name[:-5]
            
            # 检查字典是否已存在
            if dict_name in self.dict_manager.get_dictionary_names():
                # 询问是否覆盖
                reply = QMessageBox.question(
                    self, "字典已存在", 
                    f"字典'{dict_name}'已存在，是否覆盖？",
                    QMessageBox.Yes | QMessageBox.No, 
                    QMessageBox.No
                )
                
                if reply != QMessageBox.Yes:
                    # 请求新名称
                    new_name, ok = QInputDialog.getText(
                        self, "重命名字典", 
                        "请输入新的字典名称:",
                        QLineEdit.Normal, dict_name + "_导入"
                    )
                    
                    if ok and new_name.strip():
                        dict_name = new_name.strip()
                    else:
                        return
            
            # 创建字典
            self.dict_manager.create_dictionary(dict_name)
            
            # 添加条目
            for item_data in data.get("items", []):
                item = DictionaryItem.from_dict(item_data)
                self.dict_manager.add_item(dict_name, item)
            
            self.load_dictionaries()
            
            # 选择导入的字典
            for i in range(self.dict_combo.count()):
                if self.dict_combo.itemText(i) == dict_name:
                    self.dict_combo.setCurrentIndex(i)
                    break
            
            QMessageBox.information(self, "成功", f"字典'{dict_name}'已导入")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"导入字典失败: {str(e)}")

# 如果直接运行此文件，则启动字典管理器对话框
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    dialog = DictionaryManagerDialog()
    dialog.show()
    sys.exit(app.exec_())
