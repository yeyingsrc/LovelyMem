import os
import re
import time
import binascii
import mmap
import concurrent.futures
from threading import Lock

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
        self.use_mmap = True  # 默认使用内存映射
        self.num_threads = 4  # 默认线程数
        self.progress_lock = Lock()  # 用于线程安全地更新进度

    def process_chunk(self, chunk, chunk_offset, patterns, file_size=None, check_interruption=None):
        """处理一个数据块，寻找匹配"""
        results = []
        
        for pattern in patterns:
            if check_interruption and check_interruption():
                break
                
            matches = pattern.finditer(chunk)
            for match in matches:
                # 获取匹配结果
                match_bytes = match.group()
                decoded_match = match.group().decode("utf-8", errors="ignore")
                
                # 计算在整个文件中的绝对位置
                absolute_position = chunk_offset + match.start()
                
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
                
        return results

    def extract_strings(self, image_path, callback=None, check_interruption=None):
        file_size = os.path.getsize(image_path)
        results = []
        last_update_time = time.time()
        total_progress = 0

        # 更新进度的辅助函数
        def update_progress(progress_increment):
            nonlocal total_progress, last_update_time
            with self.progress_lock:
                total_progress += progress_increment
                current_time = time.time()
                if current_time - last_update_time > 0.1:  # 每0.1秒更新一次进度
                    if callback:
                        callback(min(total_progress, 99.9))  # 确保不超过100%
                    last_update_time = current_time

        if self.use_mmap:
            # 使用内存映射方式处理文件
            try:
                with open(image_path, "rb") as f:
                    # 创建内存映射
                    with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                        # 如果启用多线程，则将文件分成多个块并行处理
                        if self.num_threads > 1:
                            chunk_size = len(mmapped_file) // self.num_threads
                            chunks = []
                            
                            # 准备文件块
                            for i in range(self.num_threads):
                                start = i * chunk_size
                                end = start + chunk_size if i < self.num_threads - 1 else len(mmapped_file)
                                
                                # 读取块数据
                                mmapped_file.seek(start)
                                chunk_data = mmapped_file.read(end - start)
                                chunks.append((chunk_data, start))
                            
                            # 使用线程池并行处理
                            with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
                                futures = []
                                for chunk_data, offset in chunks:
                                    future = executor.submit(
                                        self.process_chunk,
                                        chunk_data,
                                        offset,
                                        self.compiled_patterns,
                                        file_size,
                                        check_interruption
                                    )
                                    futures.append(future)
                                
                                # 收集结果
                                completed = 0
                                for future in concurrent.futures.as_completed(futures):
                                    if check_interruption and check_interruption():
                                        break
                                    chunk_results = future.result()
                                    results.extend(chunk_results)
                                    
                                    # 更新进度
                                    completed += 1
                                    progress_increment = (completed / len(futures)) * 100
                                    update_progress(progress_increment)
                                    
                        else:
                            # 单线程模式下对整个映射文件进行处理
                            for pattern in self.compiled_patterns:
                                if check_interruption and check_interruption():
                                    break
                                    
                                # 搜索整个映射文件
                                offset = 0
                                while True:
                                    if check_interruption and check_interruption():
                                        break
                                    
                                    # 在当前位置查找匹配
                                    match = pattern.search(mmapped_file, offset)
                                    if not match:
                                        break
                                        
                                    # 获取匹配结果
                                    match_bytes = match.group()
                                    decoded_match = match.group().decode("utf-8", errors="ignore")
                                    
                                    # 计算绝对位置
                                    absolute_position = match.start()
                                    
                                    # 获取上下文字节
                                    start_context = max(0, match.start() - self.context_bytes)
                                    end_context = min(file_size, match.end() + self.context_bytes)
                                    
                                    # 定位到上下文起始位置并读取数据
                                    mmapped_file.seek(start_context)
                                    context_data = mmapped_file.read(end_context - start_context)
                                    
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
                                    
                                    # 移动到下一个搜索位置
                                    offset = match.end()
                                    
                                    # 更新进度
                                    current_progress = (offset / file_size) * 100
                                    update_progress(current_progress)
                return results
            except Exception as e:
                print(f"使用内存映射时出错: {str(e)}，回退到标准模式")
                # 如果内存映射失败，回退到标准模式
                self.use_mmap = False
        
        # 标准模式处理文件（当内存映射禁用或失败时）
        chunk_size = 1024 * 1024  # 1MB chunks
        
        # 对于多线程模式，我们先准备所有块
        if self.num_threads > 1:
            chunks = []
            offset = 0
            
            with open(image_path, "rb") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    chunks.append((chunk, offset))
                    offset += len(chunk)
            
            # 使用线程池并行处理块
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
                futures = []
                for chunk_data, chunk_offset in chunks:
                    future = executor.submit(
                        self.process_chunk,
                        chunk_data,
                        chunk_offset,
                        self.compiled_patterns,
                        file_size,
                        check_interruption
                    )
                    futures.append(future)
                
                # 收集结果
                completed = 0
                for future in concurrent.futures.as_completed(futures):
                    if check_interruption and check_interruption():
                        break
                    chunk_results = future.result()
                    results.extend(chunk_results)
                    
                    # 更新进度
                    completed += 1
                    progress_increment = (completed / len(futures)) * 100
                    update_progress(progress_increment)
        else:
            # 单线程模式
            processed_bytes = 0
            
            with open(image_path, "rb") as f:
                while True:
                    if check_interruption and check_interruption():
                        break

                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    chunk_results = self.process_chunk(chunk, processed_bytes, self.compiled_patterns, file_size, check_interruption)
                    results.extend(chunk_results)
                    
                    processed_bytes += len(chunk)
                    progress = (processed_bytes / file_size) * 100
                    update_progress(progress)

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
