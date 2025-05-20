import base64
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                              QPushButton, QLabel, QComboBox, QMessageBox, QApplication,
                              QFileDialog)
from PySide6.QtCore import Qt, QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QPixmap, QImage
import sys
import os

# 添加项目根目录到系统路径，确保可以导入ui.styles
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class Base64Tool(QWidget):
    """Base64编码解码工具"""
    
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.setWindowTitle("Base64编码解码工具")
        self.resize(800, 600)
        self.main_window = main_window
        
        # 如果传入了主窗口，则连接样式更新信号
        if self.main_window and hasattr(self.main_window, 'style_updated_signal'):
            self.main_window.style_updated_signal.connect(self.update_style)
        
        # 初始化UI
        self.setup_ui()
        
        # 应用当前样式
        self.update_style()
        
    def setup_ui(self):
        """设置界面"""
        main_layout = QVBoxLayout(self)
        
        # 添加说明标签
        self.description_label = QLabel("Base64编码解码工具 - 支持文本和图片")
        self.description_label.setAlignment(Qt.AlignCenter)
        self.description_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(self.description_label)
        
        # 创建模式选择
        mode_layout = QHBoxLayout()
        self.mode_label = QLabel("模式:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["文本编码/解码", "图片编码/解码"])
        self.mode_combo.currentIndexChanged.connect(self.mode_changed)
        mode_layout.addWidget(self.mode_label)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        main_layout.addLayout(mode_layout)
        
        # 创建输入区域
        self.input_label = QLabel("输入:")
        main_layout.addWidget(self.input_label)
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("在此处输入要编码或解码的文本")
        main_layout.addWidget(self.input_text)
        
        # 创建图片预览区域（初始隐藏）
        self.image_preview_label = QLabel("图片预览")
        self.image_preview_label.setAlignment(Qt.AlignCenter)
        self.image_preview_label.setMinimumHeight(200)
        self.image_preview_label.hide()
        main_layout.addWidget(self.image_preview_label)
        
        # 添加打开图片按钮（初始隐藏）
        self.open_image_button = QPushButton("打开图片")
        self.open_image_button.clicked.connect(self.open_image)
        self.open_image_button.hide()
        main_layout.addWidget(self.open_image_button)
        
        # 创建按钮区域
        button_layout = QHBoxLayout()
        self.encode_button = QPushButton("编码")
        self.decode_button = QPushButton("解码")
        self.clear_button = QPushButton("清除")
        
        self.encode_button.clicked.connect(self.encode_data)
        self.decode_button.clicked.connect(self.decode_data)
        self.clear_button.clicked.connect(self.clear_fields)
        
        button_layout.addWidget(self.encode_button)
        button_layout.addWidget(self.decode_button)
        button_layout.addWidget(self.clear_button)
        main_layout.addLayout(button_layout)
        
        # 创建输出区域
        self.output_label = QLabel("输出:")
        main_layout.addWidget(self.output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setPlaceholderText("编码/解码结果将显示在这里")
        self.output_text.setReadOnly(True)
        main_layout.addWidget(self.output_text)
        
        # 设置初始模式
        self.current_mode = 0  # 0: 文本, 1: 图片
        
    def mode_changed(self, index):
        """切换编码/解码模式"""
        self.current_mode = index
        if index == 0:  # 文本模式
            self.input_text.setPlaceholderText("在此处输入要编码或解码的文本")
            self.image_preview_label.hide()
            self.open_image_button.hide()
        else:  # 图片模式
            self.input_text.setPlaceholderText("在此处输入Base64编码的图片数据，或者点击解码按钮从文本中解码图片")
            self.image_preview_label.show()
            self.open_image_button.show()
        
        # 清除字段
        self.clear_fields()
    
    def encode_data(self):
        """编码数据"""
        try:
            if self.current_mode == 0:  # 文本模式
                input_text = self.input_text.toPlainText()
                if not input_text:
                    QMessageBox.warning(self, "警告", "请输入要编码的文本")
                    return
                
                # 编码文本
                encoded_bytes = base64.b64encode(input_text.encode('utf-8'))
                encoded_text = encoded_bytes.decode('utf-8')
                self.output_text.setText(encoded_text)
                
            else:  # 图片模式
                # 从剪贴板获取图片
                clipboard = QApplication.clipboard()
                pixmap = clipboard.pixmap()
                
                if pixmap.isNull():
                    QMessageBox.warning(self, "警告", "剪贴板中没有图片")
                    return
                
                # 显示预览
                scaled_pixmap = pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_preview_label.setPixmap(scaled_pixmap)
                
                # 将图片转换为Base64
                byte_array = QByteArray()
                buffer = QBuffer(byte_array)
                buffer.open(QIODevice.WriteOnly)
                pixmap.save(buffer, "PNG")
                
                # 编码并显示
                encoded_image = base64.b64encode(byte_array.data())
                encoded_text = encoded_image.decode('utf-8')
                self.output_text.setText(encoded_text)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"编码时发生错误: {str(e)}")
    
    def decode_data(self):
        """解码数据"""
        try:
            input_text = self.input_text.toPlainText()
            if not input_text:
                # 如果是图片模式且输入为空，尝试从剪贴板获取文本
                if self.current_mode == 1:
                    clipboard = QApplication.clipboard()
                    input_text = clipboard.text()
                    if not input_text:
                        QMessageBox.warning(self, "警告", "请输入要解码的Base64文本或从剪贴板获取")
                        return
                    self.input_text.setText(input_text)
                else:
                    QMessageBox.warning(self, "警告", "请输入要解码的Base64文本")
                    return
            
            # 清理输入文本（移除可能的换行符等）
            input_text = input_text.strip()
            
            if self.current_mode == 0:  # 文本模式
                # 解码文本
                decoded_bytes = base64.b64decode(input_text)
                try:
                    decoded_text = decoded_bytes.decode('utf-8')
                    self.output_text.setText(decoded_text)
                except UnicodeDecodeError:
                    # 如果不是UTF-8文本，显示十六进制
                    self.output_text.setText(f"无法以文本显示，十六进制内容: {decoded_bytes.hex()}")
                
            else:  # 图片模式
                # 解码图片
                decoded_image = base64.b64decode(input_text)
                pixmap = QPixmap()
                pixmap.loadFromData(decoded_image)
                
                if pixmap.isNull():
                    QMessageBox.warning(self, "警告", "无法将Base64数据解析为图片")
                    return
                
                # 显示预览
                scaled_pixmap = pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_preview_label.setPixmap(scaled_pixmap)
                self.output_text.setText("图片解码成功，请查看上方预览")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"解码时发生错误: {str(e)}")
    
    def clear_fields(self):
        """清除所有字段"""
        self.input_text.clear()
        self.output_text.clear()
        self.image_preview_label.clear()
        self.image_preview_label.setText("图片预览")

    def update_style(self):
        """更新样式以匹配当前主题"""
        # 导入样式变量
        from ui.styles import quick_check_style, background_color, text_color, button_bg_color, button_text_color, button_hover_color, border_color
        
        # 应用全局样式
        self.setStyleSheet(quick_check_style)
        
        # 更新标签样式
        self.description_label.setStyleSheet(f"font-size: 16px; font-weight: bold; margin: 10px; color: {text_color};")
        self.mode_label.setStyleSheet(f"color: {text_color};")
        self.input_label.setStyleSheet(f"color: {text_color};")
        self.output_label.setStyleSheet(f"color: {text_color};")
        self.image_preview_label.setStyleSheet(f"border: 1px solid {border_color}; color: {text_color};")
        
        # 更新输入输出文本框样式
        text_style = f"background-color: {background_color}; color: {text_color}; border: 1px solid {border_color};"
        self.input_text.setStyleSheet(text_style)
        self.output_text.setStyleSheet(text_style)
        
        # 更新按钮样式
        button_style = f"""
            QPushButton {{
                background-color: {button_bg_color};
                color: {button_text_color};
                border: 1px solid {border_color};
                border-radius: 3px;
                padding: 5px 15px;
            }}
            QPushButton:hover {{
                background-color: {button_hover_color};
            }}
        """
        self.encode_button.setStyleSheet(button_style)
        self.decode_button.setStyleSheet(button_style)
        self.clear_button.setStyleSheet(button_style)
        self.open_image_button.setStyleSheet(button_style)
        
        # 更新下拉框样式
        combo_style = f"""
            QComboBox {{
                background-color: {button_bg_color};
                color: {button_text_color};
                border: 1px solid {border_color};
                padding: 3px;
                border-radius: 3px;
            }}
            QComboBox:hover {{
                background-color: {button_hover_color};
            }}
            QComboBox QAbstractItemView {{
                background-color: {background_color};
                color: {text_color};
                selection-background-color: {button_hover_color};
            }}
        """
        self.mode_combo.setStyleSheet(combo_style)

    def open_image(self):
        """打开图片文件并显示"""
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("选择图片文件")
        file_dialog.setNameFilter("图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                image_path = file_paths[0]
                try:
                    # 加载图片
                    pixmap = QPixmap(image_path)
                    if pixmap.isNull():
                        QMessageBox.warning(self, "错误", "无法加载图片文件。")
                        return
                    
                    # 显示图片预览
                    self.display_image(pixmap)
                    
                    # 编码图片为Base64并显示在输出框中
                    encoded_data = self.encode_image_to_base64(pixmap)
                    self.output_text.setPlainText(encoded_data)
                    
                    # 提示用户
                    QMessageBox.information(self, "成功", "图片已加载并编码为Base64格式。")
                    
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"处理图片时出错: {str(e)}")
    
    def encode_image_to_base64(self, pixmap):
        """将图片编码为Base64字符串"""
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.WriteOnly)
        
        # 保存为PNG格式
        pixmap.save(buffer, "PNG")
        
        # 编码为Base64
        encoded_data = base64.b64encode(byte_array.data()).decode('ascii')
        return encoded_data

# 用于独立测试
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = Base64Tool()
    window.show()
    sys.exit(app.exec())
