import logging
import os
import sys
import traceback

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon, QPalette, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from core.output_redirector import setup_output_redirection
from ui.main_window import MainWindow

def main():
    # 确保必要的目录存在
    for directory in ['db', 'output', 'packed_files', 'config']:
        os.makedirs(directory, exist_ok=True)
        
    try:
        # 检查是否已存在 QApplication 实例
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        else:
            #print("警告：QApplication 实例已存在，使用现有实例。")
            pass

        app.setWindowIcon(QIcon("res\logo.ico"))
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

        QTimer.singleShot(100, show_main_window)
        
        # 检测系统是否处于深色模式
        is_dark_mode = app.palette().color(QPalette.Window).lightness() < 128

        sys.exit(app.exec())
    except Exception as e:
        error_msg = f"Unhandled exception in main: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        print(error_msg, file=sys.__stderr__)

if __name__ == "__main__":
    main()