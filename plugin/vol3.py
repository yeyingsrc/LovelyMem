import re
from plugin.config import config
import subprocess
import os
import yaml
from PySide6.QtCore import QThread, Signal, QObject
import csv
import io
from db.updatevol3cache import update_identifier_cache


class WorkerThread(QThread):
    task_completed = Signal(bool, str, bytes)

    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd

    def run(self):
        try:
            # 设置环境变量强制使用 UTF-8 编码
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            process = subprocess.Popen(
                " ".join(self.cmd), 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                shell=True,
                env=env
            )
            
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                self.task_completed.emit(True, "任务成功完成", stdout)
            else:
                error_msg = f"命令执行失败，返回代码 {process.returncode}。\n错误: {stderr.decode('utf-8', errors='replace')}"
                self.task_completed.emit(False, error_msg, b"")
        except Exception as e:
            error_msg = f"发生错误: {str(e)}"
            self.task_completed.emit(False, error_msg, b"")

class Vol3Plugin(QObject):
    task_completed_signal = Signal(str)  # 任务完成信号
    
    def __init__(self, mem_path):
        super().__init__()
        self.mem_path = mem_path
        self.workers = []
        self.readconfig()
        self.txt_plugins = ['lsadump', 'hashdump', 'cachedump', 'crashinfo', 'truecrypt']
        self.pythonpath, self.volatility3, self.volatility3_symbols = self.readconfig()

    def readconfig(self):
        with open('config/base_config.yaml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        self.pythonpath = os.path.abspath(config['base_tools']['python310']['path'])
        self.volatility3 = os.path.abspath(config['tools']['volatility3']['path'])
        self.volatility3_symbols = os.path.abspath(config['tools']['volatility3_symbols']['path'])
        return self.pythonpath, self.volatility3, self.volatility3_symbols

    def construct_command(self, plugin,offline=False):
        output_type = 'quick' if plugin in self.txt_plugins else 'csv'
        output_file = f'output/output_vol3_{plugin}.{"txt" if plugin in self.txt_plugins else "csv"}'
        if offline:
            cmd = [
                f'"{self.pythonpath}"',
                f'"{self.volatility3}"',
                '-f',
                f'"{self.mem_path}"',
                '--offline',
                '-r',   
                output_type,
                f'windows.{plugin}'
            ]
            print(' '.join(cmd))
            return cmd, output_file
        else:
            cmd = [
                f'"{self.pythonpath}"',
                f'"{self.volatility3}"',
                '-f',
                f'"{self.mem_path}"',
                '-r',   
                output_type,
                f'windows.{plugin}'
            ]
            print(' '.join(cmd))
            return cmd, output_file

    def run_vol3_task(self, plugin, offline=False):
        cmd, output_file = self.construct_command(plugin, offline=offline)
        print(f"[*] 正在执行：{' '.join(cmd)}")  
        worker = WorkerThread(cmd)
        worker.task_completed.connect(lambda success, msg, output: self.on_task_completed(success, msg, output, output_file, plugin))
        worker.start()
        self.workers.append(worker)

    def on_task_completed(self, success, msg, output, output_file, title):
        if success:
            if title in self.txt_plugins:
                self.write_to_txt(output, output_file)
            else:
                self.write_to_csv(output, output_file)
            
            print(f"[+] 执行成功：{title}")  
            
            if title not in self.txt_plugins:
                #from plugin.NewtableWidget import NewtableWidget
                from lovelyform import show_csv_viewer
                show_csv_viewer(output_file)
            else:
                from plugin.QuicklyView import QuicklyView
                new_window = QuicklyView(f'vol3-{title}', size=(800, 600))
                with open(output_file, 'r', encoding='utf-8') as f:
                    new_window.textEdit.setPlainText(f.read())
                
                new_window.show()    
            
                setattr(self, f'new_window_{title}', new_window)
            
        else:
            print(f"[×] 执行失败：{title}")  
            print(f"错误信息: {msg}")
        
        # 发出任务完成信号
        self.task_completed_signal.emit(title)

    def write_to_csv(self, output, output_file):
        try:
            # 尝试使用 UTF-8 解码处理输出
            output_io = io.TextIOWrapper(io.BytesIO(output), encoding='utf-8', errors='replace')
            reader = csv.reader(output_io)
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                for row in reader:
                    # 对每个单元格进行额外的清理，移除或替换不兼容的字符
                    cleaned_row = []
                    for cell in row:
                        if cell is not None:
                            # 替换或移除可能导致编码问题的字符
                            cleaned_cell = ''.join(c if ord(c) < 0x10000 else '?' for c in cell)
                            cleaned_row.append(cleaned_cell)
                        else:
                            cleaned_row.append('')
                    writer.writerow(cleaned_row)
        except Exception as e:
            print(f"CSV 处理错误: {str(e)}")
            # 如果处理失败，至少保存原始数据
            with open(output_file, 'wb') as f:
                f.write(output)

    def write_to_txt(self, output, output_file):
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output.decode('utf-8', errors='replace'))

    def vol3memmap(self, pid):
        cmd = [
            f'"{self.pythonpath}"',
            f'"{self.volatility3}"',
            '-f',
            f'"{self.mem_path}"',
            '-o',
            'output',
            'windows.memmap',
            f'--pid={pid}',
            '--dump'
        ]
        print(f"[*] 正在执行：{' '.join(cmd)}") 
        worker = WorkerThread(cmd)
        worker.task_completed.connect(lambda success, msg, output: self.on_memmap_completed(success, msg, pid))
        worker.start()
        self.workers.append(worker)
        # 等待线程完成
        worker.wait()
        if worker.isFinished():
            worker.deleteLater()
            return True
        else:
            return False

    def vol3procdump(self, pid):
        cmd = [
            f'"{self.pythonpath}"',
            f'"{self.volatility3}"',
            '-f',
            f'"{self.mem_path}"',
            '-o',
            '"output"',
            'windows.pslist',
            f'--pid={pid}',
            '--dump'
        ]
        print(f"[*] 正在执行：{' '.join(cmd)}") 
        worker = WorkerThread(cmd)
        worker.task_completed.connect(lambda success, msg, output: self.on_procdump_completed(success, msg, pid))
        worker.start()
        self.workers.append(worker)
    def vol3dumpfiles(self, offset):
        cmd = [self.pythonpath, self.volatility3, '-f', self.mem_path , '-o','output', f'windows.dumpfile', f'--physaddr {offset}']
        cmd2 = [self.pythonpath, self.volatility3, '-f', self.mem_path , '-o','output', f'windows.dumpfile', f'--virtaddr {offset}']
        print(f"正在执行：{' '.join(cmd)}")
        try:
            # 设置环境变量强制使用 UTF-8 编码
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            print(f"正在尝试执行：{' '.join(cmd)}")
            a = subprocess.Popen(' '.join(cmd), encoding='utf-8', env=env)
            a.wait()
            print(f"正在尝试执行：{' '.join(cmd2)}")
            b = subprocess.Popen(' '.join(cmd2), encoding='utf-8', env=env)
            b.wait()

            return True
        except Exception as e:
            print(f"执行时出错: {e}")
            return False
        
    def on_memmap_completed(self, success, msg, pid):
        if success:
            print(f"[+] 执行成功：memmap (PID: {pid})")
            print(f"已导出至 output/memmap_{pid}.dmp")
        else:
            print(f"[×] 执行失败：memmap (PID: {pid})")
            print(f"错误信息: {msg}")

    def on_procdump_completed(self, success, msg, pid):
        if success:
            print(f"[+] 执行成功：procdump (PID: {pid})")

        else:
            print(f"[×] 执行失败：procdump (PID: {pid})")
            print(f"错误信息: {msg}")

    # 定义所有 Volatility 3 插件方法
    PLUGINS = [
        'bigpools', 'cachedump', 'callbacks', 'cmdline', 'crashinfo', 'devicetree', 'dlllist',
        'driverirp', 'drivermodule', 'driverscan', 'dumpfiles', 'envars', 'filescan',
        'getservicesids', 'getsids', 'handles', 'hashdump', 'iat', 'info', 'joblinks',
        'ldrmodules', 'lsadump', 'malfind', 'mbrscan', 'modscan', 'modules', 'mutantscan',
        'netscan', 'netstat', 'poolscanner', 'privileges', 'pslist', 'psscan', 'pstree',
        'registry.certificates', 'registry.hivelist', 'registry.hivescan', 'registry.printkey',
        'registry.userassist', 'sessions', 'skeleton_key_check', 'ssdt', 'statistics',
        'strings', 'symlinkscan', 'thrdscan', 'truecrypt', 'vadinfo', 'vadwalk',
        'verinfo', 'virtmap','unloadedmodules','hollowprocesses','kpcrs','pedump','processghosting',
        'psxview','registry.getcellroutine','shimcachemem','suspicious_threads','svcdiff','svclist',
        'threads','timers','iat','deskscan','desktops','direct_system_calls','indirect_system_calls','suspended_threads',
        'vadregexscan','windows','windowstations'
    ]

    def __getattr__(self, name):
        if name.startswith('vol3_') and name[5:] in self.PLUGINS:
            return lambda offline=False: self.run_vol3_task(name[5:], offline=offline)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")