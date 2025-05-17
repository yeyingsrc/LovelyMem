import memprocfs
import json
from datetime import datetime
from tqdm import tqdm

def find_hidden_processes(vmm, verbose=True, save_results=False):
    """
    通过读取 /sys/proc/proc.txt（其中Flag='E'表示脱链进程）来找隐藏进程。
    """
    # 1. 强制刷新所有缓存，保证 sysinfo 列表最新
    vmm.set_config(memprocfs.OPT_REFRESH_ALL, 1)

    # 2. 列出 sys/proc 目录下的文件，找到 proc.txt 大小
    proc_dir = vmm.vfs.list('/sys/proc')  # 返回 dict: { 'proc.txt': {'size':...}, ... }
    size = proc_dir['proc.txt']['size']

    # 3. 读取整个 proc.txt
    raw = vmm.vfs.read('/sys/proc/proc.txt', size)
    text = raw.decode('utf-8', errors='ignore')
    lines = text.splitlines()

    hidden = []
    # 跳过标题和分隔行，真正数据一般从第3行开始
    # 格式示例（空格分隔，Flag 列可能在第三或第四列）:
    # Process                  Pid Parent   Flag User      Create Time...
    # --------------------------------------------------------------------------------
    #  - csrss.exe             396    388        SYSTEM 2020-08-01 19:20:24 UTC   ***
    for line in tqdm(lines[2:], desc="解析 proc.txt", unit="行") if verbose else lines[2:]:
        parts = line.split()
        if len(parts) < 4:
            continue
        # 假定格式：Name, PID, Parent, Flag
        name = parts[0]
        pid  = parts[1]
        flag = parts[3]
        # 标记中含 'E' 即脱链（隐藏）进程
        if 'E' in flag:
            hidden.append({
                'pid':   int(pid),
                'name': name,
                'flag': flag,
                # 额外信息可以继续从 parts 拼接，比如 User、CreateTime
                'user': parts[4] if len(parts) > 4 else '',
                'create_time': ' '.join(parts[5:8]) if len(parts) > 7 else ''
            })
            if verbose:
                print(f"[!] 隐藏进程: PID={pid}, 名称={name}, Flag={flag}")

    if verbose:
        print(f"[*] 共发现 {len(hidden)} 个隐藏进程")

    # 4. 可选：保存到 JSON 文件
    if save_results and hidden:
        fn = f"hidden_{datetime.now():%Y%m%d_%H%M%S}.json"
        with open(fn, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'hidden_processes': hidden
            }, f, indent=4)
        if verbose:
            print(f"[+] 隐藏进程结果已保存到 {fn}")

    return hidden


def main():
    import sys, os
    if len(sys.argv) < 2:
        print("用法: python memprocfstest.py <内存镜像路径> [--quiet] [--save]")
        return

    memory_path = sys.argv[1]
    verbose = "--quiet" not in sys.argv
    save = "--save" in sys.argv

    if not os.path.exists(memory_path):
        print(f"[!] 内存镜像未找到: {memory_path}")
        return

    print(f"[+] 加载内存镜像: {memory_path}")
    vmm = memprocfs.Vmm(['-device', memory_path])

    try:
        hidden = find_hidden_processes(vmm, verbose, save)
        if not hidden:
            print("[+] 未发现隐藏进程")
    except Exception as e:
        print(f"[!] 错误: {e}")

if __name__ == "__main__":
    main()
