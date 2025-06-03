# LovelyMem 使用说明书

本文档介绍了如何安装、配置和使用 LovelyMem，一款基于 **MemProcFS**、**Volatility2** 和 **Volatility3** 的可视化内存取证工具。

## 1. 准备工作

1. **安装依赖**：确保系统安装 Python3（推荐 3.10）。在项目根目录执行：

   ```bash
   pip install -r requirements.txt
   ```

2. **准备外部工具**：根据 `config/base_config.yaml` 配置外部工具路径，或在软件中通过“高级功能 -> 设置”进行图形化配置。配置示例如下：

   ```yaml
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

3. **系统组件**：程序启动时会检查是否安装 Dokan（用于挂载内存文件）。如未安装，请到 [Dokan 官方仓库](https://github.com/dokan-dev/dokany/releases) 下载并安装。

## 2. 启动程序

配置完成后，在项目根目录运行：

```bash
python launcher.py
```

启动后将进入图形界面，可在首次启动的欢迎界面中查看基本说明并选择是否显示下次提示。

## 3. 界面与功能

LovelyMem 集成多项取证相关功能，主要包括：

- **工具集成**：集中调用 `MemProcFS`、`Volatility2`、`Volatility3` 等取证工具。
- **快速检查**：常用取证命令一键执行，加快分析流程。
- **任务编排**：自定义任务流，批量执行多项操作。
- **报告编辑器**：在界面内查看并编辑取证结果，生成报告。
- **AI 助手**：可配置 OpenAI 兼容接口，对取证结果进行智能分析。
- **配置管理**：图形化设置工具路径、代理与 LLM 参数，支持主题与字体个性化。

界面主要区域包括文件槽、命令输出窗口及插件面板。可将文件拖入文件槽或通过菜单选择目标文件。各面板均支持独立窗口模式，方便根据需求调整布局。

## 4. 插件与扩展

LovelyMem 支持插件机制，扩展位于 `extensions` 目录。插件以 Python 文件形式存在，并包含 `plugin_info` 元数据与 `run(file_path)` 函数。例如，解压缩插件示例：

```python
plugin_info = {
    "title": "解压文件",
    "description": "解压ZIP、RAR等压缩文件",
    "usage": "选择一个压缩文件,然后点击此插件",
    "category": "文件操作"
}

def run(file_path):
    # 处理代码...
    pass
```

可参考现有插件进行编写，将脚本放入 `extensions` 目录后重启程序即可加载。

## 5. 常见问题

1. **项目适用场景？** 适用于一般 Windows 内存取证及没有过度混淆的取证题目。
2. **开源后是否持续维护？** 作者表示会在时间允许的情况下继续更新并欢迎社区参与。

## 6. 相关链接

- 项目主页：[GitHub - LovelyMem](https://github.com/Tokeii0/LovelyMem)
- 视频演示：[Bilibili 演示视频](https://www.bilibili.com/video/BV1z912YpECB)

希望本说明书能够帮助您顺利使用 LovelyMem 进行内存取证分析。

