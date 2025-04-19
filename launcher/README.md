# LovelyMem 启动器

<div align="center">

![LovelyMem 启动器](../res/logo_100.png)

*一个优雅的无黑框 Python 应用启动器 | Go 语言开发*

</div>

## 🔥 主要功能

- **无黑框体验**：启动 Python 应用程序时完全隐藏命令行窗口
- **智能路径检测**：自动定位项目目录，即使启动器位置变化也能正常工作
- **虚拟环境支持**：自动在 `.venv` 中查找并使用正确的 Python 解释器
- **一键更新**：集成 Git 更新功能，实时显示更新进度
- **专业界面**：定制主题和图标，提供现代化的用户体验
- **错误处理**：友好的错误提示和故障排除机制

## 💻 系统要求

- **操作系统**：Windows 7/8/10/11
- **磁盘空间**：少量磁盘空间 (<10MB)
- **依赖**：Git (用于更新功能)

## ⚙️ 安装前提

使用此启动器前，请确保：

1. **项目来源**：必须通过 `git clone` 命令克隆获取
   ```bash
   git clone https://github.com/Tokeii0/LovelyMem.git
   ```

2. **Python 环境**：已创建并激活虚拟环境，并安装必要依赖
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **完整性检查**：项目结构完整，包含所有必要的资源文件

## 🔧 使用方法

1. **启动应用**：双击 `LovelyMem.exe` 启动应用程序
2. **更新应用**：点击启动器中的“更新”按钮获取最新版本

启动器会自动执行以下操作：
- 定位项目目录和虚拟环境
- 使用正确的 Python 解释器运行应用
- 隐藏命令行窗口，提供清爽的用户体验

## 💻 开发者指南

### 编译方法

重新编译启动器：

```bash
# 安装 Go 语言环境 (https://golang.org/dl/)

# 在 launcher 目录中运行编译命令
# 生成的可执行文件将位于项目根目录
go build -ldflags "-H windowsgui -s -w" -trimpath -o ../LovelyMem.exe
```

### 技术细节

- **窗口隐藏**：使用 `syscall.SysProcAttr.HideWindow = true` 
- **图标集成**：使用 `rsrc` 工具将图标嵌入可执行文件
- **UI 框架**：基于 [Fyne](https://fyne.io/) 构建现代化界面
- **更新机制**：通过 Git 命令实现实时更新
- 使用 `-ldflags "-H windowsgui -s -w"` 和 `-trimpath` 优化可执行文件大小

## 注意事项

- 启动器需要能够访问项目的 `.venv` 虚拟环境
- 如果遇到错误，启动器会显示错误信息并等待用户按键后退出
- 启动器会自动查找项目目录，但建议将启动器放在项目根目录或其子目录中
