import os,shutil
import yaml
import subprocess
import threading
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor
from plugin.memprocfs import memprocfsplugin
import sys

class MemImageLoader(QObject):
    load_finished = Signal(bool, str)
    output_received = Signal(str, QColor)

    def __init__(self):
        super().__init__()
        self.stdout_color = QColor(100, 100, 255)  # 亮蓝色
        self.stderr_color = QColor(255, 100, 100)  # 亮红色
        self.memprocfs_plugin = memprocfsplugin(self)

    def load_mem_image(self, image_path):
        thread = threading.Thread(target=self._load_mem_image_thread, args=(image_path,))
        thread.start()

    def _load_mem_image_thread(self, image_path):
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'base_config.yaml')
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            memprocfs_path = config['tools']['memprocfs']['path']
            memprocfs_path = os.path.abspath(memprocfs_path)
            
            cmd = f'"{memprocfs_path}" -device "{image_path}" -v -license-accept-elastic-license-2-0 -forensic 1'
            self.output_received.emit(f'[+] MemProcFS加载命令：{cmd}\n', self.stdout_color)
            
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)
            
            load_success = False
            for line in process.stdout:
                self.output_received.emit(line, self.stdout_color)
                if "Forensic mode completed in" in line:
                    load_success = True
                    self.output_received.emit(f'[+] 成功加载内存镜像：{image_path}\n', self.stdout_color)
                    self.load_finished.emit(True, f"成功加载内存镜像：{image_path}\n")
                    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                    for file in os.listdir("M:\\forensic\\csv"):
                        if os.path.isfile(os.path.join("M:\\forensic\\csv", file)):
                            shutil.copy(os.path.join("M:\\forensic\\csv", file), output_dir)
                    # 复制 M:\py\regsecrets\all.txt
                    if os.path.exists("M:\\py\\regsecrets\\all.txt"):
                        #新名字 系统密码相关.txt
                        shutil.copy("M:\\py\\regsecrets\\all.txt", os.path.join(output_dir, "系统密码相关.txt"))
                    # 复制 "M:\sys\sysinfo\sysinfo.txt"
                    if os.path.exists("M:\\sys\\sysinfo\\sysinfo.txt"):
                        shutil.copy("M:\\sys\\sysinfo\\sysinfo.txt", os.path.join(output_dir, "系统信息.txt"))
                    # 如果 M:\misc\bitlocker 目录下文件数>1 则复制到output
                    if os.path.exists("M:\\misc\\bitlocker") and len(os.listdir("M:\\misc\\bitlocker")) > 1:
                        shutil.copytree("M:\\misc\\bitlocker", os.path.join(output_dir, "BitLocker信息"))
                        # 打印成功信息
                        self.output_received.emit(f'[+] 发现BitLocker信息，已复制到output(BitLocker信息)\n', self.stdout_color)
                    self.memprocfs_plugin.lovelymem_checkRun()
                    self.memprocfs_plugin.lovelymem_defaultbrowser()
                    self.memprocfs_plugin.merge_console_txt_files()
                    
            for line in process.stderr:
                self.output_received.emit(f"错误输出：{line}", self.stderr_color)
            
            returncode = process.wait()
            if returncode != 0:
                self.output_received.emit(f'[!] 加载过程中出现错误，返回码：{returncode}\n', self.stderr_color)
            
            if not load_success:
                self.output_received.emit(f'[!] 加载可能不完整，但仍继续处理\n', self.stderr_color)
                self.load_finished.emit(True, f"加载可能不完整，但仍继续处理：{image_path}\n")
            
        except Exception as e:
            error_msg = f'[×] 加载内存镜像文件时发生异常：{str(e)}\n'
            self.output_received.emit(error_msg, self.stderr_color)
            self.load_finished.emit(True, f"加载过程中发生异常，但仍继续处理：{image_path}\n")
