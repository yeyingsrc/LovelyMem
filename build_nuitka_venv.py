#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LovelyMem Nuitka 虚拟环境打包脚本
使用虚拟环境和Nuitka将LovelyMem打包为独立的可执行文件
"""

import os
import sys
import subprocess
import shutil
import venv
from pathlib import Path

def create_virtual_env(venv_path):
    """创建虚拟环境"""
    print(f"创建虚拟环境: {venv_path}")
    venv.create(venv_path, with_pip=True)
    return venv_path

def install_requirements(venv_path, requirements_file):
    """在虚拟环境中安装依赖"""
    if os.name == 'nt':  # Windows
        pip_path = os.path.join(venv_path, 'Scripts', 'pip.exe')
        python_path = os.path.join(venv_path, 'Scripts', 'python.exe')
    else:  # Linux/Mac
        pip_path = os.path.join(venv_path, 'bin', 'pip')
        python_path = os.path.join(venv_path, 'bin', 'python')
    
    print(f"安装项目依赖: {requirements_file}")
    subprocess.run([pip_path, 'install', '-r', requirements_file], check=True)
    
    print("安装Nuitka")
    subprocess.run([pip_path, 'install', 'nuitka'], check=True)
    
    return python_path

def build_with_nuitka(python_path, project_root):
    """使用虚拟环境中的Python和Nuitka构建可执行文件"""
    os.chdir(project_root)
    
    # 清理之前的构建
    build_dirs = ['main.build', 'main.dist', 'main.onefile-build', 'dist']
    for build_dir in build_dirs:
        if os.path.exists(build_dir):
            print(f"清理构建目录: {build_dir}")
            try:
                shutil.rmtree(build_dir)
            except PermissionError:
                print(f"警告: 无法删除 {build_dir}，可能被其他程序占用")
    
    # 创建输出目录
    os.makedirs('dist', exist_ok=True)
    
    # 测试Nuitka是否正常工作
    print("测试Nuitka是否正常安装...")
    try:
        test_cmd = [python_path, '-m', 'nuitka', '--version']
        version_output = subprocess.run(test_cmd, check=True, capture_output=True, text=True)
        print(f"Nuitka版本: {version_output.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Nuitka测试失败: {e}")
        print("尝试重新安装Nuitka...")
        try:
            subprocess.run([os.path.join(os.path.dirname(python_path), 'pip'), 'install', '--upgrade', 'nuitka'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ 无法安装Nuitka: {e}")
            return False
    
    # 使用简化的Nuitka命令进行初始测试
    print("使用简化命令进行测试构建...")
    test_build_cmd = [
        python_path, '-m', 'nuitka',
        '--standalone',
        '--output-dir=dist',
        'main.py'
    ]
    
    try:
        # subprocess.run(test_build_cmd, check=True)
        # print("✅ 测试构建成功!")
        pass
    except subprocess.CalledProcessError as e:
        print(f"❌ 测试构建失败: {e}")
        print("尝试使用更基本的命令...")
        try:
            basic_cmd = [python_path, '-m', 'nuitka', 'main.py']
            subprocess.run(basic_cmd, check=True)
            print("✅ 基本构建成功，但不是独立可执行文件")
            return False
        except subprocess.CalledProcessError as e:
            print(f"❌ 基本构建也失败: {e}")
            print("请检查C++编译器是否正确安装")
            return False
    
    # 完整的Nuitka构建命令
    print("\n开始完整构建...")
    nuitka_cmd = [
        python_path, '-m', 'nuitka',
        '--standalone',  # 独立模式，包含所有依赖
        '--output-dir=dist',  # 输出目录
        
        # 包含必要的数据文件和目录
        '--include-data-dir=config=config',
        '--include-data-dir=db=db', 
        '--include-data-dir=res=res',
        '--include-data-dir=font=font',
        '--include-data-dir=script=script',
        '--include-data-dir=extensions=extensions',
        '--include-data-dir=plugin=plugin',
        '--include-data-dir=ui=ui',
        '--include-data-dir=core=core',
        '--include-data-dir=utils=utils',
        '--include-data-dir=lovelyform=lovelyform',
        
        # Qt插件支持 - 解决"no Qt platform plugin could be initialized"错误
        '--include-qt-plugins=all',  # 包含所有Qt插件
        '--enable-plugin=pyside6',   # 启用PySide6插件
        
        # 确保包含必要的Qt库
        '--include-module=PySide6.QtCore',
        '--include-module=PySide6.QtGui', 
        '--include-module=PySide6.QtWidgets',
        '--include-module=PySide6.QtSvg',
        
        # 优化选项
        '--assume-yes-for-downloads',
        '--show-progress',
        
        # 主程序文件
        'main.py'
    ]
    
    # 如果是Windows系统，添加Windows特定选项
    if os.name == 'nt':
        nuitka_cmd.extend([
            '--windows-icon-from-ico=res/logo.ico',
            '--windows-console-mode=disable',
        ])
    
    print("开始使用 Nuitka 构建...")
    print(f"构建命令: {' '.join(nuitka_cmd)}")
    print("-" * 60)
    
    try:
        # 执行构建
        result = subprocess.run(nuitka_cmd, check=True)
        
        print("-" * 60)
        print("✅ 构建成功!")
        print(f"可执行文件位置: {project_root}/dist/main.exe")
        
        # 检查文件是否存在
        exe_path = os.path.join(project_root, 'dist', 'main.exe')
        if os.path.exists(exe_path):
            file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
            print(f"文件大小: {file_size:.2f} MB")
            
            # 重命名文件
            new_exe_path = os.path.join(project_root, 'dist', 'LovelyMem.exe')
            try:
                os.rename(exe_path, new_exe_path)
                print(f"已重命名为: {new_exe_path}")
            except OSError as e:
                print(f"重命名失败: {e}")
        
        # 自动修复Qt插件问题
        print("\n正在修复Qt插件问题...")
        try:
            fix_result = subprocess.run([python_path, 'fix_qt_plugins.py'], 
                                      capture_output=True, text=True, cwd=project_root)
            if fix_result.returncode == 0:
                print("Qt插件修复成功！")
            else:
                print(f"Qt插件修复失败：{fix_result.stderr}")
        except Exception as e:
            print(f"运行Qt插件修复脚本时出错：{e}")
        
        print("\n使用说明：")
        print("1. 如果遇到'no Qt platform plugin could be initialized'错误")
        print("2. 请手动运行：python fix_qt_plugins.py")
        print("3. 或者检查dist目录中是否包含plugins文件夹和qt.conf文件")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 构建过程中出现错误: {e}")
        return False
    
    return True

def build_launcher_with_nuitka(python_path, project_root):
    """使用虚拟环境中的Python和Nuitka构建启动器"""
    os.chdir(project_root)
    
    # 清理之前的构建
    build_dirs = ['launcher.build', 'launcher.dist', 'launcher.onefile-build']
    for build_dir in build_dirs:
        if os.path.exists(build_dir):
            print(f"清理构建目录: {build_dir}")
            shutil.rmtree(build_dir)
    
    # Nuitka 构建命令 (启动器)
    nuitka_cmd = [
        python_path, '-m', 'nuitka',
        '--standalone',
        '--windows-console-mode=disable',
        '--windows-icon-from-ico=res/logo.ico',
        '--output-filename=LovelyMem-Launcher.exe',
        '--output-dir=dist',
        
        # 包含必要的数据文件
        '--include-data-dir=config=config',
        '--include-data-dir=res=res',
        '--include-data-dir=font=font',
        '--include-data-dir=core=core',
        '--include-data-dir=ui=ui',
        
        '--include-qt-plugins=sensible,styles',
        '--assume-yes-for-downloads',
        '--show-progress',
        '--show-memory',
        
        'launcher.py'
    ]
    
    print("开始构建启动器...")
    print(f"构建命令: {' '.join(nuitka_cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(nuitka_cmd, check=True)
        
        print("-" * 60)
        print("✅ 启动器构建成功!")
        print(f"启动器位置: {project_root}/dist/LovelyMem-Launcher.exe")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动器构建失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 启动器构建过程中出现错误: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("LovelyMem Nuitka 虚拟环境打包工具")
    print("=" * 40)
    
    # 获取项目根目录
    project_root = os.path.abspath(os.path.dirname(__file__))
    
    # 虚拟环境路径
    venv_path = os.path.join(project_root, 'venv_build')
    requirements_file = os.path.join(project_root, 'requirements.txt')
    
    # 检查是否需要创建虚拟环境
    if not os.path.exists(venv_path):
        try:
            create_virtual_env(venv_path)
        except Exception as e:
            print(f"❌ 创建虚拟环境失败: {e}")
            return
    else:
        print(f"使用现有虚拟环境: {venv_path}")
    
    # 安装依赖
    try:
        python_path = install_requirements(venv_path, requirements_file)
    except Exception as e:
        print(f"❌ 安装依赖失败: {e}")
        return
    
    print("请选择要构建的程序:")
    print("1. 主程序 (main.py)")
    print("2. 启动器 (launcher.py)")
    print("3. 两个都构建")
    
    choice = input("请输入选择 (1/2/3): ").strip()
    
    if choice == '1':
        build_with_nuitka(python_path, project_root)
    elif choice == '2':
        build_launcher_with_nuitka(python_path, project_root)
    elif choice == '3':
        print("构建主程序...")
        if build_with_nuitka(python_path, project_root):
            print("\n构建启动器...")
            build_launcher_with_nuitka(python_path, project_root)
    else:
        print("无效选择")

if __name__ == '__main__':
    main()