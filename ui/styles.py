import sys
import logging,json
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from core.config_manager import get_saved_theme  # 添加这行
import urllib.parse

logger = logging.getLogger(__name__)

# 在文件顶部添加这些全局变量的声明
global background_color, text_color, button_bg_color, button_text_color
global button_hover_color, border_color, group_title_bg_color
global cmd_output_bg_color, cmd_output_text_color,newtable_widget_style
global theme_button_color, minimize_button_color, maximize_button_color, close_button_color
global current_font_family

# 初始化这些变量
background_color = "rgba(255, 255, 255, 0.8)"
text_color = "black"
button_bg_color = "rgba(240, 240, 240, 0.9)"
button_text_color = "#333333"
button_hover_color = "rgba(220, 220, 220, 0.9)"
border_color = "#cccccc"
group_title_bg_color = "rgba(240, 240, 240, 0.9)"
cmd_output_bg_color = "rgba(250, 250, 250, 0.9)"
cmd_output_text_color = "#333333"

# 从user_settings.json读取字体设置
try:
    with open("config/user_settings.json", "r", encoding="utf-8") as f:
        user_settings = json.load(f)
    font_settings = user_settings.get("font_settings", {})
    current_font_family = font_settings.get("font_family", "Microsoft YaHei")
except Exception as e:
    logger.warning(f"无法读取字体设置: {e}")
    current_font_family = "Microsoft YaHei"

# 检测系统是否处于深色模式
def is_dark_mode():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app.palette().color(QPalette.Window).lightness() < 128

# 预设配色方案
color_schemes = json.load(open("config/style.json", "r", encoding="utf-8"))


def get_color_scheme(scheme_name, is_dark):
    mode = "dark" if is_dark else "light"
    return color_schemes.get(scheme_name, color_schemes["默认"])[mode]

def apply_color_scheme(scheme_name, is_dark):
    global background_color, text_color, button_bg_color, button_text_color
    global button_hover_color, border_color, group_title_bg_color
    global cmd_output_bg_color, cmd_output_text_color
    global theme_button_color, minimize_button_color, maximize_button_color, close_button_color
    global current_font_family

    scheme = color_schemes[scheme_name]["dark" if is_dark else "light"]
    
    background_color = scheme["background_color"]
    text_color = scheme["text_color"]
    button_bg_color = scheme["button_bg_color"]
    button_text_color = scheme["button_text_color"]
    button_hover_color = scheme["button_hover_color"]
    border_color = scheme["border_color"]
    group_title_bg_color = scheme["group_title_bg_color"]
    cmd_output_bg_color = scheme["cmd_output_bg_color"]
    cmd_output_text_color = scheme["cmd_output_text_color"]
    
    # 设置四个特殊按钮的颜色
    global theme_button_color, minimize_button_color, maximize_button_color, close_button_color
    theme_button_color = "rgba(255, 223, 186, 0.9)"  # 深一点的黄色
    minimize_button_color = "rgba(198, 255, 198, 0.9)"  # 深一点的绿色
    maximize_button_color = "rgba(186, 225, 255, 0.9)"  # 深一点的蓝色
    close_button_color = "rgba(255, 204, 204, 0.9)"  # 深一点的红色
    
    # 更新所有样式
    update_styles()
    

def update_styles():
    global candy_background, common_font_style, button_style, tool_button_style
    global memprocfs_style, vol2_style, vol3_style, quick_check_style
    global main_window_style, splitter_style, tab_style, left_group_style
    global right_panel_style, cmd_output_style, newtable_widget_style
    global report_editor_style

    logger.info("Updating all styles")

    # 更新背景样式
    candy_background = f"background-color: {background_color};"
    # 更新通用字体样式
    common_font_style = f"""
        font-family: {current_font_family},"汉仪文黑-85W", "Microsoft YaHei", "SimHei", sans-serif;
        font-size: 13px;
        color: {text_color};
    """

    # 更新按钮样式
    button_style = f"""
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
    """

    # 更新工具按钮样式
    tool_button_style = f"""
        QToolButton {{
            background-color: {button_bg_color};
            color: {button_text_color};
            border: none;
            border-radius: 3px;
            padding: 5px;
        }}
        QToolButton:hover {{
            background-color: {button_hover_color};
        }}
        QToolButton::menu-indicator {{
            image: none;
        }}
    """

    # 更新各区域样式
    memprocfs_style = vol2_style = vol3_style = quick_check_style = f"""
        QWidget {{
            {candy_background}
            {common_font_style}
            border: 1px solid {border_color};
            border-radius: 5px;
        }}
        {button_style}
        {tool_button_style}
    """

    # 更新主窗口样式
    main_window_style = f"""
        QMainWindow {{
            {candy_background}
            {common_font_style}
            border: 1px solid {border_color};
            border-radius: 10px;
        }}
        {button_style}
        {tool_button_style}
    """

    # 更新分割器样式
    splitter_style = f"""
        QSplitter::handle {{
            background-color: {border_color};
        }}
        QSplitter::handle:hover {{
            background-color: {button_hover_color};
        }}
    """

    # 更新标签样式
    tab_style = f"""
        QTabWidget::pane {{
            border: 1px solid {border_color};
            background: {background_color};
            border-radius: 5px;
        }}
        QTabWidget::tab-bar {{
            alignment: left;
        }}
        QTabBar::tab {{
            background: {button_bg_color};
            border: 1px solid {border_color};
            border-right-color: {border_color};
            border-top-left-radius: 4px;
            border-bottom-left-radius: 4px;
            padding: 5px 0px;
            margin-bottom: 1px;
            min-height: 22px;
            max-height: 22px;
            min-width: 40px;
            max-width: 40px;
            {common_font_style}
            text-align: center;
            
            alignment: center;
        }}
        QTabBar::tab:selected, QTabBar::tab:hover {{
            background: {button_hover_color};
        }}
        QTabBar::tab:selected {{
            border-color: {border_color};
            border-right-color: {background_color};
        }}
        QTabBar::tab:!selected {{
            margin-left: 2px;
        }}
    """

    # 更新左侧分组和分组框样式
    left_group_style = f"""
        QGroupBox {{
            {candy_background}
            border: 1px solid {border_color};
            border-radius: 5px;
            margin-top: 10px;
            padding: 10px;
            color: {text_color};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 3px;
            background-color: {group_title_bg_color};
            color: {text_color};
        }}
    """

    # 更新右侧面板样式
    right_panel_style = f"""
        QWidget {{
            {candy_background}
            {common_font_style}
        }}
        QGroupBox {{
            border: 1px solid {border_color};
            border-radius: 5px;
            margin-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 3px;
            background-color: {group_title_bg_color};
            border: 1px solid {border_color};
            border-radius: 3px;
        }}
        {button_style}
        {tool_button_style}
        QListWidget, QTextEdit {{
            background-color: {background_color};
            border: 1px solid {border_color};
            border-radius: 3px;
        }}
        QComboBox {{
            background-color: {button_bg_color};
            color: {button_text_color};
            border: 1px solid {border_color};
            border-radius: 3px;
            padding: 1px 18px 1px 3px;
        }}
        QComboBox:hover {{
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
        QSplitter::handle {{
            background-color: {border_color};
        }}
        QSplitter::handle:hover {{
            background-color: {button_hover_color};
        }}
    """

    # 更新命令输出样式
    cmd_output_style = f"""
        QTextEdit {{
            background-color: {cmd_output_bg_color};
            color: {cmd_output_text_color};
            border: 1px solid {border_color};
            border-radius: 3px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 12px;
        }}
    """

    # 更新 NewtableWidget 的样式
    newtable_widget_style = f"""
        QWidget {{
            background-color: {background_color};
            color: {text_color};
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
        QTableWidget {{
            background-color: {background_color};
            color: {text_color};
            border: 1px solid {border_color};
        }}
        QTableWidget::item:selected {{
            background-color: {button_hover_color};
        }}
        QHeaderView::section {{
            background-color: {button_bg_color};
            color: {button_text_color};
            border: 1px solid {border_color};
        }}
        QLineEdit {{
            background-color: {background_color};
            color: {text_color};
            border: 1px solid {border_color};
            border-radius: 3px;
            padding: 2px;
        }}
        QListWidget {{
            background-color: {background_color};
            color: {text_color};
            border: 1px solid {border_color};
            border-radius: 3px;
        }}
        QGroupBox {{
            border: 1px solid {border_color};
            border-radius: 5px;
            margin-top: 10px;
            padding: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 3px;
            background-color: {group_title_bg_color};
        }}
    """

    # 添加 report_editor 样式
    global report_editor_style
    report_editor_style = f"""
        QWidget {{
            background-color: {background_color};
            color: {text_color};
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
        QTextEdit {{
            background-color: {cmd_output_bg_color};
            color: {cmd_output_text_color};
            border: 1px solid {border_color};
            border-radius: 3px;
        }}
        QComboBox, QLineEdit, QListWidget {{
            background-color: {button_bg_color};
            color: {button_text_color};
            border: 1px solid {border_color};
            border-radius: 3px;
            padding: 3px;
        }}
    """
    
    logger.debug("Styles updated")

# 确保在文件末尾调用这个函数
apply_color_scheme("默认", is_dark_mode())

# 在文件末尾添加这个函数
def get_current_theme():
    return get_saved_theme()
