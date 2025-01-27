<!-- markdownlint-disable MD033 MD041 -->
<p align="center">
  <a href="https://ctf.dog"><img src="https://github.com/Tokeii0/LovelyMem/blob/NewWorld/res/logo_200.png" width="250" height="250" alt="lovelymem"></a>
</p>
<div align="center">

# LovelyMem

<!-- prettier-ignore-start -->
<!-- markdownlint-disable-next-line MD036 -->
_✨ 基于*Memprocfs*和*Volatility*的可视化内存取证工具 ✨_
<!-- prettier-ignore-end -->
<a href="https://jq.qq.com/?_wv=1027&k=DzOtbzU4"><img src="https://img.shields.io/badge/QQ%E7%BE%A4-856729462-orange?style=flat-square" alt="QQGroup"></a>
  <a href="http://ctf.dog"><img src="https://img.shields.io/badge/CTF%E5%AF%BC%E8%88%AA%E7%AB%99-ctf.dog-5492ff?style=flat-square" alt="ctfnav"></a>
  <a href=".."><img src="https://img.shields.io/badge/Python%20-%203.10.11-def1f2?style=flat-square" alt="python"></a>
</div>

### 相关流程
1. 进群 856729462
2. 群文件下载 最新版本软件 ，替换最新的授权服务器更换文件
3. 在线授权直接在群内 发送 #获取授权，然后根据提示发送授权码即可
4. 如果要离线授权，私聊 群主 即可
5. 在线授权用户退群=永久放弃授权(一般来说退群不会删除授权，再进群被我发现了就会删除)


### 这是什么
一款基于memprocfs、Volatility2、Volatility3的快捷内存取证工具

区别于VolatilityPro：https://github.com/Tokeii0/VolatilityPro

有着更快的取证速度以及更便捷的功能

视频展示：https://www.bilibili.com/video/BV1z912YpECB

### 界面展示
![image](https://github.com/user-attachments/assets/345a5fe9-f1cc-489a-99c4-100c619bf788)
![image](https://github.com/user-attachments/assets/849bf2ae-5074-44e7-9235-f9b18ac9b836)
![image](https://github.com/user-attachments/assets/9c5acea2-1522-41ea-ac1e-e41ad941a609)

### 适合什么题
  - 没有套娃的取证题目
  - *Windows*内存取证
### 更新
![image](https://github.com/user-attachments/assets/7104b3cd-8023-4909-9268-bc65d495211e)

### 各种文档
- 软件使用说明书(持续更新)：
https://docs.qq.com/doc/DWGt4YU1nd1VuTW9k
- 常见问题解决：
https://docs.qq.com/doc/DWGdId2VKU05mVWN0
- 升级须知+离线须知
https://docs.qq.com/doc/DWHlFclJuUklyRHBN
- 启动无反应(没有找到WMIC命令)
https://www.ithome.com/0/781/543.htm
  
### 你都更新了点啥

📌 **更新日志**  
1. 🎨 全新界面设计，提供上百种可选择的主题配色！  
2. 🛠️ 重写了标题栏及窗口控制按钮（关闭/最小化）。  
3. 🧰 **Memprocfs** 功能区域进行了基础功能和时间线的分类，新增系统信息查看功能，集成了 `systeminfo` 的内容。  
4. 🚀 在 **vol2** 区域，功能划分为六大类：基础功能、高级功能、系统信息、用户信息、文件导出和扩展功能。  
5. 🔍 **vol3** 区域采用了与 vol2 不同的分类方式：进程信息、系统信息、文件与网络、注册表、恶意代码检测、其他功能。后续会根据用户反馈考虑是否统一分类方式。  
6. 🐍 **vol2** 版本从封装好的 exe 程序转为 Python 2 版本，需在使用前安装 VCForPython27。  
7. 📁 **Tools** 分类从 `lovelymem` 文件夹移出，与其并列存放，若不适应可自行调整位置，并修改 `lovelymem/config/base_config.yaml` 文件。  
8. ⚡ 优化了 CSV 文件的读取速度，现在速度更快。  
9. 📊 为常用功能（如 `filescan`、`pslist`）设置了表格查看时的专用菜单。  
10. 🔎 表格内搜索现在直接显示在界面下方，不会弹出新窗口。  
11. 🚀 预设槽与正则槽支持快速任务执行，帮助你快速定位所需内容。  
12. 📚 新增 **vol2** 常备知识功能，方便学习使用。  
13. 🖥️ 现在支持通过 **memprocfs**、**vol2** 和 **vol3** 三种途径导出文件，支持快速将 `memdump` 转为 GIMP 文件。


### 其他

远离内卷，还CTF圈一个朗朗乾坤

愿望是取证像喝水一样简单

### Star History Chart
 
[![Star History Chart](https://api.star-history.com/svg?repos=Tokeii0/LovelyMem&type=Date)](https://star-history.com/#Tokeii0/LovelyMem&Date)

