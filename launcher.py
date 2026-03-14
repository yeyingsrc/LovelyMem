import logging
import os
import sys
import json
import yaml
import subprocess
import math
import re
import shutil
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QTimer, Signal, QThread, QRect, QUrl,QPoint
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPalette, QFont, QFontMetrics, QDesktopServices,QPainterPath,QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QProgressBar, QSplashScreen, QFrame, QGraphicsDropShadowEffect,
    QMessageBox, QScrollArea
)

from core.config_manager import load_config, get_saved_theme
from ui.styles import is_dark_mode, get_color_scheme

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("launcher_debug.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GitUpdateWorker(QThread):
    """Git更新处理线程"""
    progress_updated = Signal(int, str)
    update_finished = Signal(str)
    update_error = Signal(str)
    
    def __init__(self, github_url):
        super().__init__()
        self.github_url = github_url
    
    def run(self):
        try:
            self.progress_updated.emit(10, "检查Git是否已安装...")
            
            # 检查Git是否已安装
            try:
                result = subprocess.run(["git", "--version"], capture_output=True, text=True, check=True)
                logger.info(f"Git版本: {result.stdout.strip()}")
            except (subprocess.SubprocessError, FileNotFoundError):
                raise Exception("未检测到Git。请安装Git后再尝试更新。")
            
            self.progress_updated.emit(20, "正在创建临时目录...")
            
            # 创建临时目录用于克隆仓库
            temp_dir = tempfile.mkdtemp(prefix="lovelymem_update_")
            current_dir = os.getcwd()
            
            try:
                self.progress_updated.emit(30, "正在从GitHub克隆最新代码...")
                
                # 克隆仓库到临时目录
                subprocess.run(
                    ["git", "clone", self.github_url, temp_dir], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                
                self.progress_updated.emit(50, "正在备份当前配置...")
                
                # 备份用户配置文件
                config_dir = os.path.join(current_dir, "config")
                if os.path.exists(os.path.join(config_dir, "user_settings.json")):
                    user_settings_backup = os.path.join(temp_dir, "config", "user_settings.json")
                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(user_settings_backup), exist_ok=True)
                    shutil.copy2(os.path.join(config_dir, "user_settings.json"), user_settings_backup)
                
                # 备份数据库和输出文件
                for folder in ["db", "output", "packed_files"]:
                    src_folder = os.path.join(current_dir, folder)
                    if os.path.exists(src_folder):
                        dest_folder = os.path.join(temp_dir, folder)
                        # 确保目标目录存在
                        os.makedirs(dest_folder, exist_ok=True)
                        # 复制文件夹内容
                        for item in os.listdir(src_folder):
                            s = os.path.join(src_folder, item)
                            d = os.path.join(dest_folder, item)
                            if os.path.isfile(s):
                                shutil.copy2(s, d)
                
                self.progress_updated.emit(70, "正在更新文件...")
                
                # 拷贝新代码到当前目录
                for item in os.listdir(temp_dir):
                    if item in [".git", ".github"]:
                        continue  # 跳过 git 相关目录
                    
                    s = os.path.join(temp_dir, item)
                    d = os.path.join(current_dir, item)
                    
                    if os.path.isdir(s):
                        # 如果是特殊目录，使用特殊处理
                        if item in ["db", "output", "packed_files", "config"]:
                            # 这些目录已经在前面备份和恢复了，这里跳过
                            continue
                        # 递归拷贝其他目录
                        if os.path.exists(d):
                            shutil.rmtree(d)
                        shutil.copytree(s, d)
                    else:
                        # 拷贝文件
                        shutil.copy2(s, d)
                
                self.progress_updated.emit(90, "正在清理临时文件...")
                
                # 清理临时目录
                shutil.rmtree(temp_dir, ignore_errors=True)
                
                self.progress_updated.emit(100, "更新完成!")
                self.update_finished.emit("程序已成功更新到最新版本！")
                
            except Exception as e:
                # 清理临时目录
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.error(f"更新过程中发生错误: {str(e)}")
                raise
                
        except Exception as e:
            logger.error(f"更新失败: {str(e)}")
            self.update_error.emit(str(e))

class LoadingThread(QThread):
    """后台加载线程，用于执行耗时操作"""
    progress_updated = Signal(int, str)
    loading_finished = Signal(list)  # 可以发送警告信息列表
    
    def run(self):
        warnings = []  # 收集警告信息

        # 检查Dokan是否安装
        self.progress_updated.emit(33, "检查Dokan安装...")
        if not self.check_dokan_installed():
            warning_msg = "未检测到Dokan安装。Dokan是一个必要的组件，用于挂载内存页面"
            warnings.append(warning_msg)
            warnings.append("- 请从 https://github.com/dokan-dev/dokany/releases 下载并安装最新版的Dokan")

        # 检查目录中是否有中文
        self.progress_updated.emit(66, "检查路径...")
        chinese_paths = self.check_chinese_in_path(os.getcwd())
        if chinese_paths:
            warning_msg = f"检测到{len(chinese_paths)}个包含中文的路径，可能会影响程序运行"
            warnings.append(warning_msg)
            for path in chinese_paths[:3]:  # 只显示前3个
                warnings.append(f"- {path}")
            if len(chinese_paths) > 3:
                warnings.append(f"... 及其他{len(chinese_paths)-3}个路径")

        # 检查工具路径
        self.progress_updated.emit(90, "检查工具...")
        try:
            missing_tools = self.check_tools_existence()

            if missing_tools:
                warning_msg = f"找不到{len(missing_tools)}个工具"
                warnings.append(warning_msg)
                for tool in missing_tools[:5]:  # 只显示前5个
                    warnings.append(f"- {tool}")
                if len(missing_tools) > 5:
                    warnings.append(f"... 还有其他{len(missing_tools)-5}个工具")
        except Exception as e:
            warnings.append(f"检查工具路径时发生错误: {str(e)}")
            logger.error(f"检查工具路径时发生错误: {str(e)}")

        # 完成
        self.progress_updated.emit(100, "准备就绪")

        # 发送加载完成信号，带上警告信息
        self.loading_finished.emit(warnings)
    
    def check_chinese_in_path(self, start_path):
        """只检查目录中是否存在包含中文的路径，不检查文件"""
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]')  # 中文字符范围
        chinese_paths = []
        
        for root, dirs, files in os.walk(start_path):
            # 只检查目录路径
            if chinese_pattern.search(root):
                chinese_paths.append(root)
                
            # 限制搜索范围，避免搜索过多
            if len(chinese_paths) >= 10:
                break
        
        return chinese_paths
    
    def check_dokan_installed(self):
        """检查Dokan是否已安装"""
        try:
            dokan_path = r"C:\Program Files\Dokan"
            return os.path.exists(dokan_path)
        except Exception as e:
            logger.error(f"检查Dokan安装时发生错误: {str(e)}")
            return False
    
    def check_tools_existence(self):
        """检查配置文件中的工具路径是否存在"""
        missing_tools = []
        config_file = os.path.join(os.getcwd(), "config", "base_config.yaml")
        
        if not os.path.exists(config_file):
            return ["config/base_config.yaml文件不存在"]
        
        try:
            # 使用限制读取时间的方式加载配置文件，避免死循环
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 检查base_tools
            if 'base_tools' in config:
                for tool_name, tool_info in config['base_tools'].items():
                    if 'path' in tool_info:
                        path = tool_info['path']
                        if not os.path.exists(path):
                            missing_tools.append(f"base_tools/{tool_name}: {path}")
            
            # 检查tools
            if 'tools' in config:
                for tool_name, tool_info in config['tools'].items():
                    if 'path' in tool_info:
                        path = tool_info['path']
                        # 处理相对路径
                        if path.startswith("../") or path.startswith("./"):
                            path = os.path.normpath(os.path.join(os.getcwd(), path))
                        if not os.path.exists(path):
                            missing_tools.append(f"tools/{tool_name}: {path}")
            
            # 检查other_tools
            if 'other_tools' in config:
                for tool_name, tool_info in config['other_tools'].items():
                    if 'path' in tool_info:
                        path = tool_info['path']
                        # 处理相对路径
                        if path.startswith("../") or path.startswith("./"):
                            path = os.path.normpath(os.path.join(os.getcwd(), path))
                        if not os.path.exists(path):
                            missing_tools.append(f"other_tools/{tool_name}: {path}")
                            
        except Exception as e:
            missing_tools.append(f"读取配置文件错误: {str(e)}")
        
        return missing_tools

class ModernProgressBar(QWidget):
    """现代风格圆环进度条"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(150, 150)  # 减小圆环大小
        self.progress = 0
        self.display_progress = 0  # 用于显示的进度值
        self.dots_position = 0
        self.animation_angle = 0
        self.loading_offset = 0  # 加载动画偏移量
        
        # 创建动画定时器
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(40)  # 加快动画速度
        
        # 创建图标
        self.logo_pixmap = QPixmap(r"res\logo_64.png")
        if self.logo_pixmap.isNull():
            self.logo_pixmap = None
        
    def setProgress(self, value):
        # 更新实际进度
        self.progress = value
        
        # 计算显示进度，让显示值逼近实际值
        if self.display_progress < self.progress:
            # 当进度增加时，以更平滑的速度逐渐增加显示值
            # 增加进度增长的平滑度，特别是80%到100%之间的进度
            if self.progress > 80 and self.progress <= 100:
                # 在高进度区间使用更小的步长，确保进度显示更加平滑
                step = max(1, (self.progress - self.display_progress) // 8)
            else:
                step = max(1, (self.progress - self.display_progress) // 5)
            self.display_progress = min(self.progress, self.display_progress + step)
        elif self.display_progress > self.progress:
            # 如果显示进度比实际进度大（通常不应该发生），直接调整
            self.display_progress = self.progress
            
        self.update()
    
    def update_animation(self):
        self.dots_position = (self.dots_position + 1) % 4
        # 旋转动画角度
        if self.display_progress < 100:
            self.animation_angle = (self.animation_angle + 5) % 360
            # 更新加载动画的偏移量
            self.loading_offset = (self.loading_offset + 2) % 100
            
            # 平滑更新显示进度
            if self.display_progress < self.progress:
                # 在后期的进度中加快进度的更新速度
                if self.progress > 90:
                    # 高进度区域加快更新速度
                    step = min(2, self.progress - self.display_progress)
                    self.display_progress = min(self.progress, self.display_progress + step)
                else:
                    self.display_progress = min(self.progress, self.display_progress + 1)
                
        self.update()
        
    def paintEvent(self, event):
        width = self.width()
        height = self.height()
        
        # 创建画家
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)  # 启用抽薄，使圆环更滑
        
        try:
            # 获取主题颜色
            is_dark = is_dark_mode()
            theme_name = get_saved_theme()
            color_scheme = get_color_scheme(theme_name, is_dark)
            
            # 设置背景透明
            painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
            
            # 定义圆环尺寸和位置
            center_x = width // 2
            # 整体向上移动圆环位置
            center_y = height // 2 - 15
            if self.logo_pixmap and not self.logo_pixmap.isNull():
                center_y = center_y - 5  # 进一步将logo往上移
            
            outer_radius = min(width, height) // 2 - 30  # 减小外圆半径
            ring_width = 6  # 减小圆环宽度
            inner_radius = outer_radius - ring_width  # 内圆半径
            
            # 绘制Logo
            if self.logo_pixmap and not self.logo_pixmap.isNull():
                logo_size = min(48, inner_radius * 1.2)  # 减小Logo大小
                logo_x = center_x - logo_size // 2
                logo_y = center_y - inner_radius - logo_size  # 在圆环上方显示Logo，移除额外间距
                painter.drawPixmap(logo_x, logo_y, logo_size, logo_size, self.logo_pixmap)
            
            # 从主题色获取圆环颜色
            if "button_hover_color" in color_scheme:
                progress_color = QColor(color_scheme["button_hover_color"])
            elif "button_text_color" in color_scheme:
                progress_color = QColor(color_scheme["button_text_color"])
            else:
                progress_color = QColor("#3498db")  # 一个显眼的蓝色
            
            # 绘制背景圆环(灰色)
            painter.setPen(Qt.NoPen)
            bg_color = QColor(color_scheme.get("border_color", "#cccccc"))
            bg_color.setAlpha(40)  # 更透明的背景
            painter.setBrush(bg_color)
            
            # 绘制完整的背景圆环
            path = QPainterPath()
            path.addEllipse(center_x - outer_radius, center_y - outer_radius, 
                           outer_radius * 2, outer_radius * 2)
            path2 = QPainterPath()
            path2.addEllipse(center_x - inner_radius, center_y - inner_radius, 
                            inner_radius * 2, inner_radius * 2)
            path = path.subtracted(path2)  # 使用路径相减创建圆环
            painter.drawPath(path)
            
            # 绘制进度圆环
            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.NoBrush)  # 清除画刷以便使用画笔绘制
            
            # 设置进度圆环的画笔
            pen = painter.pen()
            pen.setWidth(ring_width)
            pen.setColor(progress_color)
            pen.setCapStyle(Qt.RoundCap)  # 圆形端点
            painter.setPen(pen)
            
            # 计算角度 - 使用显示进度而不是实际进度
            start_angle = 90 * 16  # 从顶部开始，需要*16因为角度单位是1/16度
            span_angle = -self.display_progress * 3.6 * 16  # 进度百分比转换为角度，负值为顺时针
            
            # 绘制圆环弧
            rect = QRect(center_x - outer_radius + ring_width//2, 
                         center_y - outer_radius + ring_width//2, 
                         (outer_radius - ring_width//2) * 2, 
                         (outer_radius - ring_width//2) * 2)
            painter.drawArc(rect, start_angle, span_angle)
            
            # 加强加载动画效果
            if self.display_progress < 100:
                # 绘制加载指示器效果
                loading_pen = painter.pen()
                loading_pen.setWidth(ring_width)
                loading_pen.setColor(progress_color)
                loading_pen.setCapStyle(Qt.RoundCap)
                painter.setPen(loading_pen)
                
                # 绘制动态的加载弧，长度固定但位置旋转
                loading_start_angle = (self.animation_angle - 30) * 16
                loading_span = 60 * 16  # 固定长度的弧
                
                # 使用相同的矩形绘制加载弧
                painter.drawArc(rect, loading_start_angle, loading_span)
                
                # 绘制旋转的小圆点
                dot_radius = ring_width // 2
                # 计算动画点的位置
                dot_angle = math.radians(self.animation_angle)
                dot_x = center_x + math.cos(dot_angle) * (outer_radius - ring_width//2)
                dot_y = center_y + math.sin(dot_angle) * (outer_radius - ring_width//2)
                
                # 在动画位置绘制一个小圆点
                highlight_color = QColor(progress_color)
                highlight_color.setAlpha(200)
                painter.setBrush(highlight_color)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPoint(int(dot_x), int(dot_y)), dot_radius, dot_radius)
            
            # 绘制进度百分比文本 - 显示动态更新的进度值
            font = painter.font()
            font.setBold(True)
            font.setPointSize(16)  # 增大字号使进度值更明显
            painter.setFont(font)
            painter.setPen(QColor(color_scheme.get("text_color", "#333333")))
            percent_text = f"{self.display_progress}%"
            percent_rect = QRect(center_x - 40, center_y - 12, 80, 24)
            painter.drawText(percent_rect, Qt.AlignCenter, percent_text)
            
            # 绘制状态文本
            status_text = "准备就绪，点击按钮启动" if self.display_progress >= 100 else "正在初始化"
            
            # 根据动画添加点点
            if self.display_progress < 100:
                dots = "." * self.dots_position
                status_text += dots
            
            # 绘制状态文本
            font.setBold(False)
            font.setPointSize(9)  # 缩小字号
            painter.setFont(font)
            text_rect = QRect(0, center_y + outer_radius + 10, width, 20)
            painter.drawText(text_rect, Qt.AlignCenter, status_text)
            
        finally:
            painter.end()

class LauncherWindow(QMainWindow):
    """启动器主窗口"""
    def __init__(self):
        super().__init__()
        
        # 加载配置
        self.config = load_config()
        self.theme_name = get_saved_theme()
        self.is_dark = is_dark_mode()
        self.warnings = []  # 存储检测到的警告
        
        # 设置窗口属性
        self.setWindowTitle("LovelyMem 启动器")
        self.setWindowIcon(QIcon(r"res\logo.ico"))
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setMinimumSize(400, 400)  # 设置最小窗口大小，而不是固定大小
        
        # 初始化UI
        self.init_ui()
        
        # 应用主题
        self.apply_theme()
        
        # 监听系统主题变化
        app = QApplication.instance()
        app.paletteChanged.connect(self.on_theme_changed)
        
        # 创建加载线程
        self.loading_thread = LoadingThread()
        self.loading_thread.progress_updated.connect(self.update_progress)
        self.loading_thread.loading_finished.connect(self.on_loading_finished)
        
        # 启动加载过程
        QTimer.singleShot(500, self.loading_thread.start)
        
    def init_ui(self):
        # 创建主窗口部件
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 移除边缘
        
        # 创建自定义标题栏
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(30)
        self.title_bar.setObjectName("titleBar")
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        
        # 添加图标
        icon_label = QLabel()
        icon_label.setPixmap(QIcon('res/logo.ico').pixmap(20, 20))
        title_layout.addWidget(icon_label)
        
        # 添加标题
        title_label = QLabel("LovelyMem 启动器")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 添加最小化按钮
        self.min_button = self.create_circle_button("rgba(198, 255, 198, 0.9)")
        self.min_button.clicked.connect(self.showMinimized)
        self.min_button.setToolTip("最小化")
        
        # 添加关闭按钮
        self.close_button = self.create_circle_button("rgba(255, 204, 204, 0.9)")
        self.close_button.clicked.connect(self.close)
        self.close_button.setToolTip("关闭")
        
        # 添加标题栏按钮
        title_layout.addWidget(self.min_button)
        title_layout.addWidget(self.close_button)
        
        # 创建内容区域
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setObjectName("content_layout")  # 添加对象名便于后续查找
        content_layout.setAlignment(Qt.AlignCenter)
        content_layout.setSpacing(10)  # 减少内部间距
        content_layout.setContentsMargins(10, 5, 10, 5)  # 减少内容区域的边距，使整体往上移
        
        # 移除阴影效果，保持简洁
        
        # 添加现代风格进度条
        self.progress_bar = ModernProgressBar()
        
        # 添加状态文本
        self.status_label = QLabel("正在初始化...")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        content_layout.addWidget(self.progress_bar, 0, Qt.AlignCenter)
        content_layout.addWidget(self.status_label, 0, Qt.AlignCenter)
        
        # 添加启动按钮
        self.start_button = QPushButton("启动 LovelyMem")
        self.start_button.setFixedSize(160, 32)  # 缩小按钮尺寸
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.launch_main_app)
        
        # 创建更新按钮
        update_layout = QHBoxLayout()
        
        self.update_button = QPushButton("检查更新")
        self.update_button.setFixedSize(100, 30)
        self.update_button.setCursor(Qt.PointingHandCursor)
        self.update_button.clicked.connect(lambda: self.show_update_options())
        
        update_layout.addWidget(self.update_button)
        self.update_button.setToolTip("从GitHub更新程序")
        
        # 创建垂直布局来放置按钮
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)  # 减少按钮之间的间距
        buttons_layout.addLayout(update_layout)  # 添加更新按钮
        buttons_layout.addWidget(self.start_button)
        
        # 添加底部按钮
        bottom_layout = QHBoxLayout()
        bottom_layout.setObjectName("bottom_layout")  # 添加对象名称便于后续查找
        bottom_layout.setContentsMargins(0, 0, 0, 20)  # 减少按钮底部的边距，将按钮往上移
        bottom_layout.addStretch()
        bottom_layout.addLayout(buttons_layout)  # 添加垂直布局
        bottom_layout.addStretch()
        
        # 组装主布局
        main_layout.addWidget(self.title_bar)
        main_layout.addWidget(content_widget)
        main_layout.addSpacing(10)  # 在内容区域和按钮之间添加一小部分空间
        main_layout.addLayout(bottom_layout)
        main_layout.addStretch(1)  # 在底部增加更多的空白地方
        
        # 设置中央部件
        self.setCentralWidget(main_widget)
        
    def create_circle_button(self, base_color):
        """创建圆形按钮"""
        button = QPushButton()
        button.setFixedSize(16, 16)
        button.setStyleSheet(f"background-color: {base_color}; border-radius: 8px;")
        return button
        
    def toggle_theme(self):
        """切换主题"""
        # 获取当前主题名称
        current_theme = get_saved_theme()
        
        # 获取所有主题
        theme_names = list(get_color_scheme(current_theme, is_dark_mode()).keys())
        
        # 找到当前主题的索引
        try:
            current_index = theme_names.index(current_theme)
        except ValueError:
            current_index = 0
        
        # 切换到下一个主题
        next_index = (current_index + 1) % len(theme_names)
        next_theme = theme_names[next_index]
        
        # 保存新主题
        from core.config_manager import save_theme
        save_theme(next_theme)
        
        # 应用新主题
        self.apply_theme()
    
    def apply_theme(self):
        """应用主题样式"""
        is_dark = is_dark_mode()
        theme_name = get_saved_theme()
        color_scheme = get_color_scheme(theme_name, is_dark)
        
        # 设置窗口样式
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {color_scheme["background_color"]};
                color: {color_scheme["text_color"]};
                font-family: "Microsoft YaHei", sans-serif;
            }}
            QPushButton {{
                background-color: {color_scheme["button_bg_color"]};
                color: {color_scheme["button_text_color"]};
                border: none;
                border-radius: 5px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {color_scheme["button_hover_color"]};
            }}
            QPushButton:disabled {{
                background-color: rgba(200, 200, 200, 0.5);
                color: rgba(150, 150, 150, 0.8);
            }}
            QLabel {{
                color: {color_scheme["text_color"]};
            }}
            QFrame {{
                background-color: {color_scheme["background_color"]};
                border-radius: 3px;
            }}
            #titleBar {{
                border: none;
            }}
            #contentWidget {{
                background-color: transparent;
            }}
        """)
        
        # 更新进度条颜色
        self.progress_bar.update()
        
    def on_theme_changed(self):
        """系统主题变化时调用"""
        self.is_dark = is_dark_mode()
        self.apply_theme()
        
    def update_progress(self, value, status):
        """更新进度条和状态文本"""
        self.progress_bar.setProgress(value)
        self.status_label.setText(status)
        
    def on_loading_finished(self, warnings):
        """加载完成后调用"""
        # 确保进度条已完成到100%
        QTimer.singleShot(100, lambda: self.progress_bar.setProgress(100))
        self.warnings = warnings
        
        # 如果有警告，直接在界面上展示
        if warnings:
            # 首先清除原有警告显示
            self.clear_warning_display()
            
            # 取消状态标签，改为准备就绪
            self.status_label.setText("准备就绪，点击按钮启动")
            self.status_label.setStyleSheet("")  # 恢复默认样式
            
            # 在界面上直接创建警告标签
            scrollArea = QScrollArea()
            scrollArea.setWidgetResizable(True)
            scrollArea.setMinimumHeight(100)  # 设置最小高度而不是固定高度
            scrollArea.setMaximumHeight(200)  # 设置最大高度限制
            warnings_container = QWidget()
            warnings_layout = QVBoxLayout(warnings_container)
            
            # 添加警告标题
            warning_title = QLabel("检测到以下问题：")
            warning_title.setStyleSheet("color: #e74c3c; font-weight: bold;")
            warnings_layout.addWidget(warning_title)
            
            # 添加具体警告内容
            for warning in warnings:
                warning_label = QLabel(warning)
                warning_label.setWordWrap(True)  # 自动换行
                warning_label.setStyleSheet("color: #e74c3c;")
                warnings_layout.addWidget(warning_label)
            
            # 设置布局
            warnings_layout.addStretch()
            scrollArea.setWidget(warnings_container)
            
            # 将警告区域添加到主布局
            content_layout = self.findChild(QVBoxLayout, "content_layout")
            if content_layout:
                # 存储引用便于后续清除
                self.warning_display = scrollArea
                content_layout.insertWidget(1, scrollArea)  # 在进度条下方添加警告显示
                
                # 调整窗口大小以适应内容
                self.adjustSize()
        else:
            # 清除任何警告显示
            self.clear_warning_display()
            self.status_label.setText("准备就绪，点击按钮启动")
            self.status_label.setStyleSheet("")  # 恢复默认样式
                
        self.start_button.setEnabled(True)
    
    def clear_warning_display(self):
        """清除界面上的警告显示"""
        if hasattr(self, 'warning_display') and self.warning_display:
            self.warning_display.setParent(None)
            self.warning_display.deleteLater()
            self.warning_display = None
            
            # 调整窗口大小以适应内容变化
            QTimer.singleShot(100, self.adjustSize)
        
    def launch_main_app(self):
        """启动主应用程序"""
        try:
            # 隐藏启动器窗口
            self.hide()
            
            # 启动主程序
            python_executable = sys.executable
            main_script = os.path.join(os.getcwd(), "main.py")
            
            # 使用subprocess启动主程序
            subprocess.Popen([python_executable, main_script])
            
            # 关闭启动器并完全退出
            self.close()
            QTimer.singleShot(500, lambda: sys.exit(0))
        except Exception as e:
            logger.error(f"启动主程序失败: {e}")
            self.status_label.setText(f"启动失败: {str(e)}")
            self.show()  # 如果启动失败，重新显示启动器
    
    def update_app(self, source="github"):
        """从指定源更新程序"""
        try:
            # 禁用更新按钮，防止重复点击
            self.update_button.setEnabled(False)
            self.status_label.setText("正在检查更新...")
            
            # 更新源URL
            update_sources = {
                "github": "https://github.com/Tokeii0/LovelyMem",
                "gitee": "https://gitee.com/tokeii0/LovelyMem.git"
            }
            
            # 获取选定的更新源
            repo_url = update_sources.get(source, update_sources["github"])
            source_name = "GitHub" if source == "github" else "Gitee"
            
            # 确认是否更新
            reply = QMessageBox.question(
                self, 
                "更新确认", 
                f"确定要从{source_name}更新程序吗？\n\n更新源: {repo_url}\n\n注意: 更新前请确保已保存您的工作。", 
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 创建更新线程
                self.update_thread = QThread()
                self.update_worker = GitUpdateWorker(repo_url)
                self.update_worker.moveToThread(self.update_thread)
                
                # 连接信号
                self.update_thread.started.connect(self.update_worker.run)
                self.update_worker.progress_updated.connect(self.update_progress)
                self.update_worker.update_finished.connect(self.on_update_finished)
                self.update_worker.update_error.connect(self.on_update_error)
                
                # 启动线程
                self.update_thread.start()
            else:
                # 用户取消更新
                self.update_button.setEnabled(True)
                self.status_label.setText("更新已取消")
                # 重置状态
                QTimer.singleShot(2000, lambda: self.status_label.setText("准备就绪，点击按钮启动"))
        except Exception as e:
            logger.error(f"准备更新时发生错误: {e}")
            self.on_update_error(f"准备更新时发生错误: {str(e)}")
    
    def update_from_github(self):
        """从GitHub更新程序（兼容旧方法）"""
        self.update_app(source="github")
        
    def show_update_options(self):
        """显示更新源选择对话框"""
        # 创建一个简单的对话框
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("选择更新源")
        msg_box.setText("请选择更新源:")
        
        # 添加按钮
        github_button = msg_box.addButton("GitHub", QMessageBox.ActionRole)
        gitee_button = msg_box.addButton("Gitee", QMessageBox.ActionRole)
        cancel_button = msg_box.addButton("取消", QMessageBox.RejectRole)
        
        # 显示对话框
        msg_box.exec()
        
        # 处理选择
        clicked_button = msg_box.clickedButton()
        if clicked_button == github_button:
            self.update_app(source="github")
        elif clicked_button == gitee_button:
            self.update_app(source="gitee")
    
    def on_update_finished(self, success_message):
        """更新完成后的处理"""
        # 显示成功消息
        QMessageBox.information(self, "更新成功", success_message)
        
        # 重置UI状态
        self.update_button.setEnabled(True)
        self.status_label.setText("更新完成，请重启应用")
        
        # 询问是否立即重启
        reply = QMessageBox.question(
            self,
            "重启应用",
            "更新已完成，是否立即重启应用？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            # 重启应用
            python = sys.executable
            os.execl(python, python, *sys.argv)
    
    def on_update_error(self, error_message):
        """更新出错的处理"""
        # 重新启用按钮
        self.update_button.setEnabled(True)
        
        # 显示错误消息
        self.status_label.setText(f"更新失败: {error_message}")
        QMessageBox.critical(self, "更新失败", f"更新失败: {error_message}\n\n您可以尝试手动更新或联系开发者。")
        
        # 提供仓库链接
        reply = QMessageBox.question(
            self,
            "打开GitHub仓库",
            "是否打开GitHub仓库页面进行手动更新？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl("https://github.com/Tokeii0/LovelyMem"))
        
        # 重置状态
        QTimer.singleShot(3000, lambda: self.status_label.setText("准备就绪，点击按钮启动"))
        
        # 清理线程
        if hasattr(self, 'update_thread') and self.update_thread.isRunning():
            self.update_thread.quit()
            self.update_thread.wait()
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件，用于实现窗口拖动"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件，用于实现窗口拖动"""
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    


def main():
    # 检查是否已经有启动器实例运行
    # 如果有其他实例正在运行，则退出
    app_name = "LovelyMem Launcher"
    if is_app_running(app_name):
        logger.info(f"{app_name}已经在运行中")
        return
    
    # 确保必要的目录存在
    for directory in ['db', 'output', 'packed_files', 'config']:
        os.makedirs(directory, exist_ok=True)
    
    # 检查用户设置文件是否存在，如果不存在则创建默认设置
    user_settings_file = os.path.join(os.getcwd(), "config", "user_settings.json")
    if not os.path.exists(user_settings_file):
        default_settings = {
            "theme": "默认",
            "first_run_reminder": True,
            "LLM_CONFIG": {},
            "base_config": {"proxy": {"url": ""}},
            "font_settings": {"font_family": ""}
        }
        with open(user_settings_file, 'w', encoding='utf-8') as f:
            json.dump(default_settings, f, ensure_ascii=False, indent=4)
    
    try:
        # 检查是否已存在 QApplication 实例
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 设置应用程序图标
        app.setWindowIcon(QIcon(r"res\logo.ico"))
        
        # 创建并显示启动器窗口
        launcher = LauncherWindow()
        launcher.show()
        
        sys.exit(app.exec())
    except Exception as e:
        error_msg = f"启动器发生未处理异常: {str(e)}"
        logger.error(error_msg)
        print(error_msg, file=sys.__stderr__)

def is_app_running(app_name):
    """检查是否有相同名称的应用正在运行"""
    try:
        # 我们使用一个更简单的方法来避免编码问题
        # 直接返回false，允许启动器启动
        # 因为启动器在启动main.py后会自行退出，所以这里不需要严格检查
        return False
        
        # 以下是原来的代码，由于中文Windows系统编码差异而注释掉
        # 在Windows上使用tasklist检查Python进程
        # output = subprocess.check_output(['tasklist', '/fi', f'imagename eq python.exe', '/fo', 'csv']).decode('cp936')
        # 如果找到多个Python进程则返回true
        # python_count = output.count('python.exe')
        # 
        # 如果只有当前进程就返回false
        # if python_count <= 2:  # tasklist返回的CSV包含标题行
        #     return False
    except Exception as e:
        logger.error(f"检查应用运行状态时出错: {e}")
    
    return False

if __name__ == "__main__":
    main()
