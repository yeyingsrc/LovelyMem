import re
import mmap
import os
import time
from PySide6.QtCore import QObject, Signal

class QuickCheckWorker(QObject):
    finished = Signal()
    progress = Signal(float)
    error = Signal(str)

    def __init__(self, image_path, regex=None):
        super().__init__()
        self.image_path = image_path
        self.quick_check = QuickCheck(regex)
        self.is_interrupted = False

    def run(self):
        try:
            self.is_interrupted = False
            self.quick_check.run(self.image_path, self.progress.emit, self.check_interruption)
            if not self.is_interrupted:
                self.progress.emit(100)  # 确保进度达到100%
                self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def requestInterruption(self):
        self.is_interrupted = True

    def check_interruption(self):
        return self.is_interrupted

class QuickCheck:
    def __init__(self, regex=None):
        default_pattern = r'flag{.+}|666c6167\w+|ZmxhZ[\w=]+|&#102.+'
        self.patterns = [
            regex if regex else default_pattern,
        ]
        self.compiled_patterns = [
            re.compile(pattern.encode('utf-8') if isinstance(pattern, str) else pattern)
            for pattern in self.patterns
        ]

    def extract_strings(self, image_path, callback=None, check_interruption=None):
        file_size = os.path.getsize(image_path)
        chunk_size = 1024 * 1024  # 1MB chunks
        results = []
        processed_bytes = 0
        last_update_time = time.time()

        with open(image_path, 'rb') as f:
            while True:
                if check_interruption and check_interruption():
                    break

                chunk = f.read(chunk_size)
                if not chunk:
                    break

                for pattern in self.compiled_patterns:
                    if check_interruption and check_interruption():
                        break
                    matches = pattern.finditer(chunk)
                    for match in matches:
                        decoded_match = match.group().decode('utf-8', errors='ignore')
                        # 调整位置以反映在整个文件中的实际位置
                        absolute_position = processed_bytes + match.start()
                        results.append((decoded_match, absolute_position))

                processed_bytes += len(chunk)
                current_time = time.time()
                if current_time - last_update_time > 0.1:  # 每0.1秒更新一次进度
                    progress = (processed_bytes / file_size) * 100
                    if callback:
                        callback(progress)
                    last_update_time = current_time

        return results

    def write_results_to_file(self, results, image_path):
        output_dir = 'output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        base_name = os.path.basename(image_path)
        output_file = os.path.join(output_dir, f"{os.path.splitext(base_name)[0]}_results.txt")

        with open(output_file, 'w', encoding='utf-8') as f:
            for result, position in results:
                f.write(f"匹配: {result}, 位置: {position}\n")

        print(f"结果已保存到: {output_file}")

    def run(self, image_path, progress_callback=None, check_interruption=None):
        try:
            results = self.extract_strings(image_path, progress_callback, check_interruption)
            if not (check_interruption and check_interruption()):
                self.write_results_to_file(results, image_path)
            return True
        except Exception as e:
            print(f"处理过程中发生错误: {str(e)}")
            return False
