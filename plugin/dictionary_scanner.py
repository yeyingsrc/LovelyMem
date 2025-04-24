import os
import re
import json
import logging
from pathlib import Path
from plugin.dictionary_manager import DictionaryManager

logger = logging.getLogger(__name__)

class DictionaryScanner:
    """字典扫描器，用于在文件中快速检测字典内容"""
    
    def __init__(self):
        """初始化字典扫描器"""
        self.dict_manager = DictionaryManager()
        self.dict_manager.load_all_dictionaries()
        
    def scan_file(self, file_path, progressor_callback=None):
        """
        扫描文件，查找匹配字典条目的内容
        
        参数:
            file_path (str): 文件路径
            progressor_callback (function): 进度回调函数，接受(dict_item, matched_string, line_num, line_content)参数
            
        返回:
            dict: 键为字典条目，值为包含匹配信息的列表
        """
        results = {}
        total_items = 0
        processed_items = 0
        
        # 获取文件名（用于模式匹配）
        import os
        file_name = os.path.basename(file_path)
        
        # 计算总字典条目数
        for dict_name, dictionary in self.dict_manager.dictionaries.items():
            total_items += len(dictionary)
        
        # 辅助函数：标准化内容中的逗号和空格
        def normalize_content(content):
            # 将逗号后的空格标准化（移除所有逗号后的空格）
            if isinstance(content, str):
                return re.sub(r',\s+', ',', content)
            return content
        
        try:
            for dict_name, dictionary in self.dict_manager.dictionaries.items():
                # 预先筛选适用于该文件名的字典条目
                applicable_items = []
                for item in dictionary.values():
                    if item.match_file(file_name):
                        applicable_items.append(item)
                    processed_items += 1
                
                # 如果没有适用的条目，跳过此字典
                if not applicable_items:
                    continue
                
                if self.is_binary_file(file_path):
                    # 二进制文件扫描
                    with open(file_path, 'rb') as file:
                        content = file.read()
                        for item in applicable_items:
                            # 对二进制文件，只支持简单的二进制匹配
                            item_content = item.content
                            if item.type_name == "正则表达式":
                                # 对于正则表达式，跳过二进制文件的匹配
                                continue
                            
                            # 将字符串内容转换为二进制格式进行匹配
                            try:
                                if isinstance(item_content, str):
                                    binary_content = item_content.encode('utf-8')
                                else:
                                    binary_content = item_content
                                
                                matches = self.find_all_positions(content, binary_content)
                                if matches:
                                    if item not in results:
                                        results[item] = []
                                    
                                    for pos in matches:
                                        match_info = {
                                            'position': pos,
                                            'match': binary_content,
                                            'line_num': -1,  # 二进制文件没有行号
                                            'line_content': f"Binary match at position {pos}"
                                        }
                                        results[item].append(match_info)
                                        
                                        # 回调进度
                                        if progressor_callback:
                                            progressor_callback(item, binary_content, -1, f"Binary match at position {pos}")
                            except Exception as e:
                                logger.error(f"二进制匹配出错: {e}")
                else:
                    # 文本文件扫描
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                        for line_num, line in enumerate(file, 1):
                            for item in applicable_items:
                                item_content = item.content
                                
                                if item.type_name == "正则表达式":
                                    # 正则表达式匹配
                                    try:
                                        pattern = re.compile(item_content)
                                        matches = pattern.finditer(line)
                                        for match in matches:
                                            if item not in results:
                                                results[item] = []
                                            
                                            match_info = {
                                                'match': match.group(),
                                                'line_num': line_num,
                                                'line_content': line.strip()
                                            }
                                            results[item].append(match_info)
                                            
                                            # 回调进度
                                            if progressor_callback:
                                                progressor_callback(item, match.group(), line_num, line.strip())
                                    except Exception as e:
                                        logger.error(f"正则表达式匹配出错: {e}")
                                else:
                                    # 普通字符串匹配
                                    if item.is_exact_match:
                                        # 精确匹配模式：查找完整单词或数值
                                        import re
                                        # 标准化字典项内容和待匹配行
                                        normalized_item_content = normalize_content(item_content)
                                        normalized_line = normalize_content(line)
                                        
                                        # 如果内容包含逗号，将其拆分为多个模式进行匹配
                                        if ',' in normalized_item_content:
                                            items_to_match = [item.strip() for item in normalized_item_content.split(',')]
                                            for single_item in items_to_match:
                                                if single_item:  # 跳过空项
                                                    pattern = r'\b' + re.escape(single_item) + r'\b'
                                                    for match in re.finditer(pattern, normalized_line):
                                                        if item not in results:
                                                            results[item] = []
                                                        
                                                        match_info = {
                                                            'match': match.group(),
                                                            'line_num': line_num,
                                                            'line_content': line.strip()
                                                        }
                                                        results[item].append(match_info)
                                                        
                                                        # 回调进度
                                                        if progressor_callback:
                                                            progressor_callback(item, match.group(), line_num, line.strip())
                                        else:
                                            # 单个项目的精确匹配
                                            pattern = r'\b' + re.escape(normalized_item_content) + r'\b'
                                            for match in re.finditer(pattern, normalized_line):
                                                if item not in results:
                                                    results[item] = []
                                                
                                                match_info = {
                                                    'match': match.group(),
                                                    'line_num': line_num,
                                                    'line_content': line.strip()
                                                }
                                                results[item].append(match_info)
                                                
                                                # 回调进度
                                                if progressor_callback:
                                                    progressor_callback(item, match.group(), line_num, line.strip())
                                    else:
                                        # 普通包含匹配
                                        if item_content in line:
                                            if item not in results:
                                                results[item] = []
                                            
                                            match_info = {
                                                'match': item_content,
                                                'line_num': line_num,
                                                'line_content': line.strip()
                                            }
                                            results[item].append(match_info)
                                            
                                            # 回调进度
                                            if progressor_callback:
                                                progressor_callback(item, item_content, line_num, line.strip())
        except Exception as e:
            logger.error(f"扫描文件出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return results
    
    def is_binary_file(self, file_path):
        """
        检测文件是否为二进制文件
        
        参数:
            file_path (str): 文件路径
            
        返回:
            bool: 如果是二进制文件返回True，否则返回False
        """
        # 通过扩展名判断常见二进制文件
        binary_extensions = ['.exe', '.bin', '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.lzma']
        
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext in binary_extensions:
            return True
        
        # 尝试读取文件前4KB，检测是否为二进制
        try:
            with open(file_path, 'rb') as f:
                data = f.read(4096)
                
            # 检查是否包含NULL字节，常见的二进制文件通常包含NULL字节
            if b'\x00' in data:
                return True
            
            # 检查是否为UTF-8编码
            try:
                data.decode('utf-8')
                return False
            except UnicodeDecodeError:
                pass
            
            # 检查是否为其他常见编码
            for encoding in ['gbk', 'gb2312', 'latin-1']:
                try:
                    data.decode(encoding)
                    return False
                except UnicodeDecodeError:
                    continue
            
            return True
        except:
            return False
    
    def find_all_positions(self, content, pattern):
        """
        在二进制数据中查找所有匹配模式的位置
        
        参数:
            content (bytes): 二进制数据
            pattern (bytes): 匹配模式
            
        返回:
            list: 匹配位置列表
        """
        positions = []
        pos = 0
        while True:
            pos = content.find(pattern, pos)
            if pos == -1:
                break
            positions.append(pos)
            pos += 1
        
        return positions

# 直接从命令行运行此文件时进行测试
if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("用法: python dictionary_scanner.py <文件路径>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    scanner = DictionaryScanner()
    results = scanner.scan_file(file_path)
    
    if "error" in results:
        print(f"错误: {results['error']}")
    else:
        print(f"扫描结果: {json.dumps(results, ensure_ascii=False, indent=2)}")
