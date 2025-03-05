import os
import re
import time
import binascii

from PySide6.QtCore import QObject, Signal


class QuickCheckWorker(QObject):
    finished = Signal(list)  # 修改信号，直接传递结果列表
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
            results = self.quick_check.run(self.image_path, self.progress.emit, self.check_interruption)
            if not self.is_interrupted:
                self.progress.emit(100)  # 确保进度达到100%
                self.finished.emit(results)  # 发送结果列表
        except Exception as e:
            self.error.emit(str(e))

    def requestInterruption(self):
        self.is_interrupted = True

    def check_interruption(self):
        return self.is_interrupted


class QuickCheck:
    def __init__(self, regex=None):
        default_pattern = r"flag{.+}|666c6167\w+|ZmxhZ[\w=]+|&#102.+"
        self.patterns = [
            regex if regex else default_pattern,
        ]
        self.compiled_patterns = [re.compile(pattern.encode("utf-8") if isinstance(pattern, str) else pattern) for pattern in self.patterns]
        self.context_bytes = 16  # 匹配结果前后的上下文字节数

    def extract_strings(self, image_path, callback=None, check_interruption=None):
        file_size = os.path.getsize(image_path)
        chunk_size = 1024 * 1024  # 1MB chunks
        results = []
        processed_bytes = 0
        last_update_time = time.time()

        with open(image_path, "rb") as f:
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
                        # 获取匹配结果
                        match_bytes = match.group()
                        decoded_match = match.group().decode("utf-8", errors="ignore")
                        
                        # 计算在整个文件中的绝对位置
                        absolute_position = processed_bytes + match.start()
                        
                        # 获取上下文字节
                        start_context = max(0, match.start() - self.context_bytes)
                        end_context = min(len(chunk), match.end() + self.context_bytes)
                        context_data = chunk[start_context:end_context]
                        
                        # 转换为十六进制
                        hex_data = binascii.hexlify(context_data).decode('ascii')
                        
                        # 添加到结果
                        results.append({
                            'match': decoded_match,
                            'position': absolute_position,
                            'hex': hex_data,
                            'raw_data': context_data,
                            'match_start': match.start() - start_context,  # 相对于上下文的起始位置
                            'match_length': match.end() - match.start()    # 匹配长度
                        })

                processed_bytes += len(chunk)
                current_time = time.time()
                if current_time - last_update_time > 0.1:  # 每0.1秒更新一次进度
                    progress = (processed_bytes / file_size) * 100
                    if callback:
                        callback(progress)
                    last_update_time = current_time

        return results

    def write_results_to_file(self, results, image_path):
        import csv
        
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        base_name = os.path.basename(image_path)
        output_file = os.path.join(output_dir, f"{os.path.splitext(base_name)[0]}_results.csv")

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # 写入CSV表头
            writer.writerow(["位置(十六进制)", "匹配项", "十六进制数据", "ASCII数据", "大小(字节)"])
            
            # 写入每条搜索结果
            for result in results:
                position = result['position']
                match = result['match']
                hex_data = result['hex']
                raw_data = result['raw_data']
                match_length = result['match_length']
                
                # 生成ASCII表示
                ascii_text = "".join(chr(b) if 32 <= b <= 126 else "." for b in raw_data)
                
                # 格式化十六进制数据以便阅读
                formatted_hex = " ".join(hex_data[j:j+2] for j in range(0, len(hex_data), 2))
                
                writer.writerow([
                    f"{position:08X}",  # 位置（十六进制格式）
                    match,              # 匹配项
                    formatted_hex,      # 格式化的十六进制数据
                    ascii_text,         # ASCII表示
                    match_length        # 匹配长度（字节）
                ])
        
        print(f"结果已保存到: {output_file}")
        return output_file

    def run(self, image_path, progress_callback=None, check_interruption=None):
        try:
            results = self.extract_strings(image_path, progress_callback, check_interruption)
            if not (check_interruption and check_interruption()):
                self.write_results_to_file(results, image_path)
            return results  # 返回结果列表
        except Exception as e:
            print(f"处理过程中发生错误: {str(e)}")
            return []
