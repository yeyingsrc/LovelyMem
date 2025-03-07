from plugin.config import config
import subprocess
import os, yaml
import pandas as pd
import json
import traceback
from PySide6.QtCore import QThread, Signal, QObject

from plugin.NewtableWidget import NewtableWidget
from plugin.QuicklyView import QuicklyView
from lovelyform import show_csv_viewer

class WorkerThread(QThread):
    task_completed = Signal(bool, str)

    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd

    def run(self):
        try:
            process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding='utf-8', 
                shell=False
            )
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                print(stdout)
                self.task_completed.emit(True, "任务成功完成")
            else:
                error_msg = (
                    f"命令执行失败，返回代码 {process.returncode}。\n输出: {stdout}\n错误: {stderr}"
                )
                print(error_msg)
                self.task_completed.emit(False, error_msg)
        except Exception as e:
            error_msg = f"发生错误: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            self.task_completed.emit(False, error_msg)


class Vol2Linux:
    def __init__(self, mem_path, profile):
        self.mem_path = mem_path
        self.profile = profile
        
    def readconfig(self):
        with open('config/base_config.yaml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        python27 = config['base_tools']['python27']['path']
        python27 = os.path.abspath(python27)
        volatility2 = config['tools']['volatility2_python']['path']
        volatility2_plugin = config['tools']['volatility2_plugin']['path']
        volatility2 = os.path.abspath(volatility2)
        volatility2_plugin = os.path.abspath(volatility2_plugin)
        return python27, volatility2, volatility2_plugin

    def construct_command(self, plugin, output_type='json'):
        self.python27, self.volatility2, self.volatility2_plugin = self.readconfig()
        output_file = f'output/output_vol2linux_{plugin}.{output_type}'
        cmd = [
            self.python27,
            self.volatility2,
            f'--plugin={self.volatility2_plugin}',
            '-f',
            self.mem_path,
            plugin,
            f'--output={output_type}',
            f'--output-file={output_file}'
        ]
        return cmd, output_file
    
    def construct_command_with_args(self, plugin, output_type='json', **kwargs):
        cmd, output_file = self.construct_command(plugin, output_type)
        for key, value in kwargs.items():
            cmd.append(f'-{key}')
        return cmd, output_file

    def json_to_csv(self, json_file):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            if 'rows' in data and 'columns' in data:
                df = pd.DataFrame(data['rows'], columns=data['columns'])
                csv_file = json_file.replace('.json', '.csv')
                df.to_csv(csv_file, index=False)
                print(f"[+] 成功将 {json_file} 转换为 {csv_file}")
                # 删除json文件
                os.remove(json_file)
            else:
                print(f"[!] {json_file} 不包含预期的数据，跳过转换")
        except Exception as e:
            print(f"[!] 转换 {json_file} 时出错: {str(e)}")


class Vol2LinuxPlugin(QObject):
    def __init__(self, mem_path):
        super().__init__()
        self.mem_path = mem_path
        self.profile = None
        self.workers = []
        self.open_windows = []
        self.python27, self.volatility2, self.volatility2_plugin = self.readconfig()
        self.default_profile = "LinuxUbuntu1604x64"  # 默认Linux profile

    def readconfig(self):
        with open('config/base_config.yaml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        python27 = config['base_tools']['python27']['path']
        python27 = os.path.abspath(python27)
        volatility2 = config['tools']['volatility2_python']['path']
        volatility2_plugin = config['tools']['volatility2_plugin']['path']
        volatility2 = os.path.abspath(volatility2)
        volatility2_plugin = os.path.abspath(volatility2_plugin)
        return python27, volatility2, volatility2_plugin

    def get_linux_profiles(self):
        """获取所有可用的Linux profiles"""
        try:
            cmd = [self.python27, self.volatility2, '--info']
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                profiles = []
                lines = stdout.split("\n")
                for line in lines:
                    if 'Linux' in line and 'Profile' in line:
                        # 提取profile名称
                        profile_name = line.strip().split()[0]
                        profiles.append(profile_name)
                return profiles
            else:
                print(f"[-] 获取Linux profiles时出错: {stderr}")
                return [self.default_profile]
        except Exception as e:
            print(f"[-] 获取Linux profiles时出错: {str(e)}")
            return [self.default_profile]

    def set_profile(self, profile):
        self.profile = profile
        print(f"[+] 已设置Linux Profile: {profile}")

    def run_plugin(self, plugin_name, display_name, output_type='json', show_result=True):
        if not self.profile:
            print("[-] 请先设置Linux Profile")
            return
            
        vol2linux = Vol2Linux(self.mem_path, self.profile)
        cmd, output_file = vol2linux.construct_command(plugin_name, output_type)
        output_exists = os.path.exists(output_file)

        if output_exists:
            self.display_output(display_name, output_file)
        else:
            worker = WorkerThread(cmd)
            worker.task_completed.connect(
                lambda success, message: self.on_task_completed(
                    success, message, display_name, output_file, output_type, show_result
                )
            )
            worker.finished.connect(worker.deleteLater)
            worker.start()
            self.workers.append(worker)
            print(f"[*] 正在执行：{' '.join(cmd)}")

    def run_plugin_with_params(self, plugin_name, display_name, params, output_type='json', show_result=True):
        if not self.profile:
            print("[-] 请先设置Linux Profile")
            return
            
        vol2linux = Vol2Linux(self.mem_path, self.profile)
        cmd, output_file = vol2linux.construct_command(plugin_name, output_type)
        
        # 在命令中添加参数
        if params:
            params_list = params.split()
            cmd.extend(params_list)
            
        output_exists = os.path.exists(output_file)

        if output_exists:
            self.display_output(display_name, output_file)
        else:
            worker = WorkerThread(cmd)
            worker.task_completed.connect(
                lambda success, message: self.on_task_completed(
                    success, message, display_name, output_file, output_type, show_result
                )
            )
            worker.finished.connect(worker.deleteLater)
            worker.start()
            self.workers.append(worker)
            print(f"[*] 正在执行：{' '.join(cmd)}")

    def on_task_completed(self, success, message, display_name, output_file, output_type, show_result):
        if success:
            print(f"[+] {display_name} 执行完成")
            if output_type == 'json':
                Vol2Linux(self.mem_path, self.profile).json_to_csv(output_file)
                output_file = output_file.replace('.json', '.csv')
            if show_result and os.path.exists(output_file):
                self.display_output(display_name, output_file)
            else:
                print(f"[!] 输出文件 {output_file} 不存在")
        else:
            print(f"[-] {display_name} 执行失败: {message}")
        self.workers = [w for w in self.workers if w.isRunning()]

    def display_output(self, title, file_path):
        if file_path.endswith('.text') or file_path.endswith('.txt'):
            self.show_text_result(title, file_path)
        elif file_path.endswith('.csv'):
            self.show_result(title, file_path)
        else:
            print(f"[!] 未知的文件类型: {file_path}")

    def show_result(self, title, csv_path):
        try:
            if os.path.exists(csv_path):
                window = NewtableWidget(title, csv_path)
                window.show()
                self.open_windows.append(window)
            else:
                print(f"[!] 文件不存在: {csv_path}")
        except Exception as e:
            print(f"[!] 显示结果时出错: {str(e)}")

    def show_text_result(self, title, text_path):
        try:
            if os.path.exists(text_path):
                with open(text_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                window = QuicklyView(title, content)
                window.show()
                self.open_windows.append(window)
            else:
                print(f"[!] 文件不存在: {text_path}")
        except Exception as e:
            print(f"[!] 显示文本结果时出错: {str(e)}")

# 添加这行来保持向后兼容性
vol2LinuxPlugin = Vol2LinuxPlugin
