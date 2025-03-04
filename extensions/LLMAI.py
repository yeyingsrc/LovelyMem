# 全局变量用于保持对话框引用
_current_dialog = None

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QPushButton, 
                             QHBoxLayout, QLabel, QLineEdit, QApplication, QSplitter, QDialog,
                             QFormLayout, QMessageBox, QFrame, QTabWidget, QScrollArea,
                             QToolBar, QStatusBar, QProgressBar, QGroupBox, QSizePolicy, QFileDialog)
from PySide6.QtCore import Signal, QObject, Slot, QRunnable, QThreadPool, Qt, QSize
from PySide6.QtGui import QTextCursor, QPalette, QColor, QFont, QIcon, QAction
import openai
from openai import OpenAI
import httpx
import requests
import sys
import traceback
import json
from markdown import markdown
from core.config_manager import load_config, save_config
from ui.styles import (candy_background, common_font_style, button_style, 
                     background_color, text_color, button_bg_color, 
                     button_text_color, button_hover_color, border_color,
                     apply_color_scheme, is_dark_mode)
import os

plugin_info = {
    "title": "AI分析",
    "description": "使用AI分析文件内容",
    "usage": "选择要分析的行数,然后点击提交",
    "category": "文件分析"
}

class AISignals(QObject):
    update_response = Signal(str, int)
    stream_response = Signal(str)  # New signal for streaming responses
    finished = Signal()

class AIWorker(QRunnable):
    def __init__(self, content_to_analyze, lines_to_analyze, base_prompt, openai_api_key, proxy, 
                 openai_api_url, openai_model, openai_temperature):
        super().__init__()
        self.content_to_analyze = content_to_analyze
        self.lines_to_analyze = lines_to_analyze
        self.base_prompt = base_prompt
        self.openai_api_key = openai_api_key
        self.proxy = proxy
        self.openai_api_url = openai_api_url
        self.openai_model = openai_model
        self.openai_temperature = openai_temperature
        self.signals = AISignals()
        
        # Configure OpenAI client
        self.client = OpenAI(
            api_key=self.openai_api_key,
            base_url=self.openai_api_url if self.openai_api_url else None,
            http_client=httpx.Client(proxies=self.proxy) if self.proxy else None
        )

    def run(self):
        try:
            # 直接使用传入的内容而不是读取文件
            content = self.content_to_analyze
            msg = f"以下是需要分析的内容:\n\n{content}\n\n请根据以上内容进行分析"
            
            total_response = ""
            total_tokens = 0
            
            for chunk in self.fetch_completions(msg, self.base_prompt):
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    if content:
                        self.signals.stream_response.emit(content)
                        total_response += content
                        
            # Estimate token count (approximate)
            total_tokens = len(total_response.split()) * 1.3
            self.signals.update_response.emit(total_response, int(total_tokens))
        except Exception as e:
            self.signals.update_response.emit(f"错误: {str(e)}", 0)
            print(f"获取AI响应错误: {str(e)}")
            print(traceback.format_exc())
        finally:
            self.signals.finished.emit()

    def fetch_completions(self, msg, base_prompt):
        try:
            stream = self.client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一名Windows问题专家，专注于通过分析用户提供的内存提取内容，识别潜在问题。你需要引导用户分析数据，找到可能的突破口，通常与恶意程序或其他不常见的异常内容相关。通过详细的分析，帮助用户深入理解问题的根本原因，并提出有效的解决方案。"
                    },
                    {
                        "role": "user",
                        "content": f"{base_prompt} {msg}"
                    }
                ],
                temperature=self.openai_temperature,
                stream=True
            )
            return stream
        except Exception as e:
            raise Exception(f"OpenAI API调用失败: {str(e)}")

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("设置")
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建设置组
        settings_group = QGroupBox("OpenAI设置")
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        form_layout.setContentsMargins(8, 8, 8, 8)
        
        # API密钥
        self.api_key_input = QLineEdit(self.parent.openai_api_key if self.parent else "")
        self.api_key_input.setPlaceholderText("输入OpenAI API密钥")
        self.api_key_input.setMinimumWidth(250)
        
        # API URL
        self.api_url_input = QLineEdit(self.parent.openai_api_url if self.parent else "")
        self.api_url_input.setPlaceholderText("可选: 自定义API端点")
        
        # 模型选择
        self.model_input = QLineEdit(self.parent.openai_model if self.parent else "")
        self.model_input.setPlaceholderText("例如: gpt-3.5-turbo")
        
        # 温度设置
        self.temperature_input = QLineEdit(str(self.parent.openai_temperature if self.parent else 0.7))
        self.temperature_input.setPlaceholderText("0.0-1.0")
        self.temperature_input.setMaximumWidth(100)
        
        # 代理设置
        self.proxy_input = QLineEdit(self.parent.proxy if self.parent else "")
        self.proxy_input.setPlaceholderText("可选: 代理服务器地址")
        
        # 添加表单项
        form_layout.addRow("API密钥:", self.api_key_input)
        form_layout.addRow("API地址:", self.api_url_input)
        form_layout.addRow("模型:", self.model_input)
        form_layout.addRow("温度值:", self.temperature_input)
        form_layout.addRow("代理:", self.proxy_input)
        
        settings_group.setLayout(form_layout)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        save_button = QPushButton("保存")
        save_button.setFixedSize(80, 28)
        save_button.clicked.connect(self.save_settings)
        save_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {button_bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {button_hover_color};
            }}
        """)
        
        cancel_button = QPushButton("取消")
        cancel_button.setFixedSize(80, 28)
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {button_bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                background-color: {button_hover_color};
            }}
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addWidget(settings_group)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.resize(400, 280)
        
    def save_settings(self):
        if self.parent:
            user_config = {
                'LLM_CONFIG': {
                    'openai_api_key': self.api_key_input.text(),
                    'openai_api_url': self.api_url_input.text(),
                    'openai_model': self.model_input.text(),
                    'openai_temperature': float(self.temperature_input.text())
                },
                'base_config': {'proxy': {'url': self.proxy_input.text()}}
            }
            
            save_config(user_config)
            self.parent.config = load_config()
            self.parent.load_config()
            QMessageBox.information(self, "配置保存", "配置已成功保存。")
            self.accept()

class ResultWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.setWindowTitle("分析结果")
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 结果显示区
        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)
        
        layout.addWidget(self.result_output)
        self.setLayout(layout)
        self.resize(800, 600)
        
        # 更新主题
        self.update_theme()
        
        # 监听主题变化
        app = QApplication.instance()
        app.paletteChanged.connect(self.update_theme)

    def closeEvent(self, event):
        # 通知父窗口结果窗口已关闭
        if self.parent:
            self.parent.on_result_window_closed()
        event.accept()

    def update_theme(self):
        # 更新整体样式
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {background_color};
                color: {text_color};
            }}
            QTextEdit {{
                background-color: {background_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 4px;
            }}
            QTextEdit:focus {{
                border: 1px solid {button_hover_color};
            }}
        """)
    
    def update_text(self, text, tokens=None):
        if tokens is not None:
            # Only update the full response when we get the final result
            html_content = markdown(text)
            self.result_output.setHtml(html_content)
            if tokens > 0:
                current_text = self.result_output.toHtml()
                token_info = f"<br><br>使用的tokens数量: {tokens}"
                self.result_output.setHtml(current_text + token_info)
        else:
            # For streaming updates, append the new text
            cursor = self.result_output.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.insertText(text)
            self.result_output.setTextCursor(cursor)
            self.result_output.ensureCursorVisible()

class AIAnalysisDialog(QWidget):
    def __init__(self, file_path=None):
        super().__init__()
        self.file_path = file_path
        self.setWindowTitle("AI分析助手")
        # 设置窗口特性
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        
        self.config = load_config()
        self.load_config()
        self.init_ui()
        
        # 如果有文件路径，加载文件内容
        if self.file_path:
            self.load_file_content()
        
        self.update_theme()
        
        # 监听主题变化
        app = QApplication.instance()
        app.paletteChanged.connect(self.update_theme)
        
        # 连接设置按钮事件
        self.settings_action.clicked.connect(self.show_settings)
        
        # 创建结果窗口（但不显示）
        self.result_window = None

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 文件预览组
        preview_group = QGroupBox("文件预览")
        preview_layout = QVBoxLayout()
        
        # 创建文件预览文本框
        self.file_preview = QTextEdit()
        self.file_preview.setReadOnly(False)
        self.file_preview.setMinimumHeight(200)
        
        # 控制区域布局
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)
        
        # 分析行数输入
        lines_label = QLabel("分析行数:")
        self.lines_input = QLineEdit()
        self.lines_input.setPlaceholderText("20")
        self.lines_input.setFixedWidth(60)
        
        # 运行分析按钮
        self.run_action = QPushButton("运行分析")
        self.run_action.clicked.connect(self.on_submit)
        
        # 设置按钮
        self.settings_action = QPushButton("设置")
        
        # 载入文件按钮
        self.load_file_action = QPushButton("载入文件")
        self.load_file_action.clicked.connect(self.load_file_dialog)
        
        # 添加控件到控制布局
        control_layout.addWidget(lines_label)
        control_layout.addWidget(self.lines_input)
        control_layout.addWidget(self.run_action)
        control_layout.addWidget(self.settings_action)
        control_layout.addWidget(self.load_file_action)
        control_layout.addStretch()
        
        preview_layout.addWidget(self.file_preview)
        preview_layout.addLayout(control_layout)
        preview_group.setLayout(preview_layout)
        
        # 提示输入组
        prompt_group = QGroupBox("分析提示")
        prompt_layout = QVBoxLayout()
        self.prompt_input = QTextEdit()
        self.prompt_input.setMinimumHeight(100)
        self.prompt_input.setPlaceholderText("请输入分析提示...")
        prompt_layout.addWidget(self.prompt_input)
        prompt_group.setLayout(prompt_layout)
        
        # 添加所有组件到主布局
        main_layout.addWidget(preview_group)
        main_layout.addWidget(prompt_group)
        
        # 设置主窗口布局
        self.setLayout(main_layout)
        self.resize(600, 500)  # 减小主窗口尺寸

    def update_theme(self):
        # 更新整体样式
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {background_color};
                color: {text_color};
            }}
            QToolBar {{
                background-color: {button_bg_color};
                border: none;
                padding: 5px;
            }}
            QToolBar QToolButton {{
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 5px;
                color: {text_color};
            }}
            QToolBar QToolButton:hover {{
                background-color: {button_hover_color};
            }}
            QGroupBox {{
                background-color: {background_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                margin-top: 1em;
                padding-top: 0.5em;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QLabel {{
                color: {text_color};
                font-size: 12px;
            }}
            QTextEdit {{
                background-color: {button_bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 5px;
            }}
            QTextEdit:focus {{
                border: 1px solid {button_hover_color};
            }}
            QLineEdit {{
                background-color: {button_bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 5px;
            }}
            QLineEdit:focus {{
                border: 1px solid {button_hover_color};
            }}
            QStatusBar {{
                background-color: {button_bg_color};
                color: {text_color};
                border-top: 1px solid {border_color};
            }}
            QProgressBar {{
                border: 1px solid {border_color};
                border-radius: 4px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {button_hover_color};
                border-radius: 3px;
            }}
        """)
        
    def load_config(self):
        llm_config = self.config.get('LLM_CONFIG', {})
        self.openai_api_key = llm_config.get('openai_api_key', '')
        self.openai_api_url = llm_config.get('openai_api_url', '')
        self.openai_model = llm_config.get('openai_model', '')
        self.openai_temperature = llm_config.get('openai_temperature', 0.7)
        self.proxy = self.config.get('base_config', {}).get('proxy', {}).get('url', '')

    def load_file_content(self):
        self.update_preview()

    def update_preview(self):
        """更新预览内容"""
        try:
            if self.file_path:  # 只在有文件路径时尝试读取文件
                with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    self.file_preview.setPlainText(content)
        except Exception as e:
            print(f"更新预览错误: {str(e)}")
            traceback.print_exc()

    @Slot()
    def on_submit(self):
        """提交分析请求"""
        try:
            # 获取分析行数
            lines_text = self.lines_input.text().strip()
            lines_to_analyze = int(lines_text) if lines_text else 20  # 默认20行
            
            # 获取提示文本
            base_prompt = self.prompt_input.toPlainText().strip()
            if not base_prompt:
                QMessageBox.warning(self, "提示", "请输入分析提示")
                return
            
            # 使用编辑框中的实际内容而不是文件内容
            content_to_analyze = self.file_preview.toPlainText()
            
            self.run_action.setEnabled(False)

            worker = AIWorker(content_to_analyze, lines_to_analyze, base_prompt, 
                          self.openai_api_key, self.proxy, self.openai_api_url, 
                          self.openai_model, self.openai_temperature)
            worker.signals.update_response.connect(self.update_response_text)
            worker.signals.stream_response.connect(self.update_response_text)
            worker.signals.finished.connect(self.on_worker_finished)

            QThreadPool.globalInstance().start(worker)
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的分析行数")
        except Exception as e:
            print(f"提交错误: {str(e)}")
            print(traceback.format_exc())

    @Slot(str, int)
    def update_response_text(self, text, tokens=None):
        # 确保结果窗口存在并显示
        if self.result_window is None:
            self.result_window = ResultWindow(self)
            self.result_window.show()
        
        self.result_window.update_text(text, tokens)
        
        if tokens is not None:  # Final response received
            self.run_action.setEnabled(True)

    @Slot()
    def on_worker_finished(self):
        self.run_action.setEnabled(True)

    def update_ui_from_config(self):
        # 更新UI元素以反映当前配置
        pass

    def show_settings(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec()

    def load_file_dialog(self):
        """打开文件选择对话框"""
        try:
            # 获取output文件夹的绝对路径
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
            
            # 如果output文件夹不存在，创建它
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 打开文件选择对话框
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择文件",
                output_dir,
                "文本文件 (*.txt *.csv)"
            )
            
            if file_path:
                self.file_path = file_path
                self.load_file_content()
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"载入文件时发生错误: {str(e)}")
            print(f"载入文件错误: {str(e)}")
            print(traceback.format_exc())

    def on_result_window_closed(self):
        """处理结果窗口关闭事件"""
        self.result_window = None
        self.run_action.setEnabled(True)

def run(file_path=None):
    try:
        print(f"正在创建 AIAnalysisDialog，文件路径: {file_path}")
        dialog = AIAnalysisDialog(file_path)
        if file_path:
            try:
                print(f"正在读取文件: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    dialog.file_preview.setPlainText(content)
                print("文件内容已加载")
            except Exception as file_error:
                print(f"读取文件错误: {str(file_error)}")
                print(traceback.format_exc())
        dialog.show()
        # 保持对话框的引用
        global _current_dialog
        _current_dialog = dialog
        print("对话框已显示")
    except Exception as e:
        print(f"运行错误: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    run("test_file.txt")
    sys.exit(app.exec())
