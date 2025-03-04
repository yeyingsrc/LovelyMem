import subprocess,os
import yaml
from extensions.front.openfile import OpenFile
plugin_info = {
    "title": "Eventlog转CSV",  
    "description": "将Eventlog转CSV",
    "usage": "选择一个Eventlog文件,然后点击此插件",
    "category": "Windows日志"
}
file_analyzer = OpenFile()
def get_evtx_ecmd_path():
    with open('config/base_config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config['other_tools']['EvtxECmd']['path']

def run(file_path):
    if not file_path.lower().endswith('.evtx'):
        print("错误：只允许打开.evtx文件")
        return
    evtx_ecmd_path = get_evtx_ecmd_path()
    output_csv = file_path.replace('.evtx', '.csv')
    #文件名
    filename = os.path.basename(output_csv)
    subprocess.run([evtx_ecmd_path, '-f', file_path, '--csv', "output", '--csvf', filename],shell=False)
    
    openpath = os.path.join("output",filename)
    file_analyzer.run(openpath)