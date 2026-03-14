import json
import os
try:
    import jieba
except ImportError:
    logger_topic = logging.getLogger(__name__)
    logger_topic.warning("jieba模块未安装，无法进行离线分析。")
    logger_topic.warning("请在启动目录打开终端执行命令 '..\Tools\python3\python.exe -m pip install jieba'")
    jieba = None
import re
import yaml
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QTextCursor, QIcon
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QRadioButton, QButtonGroup, QGroupBox,
    QMessageBox, QProgressBar, QSplitter, QWidget,
    QScrollArea, QFrame, QListWidget, QListWidgetItem, QApplication, QToolButton, QCheckBox
)

from ui.styles import (
    background_color, text_color, button_bg_color, button_text_color,
    button_hover_color, border_color, group_title_bg_color,
    common_font_style, theme_button_color, minimize_button_color, 
    maximize_button_color, close_button_color
)

import logging
logger = logging.getLogger(__name__)


class TopicAnalysisWorker(QThread):
    """题意分析工作线程"""
    analysis_finished = Signal(dict)  # 分析完成信号
    error_occurred = Signal(str)  # 错误信号
    progress_updated = Signal(int)  # 进度更新信号
    
    def __init__(self, text, mode, api_config=None, available_buttons=None):
        super().__init__()
        self.text = text
        self.mode = mode  # 'online' 或 'offline'
        self.api_config = api_config
        self.available_buttons = available_buttons or []
        self.keywords_mapping = {
            # 内存取证相关关键词映射
            '进程': ['进程列表', '进程树', '隐藏进程'],
            '网络': ['网络连接', '网络扫描'],
            '注册表': ['注册表', '注册表分析'],
            '文件': ['文件列表', '文件扫描', '文件恢复'],
            '恶意软件': ['恶意软件检测', '病毒扫描'],
            '密码': ['密码提取', '哈希值'],
            '内存': ['内存映射', '内存分析'],
            '驱动': ['驱动程序', '内核模块'],
            '时间线': ['时间线分析'],
            '用户': ['用户信息', '登录记录'],
            'dll': ['DLL列表', '模块分析'],
            '句柄': ['句柄信息'],
            '服务': ['系统服务'],
            '缓存': ['缓存分析'],
            '日志': ['事件日志'],
            'flag': ['字符串搜索', '关键词搜索'],
            '字符串': ['字符串提取', '字符串搜索'],
            '加密': ['加密分析', '解密'],
            '隐写': ['隐写术检测'],
            '取证': ['取证分析', '证据提取']
        }
    
    def run(self):
        try:
            if self.mode == 'online':
                result = self._online_analysis()
            else:
                result = self._offline_analysis()
            
            self.analysis_finished.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def _online_analysis(self):
        """在线模式：使用大模型分析"""
        try:
            import openai
            
            # 配置OpenAI客户端
            if self.api_config:
                client = openai.OpenAI(
                    api_key=self.api_config.get('openai_api_key'),
                    base_url=self.api_config.get('openai_api_base')
                )
                
                self.progress_updated.emit(30)
                
                # 使用传入的按钮列表
                available_buttons = self.available_buttons if self.available_buttons else self._get_available_buttons()
                
                # 从外部文件读取提示词模板
                prompt_template = self._load_prompt_template()
                prompt = prompt_template.format(
                    text=self.text,
                    available_buttons=', '.join(available_buttons)
                )
                
                self.progress_updated.emit(60)
                
                # 调用API
                response = client.chat.completions.create(
                    model=self.api_config.get('openai_model', 'gpt-3.5-turbo'),
                    messages=[
                        {"role": "system", "content": "你是一个专业的内存取证分析专家，擅长分析CTF题目和实际案例。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                
                self.progress_updated.emit(90)
                logger.debug("提示词已发送")
                
                # 解析响应
                content = response.choices[0].message.content
                
                logger.debug(f"AI响应长度: {len(content)}")
                
                # 尝试解析JSON
                try:
                    # 检查是否被markdown代码块包裹
                    json_content = content
                    if content.strip().startswith('```json') and content.strip().endswith('```'):
                        logger.debug("检测到markdown代码块，提取JSON内容")
                        # 提取代码块中的JSON内容
                        lines = content.strip().split('\n')
                        json_lines = lines[1:-1]  # 去掉第一行的```json和最后一行的```
                        json_content = '\n'.join(json_lines)
                        #print(f"DEBUG: 提取的JSON内容: {json_content}")
                    elif '```json' in content:
                        logger.debug("检测到包含```json的内容，尝试提取")
                        # 查找```json和```之间的内容
                        start_idx = content.find('```json') + 7
                        end_idx = content.find('```', start_idx)
                        if end_idx != -1:
                            json_content = content[start_idx:end_idx].strip()
                            #print(f"DEBUG: 提取的JSON内容: {json_content}")
                    
                    result = json.loads(json_content)
                    logger.debug("JSON解析成功")
                    
                    # 确保包含推荐按钮字段
                    if 'recommended_buttons' not in result:
                        logger.debug("没有找到recommended_buttons字段，尝试从suggested_tools获取")
                        result['recommended_buttons'] = result.get('suggested_tools', [])
                    else:
                        #print(f"DEBUG: 找到recommended_buttons字段: {result['recommended_buttons']}")
                        pass
                except json.JSONDecodeError as e:
                    logger.debug(f"JSON解析失败: {e}，使用简单解析模式")
                    # 如果不是标准JSON，进行简单解析
                    result = {
                        'main_topics': [],
                        'recommended_buttons': [],
                        'keywords': [],
                        'analysis_summary': content
                    }
                    #print(f"DEBUG: 简单解析结果: {result}")
                
                self.progress_updated.emit(100)
                return result
            else:
                raise Exception("未配置API信息")
                
        except Exception as e:
            raise Exception(f"在线分析失败: {str(e)}")
    
    def _offline_analysis(self):
        """离线模式：使用jieba分词和yaml配置文件匹配"""
        logger.debug("开始离线分析")
        
        self.progress_updated.emit(20)
        
        # 加载yaml配置文件
        keywords_mapping = self._load_keywords_mapping()
        #print(f"DEBUG: 加载了 {len(keywords_mapping)} 个关键词配置")
        #print(f"DEBUG: 关键词配置键: {list(keywords_mapping.keys())[:10]}...")  # 只显示前10个
        
        # 使用jieba分词
        words = jieba.lcut(self.text)
        #print(f"DEBUG: 分词结果 ({len(words)}个词): {words[:20]}...")  # 只显示前20个词
        
        self.progress_updated.emit(50)
        
        # 关键词匹配
        matched_topics = []
        recommended_buttons = []
        keywords = []
        
        logger.debug("开始关键词匹配")
        for word in words:
            word_lower = word.lower()
            for key, config in keywords_mapping.items():
                if key in word_lower or word_lower in key:
                    #print(f"DEBUG: 匹配成功! 词: '{word}', 关键词: '{key}'")
                    if key not in matched_topics:
                        matched_topics.append(key)
                    # 从配置中获取推荐按钮
                    buttons = config.get('buttons', [])
                    #print(f"DEBUG: 从配置获取按钮: {buttons}")
                    recommended_buttons.extend(buttons)
                    if word not in keywords:
                        keywords.append(word)
        
        self.progress_updated.emit(80)
        
        # 去重并按优先级排序
        recommended_buttons = list(set(recommended_buttons))
        #print(f"DEBUG: 去重后的推荐按钮: {recommended_buttons}")
        
        # 生成分析总结
        analysis_summary = f"通过离线分析，识别出{len(matched_topics)}个主要考点，推荐{len(recommended_buttons)}个相关按钮进行高亮。"
        
        self.progress_updated.emit(100)
        
        result = {
            'main_topics': matched_topics,
            'recommended_buttons': recommended_buttons,
            'keywords': keywords,
            'analysis_summary': analysis_summary
        }
        
        #print(f"DEBUG: 离线分析最终结果: {result}")
        logger.debug("离线分析完成")
        
        return result
    
    def _load_keywords_mapping(self):
        """加载关键词映射配置文件"""
        try:
            config_path = os.path.join('config', 'topic_analysis_keywords.yaml')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                # 如果配置文件不存在，创建默认配置
                default_config = self._create_default_keywords_config()
                self._save_keywords_mapping(default_config)
                return default_config
        except Exception as e:
            logger.error(f"加载关键词配置失败: {e}")
            return self._create_default_keywords_config()
    
    def _load_prompt_template(self):
        """加载提示词模板文件"""
        prompt_path = os.path.join('config', 'topic_analysis_prompt.txt')
        if os.path.exists(prompt_path):
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"加载提示词模板文件失败: {e}")
                # 返回默认提示词
                return self._get_default_prompt_template()
        else:
            logger.info(f"提示词模板文件不存在: {prompt_path}")
            return self._get_default_prompt_template()
    
    def _get_default_prompt_template(self):
        """获取默认提示词模板"""
        return """请分析以下题目描述，作为内存取证专家，从可用的工具按钮中挑选最佳的高亮按钮：

题目内容：{text}

可用的工具按钮：{available_buttons}

请从以下角度分析：
1. 主要考点（如：进程分析、网络连接、注册表、文件系统、恶意软件检测等）
2. 从可用按钮中挑选3-5个最相关的按钮进行高亮推荐
3. 关键词提取
4. 按重要性排序推荐的按钮

请以JSON格式返回结果，包含以下字段：
- main_topics: 主要考点列表
- recommended_buttons: 推荐高亮的按钮列表（按重要性排序）
- keywords: 提取的关键词列表
- analysis_summary: 分析总结和推荐理由"""
    
    def _create_default_keywords_config(self):
        """创建默认的关键词配置"""
        return {
            '进程': {
                'buttons': ['进程列表', '进程树', '隐藏进程'],
                'priority': 1,
                'description': '进程相关分析'
            },
            '网络': {
                'buttons': ['网络连接', '网络扫描'],
                'priority': 2,
                'description': '网络连接分析'
            },
            '注册表': {
                'buttons': ['注册表', '注册表分析'],
                'priority': 2,
                'description': '注册表分析'
            },
            '文件': {
                'buttons': ['文件列表', '文件扫描', '文件恢复'],
                'priority': 1,
                'description': '文件系统分析'
            },
            '恶意软件': {
                'buttons': ['恶意软件检测', '病毒扫描'],
                'priority': 3,
                'description': '恶意软件检测'
            },
            '密码': {
                'buttons': ['密码提取', '哈希值'],
                'priority': 2,
                'description': '密码和哈希分析'
            },
            'flag': {
                'buttons': ['字符串搜索', '关键词搜索'],
                'priority': 1,
                'description': 'Flag搜索'
            }
        }
    
    def _save_keywords_mapping(self, config):
        """保存关键词映射配置"""
        try:
            config_dir = 'config'
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            config_path = os.path.join(config_dir, 'topic_analysis_keywords.yaml')
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            logger.error(f"保存关键词配置失败: {e}")
    
    def _get_available_buttons(self):
        """获取默认按钮列表（备用方案）"""
        # 返回默认按钮列表，作为备用方案
        return [
            '进程列表', '进程树', '隐藏进程', '网络连接', '网络扫描',
            '注册表', '注册表分析', '文件列表', '文件扫描', '文件恢复',
            '恶意软件检测', '病毒扫描', '密码提取', '哈希值',
            '字符串搜索', '关键词搜索', '内存映射', '驱动程序',
            '时间线分析', '用户信息', 'DLL列表', '句柄信息',
            '系统服务', '缓存分析', '事件日志'
        ]


class TopicAnalysisDialog(QDialog):
    """题意分析对话框"""
    
    def __init__(self, parent=None, highlight_manager=None):
        super().__init__(parent)
        self.setWindowTitle("题意分析")
        self.resize(800, 600)
        # 设置为非模态对话框，允许操作主界面
        self.setModal(False)
        # 设置无边框窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.highlight_manager = highlight_manager
        
        # 用于窗口拖拽的变量
        self.drag_position = None
        
        # 加载API配置
        self.api_config = self._load_api_config()
        
        # 创建界面
        self._create_ui()
        
        # 应用主题样式
        self.apply_style()
        
        # 监听主题变化
        QApplication.instance().paletteChanged.connect(self.on_theme_changed)
        
        # 工作线程
        self.worker = None
    
    def apply_style(self):
        """应用主题样式"""
        # 从ui.styles重新导入最新的样式，确保与主界面保持一致
        import ui.styles
        
        # 应用与主界面一致的样式
        self.setStyleSheet(f"""
            QDialog {{
                {ui.styles.candy_background}
                {ui.styles.common_font_style}
                border: 1px solid {ui.styles.border_color};
                border-radius: 10px;
            }}
            {ui.styles.button_style}
            {ui.styles.tool_button_style}
            
            QGroupBox {{
                background-color: {ui.styles.background_color};
                color: {ui.styles.text_color};
                border: 1px solid {ui.styles.border_color};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                {ui.styles.common_font_style}
            }}
            
            QGroupBox::title {{
                background-color: {ui.styles.group_title_bg_color};
                color: {ui.styles.text_color};
                padding: 5px 10px;
                border-radius: 3px;
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                {ui.styles.common_font_style}
            }}
            
            QTextEdit {{
                background-color: {ui.styles.background_color};
                color: {ui.styles.text_color};
                border: 1px solid {ui.styles.border_color};
                border-radius: 5px;
                padding: 5px;
                {ui.styles.common_font_style}
            }}
            
            QLabel {{
                color: {ui.styles.text_color};
                {ui.styles.common_font_style}
            }}
            
            QProgressBar {{
                border: 1px solid {ui.styles.border_color};
                border-radius: 5px;
                background-color: {ui.styles.background_color};
                color: {ui.styles.text_color};
                text-align: center;
                {ui.styles.common_font_style}
            }}
            
            QProgressBar::chunk {{
                background-color: {ui.styles.button_hover_color};
                border-radius: 3px;
            }}
            
            QScrollArea {{
                background-color: {ui.styles.background_color};
                border: 1px solid {ui.styles.border_color};
                border-radius: 5px;
            }}
            
            QFrame {{
                background-color: {ui.styles.background_color};
                border: 1px solid {ui.styles.border_color};
                border-radius: 5px;
            }}
            
            QSplitter::handle {{
                background-color: {ui.styles.border_color};
            }}
            
            QSplitter::handle:hover {{
                background-color: {ui.styles.button_hover_color};
            }}
        """)
        
        # 更新标题栏样式
        if hasattr(self, 'title_bar'):
            self.title_bar.setStyleSheet(f"""
                {ui.styles.candy_background}
                {ui.styles.common_font_style}
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            """)
            
            # 更新圆形按钮样式
            if hasattr(self, 'min_button'):
                self.update_circle_button_style(self.min_button, minimize_button_color)
            if hasattr(self, 'max_button'):
                self.update_circle_button_style(self.max_button, maximize_button_color)
            if hasattr(self, 'close_button_title'):
                self.update_circle_button_style(self.close_button_title, close_button_color)
        
        # 更新所有子组件的样式，与主界面保持一致
        for widget in self.findChildren(QWidget):
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(ui.styles.button_style)
            elif isinstance(widget, QTextEdit):
                widget.setStyleSheet(ui.styles.cmd_output_style)
            elif isinstance(widget, QGroupBox):
                widget.setStyleSheet(ui.styles.right_panel_style)
            
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            try:
                widget.update()
            except TypeError:
                # 某些组件的update方法可能需要参数，跳过这些组件
                pass
        
        # 强制更新整个对话框
        self.repaint()
    
    def on_theme_changed(self):
        """主题变化时的回调"""
        self.apply_style()
    
    def _load_api_config(self):
        """加载API配置"""
        try:
            config_path = os.path.join('config', 'user_settings.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('LLM_CONFIG', {})
        except Exception as e:
            logger.error(f"加载API配置失败: {e}")
        return {}
    
    def _create_ui(self):
        """创建用户界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建自定义标题栏
        self._create_title_bar()
        main_layout.addWidget(self.title_bar)
        
        # 创建内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建分隔器
        splitter = QSplitter(Qt.Vertical)
        content_layout.addWidget(splitter)
        
        # 上半部分：输入区域
        input_widget = self._create_input_area()
        splitter.addWidget(input_widget)
        
        # 下半部分：结果区域
        result_widget = self._create_result_area()
        splitter.addWidget(result_widget)
        
        # 设置分隔比例
        splitter.setSizes([300, 300])
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        self.analyze_button = QPushButton("开始分析")
        self.analyze_button.clicked.connect(self._start_analysis)
        
        self.highlight_button = QPushButton("应用按钮高亮")
        self.highlight_button.clicked.connect(self._apply_highlights)
        self.highlight_button.setEnabled(False)
        
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.analyze_button)
        button_layout.addWidget(self.highlight_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        content_layout.addLayout(button_layout)
        main_layout.addWidget(content_widget)
    
    def _create_title_bar(self):
        """创建自定义标题栏"""
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(30)
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        
        # 添加图标
        icon_label = QLabel()
        icon_label.setPixmap(QIcon('res/logo.ico').pixmap(20, 20))
        title_layout.addWidget(icon_label)
        
        # 添加标题
        title_label = QLabel("题意分析")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 添加最小化按钮
        self.min_button = self.create_circle_button(minimize_button_color)
        self.min_button.clicked.connect(self.showMinimized)
        self.min_button.setToolTip("最小化")
        
        # 添加最大化/还原按钮
        self.max_button = self.create_circle_button(maximize_button_color)
        self.max_button.clicked.connect(self.toggle_maximize)
        self.max_button.setToolTip("最大化")
        
        # 添加关闭按钮
        self.close_button_title = self.create_circle_button(close_button_color)
        self.close_button_title.clicked.connect(self.close)
        self.close_button_title.setToolTip("关闭")
        
        # 添加标题栏按钮
        title_layout.addWidget(self.min_button)
        title_layout.addWidget(self.max_button)
        title_layout.addWidget(self.close_button_title)
    
    def create_circle_button(self, base_color):
        """创建圆形按钮"""
        button = QPushButton()
        button.setFixedSize(14, 14)
        return button
    
    def toggle_maximize(self):
        """切换最大化/还原状态"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    
    def update_circle_button_style(self, button, base_color):
        """更新圆形按钮样式"""
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {base_color};
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {button_hover_color};
            }}
        """)
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 用于拖拽窗口"""
        if event.button() == Qt.LeftButton and self.title_bar.geometry().contains(event.position().toPoint()):
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 用于拖拽窗口"""
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self.drag_position = None
    
    def _create_input_area(self):
        """创建输入区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 模式选择
        mode_group = QGroupBox("分析模式")
        mode_layout = QHBoxLayout(mode_group)
        
        self.mode_group = QButtonGroup()
        
        self.online_radio = QRadioButton("在线模式（大模型分析）")
        self.offline_radio = QRadioButton("离线模式（关键词匹配）")
        
        # 检查是否有API配置
        if self.api_config and self.api_config.get('openai_api_key'):
            self.online_radio.setChecked(True)
        else:
            self.offline_radio.setChecked(True)
            self.online_radio.setEnabled(False)
            self.online_radio.setToolTip("请先在设置中配置API信息")
        
        self.mode_group.addButton(self.online_radio, 0)
        self.mode_group.addButton(self.offline_radio, 1)
        
        mode_layout.addWidget(self.online_radio)
        mode_layout.addWidget(self.offline_radio)
        mode_layout.addStretch()
        
        layout.addWidget(mode_group)
        
        # 区域选择
        area_group = QGroupBox("分析区域选择")
        area_layout = QVBoxLayout(area_group)
        
        # 创建区域选择复选框
        self.area_checkboxes = {}
        area_info = {
            'memprocfs': 'MemProcFS功能区',
            'vol2': 'Volatility2功能区', 
            'vol3': 'Volatility3功能区',
            'vol2linux': 'Volatility2 Linux功能区',
            'vol3linux': 'Volatility3 Linux功能区',
            'quick_check': '高级功能区',
            'miaomiao_tools': '妙妙工具区'
        }
        
        # 创建两列布局
        checkbox_layout = QHBoxLayout()
        left_column = QVBoxLayout()
        right_column = QVBoxLayout()
        
        for i, (area_key, area_name) in enumerate(area_info.items()):
            checkbox = QCheckBox(area_name)
            checkbox.setChecked(True)  # 默认全选
            self.area_checkboxes[area_key] = checkbox
            
            # 分配到左右两列
            if i % 2 == 0:
                left_column.addWidget(checkbox)
            else:
                right_column.addWidget(checkbox)
        
        checkbox_layout.addLayout(left_column)
        checkbox_layout.addLayout(right_column)
        
        # 添加全选/取消全选按钮
        select_buttons_layout = QHBoxLayout()
        select_all_button = QPushButton("全选")
        select_none_button = QPushButton("取消全选")
        
        select_all_button.clicked.connect(self._select_all_areas)
        select_none_button.clicked.connect(self._select_none_areas)
        
        select_buttons_layout.addWidget(select_all_button)
        select_buttons_layout.addWidget(select_none_button)
        select_buttons_layout.addStretch()
        
        area_layout.addLayout(checkbox_layout)
        area_layout.addLayout(select_buttons_layout)
        layout.addWidget(area_group)
        
        # 输入区域
        input_group = QGroupBox("题目描述")
        input_layout = QVBoxLayout(input_group)
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("请输入题目描述或相关信息...")
        self.input_text.setMaximumHeight(150)
        
        input_layout.addWidget(self.input_text)
        layout.addWidget(input_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        return widget
    
    def _create_result_area(self):
        """创建结果显示区域"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # 左侧：分析结果
        left_group = QGroupBox("分析结果")
        left_layout = QVBoxLayout(left_group)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        left_layout.addWidget(self.result_text)
        
        layout.addWidget(left_group)
        
        # 右侧：建议工具
        right_group = QGroupBox("建议工具")
        right_layout = QVBoxLayout(right_group)
        
        self.tools_list = QListWidget()
        right_layout.addWidget(self.tools_list)
        
        layout.addWidget(right_group)
        
        return widget
    
    def _start_analysis(self):
        """开始分析"""
        text = self.input_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "警告", "请输入题目描述")
            return
        
        # 确定分析模式
        mode = 'online' if self.online_radio.isChecked() else 'offline'
        
        # 禁用按钮
        self.analyze_button.setEnabled(False)
        self.analyze_button.setText("分析中...")
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 清空结果
        self.result_text.clear()
        self.tools_list.clear()
        self.highlight_button.setEnabled(False)
        
        # 获取可用按钮列表
        available_buttons = self._get_available_buttons()
        
        # 创建工作线程
        self.worker = TopicAnalysisWorker(
            text, 
            mode, 
            self.api_config if mode == 'online' else None,
            available_buttons
        )
        self.worker.analysis_finished.connect(self._on_analysis_finished)
        self.worker.error_occurred.connect(self._on_analysis_error)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.start()
    
    def _on_analysis_finished(self, result):
        """分析完成处理"""
        self.analysis_result = result
        
        logger.debug(f"分析完成 - 考点: {result.get('main_topics', [])}, 关键词: {result.get('keywords', [])}, 推荐按钮: {result.get('recommended_buttons', [])}")
        
        # 显示结果
        result_text = f"""分析完成！

主要考点：
{', '.join(result.get('main_topics', []))}

关键词：
{', '.join(result.get('keywords', []))}

分析总结：
{result.get('analysis_summary', '无')}
"""
        
        self.result_text.setPlainText(result_text)
        
        # DEBUG: 清空并重新添加建议工具
        self.tools_list.clear()
        recommended_buttons = result.get('recommended_buttons', [])
        #print(f"DEBUG: 准备添加 {len(recommended_buttons)} 个建议工具")
        
        # 显示建议工具
        for i, tool in enumerate(recommended_buttons):
            #print(f"DEBUG: 添加工具 {i+1}: {tool}")
            item = QListWidgetItem(tool)
            self.tools_list.addItem(item)
        
        #print(f"DEBUG: 工具列表当前项目数: {self.tools_list.count()}")
        
        # 恢复按钮状态
        self.analyze_button.setEnabled(True)
        self.analyze_button.setText("开始分析")
        self.progress_bar.setVisible(False)
        self.highlight_button.setEnabled(True)
        
        # 自动应用高亮
        self._apply_highlights()
        
        # 清理工作线程
        self.worker = None
    
    def _on_analysis_error(self, error_msg):
        """分析错误处理"""
        QMessageBox.critical(self, "分析失败", f"分析过程中发生错误：\n{error_msg}")
        
        # 恢复按钮状态
        self.analyze_button.setEnabled(True)
        self.analyze_button.setText("开始分析")
        self.progress_bar.setVisible(False)
        
        # 清理工作线程
        self.worker = None
    
    def _apply_highlights(self):
        """应用按钮高亮"""
        print("=== DEBUG: 开始应用高亮 ===")
        #print(f"DEBUG: 是否有分析结果: {hasattr(self, 'analysis_result')}")
        #print(f"DEBUG: 高亮管理器状态: {self.highlight_manager}")
        
        if not hasattr(self, 'analysis_result'):
            print("DEBUG: 没有分析结果，无法应用高亮")
            return
            
        if not self.highlight_manager:
            print("DEBUG: 没有高亮管理器，无法应用高亮")
            return
        
        # 停止所有现有高亮
        print("DEBUG: 停止所有现有高亮")
        self.highlight_manager.stop_all_highlights()
        
        # 根据分析结果高亮相关按钮
        recommended_buttons = self.analysis_result.get('recommended_buttons', [])
        #print(f"DEBUG: 推荐按钮列表: {recommended_buttons}")
        #print(f"DEBUG: 推荐按钮数量: {len(recommended_buttons)}")
        
        # 根据推荐的按钮进行高亮
        main_window = self.parent()
        #print(f"DEBUG: 主窗口对象: {main_window}")
        
        if main_window:
            highlighted_count = self._highlight_buttons_by_keywords(main_window, recommended_buttons)
            #print(f"DEBUG: 实际高亮的按钮数量: {highlighted_count}")
            #print(f"DEBUG: 已根据分析结果自动高亮了{highlighted_count}个相关按钮")
        else:
            print("DEBUG: 无法获取主窗口，高亮失败")
        
        print("=== DEBUG: 高亮应用完成 ===")
    
    def _highlight_buttons_by_keywords(self, main_window, keywords):
        """根据关键词高亮按钮"""
        print("=== DEBUG: 开始按钮匹配和高亮 ===")
        
        # 根据选择的区域获取按钮
        buttons_to_search = []
        if hasattr(self, 'area_checkboxes'):
            selected_areas = self._get_selected_areas()
            #print(f"DEBUG: 选中的区域: {selected_areas}")
            
            area_widgets = {
                'memprocfs': getattr(main_window, 'memprocfs_area', None),
                'vol2': getattr(main_window, 'vol2_area', None),
                'vol3': getattr(main_window, 'vol3_area', None),
                'vol2linux': getattr(main_window, 'vol2linux_area', None),
                'vol3linux': getattr(main_window, 'vol3linux_area', None),
                'quick_check': getattr(main_window, 'quick_check_area', None),
                'miaomiao_tools': getattr(main_window, 'miaomiao_tools_area', None)
            }
            
            for area_key in selected_areas:
                area_widget = area_widgets.get(area_key)
                if area_widget:
                    area_buttons = area_widget.findChildren(QPushButton)
                    buttons_to_search.extend(area_buttons)
                    #print(f"DEBUG: 从{area_key}区域获取了{len(area_buttons)}个按钮")
        else:
            # 如果没有区域选择，搜索所有按钮
            buttons_to_search = main_window.findChildren(QPushButton)
        
        #print(f"DEBUG: 总共需要搜索 {len(buttons_to_search)} 个按钮")
        
        # 打印按钮文本（仅用于调试）
        button_texts = [btn.text().strip() for btn in buttons_to_search if btn.text().strip()]
        #print(f"DEBUG: 搜索范围内的按钮文本: {button_texts[:20]}...")  # 只显示前20个
        
        highlighted_count = 0
        #print(f"DEBUG: 开始匹配关键词: {keywords}")
        
        for button in buttons_to_search:
            button_text = button.text().strip()
            if not button_text:  # 跳过空文本按钮
                continue
                
            # 过滤掉一些不相关的按钮
            if button_text in ['执行', '确定', '取消', '关闭', '浏览...', '保存', '删除']:
                continue
                
            for keyword in keywords:
                keyword = keyword.strip()
                if not keyword:
                    continue
                    
                # 检查匹配条件
                direct_match = keyword in button_text
                split_match = any(k.strip() in button_text for k in keyword.split() if k.strip())
                
                if direct_match or split_match:
                    #print(f"DEBUG: 匹配成功! 按钮文本: '{button_text}', 关键词: '{keyword}'")
                    #print(f"DEBUG: 直接匹配: {direct_match}, 分词匹配: {split_match}")
                    
                    try:
                        # 高亮按钮（使用随机颜色，不自动消失）
                        button_highlighter.highlight_button(
                            button,
                            effect_type="glow",
                            color=None,  # 使用随机颜色
                            duration=2000,
                            loop_count=-1,  # 无限循环
                            auto_stop=False,  # 不自动消失
                            stop_after=30000
                        )
                        
                        # 自动展开按钮所在的组
                        self._expand_button_group(button)
                        
                        highlighted_count += 1
                        #print(f"DEBUG: 成功高亮按钮: '{button_text}'")
                    except Exception as e:
                        pass
                        #print(f"DEBUG: 高亮按钮失败: {e}")
                    break
        
        #print(f"DEBUG: 总共高亮了 {highlighted_count} 个按钮")
        print("=== DEBUG: 按钮匹配和高亮完成 ===")
        return highlighted_count
    
    def _expand_button_group(self, button):
        """自动展开按钮所在的组"""
        try:
            # 向上查找父组件，寻找具有toggle_expand方法的组
            parent = button.parent()
            while parent:
                # 检查父组件是否有toggle_expand方法和is_expanded属性
                if hasattr(parent, 'toggle_expand') and hasattr(parent, 'is_expanded'):
                    if not parent.is_expanded:
                        #print(f"DEBUG: 自动展开组: {parent.__class__.__name__}")
                        parent.toggle_expand()
                    break
                
                # 检查父组件是否有content_widget属性（某些组的结构）
                if hasattr(parent, 'content_widget'):
                    # 查找同级的具有toggle_expand方法的组件
                    grandparent = parent.parent()
                    if grandparent and hasattr(grandparent, 'toggle_expand') and hasattr(grandparent, 'is_expanded'):
                        if not grandparent.is_expanded:
                            #print(f"DEBUG: 自动展开组: {grandparent.__class__.__name__}")
                            grandparent.toggle_expand()
                        break
                
                parent = parent.parent()
                
        except Exception as e:
            #print(f"DEBUG: 展开组失败: {e}")
            pass
    
    def _select_all_areas(self):
        """全选所有区域"""
        for checkbox in self.area_checkboxes.values():
            checkbox.setChecked(True)
    
    def _select_none_areas(self):
        """取消选择所有区域"""
        for checkbox in self.area_checkboxes.values():
            checkbox.setChecked(False)
    
    def _get_selected_areas(self):
        """获取选中的区域列表"""
        selected_areas = []
        for area_key, checkbox in self.area_checkboxes.items():
            if checkbox.isChecked():
                selected_areas.append(area_key)
        return selected_areas
    
    def _get_available_buttons(self):
        """根据选择的区域获取可用的按钮列表"""
        available_buttons = []
        main_window = self.parent()
        
        if main_window and hasattr(self, 'area_checkboxes'):
            selected_areas = self._get_selected_areas()
            #print(f"DEBUG: 选中的区域: {selected_areas}")
            
            # 根据选择的区域获取对应的按钮
            area_widgets = {
                'memprocfs': getattr(main_window, 'memprocfs_area', None),
                'vol2': getattr(main_window, 'vol2_area', None),
                'vol3': getattr(main_window, 'vol3_area', None),
                'vol2linux': getattr(main_window, 'vol2linux_area', None),
                'vol3linux': getattr(main_window, 'vol3linux_area', None),
                'quick_check': getattr(main_window, 'quick_check_area', None),
                'miaomiao_tools': getattr(main_window, 'miaomiao_tools_area', None)
            }
            
            for area_key in selected_areas:
                area_widget = area_widgets.get(area_key)
                if area_widget:
                    # 获取该区域的所有按钮
                    buttons = area_widget.findChildren(QPushButton)
                    for button in buttons:
                        button_text = button.text().strip()
                        if button_text and button_text not in available_buttons:
                            # 过滤掉一些不相关的按钮
                            if button_text not in ['执行', '确定', '取消', '关闭', '浏览...', '保存', '删除']:
                                available_buttons.append(button_text)
                                #print(f"DEBUG: 从{area_key}区域添加按钮: {button_text}")
        
        # 如果没有选择任何区域或无法获取，返回默认按钮列表
        if not available_buttons:
            print("DEBUG: 使用默认按钮列表")
            available_buttons = [
                '进程列表', '进程树', '隐藏进程', '网络连接', '网络扫描',
                '注册表', '注册表分析', '文件列表', '文件扫描', '文件恢复',
                '恶意软件检测', '病毒扫描', '密码提取', '哈希值',
                '字符串搜索', '关键词搜索', '内存映射', '驱动程序',
                '时间线分析', '用户信息', 'DLL列表', '句柄信息',
                '系统服务', '缓存分析', '事件日志'
            ]
        
        #print(f"DEBUG: 最终可用按钮列表 ({len(available_buttons)}个): {available_buttons[:10]}...")
        return available_buttons