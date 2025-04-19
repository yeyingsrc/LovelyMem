package main

import (
	"fmt"
	"image/color"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/canvas"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/layout"
	"fyne.io/fyne/v2/theme"
	"fyne.io/fyne/v2/widget"
)

// 定义全局变量
var (
	projectDir string
	pythonExe  string
	appIcon    fyne.Resource // 应用图标
)

// 自定义粉色主题
type pinkTheme struct {
	fyne.Theme
}

func (p pinkTheme) Color(name fyne.ThemeColorName, variant fyne.ThemeVariant) color.Color {
	if name == theme.ColorNameBackground {
		return color.NRGBA{R: 255, G: 192, B: 203, A: 255} // 浅粉色背景
	} else if name == theme.ColorNameButton {
		return color.NRGBA{R: 255, G: 182, B: 193, A: 255} // 按钮颜色
	} else if name == theme.ColorNameForeground {
		return color.NRGBA{R: 0, G: 0, B: 0, A: 255} // 黑色文字
	} else if name == theme.ColorNameDisabled {
		return color.NRGBA{R: 200, G: 200, B: 200, A: 255} // 禁用状态下的文字颜色
	} else if name == theme.ColorNameInputBackground {
		return color.NRGBA{R: 30, G: 30, B: 30, A: 255} // 输入框背景色
	}

	return p.Theme.Color(name, variant)
}

func main() {
	// 初始化应用程序
	myApp := app.New()
	myApp.Settings().SetTheme(pinkTheme{Theme: theme.DefaultTheme()})

	// 创建主窗口
	window := myApp.NewWindow("Lovelymem 启动器 Create By Tokeii")
	window.Resize(fyne.NewSize(300, 250)) // 缩小窗口大小
	window.CenterOnScreen()

	// 设置图标
	// 先尝试使用相对路径
	iconPath := filepath.Join(filepath.Dir(os.Args[0]), "..", "res", "logo.ico")
	var err error
	
	// 尝试加载图标
	appIcon, err = fyne.LoadResourceFromPath(iconPath)
	
	// 如果相对路径失败，尝试使用项目路径
	if err != nil {
		iconPath = filepath.Join(projectDir, "res", "logo.ico")
		appIcon, err = fyne.LoadResourceFromPath(iconPath)
	}
	
	// 如果仍然失败，尝试使用PNG图标
	if err != nil {
		iconPath = filepath.Join(projectDir, "res", "logo_100.png")
		appIcon, err = fyne.LoadResourceFromPath(iconPath)
	}
	
	// 设置窗口图标（任务栏图标）
	if err == nil {
		window.SetIcon(appIcon)
		// 设置应用图标（影响所有窗口）
		myApp.SetIcon(appIcon)
	}

	// 初始化项目路径和Python解释器
	initializeEnvironment()

	// 创建标题和图标
	titleLabel := widget.NewLabelWithStyle("Lovelymem 启动器", fyne.TextAlignCenter, fyne.TextStyle{Bold: true})
	subtitleLabel := widget.NewLabelWithStyle("Create By Tokeii", fyne.TextAlignCenter, fyne.TextStyle{Italic: true})

	// 尝试加载图标
	logoPath := filepath.Join(projectDir, "res", "logo_100.png")
	var logoImage *canvas.Image
	if _, err := os.Stat(logoPath); err == nil {
		logoResource, _ := fyne.LoadResourceFromPath(logoPath)
		logoImage = canvas.NewImageFromResource(logoResource)
		logoImage.SetMinSize(fyne.NewSize(50, 50))
		logoImage.FillMode = canvas.ImageFillContain
	} else {
		// 如果找不到图标，使用空白图像
		logoImage = canvas.NewImageFromResource(theme.FyneLogo())
		logoImage.SetMinSize(fyne.NewSize(50, 50))
		logoImage.FillMode = canvas.ImageFillContain
	}

	// 创建头部布局
	headerContainer := container.NewVBox(
		container.NewCenter(logoImage),
		container.NewCenter(titleLabel),
		container.NewCenter(subtitleLabel),
	)

	// 创建按钮
	startButton := createActionButton("🚀 启动", func() {
		go launchApplication(window)
	})
	startButton.Importance = widget.HighImportance

	updateButton := createActionButton("🔄 更新", func() {
		go checkForUpdates(window)
	})
	updateButton.Importance = widget.MediumImportance

	// 创建按钮容器
	// 添加间距使布局更美观
	smallSpacer := canvas.NewRectangle(color.Transparent)
	smallSpacer.SetMinSize(fyne.NewSize(0, 5))

	mediumSpacer := canvas.NewRectangle(color.Transparent)
	mediumSpacer.SetMinSize(fyne.NewSize(0, 10))

	buttonsContainer := container.NewVBox(
		mediumSpacer,
		container.NewPadded(startButton),
		smallSpacer,
		container.NewPadded(updateButton),
		smallSpacer,
	)

	// 创建主布局
	mainContainer := container.NewVBox(
		headerContainer,
		mediumSpacer,
		buttonsContainer,
	)

	// 设置窗口内容
	window.SetContent(mainContainer)

	// 显示窗口并运行应用
	window.ShowAndRun()
}

// 创建统一风格的按钮
func createActionButton(label string, action func()) *widget.Button {
	button := widget.NewButton(label, action)
	// 不在这里设置重要性，而是在创建时单独设置
	button.Alignment = widget.ButtonAlignCenter
	return button
}

// 初始化环境
func initializeEnvironment() {
	// 获取当前工作目录
	currentDir := filepath.Dir(os.Args[0])

	// 查找项目目录
	projectDir = findProjectDir(currentDir)
	if projectDir == "" {
		showErrorDialog("无法找到项目目录")
		os.Exit(1)
	}

	// 检查虚拟环境
	venvPath := filepath.Join(projectDir, ".venv")
	pythonExe = findPythonInVenv(venvPath)
	if pythonExe == "" {
		showErrorDialog("在虚拟环境中未找到Python解释器")
		os.Exit(1)
	}
}

// 启动应用程序
func launchApplication(window fyne.Window) {
	// 构建命令
	mainPyPath := filepath.Join(projectDir, "main.py")
	cmd := exec.Command(pythonExe, mainPyPath)

	// 设置工作目录
	cmd.Dir = projectDir

	// 继承标准输入输出
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	// 设置启动信息，隐藏控制台窗口
	cmd.SysProcAttr = &syscall.SysProcAttr{
		HideWindow: true,
	}

	// 运行命令
	err := cmd.Start()
	if err != nil {
		showErrorDialog(fmt.Sprintf("启动应用程序失败: %v", err))
		return
	}

	// 应用程序启动后最小化启动器窗口
	window.Hide()

	// 等待应用程序结束后恢复启动器窗口
	go func() {
		cmd.Wait()
		fyne.CurrentApp().SendNotification(&fyne.Notification{
			Title:   "LovelyMem",
			Content: "应用程序已关闭",
		})
		window.Show()
	}()
}

// 检查更新
func checkForUpdates(window fyne.Window) {
	// 创建一个新窗口显示更新过程
	updateWindow := fyne.CurrentApp().NewWindow("正在更新 LovelyMem")
	updateWindow.Resize(fyne.NewSize(400, 280)) // 缩小窗口大小
	updateWindow.CenterOnScreen()
	
	// 确保更新窗口也使用相同的图标
	if appIcon != nil {
		updateWindow.SetIcon(appIcon)
	}

	// 创建一个自定义容器显示命令输出
	// 使用深色背景和浅色文字，更易读
	outputBackground := canvas.NewRectangle(color.NRGBA{R: 30, G: 30, B: 30, A: 255}) // 深色背景

	// 创建文本区域
	outputText := widget.NewMultiLineEntry()
	outputText.SetText("准备更新...\n")
	outputText.Disable() // 禁用编辑，只用于显示

	// 设置文本样式
	outputText.TextStyle = fyne.TextStyle{
		Bold:      false,
		Italic:    false,
		Monospace: true,
	}

	// 创建一个容器，将背景和文本区域结合
	outputContainer := container.NewMax(outputBackground, outputText)

	// 添加滚动容器
	scroll := container.NewScroll(outputContainer)

	// 创建关闭按钮
	closeButton := widget.NewButton("关闭", func() {
		updateWindow.Close()
	})
	closeButton.Importance = widget.HighImportance
	closeButton.Hide() // 初始隐藏关闭按钮

	// 美化按钮
	closeButton.Alignment = widget.ButtonAlignCenter

	// 重启按钮
	restartButton := widget.NewButton("重新启动应用", func() {
		launchApplication(window)
		updateWindow.Close()
	})
	restartButton.Importance = widget.HighImportance
	restartButton.Hide() // 初始隐藏重启按钮

	// 美化按钮
	restartButton.Alignment = widget.ButtonAlignCenter

	// 创建按钮容器
	buttonContainer := container.NewHBox(
		layout.NewSpacer(),
		restartButton,
		closeButton,
		layout.NewSpacer(),
	)

	// 创建标题标签
	titleLabel := widget.NewLabel("正在更新 LovelyMem")
	titleLabel.TextStyle = fyne.TextStyle{Bold: true}
	titleLabel.Alignment = fyne.TextAlignCenter

	// 创建标题容器
	titleContainer := container.NewHBox(
		layout.NewSpacer(),
		titleLabel,
		layout.NewSpacer(),
	)

	// 添加间距
	padding := canvas.NewRectangle(color.Transparent)
	padding.SetMinSize(fyne.NewSize(0, 10))

	// 设置窗口内容
	updateWindow.SetContent(
		container.NewBorder(
			container.NewVBox(
				titleContainer,
				padding,
			),
			container.NewVBox(
				padding,
				buttonContainer,
				padding,
			),
			nil,
			nil,
			container.NewPadded(scroll),
		),
	)

	// 显示窗口
	updateWindow.Show()

	// 在后台线程中执行git pull
	go func() {
		// 创建git pull命令
		cmd := exec.Command("git", "pull")
		cmd.Dir = projectDir // 使用项目目录作为工作目录

		// 获取命令的标准输出和错误输出管道
		stdout, err := cmd.StdoutPipe()
		if err != nil {
			outputText.SetText(outputText.Text + fmt.Sprintf("错误: 无法获取输出管道 - %v\n", err))
			closeButton.Show()
			return
		}

		stderr, err := cmd.StderrPipe()
		if err != nil {
			outputText.SetText(outputText.Text + fmt.Sprintf("错误: 无法获取错误管道 - %v\n", err))
			closeButton.Show()
			return
		}

		// 启动命令
		outputText.SetText(outputText.Text + "正在执行 git pull...\n")
		err = cmd.Start()
		if err != nil {
			outputText.SetText(outputText.Text + fmt.Sprintf("错误: 无法启动命令 - %v\n", err))
			closeButton.Show()
			return
		}

		// 创建一个通道来接收所有输出
		outputChan := make(chan string)

		// 读取标准输出
		go func() {
			buffer := make([]byte, 1024)
			for {
				n, err := stdout.Read(buffer)
				if n > 0 {
					outputChan <- string(buffer[:n])
				}
				if err != nil {
					break
				}
			}
		}()

		// 读取错误输出
		go func() {
			buffer := make([]byte, 1024)
			for {
				n, err := stderr.Read(buffer)
				if n > 0 {
					outputChan <- string(buffer[:n])
				}
				if err != nil {
					break
				}
			}
		}()

		// 收集所有输出
		var fullOutput string
		done := make(chan struct{})

		go func() {
			for output := range outputChan {
				fullOutput += output
				// 更新UI
				outputText.SetText(outputText.Text + output)
				// 滚动到底部
				outputText.CursorRow = len(strings.Split(outputText.Text, "\n")) - 1
			}
			done <- struct{}{}
		}()

		// 等待命令完成
		err = cmd.Wait()
		close(outputChan)
		<-done

		// 显示按钮
		closeButton.Show()

		if err != nil {
			outputText.SetText(outputText.Text + fmt.Sprintf("\n命令执行失败: %v\n", err))
			return
		}

		// 检查输出中是否包含“Already up to date”
		if strings.Contains(fullOutput, "Already up to date") || strings.Contains(fullOutput, "已经是最新") {
			// 已经是最新版本
			outputText.SetText(outputText.Text + "\n当前已经是最新版本\n")
		} else {
			// 成功更新
			outputText.SetText(outputText.Text + "\n更新成功！可以重新启动应用了\n")
			restartButton.Show()
		}
	}()
}

// 显示更新成功对话框
func showUpdateSuccessDialog(window fyne.Window, message string) {
	fyne.CurrentApp().SendNotification(&fyne.Notification{
		Title:   "LovelyMem 更新",
		Content: "更新成功",
	})

	// 使用内置的对话框
	dialog := widget.NewModalPopUp(
		container.NewVBox(
			widget.NewLabel(message),
			container.NewHBox(
				layout.NewSpacer(),
				widget.NewButton("重新启动应用", func() {
					// 重新启动应用
					launchApplication(window)
				}),
				widget.NewButton("关闭", func() {}),
				layout.NewSpacer(),
			),
		),
		window.Canvas(),
	)
	dialog.Show()
}

// 显示错误对话框
func showErrorDialog(message string) {
	fmt.Println(message)
	// 如果在GUI环境中，可以显示对话框
	if fyne.CurrentApp() != nil {
		fyne.CurrentApp().SendNotification(&fyne.Notification{
			Title:   "错误",
			Content: message,
		})
	}
}

// 在虚拟环境中查找Python解释器
func findPythonInVenv(venvPath string) string {
	// 检查Windows下的Python可执行文件
	pythonExe := filepath.Join(venvPath, "Scripts", "python.exe")
	if _, err := os.Stat(pythonExe); err == nil {
		return pythonExe
	}

	// 检查Windows下的Python可执行文件（备选路径）
	pythonExe = filepath.Join(venvPath, "bin", "python.exe")
	if _, err := os.Stat(pythonExe); err == nil {
		return pythonExe
	}

	// 如果没有找到，尝试在PATH中查找
	paths := strings.Split(os.Getenv("PATH"), string(os.PathListSeparator))
	for _, path := range paths {
		pythonExe = filepath.Join(path, "python.exe")
		if _, err := os.Stat(pythonExe); err == nil {
			return pythonExe
		}
	}

	return ""
}

// 查找项目目录
func findProjectDir(startDir string) string {
	// 首先检查当前目录是否就是项目目录
	if isProjectDir(startDir) {
		return startDir
	}

	// 检查父目录
	parentDir := filepath.Dir(startDir)
	if isProjectDir(parentDir) {
		return parentDir
	}

	// 如果启动器在项目的子目录中，向上查找
	dir := startDir
	for {
		parentDir := filepath.Dir(dir)
		if parentDir == dir {
			// 已经到达根目录
			break
		}

		if isProjectDir(parentDir) {
			return parentDir
		}

		dir = parentDir
	}

	// 如果都没找到，返回启动器所在目录
	return startDir
}

// 判断是否是项目目录
func isProjectDir(dir string) bool {
	// 检查main.py是否存在
	mainPyPath := filepath.Join(dir, "main.py")
	if _, err := os.Stat(mainPyPath); err == nil {
		return true
	}

	return false
}
