from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                              QGroupBox, QLineEdit, QTextEdit, QLabel, QListWidget, QPushButton,
                              QSplitter, QPlainTextEdit, QFileDialog, QMenu, QMessageBox, QFrame, QToolButton, QListView, QTabBar)
from PySide6.QtGui import (QIcon, QTextCursor, QColor, QMouseEvent, QPainter, QCloseEvent,
                          QPalette, QGuiApplication, QFont, QTransform)
from PySide6.QtCore import Qt, Slot, QTimer, QPoint, Signal, QThread, QSettings, QSize
import logging
import os
from core.file_manager import FileManager  
import zipfile
from datetime import datetime
import sqlite3
import requests
from requests.exceptions import RequestException
from ui.memprocfs_area import MemProcFSArea
from ui.vol2_area import Vol2Area, CollapsibleButtonGroup
from ui.vol3_area import Vol3Area, CollapsibleButtonGroup as Vol3CollapsibleButtonGroup
from ui.vol2linux_area import Vol2LinuxArea  
from ui.quick_check_area import QuickCheckArea
from ui.preset_manager import PresetManager
from ui.file_menu_area import FileMenuArea  
from ui.main_window_rightpanel import RightPanel
from core.loadmem import MemImageLoader
from plugin.vol2 import Vol2Plugin  
from plugin.vol3 import Vol3Plugin  
from plugin.vol2linux import Vol2LinuxPlugin  
from plugin.NewtableWidget import NewtableWidget
from core.config_manager import save_theme, get_saved_theme
from ui.theme_selector import ThemeSelectorDialog
from ui.cmd_output_window import CmdOutputWindow
from ui.styles import (main_window_style, candy_background, common_font_style, 
                       splitter_style, tab_style, left_group_style,  
                       right_panel_style, memprocfs_style, vol2_style, vol3_style, 
                       quick_check_style, cmd_output_style, current_font_family,
                       background_color, text_color, button_bg_color, button_text_color,
                       button_hover_color, border_color, group_title_bg_color,
                       color_schemes, apply_color_scheme, is_dark_mode, 
                       cmd_output_text_color,
                       theme_button_color, minimize_button_color, maximize_button_color, close_button_color)

import sys,time
logger = logging.getLogger(__name__)

# 添加毛玻璃效果覆盖层类
class GlassOverlay(QWidget):
    """实现毛玻璃效果的覆盖层，在拖放文件时显示"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置无边框透明背景
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # 隐藏覆盖层（初始状态）
        self.hide()
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建内容容器
        self.content_container = QWidget(self)
        self.content_container.setObjectName("dropContainer")
        self.content_container.setStyleSheet("""
            #dropContainer {
                background-color: rgba(255, 255, 255, 0.85);
                border: 5px dashed #808080;
                border-radius: 10px;
            }
        """)
        
        # 创建内容布局
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(40, 30, 40, 30)
        
        # 创建提示标签
        self.hint_label = QLabel("释放鼠标加载内存镜像", self.content_container)
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setFont(QFont(common_font_style, 18, QFont.Bold))
        self.hint_label.setStyleSheet(f"""
            color: #3498db;
            font-size: 18px;
            font-weight: bold;
        """)
        
        # 添加内存图标
        self.mem_icon = QLabel(self.content_container)
        self.mem_icon.setPixmap(QIcon('res/mem.svg').pixmap(64, 64))
        self.mem_icon.setAlignment(Qt.AlignCenter)
        
        # 将控件添加到内容布局
        content_layout.addWidget(self.hint_label)
        content_layout.addSpacing(15)
        content_layout.addWidget(self.mem_icon)
        
        # 将内容容器添加到主布局
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.content_container, 0, Qt.AlignCenter)
        self.main_layout.addStretch(1)
    
    def showEvent(self, event):
        """显示时调整大小并居中显示提示标签"""
        super().showEvent(event)
        # 调整覆盖层大小为父窗口大小
        if self.parent():
            self.setGeometry(0, 0, self.parent().width(), self.parent().height())
    
    def paintEvent(self, event):
        """绘制毛玻璃效果背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 创建半透明背景
        painter.fillRect(self.rect(), QColor(255, 255, 255, 150))
        
        # 添加模糊效果（这里使用半透明渐变来模拟）
        gradient = QColor(41, 128, 185, 40)
        painter.fillRect(self.rect(), gradient)
        
        # 添加微妙的网格图案，增强毛玻璃效果
        pen = painter.pen()
        pen.setWidth(1)
        pen.setColor(QColor(255, 255, 255, 20))
        painter.setPen(pen)
        
        # 绘制水平和垂直线条，形成网格
        step = 20
        for i in range(0, self.width(), step):
            painter.drawLine(i, 0, i, self.height())
        for i in range(0, self.height(), step):
            painter.drawLine(0, i, self.width(), i)

class MainWindow(QMainWindow):
    style_updated_signal = Signal()

    def __init__(self):
        super().__init__()
        # 启用拖放功能（支持所有文件类型）
        self.setAcceptDrops(True)
        self.setAttribute(Qt.WA_NativeWindow, True)
        self.setAttribute(Qt.WA_DontCreateNativeAncestors, True)
        self.setWindowFlags(Qt.FramelessWindowHint)  # 移除原生标题栏
        self.setAttribute(Qt.WA_TranslucentBackground, False)  # 启用窗口背景透明
        self.setMinimumSize(900, 600)  # 设置最小窗口大小
        self.setMaximumSize(1600, 1200)  # 设置最大窗口大小
        self.resize(1000, 700)  # 设置初始窗口大小
        # 连接样式更新信号
        self.style_updated_signal.connect(self.update_all_styles)

        # 初始化主题相关变量
        self.theme_names = list(color_schemes.keys())
        self.current_theme_index = 0
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建自定义标题栏
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(30)
        # 移除这里的 setStyleSheet，我们将在 update_all_styles 中设置
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        
        # 添加图标
        icon_label = QLabel()
        icon_label.setPixmap(QIcon('res/logo.ico').pixmap(20, 20))
        title_layout.addWidget(icon_label)
        
        # 添加标题
        title_label = QLabel("Lovelymem Ver 0.93.1")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 添加主题切换按钮
        self.theme_button = self.create_circle_button(theme_button_color)
        self.theme_button.clicked.connect(self.toggle_theme)
        self.theme_button.setToolTip("切换主题")
        # 添加最小化按钮
        self.min_button = self.create_circle_button(minimize_button_color)
        self.min_button.clicked.connect(self.showMinimized)
        self.min_button.setToolTip("最小化")

        # 添加最大化/还原按钮
        self.max_button = self.create_circle_button(maximize_button_color)
        self.max_button.clicked.connect(self.toggle_maximize)
        self.max_button.setToolTip("最大化")
        
        # 添加关闭按钮
        self.close_button = self.create_circle_button(close_button_color)
        self.close_button.clicked.connect(self.close)
        self.close_button.setToolTip("关闭")
        

        
        title_layout.addWidget(self.theme_button)
        title_layout.addWidget(self.min_button)
        title_layout.addWidget(self.max_button)
        title_layout.addWidget(self.close_button)
        
        main_layout.addWidget(self.title_bar)
        
        # 创建内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)

        # 创建上半部分布局
        upper_widget = QWidget()
        upper_layout = QHBoxLayout(upper_widget)
        upper_layout.setContentsMargins(0, 0, 0, 0)

        # 左侧区域
        left_group = QGroupBox("功能区")
        left_group.setStyleSheet(left_group_style)
        left_layout = QVBoxLayout(left_group)
        left_layout.setContentsMargins(5, 5, 5, 5)  # 设置左侧布局的边距

        # 创建文件菜单区域并添加到最上面
        self.file_menu_area = FileMenuArea(self)
        self.file_menu_area.load_image_signal.connect(self.load_image)  # 连接信号到新的load_image方法
        left_layout.addWidget(self.file_menu_area)

        # 创建预设管理器
        self.preset_manager = PresetManager()

        # 创建标签页控件并应用样式
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.West)  # 将标签页设置为左侧
        self.tab_widget.setIconSize(QSize(24, 24))  # 设置图标大小为24*24
        self.tab_widget.setStyleSheet(tab_style)
        
        # 设置标签页的固定宽度，使图标居中
        tab_bar = self.tab_widget.tabBar()
        tab_bar.setFixedWidth(40)  # 设置标签栏的固定宽度
        
        # 调整标签页的大小，使每个标签高度一致且合适
        for i in range(5):  # 预计有5个标签
            tab_bar.setTabButton(i, QTabBar.RightSide, None)  # 移除右侧按钮
            tab_bar.setTabButton(i, QTabBar.LeftSide, None)   # 移除左侧按钮
        
        left_layout.addWidget(self.tab_widget)

        # 创建各个功能区域
        self.memprocfs_area = MemProcFSArea(self, self)
        self.vol2_area = Vol2Area(self, self)  # 传入 self 作为 main_window 参数
        self.vol3_area = Vol3Area(self, self)
        self.vol2linux_area = Vol2LinuxArea(self, self)  # 创建Vol2Linux区域
        self.quick_check_area = QuickCheckArea(self, self)

        # 创建旋转后的图标
        def rotate_icon(icon_path):
            pixmap = QIcon(icon_path).pixmap(24, 24)
            transform = QTransform().rotate(90)  # 顺时针旋转90度
            rotated_pixmap = pixmap.transformed(transform)
            return QIcon(rotated_pixmap)

        # 将功能区域添加到标签页中，并设置旋转后的图标
        self.tab_widget.addTab(self.memprocfs_area, rotate_icon('res/memprocfs.png'), "")
        self.tab_widget.setTabToolTip(0, "MemProcFS功能区")
        self.tab_widget.addTab(self.vol2_area, rotate_icon('res/vol2.png'), "")
        self.tab_widget.setTabToolTip(1, "Volatility2功能区")
        self.tab_widget.addTab(self.vol3_area, rotate_icon('res/vol3.png'), "")
        self.tab_widget.setTabToolTip(2, "Volatility3功能区")
        self.tab_widget.addTab(self.vol2linux_area, rotate_icon('res/vol2linux.png'), "")  # 使用Vol2的图标
        self.tab_widget.setTabToolTip(3, "Volatility2 Linux功能区")
        self.tab_widget.addTab(self.quick_check_area, rotate_icon('res/quick.png'), "")  # 使用logo图标
        self.tab_widget.setTabToolTip(4, "高级功能区")

        upper_layout.addWidget(left_group, 4)  # 左侧占比1
                # 创建文件管理器
        self.file_manager = FileManager("output")  # 确保指定了正确的输出目录

        # 添加右侧面板
        self.right_panel = RightPanel(self.file_manager)
        self.right_panel.setStyleSheet(splitter_style)  # 应用新的样式到右侧面板
        upper_layout.addWidget(self.right_panel, 5)  # 右侧占比1

        # 设置预设管理器的right_panel
        self.preset_manager.right_panel = self.right_panel

        # 连接预设添加信号
        self.preset_manager.preset_added.connect(self.right_panel.add_button_to_preset)

        # 连接RightPanel的信号
        self.right_panel.pack_files_signal.connect(self.pack_files)
        self.right_panel.clear_files_signal.connect(self.clear_files)
        self.right_panel.execute_preset_signal.connect(self.execute_preset)

        # 设置文件树
        self.file_tree = self.right_panel.file_slot.file_tree
        self.file_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        #self.file_tree.customContextMenuRequested.connect(self.right_panel.show_file_context_menu)

        # 创建定时器
        self.file_refresh_timer = QTimer(self)
        self.file_refresh_timer.timeout.connect(self.refresh_file_list)
        self.file_refresh_timer.start(500)  # 每500毫秒（0.5秒）触发一次

        # 添加命令输出区域
        cmd_output_group = QGroupBox("命令输出")
        cmd_output_group.setObjectName("cmd_output_group")
        cmd_output_group.setStyleSheet(right_panel_style)  
        cmd_output_layout = QVBoxLayout(cmd_output_group)
        cmd_output_layout.setContentsMargins(5, 5, 5, 5)
        self.cmd_output = QTextEdit()
        self.cmd_output.setReadOnly(True)
        self.cmd_output.setPlaceholderText("命令输出将显示在这里...")
        cmd_output_layout.addWidget(self.cmd_output)
        
        # 为命令输出区域添加双击事件
        cmd_output_group.mouseDoubleClickEvent = lambda event: self.on_cmd_output_double_click(event)
        
        # 设置上下区域的比例
        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.addWidget(upper_widget)
        main_splitter.addWidget(cmd_output_group)
        main_splitter.setStretchFactor(0, 1)  # 上半部分占1
        main_splitter.setStretchFactor(1, 1)  # 下半部分占1
        main_splitter.setStyleSheet(splitter_style)  # 应用新的样式

        content_layout.addWidget(main_splitter)

        main_layout.addWidget(content_widget)
        
        # 设置样式
        self.setStyleSheet(main_window_style)
        
        # 用于移动窗口的变量
        self.dragging = False
        self.drag_position = QPoint()

        self.notifications = []
        self.mem_image_loader = MemImageLoader()
        self.mem_image_loader.load_finished.connect(self.on_load_finished)
        self.mem_image_loader.output_received.connect(lambda text: self.update_cmd_output(text))  # 添加这行
        self.current_mem_path = ''  # 添加这行

        # 初始化 Vol3Plugin 为 None
        self.vol3_plugin = None

        # 添加GlassOverlay实例
        self.glass_overlay = GlassOverlay(self)
        self.glass_overlay.hide()

        self.setStyleSheet(main_window_style)
        self.memprocfs_area.setStyleSheet(memprocfs_style)
        self.vol2_area.setStyleSheet(vol2_style)
        self.vol2_area.update_styles()  # 添加这行，确保Vol2区域的按钮样式也被更新
        self.vol3_area.setStyleSheet(vol3_style)
        self.vol3_area.update_styles()
        self.vol2linux_area.setStyleSheet(vol2_style)  # 使用与Vol2相同的样式
        self.vol2linux_area.update_styles()  # 更新Vol2Linux区域的按钮样式
        self.quick_check_area.setStyleSheet(quick_check_style)
        self.right_panel.setStyleSheet(right_panel_style)

        # 在初始化时加载保存的主题
        saved_theme = get_saved_theme()
        self.apply_selected_theme(saved_theme)
                # 立即更新圆形按钮的样式
        self.update_circle_button_style(self.theme_button, theme_button_color)
        self.update_circle_button_style(self.min_button, minimize_button_color)
        self.update_circle_button_style(self.max_button, maximize_button_color)
        self.update_circle_button_style(self.close_button, close_button_color)

    def update_cmd_output(self, text, color=None):
        cursor = self.cmd_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        formatted_text = text.replace('\n', '<br>')  # 将换行符替换为HTML换行标签
        
        # 使用 styles 中定义的文本颜色，除非特别指定
        text_color = color.name() if color else cmd_output_text_color
        
        cursor.insertHtml(f'<span style="color: {text_color};">{formatted_text}</span>')
        self.cmd_output.setTextCursor(cursor)
        self.cmd_output.ensureCursorVisible()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            # 显示GlassOverlay
            self.glass_overlay.show()
            
            # 接受拖放动作
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        # 当文件拖出窗口时，恢复原来的样式
        self.glass_overlay.hide()
        event.accept()

    def dropEvent(self, event):
        # 恢复原来的样式
        self.glass_overlay.hide()
        
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        if files:
            self.handle_dropped_file(files[0])
        event.acceptProposedAction()

    def handle_dropped_file(self, file_path):
        """处理拖放的文件"""
        if self.file_tree.topLevelItemCount() > 0:
            QMessageBox.warning(self, "警告", "检测到上次运行的残留取证文件，请先打包或清空文件槽！")
            return
        self.load_image(file_path)

    def load_image(self, image_path=None):
        """加载文件，支持拖放和手动选择两种方式"""
        if not image_path:
            file_dialog = QFileDialog(self)
            image_path, _ = file_dialog.getOpenFileName(self, "选择文件", "", "所有文件 (*.*)")
            if not image_path:
                return
        if image_path:
            self.file_menu_area.set_image_path(image_path)
            title_label = self.findChild(QLabel, "title_label")
            if title_label:
                title_label.setText(f"Lovelymem Ver 0.93.1 - {image_path}")
            self.current_mem_path = image_path  # 更新当前内存镜像路径
            self.mem_image_loader.load_mem_image(image_path)
            self.cmd_output.append("正在加载内存镜像，请稍候...")
            # 保存mem_path到output/image_info.txt 格式"mem_path, "
            with open('output/image_info.txt', 'w', encoding='utf-8') as f:
                f.write(image_path + ", ")
            # 创建 Vol2Plugin 实例并开始获取 profile
            vol2_plugin = Vol2Plugin(image_path)
            vol2_plugin.start_get_profile()
            
            # 连接信号以更新 UI
            vol2_plugin.get_profile_thread.profile_obtained.connect(self.on_profile_obtained)
            
            # 更新 Vol2Area 的 vol2_plugin 实例
            self.vol2_area.vol2_plugin = vol2_plugin
            
            # 创建 Vol3Plugin 实例
            self.vol3_plugin = Vol3Plugin(image_path)
            
            # 更新 Vol3Area 的 vol3_plugin 实例
            self.vol3_area.vol3_plugin = self.vol3_plugin

    def on_profile_obtained(self, profile, profilelist):
        self.cmd_output.append(f"获取到的 Profile: {profile}")
        self.vol2_area.update_profile(profile, profilelist)

    def get_current_mem_path(self):
        return self.current_mem_path if hasattr(self, 'current_mem_path') else None

    def on_load_finished(self, success, message):
        if success:
            self.cmd_output.append(f"[成功] {message}")
        else:
            self.cmd_output.append(f"[失败] {message}")

    def unload_image(self):
        if not self.current_mem_path:
            return

        self.current_mem_path = ''
        # profile 清空
        self.vol2_area.profile = None
        # 删除 output/image_info.txt
        if os.path.exists('output/image_info.txt'):
            os.remove('output/image_info.txt')
        # 终止 MemProcFS.exe 进程
        os.system("taskkill /F /IM MemProcFS.exe")
        os.system("taskkill /F /IM python27.exe")
        print("[+] 卸载镜像成功")
        # 标题修改
        self.setWindowTitle("Lovelymem Ver 0.93.1")

    def refresh_file_list(self):
        try:
            # 获取当前展开的项目
            expanded_items = self.right_panel.file_slot.get_expanded_items(self.right_panel.file_slot.file_tree.invisibleRootItem())
            
            # 清空文件树
            self.right_panel.file_slot.file_tree.clear()
            
            # 获取文件列表
            file_list = self.file_manager.get_file_list()
            
            # 更新文件列表
            self.update_file_list(file_list)
            
            # 恢复展开的项目
            self.right_panel.file_slot.restore_expanded_items(self.right_panel.file_slot.file_tree.invisibleRootItem(), expanded_items)
        except Exception as e:
            print(f"刷新文件列表时发生错误: {str(e)}")

    def pack_files(self):
        files = self.file_manager.get_file_list()
        if not files:
            self.cmd_output.append("没有文件可以打包")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"packed_files_{timestamp}.zip"
        
        zip_path = os.path.join(self.file_manager.get_packed_dir(), zip_filename)

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file_info in files:
                file_path, _, _ = file_info
                full_path = os.path.join(self.file_manager.output_dir, file_path)
                zipf.write(full_path, file_path)

        self.cmd_output.append(f"文件已打包到 {zip_path}")
        
        # 打包完成后立即清空文件槽
        self.clear_files()

    def clear_files(self):
        if self.file_manager.clear_output_directory():
            self.cmd_output.append("所有文件已清空")
            self.refresh_file_list()
        else:
            self.cmd_output.append("清空文件失败")

    def execute_preset(self, preset_name):
        print(f"执行预设: {preset_name}")
        
        # 从数据库获取预设的按钮
        conn = sqlite3.connect('db/presets.db')
        c = conn.cursor()
        c.execute("SELECT button_text FROM presets WHERE name = ?", (preset_name,))
        buttons = c.fetchall()
        conn.close()

        if not buttons:
            QMessageBox.warning(self, "警告", f"预设 '{preset_name}' 中没按钮")
            return

        # 执行每个按钮的功能
        for button in buttons:
            button_text = button[0]
            if '-' in button_text:
                area, function = button_text.split('-', 1)
            else:
                area = "未知"
                function = button_text

            print(f"执行: 区域 = {area}, 功能 = {function}")  # 添加调试输出
            
            if area == "MemProcFS":
                self.execute_memprocfs_function(function)
            elif area == "Vol2":
                self.execute_vol2_function(function)
            elif area == "Vol3":  # 修改这里
                self.execute_vol3_function(function)
            elif area == "快速检查":
                self.execute_quick_check_function(function)
            else:
                print(f"未知区域: {area}")

    def execute_memprocfs_function(self, function):
        # 在 MemProcFS 区域查找并执行对应的函数
        for button in self.memprocfs_area.findChildren(QPushButton):
            if button.text() == function:
                button.click()
                return
        print(f"在 MemProcFS 区域未找到函数: {function}")

    def execute_vol2_function(self, function):
        # 在 Volatility 2 区域查找并执行对应的函数
        for group in self.vol2_area.findChildren(CollapsibleButtonGroup):
            for i in range(group.content_layout.count()):
                widget = group.content_layout.itemAt(i).widget()
                if isinstance(widget, QPushButton):
                    if widget.text().lower() == function.lower():
                        # 更新内存镜像路径
                        new_mem_path = self.vol2_area.update_mem_path()
                        
                        if not new_mem_path:
                            QMessageBox.warning(self, "警告", "请先载入内存镜像文件！")
                            return
                        
                        # 直接调用按钮的点击事件
                        widget.click()
                        return
        
        print(f"在 Volatility 2 区域未找到按钮: {function}")
        
        # 如果没有找到完全匹配的按钮，尝试部分匹配
        for group in self.vol2_area.findChildren(CollapsibleButtonGroup):
            for i in range(group.content_layout.count()):
                widget = group.content_layout.itemAt(i).widget()
                if isinstance(widget, QPushButton):
                    if function.lower() in widget.text().lower():
                        new_mem_path = self.vol2_area.update_mem_path()
                        
                        if not new_mem_path:
                            QMessageBox.warning(self, "警告", "请先载入内存镜像文件！")
                            return
                        
                        widget.click()
                        print(f"找到部分匹配的按钮: {widget.text()}")
                        return
        
        print(f"在 Volatility 2 区域未找到任何匹配的按钮: {function}")

    def execute_vol3_function(self, function):
        # 在 Volatility 3 区域查找并执行对应的函数
        for group in self.vol3_area.findChildren(Vol3CollapsibleButtonGroup):
            for button in group.buttons:
                if button.text() == function:
                    # 更新内存镜像路径
                    new_mem_path = self.vol3_area.update_mem_path()
                    
                    if not new_mem_path:
                        QMessageBox.warning(self, "警告", "请先载入内存镜像文件！")
                        return
                    
                    # 直接调用按钮的点击事件
                    button.click()
                    return
        
        print(f"在 Volatility 3 区域未找到按钮: {function}")

    def execute_quick_check_function(self, function):
        # 在快速检查区域查找并执行对应的函数
        for button in self.quick_check_area.findChildren(QPushButton):
            if button.text() == function:
                button.click()
                return
        print(f"在快速检查区域未找到函数: {function}")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if self.title_bar.geometry().contains(event.position().toPoint()):
                # 获取点击位置的子部件
                child_widget = self.childAt(event.position().toPoint())
                # 如果点击的不是标题栏
                if child_widget == self.title_bar or child_widget is None:
                    self.dragging = True
                    self.drag_position = event.position().toPoint() + self.mapToGlobal(QPoint(0, 0)) - self.frameGeometry().topLeft()
                    event.accept()
                else:
                    # 如果点击的是子部件（如按钮），则不处理，让事件传递给子部件
                    super().mousePressEvent(event)
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging:
            self.move(event.position().toPoint() + self.mapToGlobal(QPoint(0, 0)) - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.dragging = False
        super().mouseReleaseEvent(event)

    def create_circle_button(self, base_color):
        button = QPushButton()
        button.setFixedSize(14, 14)
        return button

    def update_file_list(self, file_list):
        self.right_panel.file_slot.file_tree.clear()
        for file_info in file_list:
            file_path, file_size, mod_time = file_info
            self.right_panel.add_file(file_path, file_size, mod_time)

    def toggle_theme(self):
        theme_selector = ThemeSelectorDialog(list(color_schemes.keys()))
        theme_selector.theme_selected.connect(self.apply_selected_theme)
        theme_selector.font_selected.connect(self.apply_selected_font)
        
        # 计算屏幕中心位置
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()
        dialog_geometry = theme_selector.geometry()
        
        # 将主题选择器窗口移动到屏幕中心
        x = screen_geometry.center().x() - dialog_geometry.width() // 2
        y = screen_geometry.center().y() - dialog_geometry.height() // 2
        theme_selector.move(x, y)
        
        theme_selector.exec()

    def apply_selected_theme(self, theme_name):
        is_dark = is_dark_mode()
        save_theme(theme_name)
        apply_color_scheme(theme_name, is_dark)
        self.update_all_styles()
        self.vol3_area.update_button_styles()  # 添加这行
        self.statusBar().showMessage(f"当前主题: {theme_name}", 3000)
        
        # 保存选择的主题
        save_theme(theme_name)
        
    def apply_selected_font(self, font):
    # 重新应用样式以更新字体
        self.update_all_styles()

    def update_all_styles(self):
        try:
            import ui.styles

            # 更新主窗口样式
            self.setStyleSheet(ui.styles.main_window_style)
            
            # 更新各个区域的样式
            self.memprocfs_area.setStyleSheet(ui.styles.memprocfs_style)
            self.vol2_area.setStyleSheet(ui.styles.vol2_style)
            self.vol2_area.update_styles()  # 添加这行，确保Vol2区域的按钮样式也被更新
            self.vol3_area.setStyleSheet(ui.styles.vol3_style)
            self.vol3_area.update_styles()
            self.vol2linux_area.setStyleSheet(ui.styles.vol2_style)  # 使用与Vol2相同的样式
            self.vol2linux_area.update_styles()  # 更新Vol2Linux区域的按钮样式
            self.quick_check_area.setStyleSheet(ui.styles.quick_check_style)
            self.right_panel.setStyleSheet(ui.styles.right_panel_style)
            #print("各个区域样式已更新")
            
            # 更新标题栏样式
            self.title_bar.setStyleSheet(f"""
                {ui.styles.candy_background}
                {ui.styles.common_font_style}
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            """)
            #print("标题栏样式已更新")
            
            # 更新圆形按钮样式
            self.update_circle_button_style(self.theme_button, theme_button_color)
            self.update_circle_button_style(self.min_button, minimize_button_color)
            self.update_circle_button_style(self.max_button, maximize_button_color)
            self.update_circle_button_style(self.close_button, close_button_color)
            
            # 更新所有子组件的样式
            for widget in self.findChildren(QWidget):
                if isinstance(widget, QPushButton):
                    widget.setStyleSheet(ui.styles.button_style)
                elif isinstance(widget, QToolButton):
                    widget.setStyleSheet(ui.styles.tool_button_style)
                elif isinstance(widget, QGroupBox):
                    widget.setStyleSheet(ui.styles.right_panel_style)
                elif isinstance(widget, QTabWidget):
                    widget.setStyleSheet(ui.styles.tab_style)
                elif isinstance(widget, QSplitter):
                    widget.setStyleSheet(ui.styles.splitter_style)
                elif isinstance(widget, QListView):
                    widget.setStyleSheet(f"""
                        QListView {{
                            background-color: {ui.styles.background_color};
                            color: {ui.styles.text_color};
                            border: 1px solid {ui.styles.border_color};
                            border-radius: 3px;
                        }}
                    """)
                    widget.viewport().update()
                elif isinstance(widget, QTextEdit):
                    widget.setStyleSheet(ui.styles.cmd_output_style)
                
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.update()
            # 强制更新整个界面
            self.repaint()
            
            # print(f"当前背景颜色: {background_color}")
            # print(f"当前文本颜色: {text_color}")
            # print(f"当前按钮背景颜色: {button_bg_color}")
            
        except Exception as e:
            pass
            # print(f"更新样式时发生错误: {str(e)}")
            # print(traceback.format_exc())
        #print("样式更新完成")

    def update_circle_button_style(self, button, base_color):
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

    def on_cmd_output_double_click(self, event):
        """处理命令输出区域的双击事件"""
        # 创建独立的命令输出窗口
        self.cmd_output_window = CmdOutputWindow(self.cmd_output)
        # 连接关闭信号
        self.cmd_output_window.closed.connect(self.on_cmd_output_window_closed)
        
        # 隐藏主界面的命令输出区域
        cmd_output_group = self.findChild(QGroupBox, "cmd_output_group")
        if cmd_output_group:
            cmd_output_group.setVisible(False)
    
    def on_cmd_output_window_closed(self, cmd_output):
        """处理命令输出窗口关闭事件"""
        # 将命令输出控件重新添加到主窗口
        cmd_output_group = self.findChild(QGroupBox, "cmd_output_group")
        if cmd_output_group:
            cmd_output_layout = cmd_output_group.layout()
            # 清除现有的控件
            while cmd_output_layout.count():
                item = cmd_output_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            # 添加回命令输出控件
            cmd_output_layout.addWidget(cmd_output)
            self.cmd_output = cmd_output
            # 显示命令输出区域
            cmd_output_group.setVisible(True)

   #关闭程序时 提示卸载镜像，清空文件槽
    def closeEvent(self, event: QCloseEvent):
        reply = QMessageBox.question(self, '确认退出', 
                                     "是否确定要退出程序？\n退出前将卸载镜像并清空文件槽。",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.unload_image()
            self.clear_files()
            super().closeEvent(event)
        else:
            event.ignore()

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def open_config_dialog(self):
        from ui.config_dialog import ConfigDialog
        config_dialog = ConfigDialog(self)
        config_dialog.exec()
