import os
import re

def contains_chinese(text):
    """检查字符串是否包含中文字符"""
    return bool(re.search(r'[\u4e00-\u9fa5]', text))

def check_directory_for_chinese(directory):
    """检查当前目录中的文件夹名是否包含中文字符"""
    found_chinese = False
    try:
        for dir_name in os.listdir(directory):
            full_dir_name = os.path.join(directory, dir_name)
            if os.path.isdir(full_dir_name) and contains_chinese(dir_name):
                print(f"目录名包含中文: {full_dir_name}")
                found_chinese = True
        if not found_chinese:
            print("未发现包含中文字符的目录名")
            return True
    except Exception as e:
        print(f"错误: {e}")
        return False

if __name__ == "__main__":
    current_directory = os.getcwd()
    check_directory_for_chinese(current_directory)
