import re
from plugin.config import config
import subprocess
import os
import yaml
from PySide6.QtCore import QThread, Signal, QObject
import csv
import io

class WorkerThread(QThread):
    task_completed = Signal(bool, str, bytes)

    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd
        
    def set_command(self, cmd):
        """设置要执行的命令"""
        self.cmd = cmd

    def run(self):
        try:
            print(f"[DEBUG] 执行命令: {' '.join(self.cmd)}")
            # 设置环境变量，指定使用UTF-8编码
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'  # Python 3.7+
            
            process = subprocess.Popen(
                " ".join(self.cmd), 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                shell=True,
                env=env
            )
            
            stdout, stderr = process.communicate()
            
            print(f"[DEBUG] 命令执行完成，返回代码: {process.returncode}")
            print(f"[DEBUG] stdout长度: {len(stdout)} 字节")
            print(f"[DEBUG] stderr长度: {len(stderr)} 字节")
            
            if stdout and len(stdout) > 0:
                print(f"[DEBUG] stdout前50个字节: {stdout[:50]}")
            
            if process.returncode == 0:
                self.task_completed.emit(True, "任务成功完成", stdout)
            else:
                try:
                    stderr_text = stderr.decode('utf-8', errors='replace')
                    print(f"[DEBUG] stderr内容: {stderr_text}")
                    error_msg = f"命令执行失败，返回代码 {process.returncode}。\n错误: {stderr_text}"
                    self.task_completed.emit(False, error_msg, b"")
                except Exception as decode_error:
                    error_msg = f"命令执行失败，返回代码 {process.returncode}。\n解码错误信息时出错: {str(decode_error)}"
                    self.task_completed.emit(False, error_msg, b"")
        except Exception as e:
            error_msg = f"发生错误: {str(e)}"
            print(f"[DEBUG] 工作线程运行异常: {str(e)}")
            self.task_completed.emit(False, error_msg, b"")


class Vol3LinuxPlugin(QObject):
    def __init__(self, mem_path):
        super().__init__()
        self.mem_path = mem_path
        self.workers = []
        self.readconfig()
        # Linux特有的txt输出插件列表
        self.txt_plugins = ['psaux',]

    def readconfig(self):
        with open('config/base_config.yaml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        self.pythonpath = os.path.abspath(config['base_tools']['python310']['path'])
        self.volatility3 = os.path.abspath(config['tools']['volatility3']['path'])
        self.volatility3_symbols = os.path.abspath(config['tools']['volatility3_symbols']['path'])
        return self.pythonpath, self.volatility3, self.volatility3_symbols

    def construct_command(self, plugin, offline=False, use_proxy=False, proxy_url=None):
        """构建Linux插件命令"""
        output_type = 'quick' if plugin in self.txt_plugins else 'csv'
        output_file = f'output/output_vol3_linux_{plugin}.{"txt" if plugin in self.txt_plugins else "csv"}'
        
        # 构建基本命令
        cmd = [
            f'"{self.pythonpath}"',
        ]
        
        # 如果使用代理，设置环境变量
        proxy_env = ""
        if use_proxy and proxy_url:
            print(f"[DEBUG] 使用代理: {proxy_url}")
            # 用于Windows系统的代理设置
            proxy_env = f"set HTTPS_PROXY={proxy_url} && set HTTP_PROXY={proxy_url} && "
        
        # 添加代理前缀到命令(如果需要)
        if use_proxy and proxy_url:
            cmd = [proxy_env + cmd[0]]
        
        # 添加volatility3路径和内存文件
        cmd.extend([
            f'"{self.volatility3}"',
            '-f',
            f'"{self.mem_path}"'
        ])
        
        # 添加离线模式或远程ISF URL参数
        if offline:
            cmd.append('--offline')
        else:
            # 如果设置了代理，使用远程ISF URL
            if use_proxy and proxy_url:
                cmd.append("--remote-isf-url")
                cmd.append('"https://github.com/Abyss-W4tcher/volatility3-symbols/raw/master/banners/banners.json"')
            else:
                # 否则使用本地符号表
                cmd.append("--single-location")
                cmd.append(f'"{os.path.join(os.path.dirname(self.volatility3), "symbols")}"')
        
        # 添加输出格式参数
        cmd.extend([
            '-r',
            output_type
        ])
        
        # 最后添加插件名称
        cmd.append(f'{plugin}')
        
        print(' '.join(cmd))
        return cmd

    def run_vol3linux_task(self, plugin, offline=False, use_proxy=False, proxy_url=None):
        """运行Linux插件任务"""
        if not self.mem_path:
            return

        print(f"[DEBUG] 执行Linux插件: {plugin}, 离线模式: {offline}, 使用代理: {use_proxy}, 代理URL: {proxy_url}")
        
        # 获取命令
        cmd = self.construct_command(plugin, offline, use_proxy, proxy_url)
        
        # 提取插件的简单名称，用于文件名
        # 例如：从'linux.pslist'中提取'pslist'
        # 从'tracing.ftrace.checkftrace'中提取'checkftrace'
        simple_name = plugin.split('.')[-1]
        
        # 在软件目录下创建output文件夹
        # 获取当前软件目录
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(app_dir, "output")
        # 确保output文件夹存在
        os.makedirs(output_dir, exist_ok=True)
        print(f"[DEBUG] 输出目录: {output_dir}")
        
        output_file = os.path.join(output_dir, f"vol3linux_{simple_name}.txt")
        title = f"Volatility 3 - {plugin}"
        
        # 异步执行命令
        worker = WorkerThread(cmd)
        
        # 连接信号
        worker.task_completed.connect(lambda success, msg, output: 
                                     self.on_task_completed(success, msg, output, output_file, title))
        
        # 开始线程
        self.workers.append(worker)
        worker.start()

    def on_task_completed(self, success, msg, output, output_file, title):
        """任务完成后的回调处理"""
        if success:
            print(f"[DEBUG] 输出类型: {type(output)}")
            print(f"[DEBUG] 输出长度: {len(output)} 字节")
            print(f"[DEBUG] 插件名称: {title}")
            print(f"[DEBUG] 是否在txt_plugins列表中: {title in self.txt_plugins}")
            print(f"[DEBUG] 输出文件: {output_file}")
            
            # 显示前100个字节以帮助调试
            if len(output) > 0:
                print(f"[DEBUG] 前100个字节: {output[:100]}")
            
            # 检查文件编码
            if title == "bash":
                print("[DEBUG] 开始处理bash命令输出")
                # 尝试异常位置附近的字节
                problem_area_start = max(0, 40100)
                problem_area_end = min(len(output), 40200)
                if problem_area_end > problem_area_start:
                    print(f"[DEBUG] 编码问题区域附近的字节: {output[problem_area_start:problem_area_end]}")
            
            try:
                # 使用二进制模式直接写入文件
                with open(output_file, 'wb') as f:
                    f.write(output)
                print(f"[DEBUG] 成功以二进制模式写入输出文件")
                
                # 成功响应
                print(f"[+] 执行成功：{title}")
                
                # 处理不同类型的输出文件
                if title not in self.txt_plugins:
                    # CSV输出
                    try:
                        # 解决CSV编码问题的更强大方法
                        # 先保存为文本文件
                        temp_txt = output_file.replace('.csv', '.txt')
                        with open(temp_txt, 'wb') as f:
                            f.write(output)
                            
                        # 然后读取文本，线通线处理
                        with open(temp_txt, 'r', encoding='utf-8', errors='replace') as f:
                            lines = f.readlines()
                        
                        # 重新输出为CSV
                        with open(output_file, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            for line in lines:
                                # 安全地处理每一行
                                try:
                                    # 尝试作为CSV处理
                                    parts = [part.strip() for part in line.split(',')]
                                    writer.writerow(parts)
                                except Exception:
                                    # 如果失败，将整行当作一个列
                                    writer.writerow([line.strip()])
                                    
                        print(f"[DEBUG] 成功将CSV安全转换为UTF-8编码")
                    except Exception as e:
                        print(f"[DEBUG] 转换CSV编码出错: {e}")
                        # 如果转换失败，尝试直接保存原始二进制数据
                        try:
                            with open(output_file, 'wb') as f:
                                f.write(output)
                            print(f"[DEBUG] 已将原始数据保存到: {output_file}")
                        except Exception as e2:
                            print(f"[DEBUG] 写入原始数据失败: {e2}")
                    
                    try:
                        from lovelyform import show_csv_viewer
                        show_csv_viewer(output_file)
                    except Exception as e:
                        print(f"[DEBUG] 显示CSV出错: {e}")
                else:
                    # TXT输出
                    try:
                        from plugin.QuicklyView import QuicklyView
                        new_window = QuicklyView(f'vol3linux-{title}', size=(800, 600))
                        
                        try:
                            # 先尝试以替代模式打开文件
                            with open(output_file, 'r', encoding='utf-8', errors='replace') as f:
                                content = f.read()
                                new_window.text_edit.setPlainText(content)
                                print(f"[DEBUG] 使用UTF-8(替代)成功打开文件")
                        except Exception as e:
                            print(f"[DEBUG] 打开文件时出错: {e}")
                            # 如果还是失败，尝试以二进制模式读取
                            with open(output_file, 'rb') as f:
                                content = f.read()
                                try:
                                    decoded = content.decode('latin-1')
                                    new_window.text_edit.setPlainText(decoded)
                                    print(f"[DEBUG] 使用latin-1成功打开文件")
                                except Exception as e2:
                                    print(f"[DEBUG] latin-1解码也失败: {e2}")
                        new_window.show()
                    except Exception as e:
                        print(f"[DEBUG] 创建QuicklyView窗口失败: {e}")
            except Exception as e:
                print(f"[DEBUG] 处理命令输出时出错: {e}")
                raise
        else:
            print(f"[×] 执行失败：{title}")
            print(f"错误信息：{msg}")

    def write_to_csv(self, output, output_file):
        """将输出写入CSV文件
        使用更安全的方法处理CSV编码问题
        """
        try:
            # 首先保存原始数据为文本文件
            temp_txt = output_file.replace('.csv', '.txt')
            with open(temp_txt, 'wb') as f:
                f.write(output)
            
            # 尝试以UTF-8打开该文件
            with open(temp_txt, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            # 将内容安全地转换为CSV格式
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for line in lines:
                    # 尝试拆分列，如果失败则将整行作为一列
                    try:
                        columns = line.strip().split(',')
                        writer.writerow(columns)
                    except Exception:
                        writer.writerow([line.strip()])
            
            # 如果成功，删除临时文本文件
            if os.path.exists(temp_txt):
                os.remove(temp_txt)
                
            return True
        except Exception as e:
            print(f"[ERROR] 写入CSV时出错: {e}")
            # 如果转换失败，就直接将原始数据保存为CSV
            try:
                with open(output_file, 'wb') as f:
                    f.write(output)
                return True
            except:
                return False

    def write_to_txt(self, output, output_file):
        """将输出写入文本文件"""
        print(f"[DEBUG] write_to_txt 被调用，输出文件: {output_file}")
        # 先尝试写入二进制数据，确保数据被保存
        with open(output_file, 'wb') as f:
            f.write(output)
            print(f"[DEBUG] 二进制数据已成功写入: {output_file}")
        
        # 然后再尝试解码为文本进行具体处理
        try:
            # 检查前入10个字节
            if len(output) > 10:
                print(f"[DEBUG] 前10个字节: {output[:10]}")
            
            # 尝试UTF-8解码
            decoded_utf8 = output.decode('utf-8', errors='replace')
            print(f"[DEBUG] UTF-8解码成功（使用替代模式）")
            
            # 如果解码成功，则不需要其他尝试
            return
        except Exception as e:
            print(f"[DEBUG] UTF-8解码失败: {e}")
            # 如果失败，我们已经保存了二进制数据，所以不会丢失信息

    # 定义所有 Volatility 3 Linux 插件方法 - 根据linux_func.md更新
    LINUX_PLUGINS = [
        # 系统基础信息
        'banners', 'boottime', 'iomem', 'vmcoreinfo', 'dmesg', 'kmsg', 'kallsyms',
        # 进程信息
        'pslist', 'psscan', 'pstree', 'psaux', 'proc_maps', 'pscallstack', 'pidhashtable',
        'capabilities', 'ptrace',
        # 用户与环境
        'bash', 'bash_history', 'bash_hash', 'envars', 'users',
        # 网络与通信
        'ip_addr', 'ip_link', 'arp', 'netstat', 'route', 'sockstat', 'netfilter',
        # 文件系统
        'fs_metadata', 'getcwd', 'mountinfo', 'lsof', 'pagecache_files', 'pagecache_inodepages',
        'pagecache_recoverfs',
        # 内核与模块
        'elfs', 'lsmod', 'kthreads', 'module_extract', 'modxview', 'hidden_modules', 'library_list',
        # 图形和输入
        'fbdev', 'keyboard_notifiers', 'tty_check',
        # 跟踪与性能
        'ebpf', 'ftrace', 'perf_events', 'tracepoints',
        # 安全检查
        'check_afinfo', 'check_creds', 'check_idt', 'check_syscall', 'check_modules',
        'malfind', 'vmaregexscan',
        # 兼容旧版本命令
        'getenv', 'ifconfig', 'list_files', 'sudoers', 'whoami'
    ]

    def __getattr__(self, name):
        """动态处理未定义的方法，支持所有Linux插件"""
        if name.startswith('vol3linux_'):
            # 检查是否已经是重复的前缀 - 避免出现vol3linux_vol3linux_情况
            if name[10:].startswith('vol3linux_'):
                print(f"[DEBUG] 检测到重复的前缀: {name}")
                # 如果是重复的，则去掉第一个前缀
                return self.__getattr__(name[10:])
                
            # 提取插件名称，去除vol3linux_前缀
            plugin_name = name[10:]
            # 特殊处理一些特殊格式的插件名称
            # if plugin_name == 'proc_maps':
            #     plugin_name = 'proc.maps'  # 将proc_maps转换为proc.maps
            # elif plugin_name.startswith('pagecache_'):
            #     # 将pagecache_files转换为pagecache.files等
            #     plugin_name = f"pagecache.{plugin_name[10:]}"
            # elif plugin_name == 'ip_addr':
            #     plugin_name = 'ip.addr'
            # elif plugin_name == 'ip_link':
            #     plugin_name = 'ip.link'
            # elif plugin_name == 'ftrace':
            #     plugin_name = 'tracing.ftrace.checkftrace'
            # elif plugin_name == 'perf_events':
            #     plugin_name = 'tracing.perf_events.perfevents'
            # elif plugin_name == 'tracepoints':
            #     plugin_name = 'tracing.tracepoints.checktracepoints'
            
            # 根据插件名称判断是否需要使用linux.前缀
            if plugin_name.startswith(('ip.', 'pagecache.', 'tracing.')) or plugin_name == 'proc.maps':
                # 已经包含了适当的前缀/路径，不需要再加前缀
                full_plugin_name = plugin_name
            elif plugin_name == 'banners':
                # banners是特殊的插件，不需要linux.前缀
                full_plugin_name = plugin_name
            else:
                # 其他插件都需要加上linux.前缀
                full_plugin_name = f"linux.{plugin_name.replace('_','.')}"
                
            print(f"[DEBUG] 将调用插件: {full_plugin_name}")
            return lambda offline=False, use_proxy=False, proxy_url=None: self.run_vol3linux_task(full_plugin_name, offline=offline, use_proxy=use_proxy, proxy_url=proxy_url)
            
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
