def search_hidden_process():
    """
    搜索隐藏进程 - 通过查找 proc-time.txt 中标记为 E, 32E 或 64E 的进程
    结果保存为CSV格式
    """
    try:
        import csv
        import os
        from datetime import datetime
        
        # 读取 proc-time.txt 文件
        proc_time_path = r'M:\sys\proc\proc-time.txt'
        with open(proc_time_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        hidden_processes = []
        # 跳过标题行，从数据行开始解析
        for line in lines[2:]:
            parts = line.split()
            if len(parts) < 4:
                continue
            
            # 查找标记为 E, 32E 或 64E 的进程
            flag = parts[3] if len(parts) > 3 else ''
            if flag in ['E', '32E', '64E']:
                process_info = {
                    'name': parts[0],
                    'pid': parts[1],
                    'parent': parts[2],
                    'flag': flag
                }
                hidden_processes.append(process_info)
        
        # 确保输出目录存在
        os.makedirs('output', exist_ok=True)
        
        # 输出结果到CSV文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f'output/hidden_processes_{timestamp}.csv'
        
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            # 写入标题行
            writer.writerow(['进程名', 'PID', '父PID', '标记'])
            # 写入数据行
            for proc in hidden_processes:
                writer.writerow([proc['name'], proc['pid'], proc['parent'], proc['flag']])
                print(f"进程名: {proc['name']}, PID: {proc['pid']}, 父PID: {proc['parent']}, 标记: {proc['flag']}")
        
        print(f"发现 {len(hidden_processes)} 个隐藏进程，已保存到 {output_path}")
        return hidden_processes
    except Exception as e:
        print(f"搜索隐藏进程时出错: {str(e)}")
        return []



