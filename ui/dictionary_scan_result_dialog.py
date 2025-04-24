import os
import json
import csv
import threading
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTreeWidget, QTreeWidgetItem, QSplitter, QTextEdit,
    QHeaderView, QProgressBar, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QColor

from ui.styles import (
    button_bg_color, button_text_color, button_hover_color, border_color,
    background_color, text_color, common_font_style
)

class DictionaryScanResultDialog(QDialog):
    """字典扫描结果对话框"""
    
    # 定义信号用于更新UI
    update_ui_signal = Signal(dict)
    scan_complete_signal = Signal()
    
    def __init__(self, file_path, scan_results=None, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.scan_results = scan_results or {}
        self.scanning = False
        self.scanner = None
        self.scan_thread = None
        
        # 设置窗口标志，使其成为非模态窗口
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint | Qt.WindowSystemMenuHint)
        
        self.init_ui()
        
        # 连接信号槽
        self.update_ui_signal.connect(self.update_results)
        self.scan_complete_signal.connect(self.on_scan_complete)
        
        # 如果已经有结果，直接加载
        if scan_results:
            self.load_results()
        else:
            # 否则启动异步扫描
            self.start_scanning()
            
        # 显示窗口，但不阻塞主线程
        self.show()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(f"字典扫描结果 - {os.path.basename(self.file_path)}")
        self.resize(900, 700)
        
        layout = QVBoxLayout(self)
        
        # 文件信息
        file_info_layout = QHBoxLayout()
        file_info_layout.addWidget(QLabel(f"文件: {self.file_path}"))
        layout.addLayout(file_info_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 指示忙碌状态
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("正在扫描...")
        layout.addWidget(self.progress_bar)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 上方区域 - 结果树和详细信息的水平分割
        top_splitter = QSplitter(Qt.Horizontal)
        
        # 结果树
        self.result_tree = QTreeWidget()
        self.result_tree.setHeaderLabels(["名称", "类型", "标签", "匹配数"])
        self.result_tree.setColumnCount(4)
        self.result_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.result_tree.itemSelectionChanged.connect(self.on_item_selected)
        top_splitter.addWidget(self.result_tree)
        
        # 详细信息区域
        detail_widget = QDialog()
        detail_layout = QVBoxLayout(detail_widget)
        
        # 内容显示
        content_label = QLabel("匹配内容:")
        self.content_edit = QTextEdit()
        self.content_edit.setReadOnly(True)
        detail_layout.addWidget(content_label)
        detail_layout.addWidget(self.content_edit)
        
        # 描述显示
        desc_label = QLabel("描述:")
        self.desc_edit = QTextEdit()
        self.desc_edit.setReadOnly(True)
        detail_layout.addWidget(desc_label)
        detail_layout.addWidget(self.desc_edit)
        
        top_splitter.addWidget(detail_widget)
        top_splitter.setSizes([400, 500])  # 设置初始分割比例
        
        # 下方区域 - 匹配行列表
        bottom_widget = QDialog()
        bottom_layout = QVBoxLayout(bottom_widget)
        
        match_label = QLabel("匹配行列表:")
        bottom_layout.addWidget(match_label)
        
        self.match_tree = QTreeWidget()
        self.match_tree.setHeaderLabels(["行号", "行内容"])
        self.match_tree.setColumnCount(2)
        self.match_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.match_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        bottom_layout.addWidget(self.match_tree)
        
        # 添加到主分割器
        splitter.addWidget(top_splitter)
        splitter.addWidget(bottom_widget)
        splitter.setSizes([200, 500])  # 修改分割比例为1:5 (上部分:下部分)
        
        layout.addWidget(splitter)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        # 导出CSV按钮
        self.export_csv_button = QPushButton("导出为CSV")
        self.export_csv_button.clicked.connect(self.export_to_csv)
        button_layout.addWidget(self.export_csv_button)
        
        # 在LovelyForm中打开按钮
        self.open_in_lovelyform_button = QPushButton("在LovelyForm中打开")
        self.open_in_lovelyform_button.clicked.connect(self.open_in_lovelyform)
        button_layout.addWidget(self.open_in_lovelyform_button)
        
        button_layout.addStretch()
        
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)
        
        # 初始时禁用导出按钮，等有结果后启用
        self.export_csv_button.setEnabled(False)
        self.open_in_lovelyform_button.setEnabled(False)
        
        # 应用样式
        self.apply_style()
    
    def apply_style(self):
        """应用样式"""
        self.setStyleSheet(f"""
            QDialog {{
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
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {button_hover_color};
            }}
            QTreeWidget {{
                background-color: {background_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 3px;
            }}
            QTreeWidget::item:selected {{
                background-color: {button_hover_color};
            }}
            QHeaderView::section {{
                background-color: {button_bg_color};
                color: {button_text_color};
                border: 1px solid {border_color};
                padding: 4px;
            }}
            QTextEdit {{
                background-color: {background_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 3px;
            }}
            QProgressBar {{
                border: 1px solid {border_color};
                border-radius: 3px;
                background-color: {background_color};
                color: {text_color};
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {button_bg_color};
                width: 20px;
            }}
        """)
    
    def start_scanning(self):
        """开始异步扫描"""
        if self.scanning:
            return
        
        self.scanning = True
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 设置为忙碌状态
        
        # 创建扫描线程
        self.scan_thread = threading.Thread(target=self.run_scan)
        self.scan_thread.daemon = True
        self.scan_thread.start()
    
    def run_scan(self):
        """执行扫描线程"""
        try:
            from plugin.dictionary_scanner import DictionaryScanner
            
            self.scanner = DictionaryScanner()
            self.scan_results = self.scanner.scan_file(self.file_path, self.scan_callback)
            
            # 通知扫描完成
            self.scan_complete_signal.emit()
            
        except Exception as e:
            print(f"扫描过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 添加错误信息
            self.scan_results = {"error": str(e)}
            self.scan_complete_signal.emit()
    
    def scan_callback(self, dict_item, matched_string, line_num, line_content):
        """扫描回调函数，用于接收部分结果"""
        # 创建包含单个匹配项的结果
        match_info = {
            "match": matched_string,
            "line_num": line_num,
            "line_content": line_content
        }
        
        partial_results = {dict_item: [match_info]}
        
        # 通过信号将结果发送到主线程更新UI
        self.update_ui_signal.emit(partial_results)
    
    def update_results(self, partial_results):
        """更新UI显示部分结果"""
        # 合并结果到当前结果集
        for item, matches in partial_results.items():
            if item not in self.scan_results:
                self.scan_results[item] = []
            
            # 添加新匹配
            self.scan_results[item].extend(matches)
        
        # 更新树形控件
        self.load_results(append=True)
    
    def on_scan_complete(self):
        """扫描完成时的处理"""
        self.scanning = False
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("扫描完成")
        
        # 如果有结果，启用导出按钮
        has_results = len(self.scan_results) > 0
        self.export_csv_button.setEnabled(has_results)
        self.open_in_lovelyform_button.setEnabled(has_results)
        
        # 加载最终结果
        self.load_results()
    
    def load_results(self, append=False):
        """加载扫描结果到树控件"""
        if not append:
            self.result_tree.clear()
            self.match_tree.clear()
        
        # 扫描失败时显示错误信息
        if isinstance(self.scan_results, dict) and "error" in self.scan_results:
            error_item = QTreeWidgetItem(["扫描错误", "", "", ""])
            error_item.setForeground(0, QColor("#FF0000"))  # 直接使用红色的十六进制代码
            error_item.setToolTip(0, str(self.scan_results["error"]))
            self.result_tree.addTopLevelItem(error_item)
            return
        
        # 按字典名称组织结果
        dict_results = {}
        for item, matches in self.scan_results.items():
            dict_name = item.type_name
            if dict_name not in dict_results:
                dict_results[dict_name] = []
            
            # 创建新格式的项目记录
            result_item = {
                "name": item.name,
                "content": item.content,
                "description": item.description,
                "tags": item.tags,
                "type": item.type_name,
                "file_pattern": item.file_pattern,
                "matches": matches,
                "original_item": item  # 保存原始对象引用
            }
            
            dict_results[dict_name].append(result_item)
            
        # 逐个添加到树控件
        for dict_name, items in dict_results.items():
            # 检查字典是否已存在
            found = False
            dict_item = None
            
            if append:
                for i in range(self.result_tree.topLevelItemCount()):
                    top_item = self.result_tree.topLevelItem(i)
                    if top_item.text(0) == dict_name:
                        dict_item = top_item
                        found = True
                        break
            
            if not found:
                dict_item = QTreeWidgetItem([dict_name, "", "", str(len(items))])
                dict_item.setExpanded(True)
                self.result_tree.addTopLevelItem(dict_item)
            
            # 遍历字典中的项目
            for item in items:
                # 检查项目是否已存在
                if append:
                    existing = False
                    for i in range(dict_item.childCount()):
                        child = dict_item.child(i)
                        if child.text(0) == item["name"]:
                            existing = True
                            break
                    if existing:
                        continue
                
                # 创建新项目
                match_count = len(item.get("matches", []))
                item_widget = QTreeWidgetItem([
                    item["name"],
                    item["type"],
                    ", ".join(item["tags"]),
                    str(match_count)
                ])
                
                # 存储完整项数据
                item_widget.setData(0, Qt.UserRole, item)
                
                dict_item.addChild(item_widget)
        
        # 更新按钮状态
        has_results = len(self.scan_results) > 0
        self.export_csv_button.setEnabled(has_results)
        self.open_in_lovelyform_button.setEnabled(has_results)
    
    def on_item_selected(self):
        """项目选择变化事件"""
        selected_items = self.result_tree.selectedItems()
        if not selected_items:
            self.content_edit.clear()
            self.desc_edit.clear()
            self.match_tree.clear()
            return
        
        # 获取选中项
        selected_item = selected_items[0]
        item_data = selected_item.data(0, Qt.UserRole)
        
        # 如果是顶级项（字典），不显示详情
        if selected_item.parent() is None:
            self.content_edit.clear()
            self.desc_edit.clear()
            self.match_tree.clear()
            return
        
        # 显示项目详情
        if item_data:
            self.content_edit.setText(item_data.get("content", ""))
            self.desc_edit.setText(item_data.get("description", ""))
            
            # 清空并添加匹配结果
            self.match_tree.clear()
            
            for match in item_data.get("matches", []):
                line_num = match.get("line_num", -1)
                line_content = match.get("line_content", "")
                
                if line_num >= 0:
                    match_item = QTreeWidgetItem([
                        f"行 {line_num}",
                        line_content
                    ])
                else:
                    match_item = QTreeWidgetItem([
                        "二进制匹配",
                        line_content
                    ])
                
                self.match_tree.addTopLevelItem(match_item)
    
    def export_to_csv(self):
        """导出结果为CSV文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出为CSV", "", "CSV文件 (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 写入标题行
                writer.writerow(["字典类型", "项目名称", "内容", "描述", "标签", "类型", "行号", "行内容", "文件名匹配"])
                
                # 写入数据行
                for dict_item, matches in self.scan_results.items():
                    for match in matches:
                        line_num = match.get("line_num", -1)
                        line_content = match.get("line_content", "")
                        
                        writer.writerow([
                            dict_item.type_name,
                            dict_item.name,
                            dict_item.content,
                            dict_item.description,
                            ", ".join(dict_item.tags),
                            dict_item.type_name,
                            line_num,
                            line_content,
                            dict_item.file_pattern
                        ])
                
            QMessageBox.information(self, "导出成功", f"结果已成功导出到: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出过程中发生错误: {str(e)}")
    
    def open_in_lovelyform(self):
        """在LovelyForm中打开CSV文件，对行内容进行分割"""
        if not self.scan_results or "error" in self.scan_results:
            QMessageBox.warning(self, "打开失败", "没有可显示的结果")
            return
        
        try:
            # 为LovelyForm创建简化的CSV，只包含匹配行内容
            output_dir = os.path.dirname(self.file_path)
            base_name = os.path.splitext(os.path.basename(self.file_path))[0]
            temp_csv_path = os.path.join(output_dir, f"{base_name}_字典扫描匹配行.csv")
            
            # 判断文件类型，决定如何分割行内容
            file_ext = os.path.splitext(self.file_path)[1].lower()
            
            with open(temp_csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                # 写入标题行
                headers = ["字典名称", "匹配项", "行号"]
                
                # 根据文件类型设置不同的列标题
                if file_ext == '.csv':
                    # 读取CSV第一行来获取头部
                    try:
                        with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            csv_reader = csv.reader(f)
                            original_headers = next(csv_reader, [])
                            headers.extend(original_headers)
                    except:
                        # 如果无法读取头部，使用默认列名
                        headers.extend(["列1", "列2", "列3", "列4", "列5"])
                elif file_ext in ['.json', '.xml']:
                    headers.extend(["键", "值"])
                else:
                    headers.extend(["行内容"])
                
                writer.writerow(headers)
                
                # 写入匹配行内容
                for dict_item, matches in self.scan_results.items():
                    for match in matches:
                        line_content = match.get("line_content", "")
                        row = [
                            dict_item.type_name,           # 字典名称
                            dict_item.name,        # 匹配项名称
                            match.get("line_num", ""),  # 行号
                        ]
                        
                        # 根据文件类型分割行内容
                        if file_ext == '.csv':
                            try:
                                # 尝试解析CSV行
                                parsed = next(csv.reader([line_content]))
                                row.extend(parsed)
                            except:
                                # 解析失败，作为单一列添加
                                row.append(line_content)
                        elif file_ext == '.json':
                            try:
                                # 尝试解析JSON
                                line_content = line_content.strip()
                                if line_content.startswith('{') and line_content.endswith('}'):
                                    # JSON对象
                                    data = json.loads(line_content)
                                    for k, v in data.items():
                                        writer.writerow(row + [k, str(v)])
                                    continue  # 已写入多行，跳过下面的写入
                                elif line_content.startswith('[') and line_content.endswith(']'):
                                    # JSON数组
                                    data = json.loads(line_content)
                                    for i, v in enumerate(data):
                                        writer.writerow(row + [f"[{i}]", str(v)])
                                    continue  # 已写入多行，跳过下面的写入
                                elif ':' in line_content:
                                    # 可能是键值对
                                    parts = line_content.split(':', 1)
                                    row.extend([parts[0].strip(' "\''), parts[1].strip(' "\',}')])
                                else:
                                    row.append(line_content)
                            except:
                                # 解析失败，保持原样
                                row.append(line_content)
                        elif file_ext in ['.xml', '.html', '.htm']:
                            # 简单处理XML/HTML格式，查找标签和内容
                            import re
                            tags = re.findall(r'<([^>]+)>(.*?)</\1>', line_content)
                            if tags:
                                for tag, content in tags:
                                    writer.writerow(row + [tag, content])
                                continue
                            else:
                                row.append(line_content)
                        elif ',' in line_content and len(line_content.split(',')) > 1:
                            # 如果包含逗号，尝试按逗号分割
                            parts = line_content.split(',')
                            row.extend([p.strip() for p in parts])
                        elif ';' in line_content and len(line_content.split(';')) > 1:
                            # 如果包含分号，尝试按分号分割
                            parts = line_content.split(';')
                            row.extend([p.strip() for p in parts])
                        elif '=' in line_content and len(line_content.split('=')) > 1:
                            # 如果包含等号，尝试按等号分割为键值对
                            parts = line_content.split('=')
                            row.extend([parts[0].strip(), '='.join(parts[1:]).strip()])
                        elif '\t' in line_content:
                            # 如果包含制表符，按制表符分割
                            parts = line_content.split('\t')
                            row.extend([p.strip() for p in parts])
                        elif '  ' in line_content:
                            # 如果包含多个空格，按多个空格分割
                            parts = re.split(r'\s{2,}', line_content)
                            row.extend([p.strip() for p in parts])
                        else:
                            # 无法识别的格式，保持原样
                            row.append(line_content)
                        
                        # 写入行数据
                        writer.writerow(row)
            
            # 调用lovelyform打开简化的CSV
            from lovelyform import show_csv_viewer
            show_csv_viewer(temp_csv_path)
            
            # 保存路径以便后续使用
            self.lovelyform_csv_path = temp_csv_path
            
        except Exception as e:
            QMessageBox.critical(self, "打开失败", f"在LovelyForm中打开时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def closeEvent(self, event):
        """关闭窗口时停止扫描"""
        if self.scanning:
            self.scanning = False
        super().closeEvent(event)
