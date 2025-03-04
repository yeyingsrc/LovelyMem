from PySide6.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, 
                               QHBoxLayout, QLabel, QFrame, QScrollArea)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, QPoint, QSize
import sys
import os
from check_chinese import check_directory_for_chinese
from check_wmic import check_wmic
from check_dokan import check_dokan_installed

class CheckTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(400, 500)
        self.setup_ui()
        
        self.dragging = False
        self.drag_position = QPoint()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建标题栏
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet("""
            background-color: rgba(255, 230, 240, 0.9);
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        """)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        
        # 添加标题
        title_label = QLabel("Lovelymem 环境检测工具")
        title_label.setStyleSheet("""
            font-family: 'Microsoft YaHei', 'SimHei', sans-serif;
            font-size: 13px;
            font-weight: bold;
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 添加关闭按钮
        close_button = QPushButton("×")
        close_button.setFixedSize(20, 20)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 235, 238, 0.9);
                border: none;
                border-radius: 10px;
                color: #333333;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 180, 190, 0.9);
            }
        """)
        close_button.clicked.connect(self.close)
        title_layout.addWidget(close_button)
        
        main_layout.addWidget(self.title_bar)
        
        # 创建内容区域
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            background-color: rgba(255, 230, 240, 1);
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
        """)
        content_layout = QVBoxLayout(content_widget)
        
        # 创建滚动区域用于显示检测结果
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        self.result_widget = QWidget()
        self.result_layout = QVBoxLayout(self.result_widget)
        scroll_area.setWidget(self.result_widget)
        
        # 添加检测按钮
        check_button = QPushButton("🔍 开始检测")
        check_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 200, 210, 0.9);
                color: #333333;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-family: 'Microsoft YaHei', 'SimHei', sans-serif;
                font-size: 13px;
                height: 35px;
            }
            QPushButton:hover {
                background-color: rgba(255, 180, 190, 0.9);
            }
        """)
        check_button.clicked.connect(self.run_checks)
        
        content_layout.addWidget(scroll_area)
        content_layout.addWidget(check_button)
        
        main_layout.addWidget(content_widget)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.geometry().contains(event.position().toPoint()):
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def add_result_item(self, title, result, details=""):
        item_frame = QFrame()
        item_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 245, 250, 0.9);
                border-radius: 5px;
                margin: 5px;
                padding: 5px;
            }
        """)
        
        item_layout = QVBoxLayout(item_frame)
        
        # 添加标题和结果
        status_layout = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(title_label)
        
        result_label = QLabel("✅ 通过" if result else "❌ 未通过")
        result_label.setStyleSheet(f"color: {'green' if result else 'red'};")
        status_layout.addWidget(result_label)
        
        item_layout.addLayout(status_layout)
        
        # 如果有详细信息，添加详细信息
        if details:
            details_label = QLabel(details)
            details_label.setWordWrap(True)
            details_label.setStyleSheet("color: #666666;")
            item_layout.addWidget(details_label)
        
        self.result_layout.addWidget(item_frame)

    def clear_results(self):
        # 清除所有检测结果
        while self.result_layout.count():
            child = self.result_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def run_checks(self):
        self.clear_results()
        
        # 检查中文目录
        current_dir = os.getcwd()
        chinese_result = check_directory_for_chinese(current_dir)
        self.add_result_item(
            "中文目录检测",
            chinese_result,
            "检测当前目录是否包含中文名称的文件夹"
        )
        
        # 检查WMIC
        wmic_result = check_wmic()
        self.add_result_item(
            "WMIC检测",
            wmic_result,
            "检测系统是否安装WMIC工具"
        )
        
        # 检查Dokan
        dokan_result = check_dokan_installed()
        self.add_result_item(
            "Dokan驱动检测",
            dokan_result,
            "检测系统是否安装Dokan驱动"
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    check_tool = CheckTool()
    check_tool.show()
    
    sys.exit(app.exec())