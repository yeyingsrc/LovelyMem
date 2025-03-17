from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                               QPushButton, QTreeWidget, QTreeWidgetItem, QHeaderView, 
                               QApplication, QMenu, QMessageBox, QLabel, QFrame, QSizeGrip)
from PySide6.QtCore import Qt, Signal, QPoint, QMimeData
from PySide6.QtGui import QCursor, QDrag, QIcon, QFont
import os
import sys
from datetime import datetime
from ui.styles import (right_panel_style, background_color, text_color, 
                      button_bg_color, button_text_color, button_hover_color, 
                      border_color, group_title_bg_color, cmd_output_bg_color,
                      theme_button_color, minimize_button_color, maximize_button_color, close_button_color,
                      current_font_family)
import logging
import traceback
import subprocess
import importlib.util
import importlib

class CustomTreeWidget(QTreeWidget):
    """自定义树形控件，用于文件槽显示"""
    double_clicked_signal = Signal()  # 添加双击信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setExpandsOnDoubleClick(False)  # 禁用双击展开
        self.last_clicked_item = None
        self.setHeaderLabels(["文件名", "大小", "修改日期"])
        self.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.setSortingEnabled(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def mouseReleaseEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        if item:
            if self.last_clicked_item and self.last_clicked_item == item:
                # 如果是同一个项目被点击两次，切换展开状态
                item.setExpanded(not item.isExpanded())
            else:
                # 如果是新的项目被点击，只选中它，不展开
                self.setCurrentItem(item)
            self.last_clicked_item = item
        else:
            self.last_clicked_item = None
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """重写双击事件"""
        print("树控件双击")  # 调试信息
        super().mouseDoubleClickEvent(event)
        self.double_clicked_signal.emit()  # 发送双击信号

    def clear(self):
        self.last_clicked_item = None
        super().clear()


class FileSlotWindow(QWidget):
    """独立的文件槽窗口"""
    closed = Signal(QTreeWidget, QPushButton, QPushButton)  # 返回树控件和按钮

    def __init__(self, file_tree, pack_button, clear_button, file_manager, file_slot):
        super().__init__(None, Qt.Window)  # 使用Qt.Window标志创建顶级窗口
        self.setWindowTitle("文件槽")
        self.setWindowFlags(Qt.FramelessWindowHint)  # 移除原生标题栏
        self.setAttribute(Qt.WA_TranslucentBackground)  # 启用窗口背景透明
        self.resize(500, 400)  # 设置合适的默认大小
        
        self.file_tree = file_tree
        self.pack_button = pack_button
        self.clear_button = clear_button
        self.file_manager = file_manager
        self.file_slot = file_slot  # 保存对原始FileSlot的引用
        
        # 先设置父控件，确保控件可见
        self.file_tree.setParent(self)
        self.pack_button.setParent(self)
        self.clear_button.setParent(self)
        
        self.setup_ui()
        
        # 确保文件树可见
        self.file_tree.setVisible(True)
        self.pack_button.setVisible(True)
        self.clear_button.setVisible(True)
        
        # 手动加载文件列表
        self.load_file_list()
        
        # 设置文件树的双击事件处理
        self.file_tree.double_clicked_signal.connect(self.on_tree_double_click)
        
        # 设置文件树的右键菜单，完全重新设置而不是尝试断开旧连接
        self.file_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self.show_file_context_menu)
        
        # 创建查看器列表，防止被垃圾回收
        self.viewers = []
        
        # 用于移动窗口的变量
        self.dragging = False
        self.drag_position = QPoint()
        
        # 应用样式
        self.apply_style()
        
        # 设置字体
        self.apply_font()
        
        # 监听主题变化
        QApplication.instance().paletteChanged.connect(self.on_theme_changed)
        
        # 显示窗口
        self.show()
        QApplication.processEvents()

    def create_circle_button(self, base_color):
        """创建圆形按钮"""
        button = QPushButton()
        button.setFixedSize(15, 15)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {base_color};
                border-radius: 7px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {self.lighten_color(base_color, 20)};
            }}
        """)
        return button
    
    def lighten_color(self, color, amount=20):
        """使颜色变亮"""
        # 简单处理 rgba 格式
        if color.startswith("rgba("):
            parts = color.strip("rgba()").split(",")
            r = min(255, int(parts[0]) + amount)
            g = min(255, int(parts[1]) + amount)
            b = min(255, int(parts[2]) + amount)
            a = float(parts[3])
            return f"rgba({r}, {g}, {b}, {a})"
        # 简单处理 #rrggbb 格式
        elif color.startswith("#"):
            r = min(255, int(color[1:3], 16) + amount)
            g = min(255, int(color[3:5], 16) + amount)
            b = min(255, int(color[5:7], 16) + amount)
            return f"#{r:02x}{g:02x}{b:02x}"
        return color
    
    def apply_style(self):
        """应用样式"""
        from ui.styles import (right_panel_style, background_color, text_color, 
                      button_bg_color, button_text_color, button_hover_color, 
                      border_color, group_title_bg_color, cmd_output_bg_color,
                      theme_button_color, minimize_button_color, maximize_button_color, close_button_color,
                      current_font_family)
        self.setStyleSheet(f"""
            QWidget {{
                color: {text_color};
            }}
            
            #contentContainer {{
                background-color: {background_color};
                border-radius: 10px;
                border: 1px solid {border_color};
            }}
            
            #titleBar {{
                background-color: {group_title_bg_color};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom: 1px solid {border_color};
            }}
            
            QLabel {{
                color: {text_color};
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
            }}
            
            QPushButton {{
                background-color: {button_bg_color};
                color: {button_text_color};
                border: none;
                border-radius: 3px;
                padding: 5px;
            }}
            
            QPushButton:hover {{
                background-color: {button_hover_color};
            }}
            
            QSizeGrip {{
                background-color: transparent;
            }}
        """)
    
    def apply_font(self):
        """应用字体"""
        font = QFont(current_font_family, 9)  # 使用与主窗口相同的字体
        self.setFont(font)
        
        # 为所有子控件设置字体
        for widget in self.findChildren(QWidget):
            widget.setFont(font)
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)  # 设置边距，为圆角留出空间
        main_layout.setSpacing(0)
        
        # 创建内容容器（带圆角的主窗口）
        self.content_container = QWidget()
        self.content_container.setObjectName("contentContainer")
        container_layout = QVBoxLayout(self.content_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
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
        title_label = QLabel("文件槽")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 添加最小化按钮
        self.min_button = self.create_circle_button(minimize_button_color)
        self.min_button.clicked.connect(self.showMinimized)
        self.min_button.setToolTip("最小化")
        
        # 添加关闭按钮
        self.close_button = self.create_circle_button(close_button_color)
        self.close_button.clicked.connect(self.close)
        self.close_button.setToolTip("关闭")
        
        title_layout.addWidget(self.min_button)
        title_layout.addWidget(self.close_button)
        
        container_layout.addWidget(self.title_bar)
        
        # 创建内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)
        
        # 添加文件树
        content_layout.addWidget(self.file_tree)
        
        # 添加按钮布局
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.pack_button)
        button_layout.addWidget(self.clear_button)
        content_layout.addLayout(button_layout)
        
        container_layout.addWidget(content_widget)
        
        # 添加大小调整手柄
        size_grip = QSizeGrip(self.content_container)
        size_grip.setFixedSize(16, 16)
        
        # 创建一个布局来放置大小调整手柄在右下角
        grip_layout = QHBoxLayout()
        grip_layout.setContentsMargins(0, 0, 0, 0)
        grip_layout.addStretch()
        grip_layout.addWidget(size_grip)
        
        container_layout.addLayout(grip_layout)
        
        main_layout.addWidget(self.content_container)
    
    def on_tree_double_click(self):
        """处理文件树的双击事件"""
        # 如果双击的是文件，则打开文件
        item = self.file_tree.currentItem()
        if item and item.childCount() == 0:  # 是文件而不是文件夹
            file_path = self.file_slot.get_full_path(item)
            self.file_slot.quick_open_file(file_path)
    
    def show_file_context_menu(self, position):
        """显示文件右键菜单"""
        item = self.file_tree.itemAt(position)
        if item and item.childCount() == 0:  # 确保选中的是文件而不是文件夹
            file_path = self.file_slot.get_full_path(item)
            return self.file_slot.show_context_menu_for_path(file_path, self.file_tree.mapToGlobal(position))
        return False
    
    def load_file_list(self):
        """加载文件列表"""
        #print("加载文件列表")  # 调试信息
        try:
            # 清空文件树
            self.file_tree.clear()
            
            # 获取文件列表
            file_list = self.file_manager.get_file_list()
            #print(f"文件列表: {file_list}")  # 调试信息
            
            # 添加文件到文件树
            for rel_path, file_size, mod_time in file_list:
                self.file_slot.add_file(rel_path, file_size, mod_time)
            
            # 更新UI
            QApplication.processEvents()
        except Exception as e:
            print(f"加载文件列表时出错: {e}")  # 调试信息
    
    def update_file_list(self):
        """更新文件列表，确保内容显示"""
        try:
            # 记录展开状态
            expanded_items = self.file_slot.get_expanded_items(self.file_tree.invisibleRootItem())
            
            # 清空并重新加载文件列表
            self.file_tree.clear()
            file_list = self.file_manager.get_file_list()
            for rel_path, file_size, mod_time in file_list:
                self.file_slot.add_file(rel_path, file_size, mod_time)
            
            # 恢复展开状态
            self.file_slot.restore_expanded_items(self.file_tree.invisibleRootItem(), expanded_items)
            
            # 确保文件树可见
            self.file_tree.setVisible(True)
            QApplication.processEvents()
        except Exception as e:
            print(f"更新文件列表时出错: {e}")  # 调试信息

    def mousePressEvent(self, event):
        """处理鼠标按下事件，用于移动窗口"""
        if event.button() == Qt.LeftButton and self.title_bar.geometry().contains(event.position().toPoint()):
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件，用于移动窗口"""
        if event.buttons() & Qt.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件，用于移动窗口"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def closeEvent(self, event):
        self.closed.emit(self.file_tree, self.pack_button, self.clear_button)
        super().closeEvent(event)

    def on_theme_changed(self):
        """主题变化时更新样式"""
        self.apply_style()
        self.apply_font()


class FileSlot(QGroupBox):
    """文件槽组件，可以作为面板的一部分或独立窗口"""
    pack_files_signal = Signal()
    clear_files_signal = Signal()
    
    def __init__(self, file_manager):
        super().__init__("文件槽")
        self.file_manager = file_manager
        self.file_slot_window = None
        self.drag_start_position = None
        self.viewers = []
        self.plugins = self.load_plugins()  # 加载插件
        self.setup_ui()
        
        # 设置文件槽可拖动
        self.setMouseTracking(True)
        
        # 添加双击事件处理
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_file_context_menu)
        
        # 双击GroupBox标题栏创建独立窗口
        self.original_double_click_event = self.mouseDoubleClickEvent  # 保存原始方法
        self.mouseDoubleClickEvent = self.on_group_box_double_click
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建文件树
        self.file_tree = CustomTreeWidget()
        self.file_tree.customContextMenuRequested.connect(self.show_file_context_menu)
        self.file_tree.double_clicked_signal.connect(self.on_tree_double_click)  # 连接自定义双击信号
        layout.addWidget(self.file_tree)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        self.pack_button = QPushButton("打包")
        self.clear_button = QPushButton("清空")
        button_layout.addWidget(self.pack_button)
        button_layout.addWidget(self.clear_button)
        layout.addLayout(button_layout)
        
        # 连接信号
        self.pack_button.clicked.connect(self.pack_files_signal.emit)
        self.clear_button.clicked.connect(self.clear_files_signal.emit)
    
    def on_group_box_double_click(self, event):
        """处理GroupBox的双击事件"""
        # 检查点击位置是否在标题栏区域
        if event.position().y() <= 20:  # 标题栏高度约为20像素
            # 通知主窗口创建独立窗口
            parent = self.window()
            if hasattr(parent, 'on_file_slot_double_click'):
                parent.on_file_slot_double_click(event)
            else:
                # 如果主窗口没有处理方法，则调用原始的双击事件
                if hasattr(self, 'original_double_click_event') and self.original_double_click_event:
                    self.original_double_click_event(event)
                else:
                    super().mouseDoubleClickEvent(event)
        else:
            # 如果不是在标题栏区域，则调用原始的双击事件
            if hasattr(self, 'original_double_click_event') and self.original_double_click_event:
                self.original_double_click_event(event)
            else:
                super().mouseDoubleClickEvent(event)
    
    def on_tree_double_click(self):
        """处理文件树的双击事件"""
        # 如果双击的是文件，则打开文件
        item = self.file_tree.currentItem()
        if item and item.childCount() == 0:  # 是文件而不是文件夹
            file_path = self.get_full_path(item)
            self.quick_open_file(file_path)
        else:
            # 如果双击的是空白区域或文件夹，则创建独立窗口
            if not self.file_slot_window:
                self.create_file_slot_window()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton) or not self.drag_start_position:
            return
        
        # 计算移动距离，只有超过拖动阈值才开始拖动
        if (event.position().toPoint() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return

        # 创建拖动对象
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText("file_slot")
        drag.setMimeData(mime_data)

        # 执行拖动操作
        if drag.exec(Qt.MoveAction) == Qt.MoveAction:
            self.create_file_slot_window()
            
        super().mouseMoveEvent(event)

    def create_file_slot_window(self):
        """创建独立的文件槽窗口"""
        if self.file_slot_window is None:
            try:
                #print("创建文件槽窗口")  # 调试信息
                
                # 从布局中移除控件
                self.layout().removeWidget(self.file_tree)
                button_layout = self.layout().itemAt(1)
                if button_layout and button_layout.layout():
                    button_layout.layout().removeWidget(self.pack_button)
                    button_layout.layout().removeWidget(self.clear_button)
                
                # 创建独立窗口
                self.file_slot_window = FileSlotWindow(
                    self.file_tree, 
                    self.pack_button, 
                    self.clear_button,
                    self.file_manager,
                    self  # 传递自身引用
                )
                
                # 连接关闭信号
                self.file_slot_window.closed.connect(self.restore_file_slot)
                
                # 将自身隐藏，不显示占位符
                self.setVisible(False)
                
                print("文件槽窗口创建完成")  # 调试信息
            except Exception as e:
                print(f"创建文件槽窗口时出错: {e}")  # 调试信息
                # 恢复控件到原来的布局
                self.restore_file_slot(self.file_tree, self.pack_button, self.clear_button)
    
    def restore_file_slot(self, file_tree, pack_button, clear_button):
        """恢复文件槽到面板"""
        self.file_tree = file_tree
        self.pack_button = pack_button
        self.clear_button = clear_button
        
        # 重新添加到布局
        self.layout().addWidget(self.file_tree)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.pack_button)
        button_layout.addWidget(self.clear_button)
        self.layout().addLayout(button_layout)
        
        # 重置窗口引用
        self.file_slot_window = None
        
        # 显示自身
        self.setVisible(True)

    def add_file(self, file_path, file_size, mod_time):
        """添加文件到文件树"""
        if not file_path.lower().endswith('.json'):
            parts = file_path.split(os.sep)
            current_item = self.file_tree.invisibleRootItem()
            for i, part in enumerate(parts):
                found = False
                for j in range(current_item.childCount()):
                    if current_item.child(j).text(0) == part:
                        current_item = current_item.child(j)
                        found = True
                        break
                if not found:
                    new_item = QTreeWidgetItem(current_item)
                    new_item.setText(0, part)
                    if i == len(parts) - 1:  # 如果是最后一部分，即文件
                        new_item.setText(1, self.format_size(file_size))
                        new_item.setText(2, mod_time.strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        # 如果不是最后一部分，说明是文件夹，设置展开指示器
                        new_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
                    current_item = new_item
                
                # 不自动展开项目
                if i < len(parts) - 1:
                    current_item.setExpanded(False)

    def format_size(self, size):
        """格式化文件大小显示"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0

    def update_file_list(self):
        """更新文件列表"""
        # 记录展开状态
        expanded_items = self.get_expanded_items(self.file_tree.invisibleRootItem())

        self.file_tree.clear()
        file_list = self.file_manager.get_file_list()
        for rel_path, file_size, mod_time in file_list:
            self.add_file(rel_path, file_size, mod_time)
        
        # 恢复展开状态
        self.restore_expanded_items(self.file_tree.invisibleRootItem(), expanded_items)

    def get_expanded_items(self, item, path=""):
        """获取展开的项目"""
        expanded_items = {}
        for i in range(item.childCount()):
            child = item.child(i)
            child_path = os.path.join(path, child.text(0))
            if child.isExpanded():
                expanded_items[child_path] = True
            if child.childCount() > 0:
                expanded_items.update(self.get_expanded_items(child, child_path))
        return expanded_items

    def restore_expanded_items(self, item, expanded_items, path=""):
        """恢复展开的项目"""
        for i in range(item.childCount()):
            child = item.child(i)
            child_path = os.path.join(path, child.text(0))
            if expanded_items.get(child_path, False):
                child.setExpanded(True)
            if child.childCount() > 0:
                self.restore_expanded_items(child, expanded_items, child_path)

    def collapse_all_items(self, item):
        """折叠所有项目"""
        for i in range(item.childCount()):
            child = item.child(i)
            child.setExpanded(False)
            if child.childCount() > 0:
                self.collapse_all_items(child)

    def show_file_context_menu(self, position):
        """显示文件右键菜单"""
        item = self.file_tree.itemAt(position)
        if item and item.childCount() == 0:  # 确保选中的是文件而不是文件夹
            file_path = self.get_full_path(item)
            return self.show_context_menu_for_path(file_path, self.file_tree.mapToGlobal(position))
        return False
    
    def show_context_menu_for_path(self, file_path, global_pos):
        """为指定文件路径显示上下文菜单"""
        try:
            menu = QMenu()
            open_action = menu.addAction("快速打开")
            open_file_dir_action = menu.addAction("打开文件目录")
            
            # 添加扩展菜单
            reload_plugins_action = menu.addAction("重新加载插件")
            extensions_menu = menu.addMenu("扩展")
            
            # 添加扩展子菜单
            for category, category_plugins in self.plugins.items():
                category_menu = extensions_menu.addMenu(category)
                for plugin_title, plugin_data in category_plugins.items():
                    plugin_action = category_menu.addAction(plugin_title)
                    # 使用lambda创建闭包，确保正确捕获参数
                    plugin_action.triggered.connect(lambda checked=False, fp=file_path, pd=plugin_data: self.execute_plugin(fp, pd))
            
            delete_action = menu.addAction("删除")
            reload_plugins_action.triggered.connect(self.reload_plugins)
            
            action = menu.exec(global_pos)
            
            if action == open_action:
                self.quick_open_file(file_path)
                return True
            elif action == delete_action:
                self.delete_selected_file(file_path)
                self.update_file_list()  # 在删除文件后更新文件列表
                return True
            elif action == open_file_dir_action:
                self.open_file_dir(file_path)
                return True
            elif action == reload_plugins_action:
                self.reload_plugins()
                return True
                
            # 检查是否选择了插件操作
            for category, category_plugins in self.plugins.items():
                for plugin_title, plugin_data in category_plugins.items():
                    plugin_action_text = plugin_title
                    if action and action.text() == plugin_action_text:
                        return True
                        
            return action is not None  # 如果选择了任何操作，返回True
            
        except Exception as e:
            print(f"显示上下文菜单时出错: {e}")
            traceback.print_exc()
            return False

    def get_full_path(self, item):
        """获取完整文件路径"""
        path = []
        while item is not None:
            path.insert(0, item.text(0))
            item = item.parent()
        
        # 移除路径开头的 'output' 前缀（如果存在）
        if path and path[0] == 'output':
            path.pop(0)
        
        # 构建相对'output' 目录的路径
        relative_path = os.path.join(*path)
        
        # 获取当前工作目录
        current_dir = os.getcwd()
        
        # 构建完整路径
        full_path = os.path.normpath(os.path.join(current_dir, 'output', relative_path))
        
        return full_path

    def quick_open_file(self, file_path):
        """快速打开文件"""
        print(f"尝试打开文件: {file_path}")

        if not os.path.exists(file_path):
            QMessageBox.warning(self, "文件不存在", f"文件 {os.path.basename(file_path)} 不存在")
            return

        try:
            if file_path.lower().endswith('.csv'):
                self.open_csv_file(file_path)
            elif file_path.lower().endswith(('.txt', '.text', '.log','.dat')):
                self.open_text_file(file_path)
            elif file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.ico')):
                self.open_image_file(file_path)
            else:
                self.open_other_file(file_path)
        except Exception as e:
            print(f"打开文件时发生错误: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"打开文件时发生错误: {str(e)}")

    def open_csv_file(self, file_path):
        """打开CSV文件"""
        try:
            from lovelyform import show_csv_viewer
            show_csv_viewer(file_path)
        except Exception as e:
            print(f"打开 CSV 文件时发生错误: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"打开 CSV 文件时发生错误: {str(e)}")

    def open_text_file(self, file_path):
        """打开文本文件"""
        try:
            # 确保导入正确
            import importlib.util
            spec = importlib.util.spec_from_file_location("QuicklyView", "plugin/QuicklyView.py")
            module = importlib.util.module_from_spec(spec)
            sys.modules[module.__name__] = module
            spec.loader.exec_module(module)
            
            text_viewer = module.QuicklyView(f"快速文本查看器 - {os.path.basename(file_path)}")
            text_viewer.load_file_content(file_path)
            text_viewer.show()
            
            # 保存查看器引用，防止被垃圾回收
            self.viewers.append(text_viewer)
        except Exception as e:
            print(f"打开文本文件时发生错误: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"打开文本文件时发生错误: {str(e)}")

    def open_image_file(self, file_path):
        """打开图片文件"""
        from PIL import Image
        image = Image.open(file_path)
        image.show()

    def open_other_file(self, file_path):
        """打开其他类型文件"""
        QMessageBox.information(self, "不支持的文件类型", f"暂不支持打开 {os.path.basename(file_path)} 格式的文件")

    def open_file_dir(self, file_path):
        """打开文件所在目录"""
        if not file_path:
            QMessageBox.warning(self, "错误", "无法获取文件路径")
            return

        # 移除所有开头的 'output/'
        while file_path.startswith('output/'):
            file_path = file_path[7:]

        # 获取当前工作目录
        current_dir = os.getcwd()
        
        # 构建完整路径
        full_path = os.path.normpath(os.path.join(current_dir, 'output', file_path))
        
        print(f"尝试打开目录: {full_path}")
        if os.path.exists(full_path):
            # 在Windows上使用explorer选中文件
            subprocess.run(['explorer', '/select,', full_path])
        else:
            QMessageBox.warning(self, "文件不存在", f"文件 {file_path} 不存在")

    def delete_selected_file(self, file_path):
        """删除选中的文件"""
        try:
            if self.file_manager.delete_file(file_path):
                print(f"已删除文件：{file_path}")
                self.update_file_list()
                QMessageBox.information(self, "删除成功", f"文件 {os.path.basename(file_path)} 已成功删除")
            else:
                QMessageBox.warning(self, "删除失败", f"无法删除文件 {os.path.basename(file_path)}")
        except Exception as e:
            print(f"删除文件时发生错误: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"删除文件时发生错误: {str(e)}")

    def load_plugins(self):
        """加载插件"""
        plugins = {}
        plugin_dir = "extensions"
        
        def load_plugin_from_file(file_path):
            try:
                module_name = os.path.splitext(os.path.basename(file_path))[0]
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module.__name__] = module
                spec.loader.exec_module(module)
                if hasattr(module, "plugin_info"):
                    category = module.plugin_info.get("category", "其他")
                    if category not in plugins:
                        plugins[category] = {}
                    plugins[category][module.plugin_info["title"]] = {
                        "module": module,
                        "info": module.plugin_info,
                        "file_path": file_path
                    }
                    logging.info(f"成功加载插件: {file_path}")
                else:
                    logging.warning(f"插件文件 {file_path} 缺少 plugin_info")
            except Exception as e:
                logging.error(f"加载插件 {file_path} 时出错: {str(e)}")
                logging.error(traceback.format_exc())

        for root, dirs, files in os.walk(plugin_dir):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    load_plugin_from_file(file_path)

        return plugins

    def reload_plugins(self):
        """重新加载插件"""
        self.plugins = self.load_plugins()
        QMessageBox.information(self, "插件重新加载", "所有插件已重新加载")

    def execute_plugin(self, file_path, plugin_data):
        """执行插件"""
        print(f"执行插件，文件路径: {file_path}")  # 调试信息

        try:
            # 获取插件文件路径
            plugin_file_path = plugin_data["file_path"]
            print(f"插件文件路径: {plugin_file_path}")  # 调试信息
            
            # 使用 importlib.util.spec_from_file_location 重新加载模块
            spec = importlib.util.spec_from_file_location(plugin_data["module"].__name__, plugin_file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 更新 sys.modules
            sys.modules[plugin_data["module"].__name__] = module
            
            # 执行插件的run函数
            module.run(file_path)
            
            logging.info(f"成功执行插件: {plugin_data['info']['title']}")
        except Exception as e:
            print(f"执行插件时发生错误: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "插件执行错误", f"执行插件时发生错误: {str(e)}")

    def closeEvent(self, event):
        """关闭事件处理"""
        for viewer in self.viewers:
            viewer.close()
        self.viewers.clear()
        super().closeEvent(event)

    def show_sort_menu(self):
        """显示排序菜单"""
        menu = QMenu()
        menu.addAction("按名称排序", lambda: self.file_tree.sortItems(0, Qt.AscendingOrder))
        menu.addAction("按大小排序", lambda: self.file_tree.sortItems(1, Qt.AscendingOrder))
        menu.addAction("按修改日期排序", lambda: self.file_tree.sortItems(2, Qt.AscendingOrder))
        menu.exec(QCursor.position().toPoint())
