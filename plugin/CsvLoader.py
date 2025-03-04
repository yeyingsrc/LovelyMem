from PySide6.QtCore import QObject, Signal
import pandas as pd

class CsvLoader(QObject):
    data_loaded = Signal(object)  # 发送 DataFrame
    progress_updated = Signal(int)
    finished = Signal()

    def __init__(self, path, chunk_size=10000):
        super().__init__()
        self.path = path
        self.chunk_size = chunk_size

    def load_csv(self):
        try:
            # 获取文件总行数
            total_rows = sum(1 for _ in open(self.path, 'r', encoding='utf-8'))
            
            # 使用 pandas 分块读取 CSV 文件
            for i, chunk in enumerate(pd.read_csv(self.path, chunksize=self.chunk_size, low_memory=False)):
                self.data_loaded.emit(chunk)
                progress = min(100, int((i * self.chunk_size + len(chunk)) / total_rows * 100))
                self.progress_updated.emit(progress)

            self.progress_updated.emit(100)
        except Exception as e:
            print(f"Error loading CSV: {str(e)}")
        finally:
            self.finished.emit()
