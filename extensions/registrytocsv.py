plugin_info = {
    "title": "注册表转表格", 
    "description": "将注册表导出为CSV格式",
    "usage": "选择一个注册表文件,然后点击此插件",
    "category": "注册表"
}

import csv
from Registry import Registry
import os

def run(file_path):
    try:
        # 将注册表文件转换为CSV文件
        parse_registry_hive(file_path)
    except Registry.RegistryParse.ParseException as e:
        print(f"解析注册表文件时发生错误: {str(e)}")
        print("请确保选择的是有效的注册表文件。")
    except Exception as e:
        print(f"执行插件时发生未知错误: {str(e)}")

def parse_registry_hive(file_path):
    try:
        reg = Registry.Registry(file_path)
    except Registry.RegistryParse.ParseException as e:
        raise e
    file_name = os.path.basename(file_path)
    if "reghive" in file_name:
        output_name = file_name.rsplit('-', 1)[1].replace('.reghive', '.csv')
        
    elif file_name.startswith("registry."):
        output_name = file_name.rsplit('.', 2)[1] + ".csv"
    else:
        output_name = file_name.rsplit('.', 1)[0] + ".csv"
    
    # 创建输出CSV文件
    output_csv = os.path.join("output", output_name)
    
    with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Path", "Name", "Value", "Type"])

        def recurse_key(key, path=""):
            for subkey in key.subkeys():
                recurse_key(subkey, path + "\\" + subkey.name())

            for value in key.values():
                try:
                    # 尝试对名称进行编码处理，避免UnicodeDecodeError
                    name = value.name().encode('utf-8', errors='replace').decode('utf-8')
                except UnicodeDecodeError as e:
                    # 如果遇到错误，记录错误并跳过该值
                    name = f"Error decoding name: {e}"
                
                writer.writerow([
                    path + "\\" + key.name(),
                    name,
                    value.value(),
                    value.value_type_str()
                ])

        recurse_key(reg.root())
    
    print(f"注册表文件已成功转换为CSV格式: {output_csv}")
