# LovelyMem 使用说明书

本文档详细介绍如何安装和使用 LovelyMem。该软件集成 **MemProcFS**、**Volatility2** 与 **Volatility3**，通过图形化界面提供快速的内存取证分析能力。

## 1. 环境准备

1. **安装 Python**：推荐使用 Python 3.10，并确保 `pip` 可用。
2. **安装依赖库**：在项目根目录执行：
   ```bash
   pip install -r requirements.txt
   ```
3. **获取外部取证工具**：下载 MemProcFS、Volatility2/3 等并放置在自定义目录。
4. **配置路径**：复制 `config/base_config.yaml` 为同名文件或在程序中"高级功能 -> 设置"图形化配置，示例：
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
5. **安装 Dokan**：程序启动会检查 Dokan，用于挂载内存映像。若未安装，请从 [Dokan Releases](https://github.com/dokan-dev/dokany/releases) 下载并安装。

## 2. 启动与初始化

1. 在命令行运行：
   ```bash
   python launcher.py
   ```
2. 首次启动会显示欢迎界面，可选择是否下次再提示。
3. 进入主界面后，建议先在“高级功能 -> 设置”中确认工具路径、代理及主题等选项。

## 3. 基本操作流程

1. **载入内存文件**
   - 将内存镜像拖入窗口左侧的文件槽，或点击菜单选择文件。
   - 程序会在 `output` 目录创建处理结果。
2. **快速检查**
   - 点击“快速检查”可执行常见扫描，如搜索 flag 或敏感字符串，适合 CTF 场景快速获取线索。
3. **MemProcFS 模块**
   - 在“基础功能”中选择系统信息、进程信息或网络信息，调用 MemProcFS 快速解析并在表格中展示。
4. **Volatility2 模块**
   - 通过菜单或按钮运行诸如 `pslist`、`netscan`、`timeliner` 等插件。
   - 结果以 CSV 或文本形式保存在 `output/`，可在界面内直接查看。
5. **Volatility3 模块**
   - 针对较新系统，可切换到 Volatility3 进行分析，支持离线模式与导出内存段等操作。
6. **字典扫描与知识库**
   - 利用“字典扫描”插件匹配常见敏感词或路径。
   - “知识库”面板提供 Volatility 插件说明与示例，便于了解各插件用途。
7. **任务编排与批量执行**
   - 在“任务流”界面自定义节点，按顺序批量执行多个取证步骤。
   - 任务结果会依次输出到命令窗口，并在完成后生成报表。
8. **报告编辑器与导出**
   - 所有表格或文本结果均可一键导出到 `output/` 下，也可在“报告编辑器”中整理并生成最终报告。
9. **AI 助手（可选）**
   - 在设置中填入兼容 OpenAI 的接口和密钥后，可对结果进行自然语言分析和自动摘要。

## 4. 插件开发指南

1. 在 `extensions` 目录新建 Python 脚本，如 `myplugin.py`。
2. 文件需包含 `plugin_info` 字典和 `run(file_path)` 函数：
   ```python
   plugin_info = {
       "title": "示例插件",
       "description": "对文件执行自定义处理",
       "usage": "选择文件后点击插件",
       "category": "自定义"
   }

   def run(file_path):
       # 在此编写你的处理逻辑
       print(f"正在处理 {file_path}")
   ```
3. 重启程序后插件将自动出现在扩展列表中，可在界面中点击执行。

## 5. 设置与个性化

- **主题与字体**：在设置中切换浅色或深色主题，并调整显示字体。
- **代理与网络**：若需要访问外部服务，可在“代理设置”中配置 HTTP/HTTPS 代理。
- **输出目录**：所有生成的文件默认位于 `output/`，可在设置中修改。
- **快捷按钮**：可在 `config/highlight_buttons.json` 定制常用命令按钮。

## 6. 常见问题

1. **软件适用于哪些场景？** 主要针对 Windows 内存取证，适合解题和日常分析。对于混淆复杂或其他平台，可根据需要编写自定义插件。
2. **未检测到 Dokan 如何处理？** 请确认已安装对应版本的 Dokan，并重新启动系统或程序。
3. **Volatility 输出乱码？** 确保外部工具路径正确并使用 UTF‑8 编码，在设置中可调整环境变量。
4. **如何更新程序？** 直接从仓库拉取最新代码，或运行 `git pull` 后重新安装新依赖。

## 7. 相关资源

- 项目仓库：[GitHub - LovelyMem](https://github.com/Tokeii0/LovelyMem)
- 演示视频：[Bilibili](https://www.bilibili.com/video/BV1z912YpECB)

通过以上步骤，你就可以顺利使用 LovelyMem 对内存镜像进行取证分析并生成报告。祝你玩得愉快！
