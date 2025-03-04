from plugin.NewtableWidget import NewtableWidget
from plugin.QuicklyView import QuicklyView
import shutil
import os
from lovelyform import show_csv_viewer


class memprocfsplugin:
    def __init__(self, parent):
        self.parent = parent
    # def loadproc(self):
    #     procpath = r'M:/forensic/csv/process.csv'
    #     self.new_window = NewtableWidget(procpath, 'MemPorcfs-进程信息')
    #     self.new_window.show()
    #     #复制一份到output文件夹
    #     shutil.copy(procpath, 'output/process.csv')
    def loadproc(self):
        procpath = r'M:/forensic/csv/process.csv'
        show_csv_viewer(procpath)
        shutil.copy(procpath, 'output/process.csv')

        
        
    def load_netstat(self):
        netstatpath = r'M:/forensic/csv/net.csv'
        self.new_window_memprofs_netstat = NewtableWidget(netstatpath, 'MemPorcfs-网络信息')
        self.new_window_memprofs_netstat.show()
        #复制一份到output文件夹
        shutil.copy(netstatpath, 'output/net.csv')
    def load_handles(self):
        handlespath = r'M:/forensic/csv/handles.csv'
        self.new_window_memprofs_handles = NewtableWidget(handlespath, 'MemPorcfs-句柄信息')
        self.new_window_memprofs_handles.show()
        #复制一份到output文件夹
        shutil.copy(handlespath, 'output/handles.csv')
    def copy_all_certificates2output(self):
        # M:\sys\certificates
        certificates_path = r'M:/sys/certificates'
        shutil.copytree(certificates_path, 'output/certificates')
        print('导出全部证书完成')
        # Quicklyview "M:\sys\certificates\certificates.txt"
        certificates_txt_path = r'M:/sys/certificates/certificates.txt'
        self.new_window_memprofs_certificates_txt = QuicklyView('MemPorcfs-证书', size=(500, 900))
        self.new_window_memprofs_certificates_txt.load_file_content(certificates_txt_path)
        self.new_window_memprofs_certificates_txt.show()
        
    def loadtasks(self):
        taskspath = r'M:/forensic/csv/tasks.csv'
        self.new_window_memprofs_tasks = NewtableWidget(taskspath, 'MemPorcfs-Tasks')
        self.new_window_memprofs_tasks.show()
        #复制一份到output文件夹
        shutil.copy(taskspath, 'output/tasks.csv')

    def loaddrivers(self):
        driverspath = r'M:/forensic/csv/drivers.csv'
        self.new_window_memprofs_drivers = NewtableWidget(driverspath, 'MemPorcfs-驱动程序')
        self.new_window_memprofs_drivers.show()
        #复制一份到output文件夹
        shutil.copy(driverspath, 'output/drivers.csv')

        
        
    # def loadallfiles(self):
    #     allfilespath = r'M:/forensic/csv/files.csv'
    #     self.new_window_memprofs_allfiles = NewtableWidget(allfilespath, 'MemPorcfs-所有文件')
    #     self.new_window_memprofs_allfiles.show()
    #     #复制一份到output文件夹
    #     shutil.copy(allfilespath, 'output/files.csv')
        
    def loadallfiles(self):
        
        allfilespath = r'M:/forensic/csv/files.csv'
        show_csv_viewer(allfilespath)

        
    def loadfindevil(self):
        findevilpath = r'M:/forensic/csv/findevil.csv'
        self.new_window_memprofs_findevil = NewtableWidget(findevilpath, 'MemPorcfs-恶意软件检测')
        self.new_window_memprofs_findevil.show()
        #复制一份到output文件夹
        shutil.copy(findevilpath, 'output/findevil.csv')
        
    def loadnetstat_timeline(self):
        netstat_timelinepath = r'M:/forensic/csv/timeline_net.csv'
        self.new_window_memprofs_netstat_timeline = NewtableWidget(netstat_timelinepath, 'MemPorcfs-网络时间线')
        self.new_window_memprofs_netstat_timeline.show()
        shutil.copy(netstat_timelinepath, 'output/net_timeline.csv')
        
        
    def loadntfs_timeline(self):
        ntfs_timelinepath = r'M:/forensic/csv/timeline_ntfs.csv'
        self.new_window_memprofs_ntfs_timeline = NewtableWidget(ntfs_timelinepath, 'MemPorcfs-NTFS文件时间线')
        self.new_window_memprofs_ntfs_timeline.show()
        shutil.copy(ntfs_timelinepath, 'output/ntfs_timeline.csv')
        
        
    def loadproc_timeline(self):
        proc_timelinepath = r'M:/forensic/csv/timeline_process.csv'
        self.new_window_memprofs_proc_timeline = NewtableWidget(proc_timelinepath, 'MemPorcfs-进程时间线')
        self.new_window_memprofs_proc_timeline.show()
        shutil.copy(proc_timelinepath, 'output/proc_timeline.csv')
    
    def loadtasks_timeline(self):
        tasks_timelinepath = r'M:/forensic/csv/timeline_tasks.csv'
        self.new_window_memprofs_tasks_timeline = NewtableWidget(tasks_timelinepath, 'MemPorcfs-Tasks时间线')
        self.new_window_memprofs_tasks_timeline.show()
        shutil.copy(tasks_timelinepath, 'output/task_timeline.csv')
        
        
    def loadweb_timeline(self):
        web_timelinepath = r'M:/forensic/csv/timeline_web.csv'
        self.new_window_memprofs_web_timeline = NewtableWidget(web_timelinepath, 'MemPorcfs-Web时间线')
        self.new_window_memprofs_web_timeline.show()
        shutil.copy(web_timelinepath, 'output/web_timeline.csv')
        
        
        
    def loadservices(self):
        servicespath = r'M:/forensic/csv/services.csv'
        self.new_window_memprofs_services = NewtableWidget(servicespath, 'MemPorcfs-服务')
        self.new_window_memprofs_services.show()
        #复制一份到output文件夹
        shutil.copy(servicespath, 'output/services.csv')
    def yara_scan(self):
        yarapath = r'M:/forensic/csv/yara.csv'
        self.new_window_memprofs_yara = NewtableWidget(yarapath, 'MemPorcfs-Yara结果')
        self.new_window_memprofs_yara.show()
        #复制一份到output文件夹
        shutil.copy(yarapath, 'output/yara.csv')
    
    def yara_detail(self):
        # "M:\forensic\findevil\yara.txt"
        yaradetailpath = r'M:/forensic/findevil/yara.txt'
        self.new_window_memprofs_yara_detail = QuicklyView('MemPorcfs-Yara详情', size=(666, 900))
        self.new_window_memprofs_yara_detail.load_file_content(yaradetailpath)
        self.new_window_memprofs_yara_detail.show()
        
    def loadtimeline_registry(self):
        registrypath = r'M:/forensic/csv/timeline_registry.csv'
        self.new_window_memprofs_registry = NewtableWidget(registrypath, 'MemPorcfs-注册表时间线')
        self.new_window_memprofs_registry.show()
        #复制一份到output文件夹
        shutil.copy(registrypath, 'output/registry_timeline.csv')
    def timeline_prefetch(self):
        prefetchpath = r'M:/forensic/csv/timeline_prefetch.csv'
        self.new_window_memprofs_prefetch = NewtableWidget(prefetchpath, 'MemPorcfs-Prefetch时间线')
        self.new_window_memprofs_prefetch.show()
        #复制一份到output文件夹
        shutil.copy(prefetchpath, 'output/prefetch_timeline.csv')
    # timeline_all.csv    
    def alltimeline(self):
        alltimelinepath = r'M:/forensic/csv/timeline_all.csv'
        self.new_window_memprofs_alltimeline = NewtableWidget(alltimelinepath, 'MemPorcfs-所有时间线')
        self.new_window_memprofs_alltimeline.show()
        #复制一份到output文件夹
        shutil.copy(alltimelinepath, 'output/timeline_all.csv')
    
    def systeminfo(self):
        systeminfopath = r"M:\sys\sysinfo\sysinfo.txt"
        self.new_window_memprofs_systeminfo = QuicklyView('MemPorcfs-系统信息', (800, 600))
        self.new_window_memprofs_systeminfo.load_file_content(systeminfopath)
        self.new_window_memprofs_systeminfo.show()
        #复制一份到output文件夹
        shutil.copy(systeminfopath, 'output/systeminfo.txt')

    def copy_alleventlog2output(self):
        # M:\misc\eventlog,拷贝文件夹到output
        eventlog_path = r'M:/misc/eventlog'
        shutil.copytree(eventlog_path, 'output/eventlog')
        print('导出全部Eventlog完成')
    def copy_all_registry2output(self):
        # M:\registry\hive_files
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
        # 除 "(_Key_).txt" 外的所有txt 内容第三行，文件名spilt('.')[0]:第三行内容
        for root, dirs, files in os.walk(run_path):
            for file in files:
                if file.endswith('.txt') and file != '(_Key_).txt':
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                        if len(lines) >= 3:
                            third_line = lines[2].strip()
                            # file spilt('.')[0]:第三行内容
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
                            # file spilt('.')[0]:第三行内容
                            name = file.split('.')[0]
                            runlist.append(f"{name}: {third_line}")
        runlist = list(set(runlist))

        
        output_file = 'output/开机自启项目.txt'
        with open(output_file, 'w') as f:
            for item in runlist:
                f.write(f"{item}\n")

        # self.new_window_memprofs_lovelymem_checkRun = QuicklyView('MemPorcfs-开机自启项目', size=(666, 900))
        # self.new_window_memprofs_lovelymem_checkRun.load_file_content(output_file)
        # self.new_window_memprofs_lovelymem_checkRun.show()


        
    def lovelymem_defaultbrowser(self):
        # First read the username from users.txt
        with open(r'M:/sys/users/users.txt', 'r') as f:
            for line in f:
                if line.startswith('0000'):
                    username = line.split()[1]
                    break
        
        # Read browser settings using the found username
        try:
            http_browser = open(fr'M:/registry/HKU/{username}/SOFTWARE/Microsoft/Windows/Shell/Associations/UrlAssociations/http/UserChoice/ProgId', 'r')
            httpbrowser = http_browser.read()
            https_browser = open(fr'M:/registry/HKU/{username}/SOFTWARE/Microsoft/Windows/Shell/Associations/UrlAssociations/https/UserChoice/ProgId', 'r')
            httpsbrowser = https_browser.read()
                    # Output to file
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