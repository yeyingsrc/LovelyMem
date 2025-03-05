import logging
import os
import sys
import traceback
import json
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon, QPalette, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from core.output_redirector import setup_output_redirection
from ui.main_window import MainWindow
from ui.welcome_dialog import WelcomeDialog

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
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
    
    # 加载用户设置
    try:
        with open(user_settings_file, 'r', encoding='utf-8') as f:
            user_settings = json.load(f)
    except Exception as e:
        logger.error(f"加载用户设置失败: {e}")
        user_settings = {"first_run_reminder": True}
        
    try:
        # 检查是否已存在 QApplication 实例
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        else:
            #print("警告：QApplication 实例已存在，使用现有实例。")
            pass

        app.setWindowIcon(QIcon(r"res\logo.ico"))
        splash_pix = QPixmap(r"res/logo_200.png")
        splash = QSplashScreen(splash_pix)
        splash.show()
        # 创建主窗口
        window = MainWindow()
        setup_output_redirection(window)

        # 使用定时器在0.5秒后关闭启动画面并显示主窗口
        def show_main_window():
            splash.close()
            window.show()
            
            # 检查是否需要显示首次使用提醒
            show_welcome = user_settings.get("first_run_reminder", True)
            if show_welcome:
                QTimer.singleShot(500, lambda: show_first_run_reminder(window))

        QTimer.singleShot(100, show_main_window)
        
        # 检测系统是否处于深色模式
        is_dark_mode = app.palette().color(QPalette.Window).lightness() < 128

        sys.exit(app.exec())
    except Exception as e:
        error_msg = f"Unhandled exception in main: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        print(error_msg, file=sys.__stderr__)

def show_first_run_reminder(window):
    """显示首次使用提醒对话框"""
    welcome_dialog = WelcomeDialog(window)
    welcome_dialog.setMinimumSize(600, 500)
    
    # 计算居中位置
    screen_geometry = window.screen().geometry()
    dialog_geometry = welcome_dialog.geometry()
    x = screen_geometry.center().x() - dialog_geometry.width() // 2
    y = screen_geometry.center().y() - dialog_geometry.height() // 2
    welcome_dialog.move(x, y)
    
    welcome_dialog.exec()
    # 注意：设置保存已经在WelcomeDialog.accept()方法中处理

if __name__ == "__main__":
    main()