package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
)

func main() {
	// 获取当前工作目录
	currentDir := filepath.Dir(os.Args[0])

	// 确保工作目录正确（如果启动器在不同的文件夹中）
	projectDir := findProjectDir(currentDir)
	if projectDir == "" {
		showErrorAndExit("无法找到项目目录", nil)
	}

	// 检查虚拟环境
	venvPath := filepath.Join(projectDir, ".venv")
	pythonExe := findPythonInVenv(venvPath)
	if pythonExe == "" {
		showErrorAndExit("在虚拟环境中未找到Python解释器", nil)
	}

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
	err := cmd.Run()
	if err != nil {
		showErrorAndExit("运行Python脚本失败", err)
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

// 显示错误并退出
func showErrorAndExit(message string, err error) {
	if err != nil {
		fmt.Printf("%s: %v\n", message, err)
	} else {
		fmt.Println(message)
	}
	
	// 在退出前等待用户按键，这样用户可以看到错误信息
	fmt.Println("按任意键退出...")
	fmt.Scanln()
	os.Exit(1)
}
