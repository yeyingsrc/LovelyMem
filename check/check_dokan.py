import ctypes
import os

def check_dokan_installed():
    # 尝试加载 dokan2.dll
    try:
        # 尝试加载系统目录中的 dokan2.dll
        dokan_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'dokan2.dll')
        dokan_lib = ctypes.CDLL(dokan_path)

        # 检查是否成功加载
        if dokan_lib:
            print("Dokan 已安装。")
            return True
    except OSError:
        print("Dokan 未安装。在\"前置包必装\"中查找安装[2]DokanSetup2.1.exe,若安装失败请安装DokanSetup2.0.6.exe")
        return False

if __name__ == "__main__":
    check_dokan_installed()
