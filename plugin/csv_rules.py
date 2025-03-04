from PySide6.QtWidgets import QMenu

# 定义不同CSV文件的读取规则

def default_rule(row):
    return row

def a_csv_rule(row):
    # 对A.csv的特殊处理
    return [cell.strip() for cell in row]

def b_csv_rule(row):
    # 对B.csv的特殊处理
    return [cell.upper() for cell in row]

def default_context_menu(widget):
    context_menu = QMenu(widget)
    actions = {
        "删除所选列": widget.delete_column,
        "删除所选行": widget.delete_row,
        "打开文件所在目录(需memprocfs正常加载)": widget.open_directory,
        "快速查看文本": widget.quickly_view,
        "快速查看图片": widget.quickly_view_img,
        "hex转字符串": widget.hex_to_str,
        "将该行内容转为新的表格打开": widget.open_new_table,
    }

    for action_name, action_func in actions.items():
        action = context_menu.addAction(action_name)
        action.triggered.connect(action_func)

    return context_menu  # 确保返回创建的菜单
def regax_context_menu(widget):
    context_menu = QMenu(widget)
    actions = {
        "打开文件所在目录(需memprocfs正常加载)": widget.open_directory,
        "快速查看文本": widget.quickly_view,
        "快速查看图片": widget.quickly_view_img,
        "hex转字符串": widget.hex_to_str,
        "导出该文件(选择offset列,vol2)": widget.export_file_vol2,
        "导出该文件(选择offset列,vol3)": widget.export_file_vol3,
        "通过GIMP打开程序内存(选择PID列,memprocfs途径)": widget.proc_to_gimp_memprocfs,
        "通过GIMP打开程序内存(选择PID列,vol2途径,找不到内容试试这个)": widget.proc_to_gimp_vol2,
        "通过GIMP打开程序内存(选择PID列,vol3途径)": widget.proc_to_gimp_vol3,
        "查看该进程内存中的字符串(选择PID列)": widget.proc_to_strings,
        "转储进程的可执行文件(选择PID列,vol2)": widget.procdump_vol2,
        "转储进程的可执行文件(选择PID列,vol3)": widget.procdump_vol3,
    }

    for action_name, action_func in actions.items():
        action = context_menu.addAction(action_name)
        action.triggered.connect(action_func)

    return context_menu  # 确保返回创建的菜单
def userassist_context_menu(widget):
    context_menu = QMenu(widget)
    actions = {
        "删除所选列": widget.delete_column,
        "删除所选行": widget.delete_row,
    }

    for action_name, action_func in actions.items():
        action = context_menu.addAction(action_name)
        action.triggered.connect(action_func)

    return context_menu

def vol2_file_context_menu(widget):
    context_menu = QMenu(widget)
    actions = {
        "删除所选列": widget.delete_column,
        "删除所选行": widget.delete_row,
        "导出该文件(选择offset列,vol2)": widget.export_file_vol2,
        "打开文件所在目录(需memprocfs正常加载)": widget.open_directory,
        "快速查看文本(需memprocfs正常加载)": widget.quickly_view,
        "快速查看图片(需memprocfs正常加载)": widget.quickly_view_img,
    }

    for action_name, action_func in actions.items():
        action = context_menu.addAction(action_name)
        action.triggered.connect(action_func)

    return context_menu    
def vol3_file_context_menu(widget):
    context_menu = QMenu(widget)
    actions = {
        "删除所选列": widget.delete_column,
        "删除所选行": widget.delete_row,
        "导出该文件(选择offset列,vol3)": widget.export_file_vol3,
        "打开文件所在目录(需memprocfs正常加载)": widget.open_directory,
        "快速查看文本(需memprocfs正常加载)": widget.quickly_view,
        "快速查看图片(需memprocfs正常加载)": widget.quickly_view_img,
    }

    for action_name, action_func in actions.items():
        action = context_menu.addAction(action_name)
        action.triggered.connect(action_func)

    return context_menu
def pslist_context_menu(widget):
    context_menu = QMenu(widget)
    actions = {
        "删除所选列": widget.delete_column,
        "删除所选行": widget.delete_row,
        "通过GIMP打开程序内存(选择PID列,memprocfs途径)": widget.proc_to_gimp_memprocfs,
        "通过GIMP打开程序内存(选择PID列,vol2途径,找不到内容试试这个)": widget.proc_to_gimp_vol2,
        "通过GIMP打开程序内存(选择PID列,vol3途径)": widget.proc_to_gimp_vol3,
        "查看该进程内存中的字符串(选择PID列)": widget.proc_to_strings,
        "转储进程的可执行文件(选择PID列,vol2)": widget.procdump_vol2,
        "转储进程的可执行文件(选择PID列,vol3)": widget.procdump_vol3,
        "复制该程序所需的所有文件(选择PID列)": widget.proc_to_files,
        "句柄信息(选择PID列)": widget.proc_to_handle,
        "权限标识(选择PID列)": widget.proc_to_flags,
        "该程序加载的模块版本信息表(选择PID列)": widget.proc_to_verinfo,
    }

    for action_name, action_func in actions.items():
        action = context_menu.addAction(action_name)
        action.triggered.connect(action_func)

    return context_menu

def tasks_context_menu(widget):
    context_menu = QMenu(widget)
    actions = {
        "该任务注册表相关信息(选择taskname列)": widget.task_to_regedit,
    }
    for action_name, action_func in actions.items():
        action = context_menu.addAction(action_name)
        action.triggered.connect(action_func)

    return context_menu
def services_context_menu(widget):
    context_menu = QMenu(widget)
    actions = {
        "该服务注册表相关信息(选择Ordinal列)": widget.server_to_regedit,
    }
    for action_name, action_func in actions.items():
        action = context_menu.addAction(action_name)
        action.triggered.connect(action_func)

    return context_menu
def no_context_menu(widget):
    return None

csv_rules = {
    'output_vol2_userassist.csv': {'process': default_rule, 'menu': userassist_context_menu},
    'output_vol2_filescan.csv': {'process': default_rule, 'menu': vol2_file_context_menu},
    'output_vol3_filescan.csv': {'process': default_rule, 'menu': vol3_file_context_menu},
    'output_vol2_pslist.csv': {'process': default_rule, 'menu': pslist_context_menu},
    'process.csv': {'process': default_rule, 'menu': pslist_context_menu},
    'tasks.csv': {'process': default_rule, 'menu': tasks_context_menu},
    'services.csv': {'process': default_rule, 'menu': services_context_menu},
}

def get_rule(filename):
    rule = csv_rules.get(filename, {'process': default_rule, 'menu': default_context_menu})
    return rule['process'], rule['menu']