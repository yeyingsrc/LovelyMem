from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QGroupBox, QLabel, QHeaderView, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
import csv
import os

class StringSearchResults(QGroupBox):
    """字符串搜索结果显示组件"""
    
    def __init__(self, results, image_path):
        super().__init__("字符串搜索结果")
        self.results = results
        self.image_path = image_path
        self.setup_ui()
        self.display_results()
        
    def setup_ui(self):
        """设置UI界面"""
        main_layout = QVBoxLayout(self)
        
        # 添加结果信息标签
        info_layout = QHBoxLayout()
        self.info_label = QLabel(f"在镜像 {os.path.basename(self.image_path)} 中找到 {len(self.results)} 个匹配项")
        info_layout.addWidget(self.info_label)
        info_layout.addStretch()
        
        # 添加导出按钮
        export_button = QPushButton("导出结果")
        export_button.clicked.connect(self.export_results)
        info_layout.addWidget(export_button)
        
        main_layout.addLayout(info_layout)
        
        # 创建表格
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["位置", "匹配内容", "十六进制数据", "上下文"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSortingEnabled(True)
        
        main_layout.addWidget(self.results_table)
    
    def display_results(self):
        """显示搜索结果"""
        self.results_table.setRowCount(len(self.results))
        
        for row, result in enumerate(self.results):
            # 位置
            position_item = QTableWidgetItem(f"0x{result['position']:X}")
            position_item.setData(Qt.UserRole, result['position'])  # 存储原始位置用于排序
            self.results_table.setItem(row, 0, position_item)
            
            # 匹配内容
            match_item = QTableWidgetItem(result['match'])
            self.results_table.setItem(row, 1, match_item)
            
            # 十六进制数据
            hex_item = QTableWidgetItem(result['hex'])
            self.results_table.setItem(row, 2, hex_item)
            
            # 上下文 - 将原始数据转换为可读形式
            context = ""
            if 'raw_data' in result:
                context = result['raw_data'].decode('utf-8', errors='replace')
            context_item = QTableWidgetItem(context)
            self.results_table.setItem(row, 3, context_item)
    
    def export_results(self):
        """导出搜索结果到CSV文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出搜索结果", "string_search_results.csv", "CSV文件 (*.csv)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["位置", "匹配内容", "十六进制数据", "上下文"])
                
                for result in self.results:
                    context = ""
                    if 'raw_data' in result:
                        context = result['raw_data'].decode('utf-8', errors='replace')
                    
                    writer.writerow([
                        f"0x{result['position']:X}",
                        result['match'],
                        result['hex'],
                        context
                    ])
                    
            QMessageBox.information(self, "导出成功", f"搜索结果已成功导出到 {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出结果时发生错误: {str(e)}")
