plugin_info = {
    "title": "使用RegistryExplorer打开该注册表", 
    "description": "使用RegistryExplorer打开注册表",
    "usage": "选择一个.reg注册表文件,然后点击此插件",
    "category": "注册表"
}
import yaml
import subprocess
import os

def get_registry_explorer_path():
    with open('config/base_config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config['other_tools']['RegistryExplorer']['path']

def run(file_path):
    if not file_path.lower().endswith(('.reg', '.reghive')):
        print("错误：只允许打开.reg和.reghive文件")
        return
    
    registry_explorer_path = get_registry_explorer_path()
    subprocess.Popen([registry_explorer_path, file_path])
