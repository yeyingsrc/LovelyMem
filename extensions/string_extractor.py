import re
import os
import csv

plugin_info = {
    "title": "字符串提取", 
    "description": "从文件中提取可打印字符串",
    "usage": "选择一个文件,然后点击此插件",
    "category": "文件分析"
}

def run(file_path):
    with open(file_path, 'rb') as f:
        content = f.read()
    
    strings = re.findall(b'[\x20-\x7E]{4,}', content)
    
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'extracted_strings.csv')
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Index', 'String'])
        for index, s in enumerate(strings, 1):
            writer.writerow([index, s.decode(errors='replace')])
    
    print(f"已提取 {len(strings)} 个字符串并保存到 {output_file}")
