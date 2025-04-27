import csv
import re

def convert_driver_to_csv(input_file='driver_irp.txt', output_file='driver_irp.csv'):
    input_file = r"M:\sys\drivers\driver_irp.txt"
    output_file = r"output\driver_irp.csv"
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 过滤掉无关的头部、分隔线
    data_lines = []
    for line in lines:
        if re.match(r'^[0-9a-fA-F]{4}\s', line):  # 每行以4位hex数开头
            data_lines.append(line.strip())

    # 处理成表格数据
    rows = []
    for line in data_lines:
        # 按空白分隔，但Driver名字可能包含空格，所以稍微复杂点处理
        parts = re.split(r'\s+', line, maxsplit=3)
        if len(parts) == 4:
            number, driver, irp_mj, rest = parts
            address, target_module = rest.rsplit(' ', 1)
            rows.append([number, driver, irp_mj, address, target_module])

    # 写入 CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Number', 'Driver', 'IRP_MJ', 'Address', 'Target_Module'])  # 写表头
        writer.writerows(rows)
    
    print(f'转换完成！输出文件是 {output_file}')
