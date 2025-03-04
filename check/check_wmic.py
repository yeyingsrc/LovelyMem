import subprocess

def check_wmic():
    try:
        # 尝试运行 `wmic` 命令
        result = subprocess.run(['wmic', 'os', 'get', 'caption'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 检查命令是否成功
        if result.returncode == 0:
            print("WMIC 已安装.")
            return True
        else:
            print("WMIC 未安装请管理员权限执行安装(包括后面的波浪号): DISM /Online /Add-Capability /CapabilityName:WMIC~~~~")
            return False
    except FileNotFoundError:
        print("WMIC 未安装请管理员权限执行安装(包括后面的波浪号): DISM /Online /Add-Capability /CapabilityName:WMIC~~~~")
        return False

if __name__ == "__main__":
    check_wmic()
