import sys
import traceback
import logging
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QColor
from datetime import datetime
from weakref import ref

# 设置日志
logging.basicConfig(filename='error_log.txt', level=logging.ERROR, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OutputRedirector(QObject):
    output_written = Signal(str, QColor)

    def __init__(self, stream, color):
        super().__init__()
        self.stream = stream
        self.color = color
        self.main_window = None

    def set_main_window(self, main_window):
        self.main_window = ref(main_window)

    def write(self, text):
        try:
            self.stream.write(text)
            formatted_text = f"{text}"
            if self.main_window and self.main_window():
                # 使用 Qt.ConnectionType.QueuedConnection 确保在主线程中更新UI
                self.output_written.emit(formatted_text, self.color)
            else:
                # 如果main_window不存在，直接写入stderr
                sys.__stderr__.write(formatted_text)
        except Exception as e:
            error_msg = f"Error in OutputRedirector.write: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            sys.__stderr__.write(error_msg)

    def flush(self):
        try:
            self.stream.flush()
        except Exception as e:
            error_msg = f"Error in OutputRedirector.flush: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            sys.__stderr__.write(error_msg)

def setup_output_redirection(main_window):
    try:
        # 使用之前定义的颜色
        stdout_color = QColor(100, 100, 255)  # 亮蓝色
        stderr_color = QColor(255, 100, 100)  # 亮红色

        stdout_redirector = OutputRedirector(sys.stdout, stdout_color)
        stderr_redirector = OutputRedirector(sys.stderr, stderr_color)

        stdout_redirector.set_main_window(main_window)
        stderr_redirector.set_main_window(main_window)

        stdout_redirector.output_written.connect(main_window.update_cmd_output, Qt.ConnectionType.QueuedConnection)
        stderr_redirector.output_written.connect(main_window.update_cmd_output, Qt.ConnectionType.QueuedConnection)

        sys.stdout = stdout_redirector
        sys.stderr = stderr_redirector
        logger.info("输出重定向设置成功完成。")
    except Exception as e:
        error_msg = f"setup_output_redirection 中出错: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        sys.__stderr__.write(error_msg)
