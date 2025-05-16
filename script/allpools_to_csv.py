#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将 allpools.txt 转换为 CSV 格式
用法: python allpools_to_csv.py [输入文件路径] [输出文件路径]
如果未指定路径，默认从 ../output/allpools.txt 读取，输出到 ../output/allpools.csv
"""

import os
import sys
import csv
import re
from pathlib import Path

def convert_allpools_to_csv(input_file, output_file):
    """
    将 allpools.txt 文件转换为 CSV 格式
    
    Args:
        input_file (str): 输入文件路径
        output_file (str): 输出文件路径
    """
    print(f"正在将 {input_file} 转换为 {output_file}...")
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    
    # 读取输入文件并解析
    with open(input_file, 'r', encoding='utf-8') as f_in:
        lines = f_in.readlines()
    
    # 查找表头行
    header_index = -1
    for i, line in enumerate(lines):
        if '#' in line and 'Tag' in line and 'Address' in line and 'Size' in line:
            header_index = i
            break
    
    if header_index == -1:
        print("错误：未找到表头行")
        return False
    
    # 解析表头
    header_line = lines[header_index].strip()
    # 提取表头字段
    headers = re.findall(r'#\s+Tag|A|Address|Size|Type|Pool', header_line)
    # 清理表头字段
    headers = [h.strip() for h in headers]
    
    # 如果表头中有 '#  Tag'，将其替换为 'Index' 和 'Tag'
    if '#  Tag' in headers:
        headers[headers.index('#  Tag')] = 'Index'
        headers.insert(1, 'Tag')
    
    # 写入CSV文件
    with open(output_file, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.writer(f_out)
        writer.writerow(headers)
        
        # 跳过表头行和分隔线
        start_index = header_index + 2
        
        # 处理数据行
        for i in range(start_index, len(lines)):
            line = lines[i].strip()
            if not line:  # 跳过空行
                continue
            
            # 解析数据行
            # 使用正则表达式匹配固定宽度的字段
            parts = re.findall(r'\S+', line)
            if len(parts) >= 6:  # 确保至少有6个字段
                row = parts[:6]  # 取前6个字段
                writer.writerow(row)
    
    print(f"转换完成！CSV文件已保存到 {output_file}")
    return True

def main():
    # 设置默认路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_input = os.path.join(script_dir, "..", "output", "allpools.txt")
    default_output = os.path.join(script_dir, "..", "output", "allpools.csv")
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = default_input
    
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = default_output
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误：输入文件 {input_file} 不存在")
        return 1
    
    # 转换文件
    success = convert_allpools_to_csv(input_file, output_file)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
