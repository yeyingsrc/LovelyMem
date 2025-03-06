from plugin.QuicklyView import QuicklyView
import shutil
import os   
import glob
from lovelyform import show_csv_viewer


class memprocfsplugin:
    def __init__(self, parent):
        self.parent = parent

    def loadproc(self):
        procpath = r'M:/forensic/csv/process.csv'
        show_csv_viewer(procpath)
        shutil.copy(procpath, 'output/process.csv')

    def load_netstat(self):
        netstatpath = r'M:/forensic/csv/net.csv'
        show_csv_viewer(netstatpath)
        shutil.copy(netstatpath, 'output/net.csv')

    def load_handles(self):
        handlespath = r'M:/forensic/csv/handles.csv'
        show_csv_viewer(handlespath)
        shutil.copy(handlespath, 'output/handles.csv')

    def copy_all_certificates2output(self):
        certificates_path = r'M:/sys/certificates'
        shutil.copytree(certificates_path, 'output/certificates')
        print('导出全部证书完成')
        certificates_txt_path = r'M:/sys/certificates/certificates.txt'
        self.new_window_memprofs_certificates_txt = QuicklyView('MemPorcfs-证书', size=(500, 900))
        self.new_window_memprofs_certificates_txt.load_file_content(certificates_txt_path)
        self.new_window_memprofs_certificates_txt.show()
        
    def loadtasks(self):
        taskspath = r'M:/forensic/csv/tasks.csv'
        show_csv_viewer(taskspath)
        shutil.copy(taskspath, 'output/tasks.csv')

    def loaddrivers(self):
        driverspath = r'M:/forensic/csv/drivers.csv'
        show_csv_viewer(driverspath)
        shutil.copy(driverspath, 'output/drivers.csv')
        
    def loadallfiles(self):
        allfilespath = r'M:/forensic/csv/files.csv'
        show_csv_viewer(allfilespath)

    def loadfindevil(self):
        findevilpath = r'M:/forensic/csv/findevil.csv'
        show_csv_viewer(findevilpath)
        shutil.copy(findevilpath, 'output/findevil.csv')
        
    def loadnetstat_timeline(self):
        netstat_timelinepath = r'M:/forensic/csv/timeline_net.csv'
        show_csv_viewer(netstat_timelinepath)
        shutil.copy(netstat_timelinepath, 'output/net_timeline.csv')
        
    def loadntfs_timeline(self):
        ntfs_timelinepath = r'M:/forensic/csv/timeline_ntfs.csv'
        show_csv_viewer(ntfs_timelinepath)
        shutil.copy(ntfs_timelinepath, 'output/ntfs_timeline.csv')
        
    def loadproc_timeline(self):
        proc_timelinepath = r'M:/forensic/csv/timeline_process.csv'
        show_csv_viewer(proc_timelinepath)
        shutil.copy(proc_timelinepath, 'output/proc_timeline.csv')
    
    def loadtasks_timeline(self):
        tasks_timelinepath = r'M:/forensic/csv/timeline_tasks.csv'
        show_csv_viewer(tasks_timelinepath)
        shutil.copy(tasks_timelinepath, 'output/task_timeline.csv')
        
    def loadweb_timeline(self):
        web_timelinepath = r'M:/forensic/csv/timeline_web.csv'
        show_csv_viewer(web_timelinepath)
        shutil.copy(web_timelinepath, 'output/web_timeline.csv')
        
    def loadservices(self):
        servicespath = r'M:/forensic/csv/services.csv'
        show_csv_viewer(servicespath)
        shutil.copy(servicespath, 'output/services.csv')

    def yara_scan(self):
        yarapath = r'M:/forensic/csv/yara.csv'
        show_csv_viewer(yarapath)
        shutil.copy(yarapath, 'output/yara.csv')
    
    def yara_detail(self):
        yaradetailpath = r'M:/forensic/findevil/yara.txt'
        self.new_window_memprofs_yara_detail = QuicklyView('MemPorcfs-Yara详情', size=(666, 900))
        self.new_window_memprofs_yara_detail.load_file_content(yaradetailpath)
        self.new_window_memprofs_yara_detail.show()
        
    def loadtimeline_registry(self):
        registrypath = r'M:/forensic/csv/timeline_registry.csv'
        show_csv_viewer(registrypath)
        shutil.copy(registrypath, 'output/registry_timeline.csv')

    def timeline_prefetch(self):
        prefetchpath = r'M:/forensic/csv/timeline_prefetch.csv'
        show_csv_viewer(prefetchpath)
        shutil.copy(prefetchpath, 'output/prefetch_timeline.csv')
    
    def alltimeline(self):
        alltimelinepath = r'M:/forensic/csv/timeline_all.csv'
        show_csv_viewer(alltimelinepath)
        shutil.copy(alltimelinepath, 'output/timeline_all.csv')
    
    def systeminfo(self):
        systeminfopath = r"M:\sys\sysinfo\sysinfo.txt"
        self.new_window_memprofs_systeminfo = QuicklyView('MemPorcfs-系统信息', (800, 600))
        self.new_window_memprofs_systeminfo.load_file_content(systeminfopath)
        self.new_window_memprofs_systeminfo.show()
        shutil.copy(systeminfopath, 'output/systeminfo.txt')

    # 获取产品id M:\registry\HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProductId
    def get_product_id(self):
        product_txt = r'M:/registry/HKLM/SOFTWARE/Microsoft/Windows NT/CurrentVersion/ProductId'
        self.new_window_memprofs_product_id = QuicklyView('MemPorcfs-产品id', (800, 600))
        self.new_window_memprofs_product_id.load_file_content(product_txt)
        self.new_window_memprofs_product_id.show()
        shutil.copy(product_txt, 'output/product_id.txt')
        print('导出产品id完成')
        

    def copy_alleventlog2output(self):
        eventlog_path = r'M:/misc/eventlog'
        shutil.copytree(eventlog_path, 'output/eventlog')
        print('导出全部Eventlog完成')

    def copy_all_registry2output(self):
        registry_path = r'M:/registry/hive_files'
        shutil.copytree(registry_path, 'output/registry_memprocfs')
        print('导出全部注册表完成')

    def lovelymem_checkRun(self):
        import os
        with open(r'M:/sys/users/users.txt', 'r') as f:
            for line in f:
                if line.startswith('0000'):
                    username = line.split()[1]
                    break
        run_path = r'M:/registry/HKLM/SOFTWARE/Microsoft/Windows/CurrentVersion/Run'
        runlist = []
        for root, dirs, files in os.walk(run_path):
            for file in files:
                if file.endswith('.txt') and file != '(_Key_).txt':
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                        if len(lines) >= 3:
                            third_line = lines[2].strip()
                            name = file.split('.')[0]
                            runlist.append(f"{name}: {third_line}")
        runlist = list(set(runlist))

        run2_path = rf'M:\registry\HKU\{username}\SOFTWARE\Microsoft\Windows\CurrentVersion\Run'
        for root, dirs, files in os.walk(run2_path):
            for file in files:
                if file.endswith('.txt') and file != '(_Key_).txt':
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                        if len(lines) >= 3:
                            third_line = lines[2].strip()
                            name = file.split('.')[0]
                            runlist.append(f"{name}: {third_line}")
        runlist = list(set(runlist))

        output_file = 'output/开机自启项目.txt'
        with open(output_file, 'w') as f:
            for item in runlist:
                f.write(f"{item}\n")

    def lovelymem_defaultbrowser(self):
        with open(r'M:/sys/users/users.txt', 'r') as f:
            for line in f:
                if line.startswith('0000'):
                    username = line.split()[1]
                    break
        
        try:
            http_browser = open(fr'M:/registry/HKU/{username}/SOFTWARE/Microsoft/Windows/Shell/Associations/UrlAssociations/http/UserChoice/ProgId', 'r')
            httpbrowser = http_browser.read()
            https_browser = open(fr'M:/registry/HKU/{username}/SOFTWARE/Microsoft/Windows/Shell/Associations/UrlAssociations/https/UserChoice/ProgId', 'r')
            httpsbrowser = https_browser.read()
            output_file = 'output/默认浏览器.txt'
            with open(output_file, 'w') as f:
                f.write(f"PS:AppXq0fevzme2pys62n3e0fbqa7peapykr8v为Edge\n")
                f.write(f"http默认浏览器：{httpbrowser}\n")
                f.write(f"https默认浏览器：{httpsbrowser}")
        except Exception as e:
            print(e)

    def lovelymem_ifeodebug(self):
        # M:\registry\HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options
        # 查看这个目录下包括子文件夹是否含有 "Debugger" 文件，如果有就是有疑似劫持
        try:
            ifeodebug_path = r'M:/registry/HKLM/SOFTWARE/Microsoft/Windows NT/CurrentVersion/Image File Execution Options'
            for root, dirs, files in os.walk(ifeodebug_path):
                if 'Debugger' in files:
                    # 读取该文件 内容 然后复制文件夹到output
                    file_path = os.path.join(root, 'Debugger')
                    with open(file_path, 'r') as f:
                        content = f.read()
                    # 复制文件夹到output
                    output_path = os.path.join('output', os.path.basename(root))
                    shutil.copytree(root, output_path)
                    # 输出到文件
                    output_file = 'output/ifeodebug.txt'
                    with open(output_file, 'w', encoding='utf-8') as f:
                        # 文件夹名+debugger内容
                        f.write(f"{os.path.basename(root)}:\n")
                        f.write(content.encode('utf-8').decode('utf-8', 'ignore'))
                    print('查找到有疑似劫持')
                    # 打印内容
                    print(content)
        except Exception as e:
            print(e)
        
            
        # "M:\registry\HKU\skills\SOFTWARE\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice\ProgId"


    

    def merge_console_txt_files(self, base_path=r'M:\name', output_dir='output', output_file='控制台输出.txt'):

        conhost_folders = glob.glob(os.path.join(base_path, '*conhost.exe*'))
        
        # 过滤掉非文件夹的路径
        conhost_folders = [folder for folder in conhost_folders if os.path.isdir(folder)]
        
        # 存储找到的 'console.txt' 文件路径
        console_txt_files = []
        
        # 遍历每个文件夹，查找 'console\console.txt' 文件
        for folder in conhost_folders:
            console_txt_path = os.path.join(folder, 'console', 'console.txt')
            if os.path.isfile(console_txt_path):
                console_txt_files.append(console_txt_path)
        
        # 如果没有找到文件，直接返回
        if not console_txt_files:
            return
        
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 输出文件的完整路径
        output_path = os.path.join(output_dir, output_file)
        
        # 打开输出文件，准备写入
        with open(output_path, 'w', encoding='utf-8') as outfile:
            for file_path in console_txt_files:
                # 写入每个文件的内容
                with open(file_path, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())
                    outfile.write('\n')  # 文件之间添加换行符
