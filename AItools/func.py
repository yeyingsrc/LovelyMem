import asyncio
import json
import re
from turtle import st
import yaml
import subprocess
import os
import time
import sys
import threading

def get_image_info_file():
    mem_path = open('output/image_info.txt', 'r',encoding='utf-8').read().split(',')[0]
    profile = open('output/image_info.txt', 'r',encoding='utf-8').read().split(',')[1]
    return mem_path, profile

def get_tools():
    # config\base_config.yaml
    with open('config/base_config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    python27 = config['base_tools']['python27']['path']
    python27 = os.path.abspath(python27)
    python30 = config['base_tools']['python310']['path']
    python30 = os.path.abspath(python30)
    volatility2 = config['tools']['volatility2_python']['path']
    volatility2 = os.path.abspath(volatility2)
    volatility2_plugin = config['tools']['volatility2_plugin']['path']
    volatility2_plugin = os.path.abspath(volatility2_plugin)
    volatility3 = config['tools']['volatility3']['path']
    volatility3 = os.path.abspath(volatility3)
    volatility3_symbols = config['tools']['volatility3_symbols']['path']
    volatility3_symbols = os.path.abspath(volatility3_symbols)
    gimp = config['tools']['gimp']['path']
    gimp = os.path.abspath(gimp)
    return python27, python30, volatility2, volatility2_plugin, volatility3, volatility3_symbols, gimp

def show_loading_animation(stop_event, start_time):
    animation = ["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"]
    idx = 0
    while not stop_event.is_set():
        elapsed_time = time.time() - start_time
        print(f"\r[{animation[idx]}] 命令执行中... {elapsed_time:.1f}s", end="")
        sys.stdout.flush()
        idx = (idx + 1) % len(animation)
        time.sleep(0.1)
    print("\r完成!                        ", end="\n")
    sys.stdout.flush()

def run_with_animation(cmd, encoding='gbk'):
    print(f"[*] 正在执行：{' '.join(cmd)}")
    stop_event = threading.Event()
    start_time = time.time()
    animation_thread = threading.Thread(target=show_loading_animation, args=(stop_event, start_time))
    animation_thread.daemon = True
    animation_thread.start()
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, encoding=encoding)
        stdout, stderr = process.communicate()
        execution_time = time.time() - start_time
        stop_event.set()
        animation_thread.join()
        return stdout, stderr
    except Exception as e:
        execution_time = time.time() - start_time
        stop_event.set()
        animation_thread.join()
        raise e

async def vol3_pslist(value,name="None"):
    python27, python3, volatility2, volatility2_plugin, volatility3, volatility3_symbols, gimp = get_tools()
    mem_path, profile = get_image_info_file()
    if value == 1:
        cmd = [
            python3,
            volatility3,
            '-f',
            mem_path,
            'windows.pslist',
            '|',
            'findstr',
            name
        ]
    else:  # 默认情况和 value == 0 的情况
        cmd = [
            python3,
            volatility3,
            '-f',
            mem_path,
            'windows.pslist'
        ]
    
    try:
        stdout, stderr = run_with_animation(cmd)
        if stderr:
            pass
        if stdout:
            print(f"执行结果：\n{stdout}")
            return f"返回结果如下，往往第一个为PID，第二个为PPID： \n{stdout}"
        else:
            print("没有找到匹配的结果")
            return False
    except Exception as e:
        print(f"[-] 执行失败：{str(e)}")
        return False

async def vol3_netscan(string):
    python27, python3, volatility2, volatility2_plugin, volatility3, volatility3_symbols, gimp = get_tools()
    mem_path, profile = get_image_info_file()
    cmd = [
        python3,
        volatility3,
        '-f',
        mem_path,
        '-o',
        'output',
        'windows.netscan'
    ]
    try:
        stdout, stderr = run_with_animation(cmd)
        if stdout:
            print(f"执行结果：\n{stdout}")
            return f"返回结果如下，列顺序分别为：Offset  Proto   LocalAddr       LocalPort       ForeignAddr     ForeignPort     State   PID     Owner   Created \n{stdout}"
        else:
            print("没有找到匹配的结果")
        
    except Exception as e:
        print(f"[-] 执行失败：{str(e)}")
        return False

async def vol3_filescan(string):
    python27, python3, volatility2, volatility2_plugin, volatility3, volatility3_symbols, gimp = get_tools()
    mem_path, profile = get_image_info_file()
    cmd = [
        python3,
        volatility3,
        '-f',
        mem_path,
        '-o',
        'output',
        'windows.filescan',
        '|',
        'findstr',
        string
    ]
    try:
        stdout, stderr = run_with_animation(cmd)
        if stdout:
            print(f"执行结果：\n{stdout}")
        else:
            print("没有找到匹配的结果")
            
        return stdout
    except Exception as e:
        print(f"[-] 执行失败：{str(e)}")
        return False

async def vol3_dumpfile(offset):
    python27, python3, volatility2, volatility2_plugin, volatility3, volatility3_symbols, gimp = get_tools()
    mem_path, profile = get_image_info_file()
    cmd1 = [
        python3,
        volatility3,
        '-f',
        mem_path,
        '-o',
        'output',
        'windows.dumpfile',
        '--physaddr',
        offset
    ]
    cmd2 = [
        python3,
        volatility3,
        '-f',
        mem_path,
        '-o',
        'output',
        'windows.dumpfile',
        '--virtaddr',
        offset
    ]
    try:
        stdout1, stderr1 = run_with_animation(cmd1)
        stdout2, stderr2 = run_with_animation(cmd2)
        
        if stdout1:
            print(f"执行结果：\n{stdout1}")
        if stdout2:
            print(f"执行结果：\n{stdout2}")
        else:
            print("没有找到匹配的结果")
            
        return stdout1+stdout2
    except Exception as e:
        print(f"[-] 执行失败：{str(e)}")
        return False

async def vol3_hashdump(string):
    python27, python3, volatility2, volatility2_plugin, volatility3, volatility3_symbols, gimp = get_tools()
    mem_path, profile = get_image_info_file()
    cmd = [
        python3,
        volatility3,
        '-f',
        mem_path,
        'windows.hashdump'
    ]
    try:
        stdout, stderr = run_with_animation(cmd)
        if stdout:
            print(f"执行结果：\n{stdout}")
        else:
            print("没有找到匹配的结果")
            
        return stdout
    except Exception as e:
        print(f"[-] 执行失败：{str(e)}")
        return False

async def readfile(filename):
    try:
        print(f"[*] 正在读取文件：{filename}")
        path = f"output/{filename}"
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            return content
    except Exception as e:
        print(f"[-] 执行失败：{str(e)}")
        return False

async def getoutputlist(string):
    # 读取output目录下的文件名
    try:
        print(f"[*] 正在获取文件列表")
        path = f"output"
        files = os.listdir(path)
        result = "\n".join(files)
        print(f"文件列表：\n{result}")
        return result
    except Exception as e:
        print(f"[-] 执行失败：{str(e)}")
        return False

async def vol3_malfind(string):
    python27, python3, volatility2, volatility2_plugin, volatility3, volatility3_symbols, gimp = get_tools()
    mem_path, profile = get_image_info_file()
    cmd = [
        python3,
        volatility3,
        '-f',
        mem_path,
        'windows.malfind'
    ]
    try:
        stdout, stderr = run_with_animation(cmd)
        if stdout:
            print(f"执行结果：\n{stdout}")
        else:
            print("没有找到匹配的结果")
            
        return stdout
    except Exception as e:
        print(f"[-] 执行失败：{str(e)}")

async def vol2_consoles(string):
    python27, python3, volatility2, volatility2_plugin, volatility3, volatility3_symbols, gimp = get_tools()
    mem_path, profile = get_image_info_file()
    cmd = [
        python27,
        volatility2,
        '-f',
        mem_path,
        f'--profile={profile}',
        'consoles'
    ]
    try:
        stdout, stderr = run_with_animation(cmd)
        if stdout:
            print(f"执行结果：\n{stdout}")
        else:
            print("没有找到匹配的结果")
            
        return stdout
    except Exception as e:
        print(f"[-] 执行失败：{str(e)}")

async def vol3_handle(string):
    python27, python3, volatility2, volatility2_plugin, volatility3, volatility3_symbols, gimp = get_tools()
    mem_path, profile = get_image_info_file()
    cmd = [
        python3,
        volatility3,
        '-f',
        mem_path,
        'windows.handle',
        '--pid',
        string
    ]
    try:
        stdout, stderr = run_with_animation(cmd)
        if stdout:
            print(f"执行结果：\n{stdout}")
        else:
            print("没有找到匹配的结果")
            
        return stdout
    except Exception as e:
        print(f"[-] 执行失败：{str(e)}")

async def vol3_privileges(pid):
    python27, python3, volatility2, volatility2_plugin, volatility3, volatility3_symbols, gimp = get_tools()
    mem_path, profile = get_image_info_file()
    cmd = [
        python3,
        volatility3,
        '-f',
        mem_path,
        'windows.privileges',
        '--pid',
        pid
    ]
    try:
        stdout, stderr = run_with_animation(cmd)
        if stdout:
            print(f"执行结果：\n{stdout}")
        else:
            print("没有找到匹配的结果")
            
        return stdout
    except Exception as e:
        print(f"[-] 执行失败：{str(e)}")

async def readevilent(filename):
    try:
        print(f"[*] 正在读取文件：{filename}")
        path = f"output/{filename}"
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            return content
    except Exception as e:
        print(f"[-] 执行失败：{str(e)}")
        return False

async def vol3_cmdline(pid):
    python27, python3, volatility2, volatility2_plugin, volatility3, volatility3_symbols, gimp = get_tools()
    mem_path, profile = get_image_info_file()
    if pid == "None" or pid == "":
        cmd = [
            python3,
            volatility3,
            '-f',
            mem_path,
            'windows.cmdline'
        ]
    else:
        cmd = [
            python3,
            volatility3,
            '-f',
            mem_path,
            'windows.cmdline',
            '--pid',
            pid
        ]
    try:
        stdout, stderr = run_with_animation(cmd)
        if stdout:
            print(f"执行结果：\n{stdout}")
        else:
            print("没有找到匹配的结果")
            
        return stdout
    except Exception as e:
        print(f"[-] 执行失败：{str(e)}")

async def vol3_dlllist(pid):
    python27, python3, volatility2, volatility2_plugin, volatility3, volatility3_symbols, gimp = get_tools()
    mem_path, profile = get_image_info_file()
    cmd = [
        python3,
        volatility3,
        '-f',
        mem_path,
        'windows.dlllist',
        '--pid',
        str(pid)
    ]
    try:
        stdout, stderr = run_with_animation(cmd)
        if stdout:
            print(f"执行结果：\n{stdout}")
        else:
            print("没有找到匹配的结果")
            
        return stdout
    except Exception as e:
        print(f"[-] 执行失败：{str(e)}")

async def vol3_userassist(string):
    python27, python3, volatility2, volatility2_plugin, volatility3, volatility3_symbols, gimp = get_tools()
    mem_path, profile = get_image_info_file()
    cmd = [
        python3,
        volatility3,
        '-f',
        mem_path,
        'windows.userassist'
    ]
    try:
        stdout, stderr = run_with_animation(cmd)
        if stdout:
            print(f"执行结果：\n{stdout}")
        else:
            print("没有找到匹配的结果")
            
        return stdout
    except Exception as e:
        print(f"[-] 执行失败：{str(e)}")    

async def vol3_envars(string):
    python27, python3, volatility2, volatility2_plugin, volatility3, volatility3_symbols, gimp = get_tools()
    mem_path, profile = get_image_info_file()
    cmd = [
        python3,
        volatility3,
        '-f',
        mem_path,
        'windows.envars',
        '--pid',
        string
    ]
    try:
        stdout, stderr = run_with_animation(cmd)
        if stdout:
            print(f"执行结果：\n{stdout}")
        else:
            print("没有找到匹配的结果")
            
        return stdout
    except Exception as e:
        print(f"[-] 执行失败：{str(e)}")

async def vol3_custom(string):
    python27, python3, volatility2, volatility2_plugin, volatility3, volatility3_symbols, gimp = get_tools()
    mem_path, profile = get_image_info_file()
    cmd = [
        python3,
        volatility3,
        '-f',
        mem_path,
        string
    ]
    try:
        stdout, stderr = run_with_animation(cmd)
        if stdout:
            print(f"执行结果：\n{stdout}")
        else:
            print("没有找到匹配的结果")
            
        return stdout
    except Exception as e:
        print(f"[-] 执行失败：{str(e)}")