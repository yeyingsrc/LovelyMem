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



### 这是什么
一款基于memprocfs、Volatility2、Volatility3的快捷内存取证工具

区别于VolatilityPro：https://github.com/Tokeii0/VolatilityPro

有着更快的取证速度以及更便捷的功能

视频展示：https://www.bilibili.com/video/BV1z912YpECB

### 界面展示
![image](https://github.com/user-attachments/assets/22f8c9e5-f85e-4f29-baa0-914bda63c09b)

### 具体准备
根据config文件夹下面的base_config.yaml自助配置以下内容
```
tools:
  memprocfs:
    path: "../Tools/MemProcFS/MemProcFS.exe"
  volatility2:
    path: "../Tools/volatility2/vol.exe"
  volatility2_python:
    path: "../Tools/volatility2_python/vol.py"
  volatility3:
    path: "../Tools/volatility3/vol.py"
  volatility3_symbols:
    path: "../Tools/volatility3/symbols"
  gimp:
    path: "../Tools/gimp/bin/gimp-console-2.10.exe"
  volatility2_plugin:
    path: "../Tools/volatility2_plugin"

base_tools:
  python310:
    path: "../Tools/python3/python.exe"
  python27:
    path: "../Tools/python27/python27.exe" 
  strings:
    path: "../Tools/other/strings.exe"

other_tools:
  RegistryExplorer:
    path: "../Tools/RegistryExplorer/RegistryExplorer.exe"
  EvtxECmd:
    path: "../Tools/EvtxECmd/EvtxECmd.exe"
```


### 适合什么题
  - 没有套娃的取证题目
  - *Windows*内存取证
  
### 几个问题

Q:为什么一开始收费，突然就现在开源？

A：在项目开始收费的时候就立了个flag,要么star1000,要么被人逆了，很明显为什么

Q:开源之后还更新吗

A:更啊,这个项目是我第一个这么高star的项目，只要我有时间就会一直更新，也希望各位师傅多多参与~




### 其他

远离内卷，还CTF圈一个朗朗乾坤

愿望是取证像喝水一样简单

### Star History Chart
 
[![Star History Chart](https://api.star-history.com/svg?repos=Tokeii0/LovelyMem&type=Date)](https://star-history.com/#Tokeii0/LovelyMem&Date)

