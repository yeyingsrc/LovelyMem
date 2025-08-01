from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QPushButton, QLabel, QLineEdit, QFileDialog, 
                             QGroupBox, QTabWidget, QWidget, QMessageBox,
                             QCheckBox)  
from PySide6.QtCore import Qt
import yaml
import os
import logging
import json
from db.updatevol3cache import update_identifier_cache  

logger = logging.getLogger(__name__)

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("配置设置")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        # 加载配置文件
        self.config_file = os.path.join(os.getcwd(), "config", "base_config.yaml")
        self.load_config()
        
        # 加载用户设置
        self.user_settings_file = os.path.join(os.getcwd(), "config", "user_settings.json")
        self.load_user_settings()
        
        # 创建主布局
        self.setup_ui()
        
    def load_config(self):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self.config = {}
            QMessageBox.critical(self, "错误", f"加载配置文件失败: {e}")
    
    def load_user_settings(self):
        try:
            if os.path.exists(self.user_settings_file):
                with open(self.user_settings_file, 'r', encoding='utf-8') as f:
                    self.user_settings = json.load(f)
            else:
                self.user_settings = {
                    "theme": "默认",
                    "first_run_reminder": True,  
                    "LLM_CONFIG": {},
                    "base_config": {"proxy": {"url": ""}},
                    "font_settings": {"font_family": ""},
                    "show_regex_slot": True,
                    "show_preset_slot": True
                }
        except Exception as e:
            logger.error(f"加载用户设置失败: {e}")
            self.user_settings = {
                "theme": "默认",
                "first_run_reminder": True,  
                "LLM_CONFIG": {},
                "base_config": {"proxy": {"url": ""}},
                "font_settings": {"font_family": ""},
                "show_regex_slot": True,
                "show_preset_slot": True
            }
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("QTabBar::tab {min-width: 100px;}")
        
        # 工具路径设置选项卡
        tools_tab = QWidget()
        tools_layout = QVBoxLayout(tools_tab)
        
        # 初始化工具输入控件字典
        self.tool_inputs = {}
        
        # MemProcFS 工具设置
        memprocfs_group = self.create_tools_group("MemProcFS 工具", self.config.get("tools", {}))
        tools_layout.addWidget(memprocfs_group)
        
        # Volatility2 工具设置
        vol2_group = self.create_tools_group("Volatility2 工具", self.config.get("tools", {}))
        tools_layout.addWidget(vol2_group)
        
        # Volatility3 工具设置
        vol3_group = self.create_tools_group("Volatility3 工具", self.config.get("tools", {}))
        tools_layout.addWidget(vol3_group)
        
        # 其他工具设置
        other_tools_group = self.create_tools_group("其他工具", self.config.get("tools", {}))
        tools_layout.addWidget(other_tools_group)
        
        # 基础工具设置
        base_tools_group = self.create_tools_group("基础工具", self.config.get("base_tools", {}))
        tools_layout.addWidget(base_tools_group)
        
        # 其他工具设置（RegistryExplorer 和 EvtxECmd）
        registry_tools_group = self.create_tools_group("注册表和事件工具", self.config.get("other_tools", {}))
        tools_layout.addWidget(registry_tools_group)
        
        # 添加到选项卡
        tab_widget.addTab(tools_tab, "工具路径")
        
        # LLM 设置选项卡
        llm_tab = QWidget()
        llm_layout = QVBoxLayout(llm_tab)
        
        # LLM 配置设置
        llm_group = QGroupBox("LLM 配置")
        llm_grid = QGridLayout()
        
        llm_config = self.config.get("LLM_CONFIG", {})
        row = 0
        self.llm_inputs = {}
        
        for key, value in llm_config.items():
            label = QLabel(key + ":")
            line_edit = QLineEdit(str(value) if value is not None else "")
            self.llm_inputs[key] = line_edit
            llm_grid.addWidget(label, row, 0)
            llm_grid.addWidget(line_edit, row, 1)
            row += 1
        
        llm_group.setLayout(llm_grid)
        llm_layout.addWidget(llm_group)
        
        # 添加到选项卡
        tab_widget.addTab(llm_tab, "LLM 设置")
        
        # 代理设置选项卡
        proxy_tab = QWidget()
        proxy_layout = QVBoxLayout(proxy_tab)
        
        # 代理配置设置
        proxy_group = QGroupBox("代理配置")
        proxy_grid = QGridLayout()
        
        proxy_config = self.config.get("base_config", {}).get("proxy", {})
        self.proxy_url_input = QLineEdit(proxy_config.get("url", ""))
        proxy_grid.addWidget(QLabel("代理 URL:"), 0, 0)
        proxy_grid.addWidget(self.proxy_url_input, 0, 1)
        
        proxy_group.setLayout(proxy_grid)
        proxy_layout.addWidget(proxy_group)
        
        # 添加到选项卡
        tab_widget.addTab(proxy_tab, "代理设置")
        
        # 添加首次使用提醒设置选项卡
        first_run_tab = QWidget()
        first_run_layout = QVBoxLayout(first_run_tab)
        
        # 首次使用提醒设置
        first_run_group = QGroupBox("首次使用提醒设置")
        first_run_grid = QGridLayout()
        
        # 添加首次使用提醒复选框
        self.first_run_checkbox = QCheckBox("启用首次使用提醒")
        self.first_run_checkbox.setChecked(self.user_settings.get("first_run_reminder", True))
        first_run_grid.addWidget(self.first_run_checkbox, 0, 0, 1, 2)
        
        # 添加说明标签
        first_run_description = QLabel("启用后，程序将在首次启动时显示使用提示和帮助信息。")
        first_run_description.setWordWrap(True)
        first_run_grid.addWidget(first_run_description, 1, 0, 1, 2)
        
        # 添加Vol3缓存更新按钮
        vol3_cache_group = QGroupBox("Volatility3 缓存更新")
        vol3_cache_layout = QVBoxLayout()
        
        vol3_cache_description = QLabel("更新Volatility3符号缓存，解决符号路径问题。如果Volatility3无法正常工作，请尝试更新缓存。")
        vol3_cache_description.setWordWrap(True)
        vol3_cache_layout.addWidget(vol3_cache_description)
        
        update_vol3_cache_button = QPushButton("更新Volatility3缓存")
        update_vol3_cache_button.clicked.connect(self.update_vol3_cache)
        vol3_cache_layout.addWidget(update_vol3_cache_button)
        
        vol3_cache_group.setLayout(vol3_cache_layout)
        
        first_run_group.setLayout(first_run_grid)
        first_run_layout.addWidget(first_run_group)
        first_run_layout.addWidget(vol3_cache_group)
        first_run_layout.addStretch()
        
        # 添加到选项卡
        tab_widget.addTab(first_run_tab, "首次使用提醒")
        
        # 添加界面设置选项卡
        ui_tab = QWidget()
        ui_layout = QVBoxLayout(ui_tab)
        
        # 界面组件显示设置
        ui_group = QGroupBox("界面组件显示设置")
        ui_grid = QGridLayout()
        
        # 添加正则槽显示复选框
        self.regex_slot_checkbox = QCheckBox("显示正则槽")
        self.regex_slot_checkbox.setChecked(self.user_settings.get("show_regex_slot", True))
        ui_grid.addWidget(self.regex_slot_checkbox, 0, 0, 1, 2)
        
        # 添加预设显示复选框
        self.preset_slot_checkbox = QCheckBox("显示预设")
        self.preset_slot_checkbox.setChecked(self.user_settings.get("show_preset_slot", True))
        ui_grid.addWidget(self.preset_slot_checkbox, 1, 0, 1, 2)
        
        # 添加说明标签
        ui_description = QLabel("取消勾选将在主界面中隐藏相应组件。更改将在重启应用后生效。")
        ui_description.setWordWrap(True)
        ui_grid.addWidget(ui_description, 2, 0, 1, 2)
        
        ui_group.setLayout(ui_grid)
        ui_layout.addWidget(ui_group)
        ui_layout.addStretch()
        
        # 添加到选项卡
        tab_widget.addTab(ui_tab, "界面设置")
        
        main_layout.addWidget(tab_widget)
        
        # 确定和取消按钮
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        main_layout.addLayout(buttons_layout)
        
        # 连接信号
        ok_button.clicked.connect(self.save_config)
        cancel_button.clicked.connect(self.reject)
    
    def update_vol3_cache(self):
        try:
            update_identifier_cache()
            QMessageBox.information(self, "成功", "Volatility3缓存更新成功！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新Volatility3缓存失败: {e}")
    
    def create_tools_group(self, title, tools_dict):
        group = QGroupBox(title)
        grid = QGridLayout()
        
        row = 0
        
        # 根据标题筛选相关工具
        if title == "MemProcFS 工具":
            # 只显示 memprocfs 相关工具
            filtered_tools = {k: v for k, v in tools_dict.items() if k == "memprocfs"}
        elif title == "Volatility2 工具":
            # 显示 volatility2 和 volatility2_python 相关工具
            filtered_tools = {k: v for k, v in tools_dict.items() if k in ["volatility2", "volatility2_python"]}
        elif title == "Volatility3 工具":
            # 显示 volatility3 和 volatility3_symbols 相关工具
            filtered_tools = {k: v for k, v in tools_dict.items() if k in ["volatility3", "volatility3_symbols"]}
        elif title == "其他工具":
            # 显示 lovelypixelweaver 和 volatility2_plugin 相关工具
            filtered_tools = {k: v for k, v in tools_dict.items() if k in ["lovelypixelweaver", "volatility2_plugin"]}
        elif title == "注册表和事件工具":
            # 显示 RegistryExplorer 和 EvtxECmd 工具
            filtered_tools = {k: v for k, v in tools_dict.items() if k in ["RegistryExplorer", "EvtxECmd"]}
        else:
            # 基础工具或其他类别，直接使用传入的字典
            filtered_tools = tools_dict
        
        for key, tool_info in filtered_tools.items():
            if isinstance(tool_info, dict) and 'path' in tool_info:
                path = tool_info['path']
                label = QLabel(f"{key}:")
                line_edit = QLineEdit(path)
                browse_button = QPushButton("浏览...")
                
                # 存储输入控件引用
                self.tool_inputs[key] = line_edit
                
                grid.addWidget(label, row, 0)
                grid.addWidget(line_edit, row, 1)
                grid.addWidget(browse_button, row, 2)
                
                # 连接浏览按钮信号
                browse_button.clicked.connect(lambda checked, le=line_edit: self.browse_file(le))
                
                row += 1
        
        group.setLayout(grid)
        return group
    
    def browse_file(self, line_edit):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "所有文件 (*)")
        if file_path:
            line_edit.setText(file_path)
    
    def save_config(self):
        try:
            # 更新工具路径
            for key, line_edit in self.tool_inputs.items():
                path = line_edit.text().strip()
                
                # 查找并更新配置
                for section in ['tools', 'base_tools', 'other_tools']:
                    if section in self.config:
                        for tool_key, tool_info in self.config[section].items():
                            if tool_key == key and isinstance(tool_info, dict) and 'path' in tool_info:
                                self.config[section][tool_key]['path'] = path
                                break
            
            # 更新 LLM 配置
            if 'LLM_CONFIG' in self.config:
                for key, line_edit in self.llm_inputs.items():
                    value = line_edit.text().strip()
                    # 尝试转换为适当的类型
                    try:
                        if value.lower() == 'true':
                            value = True
                        elif value.lower() == 'false':
                            value = False
                        elif value.isdigit():
                            value = int(value)
                        elif value.replace('.', '', 1).isdigit() and value.count('.') == 1:
                            value = float(value)
                    except:
                        pass
                    self.config['LLM_CONFIG'][key] = value
            
            # 更新代理配置
            if 'base_config' in self.config and 'proxy' in self.config['base_config']:
                self.config['base_config']['proxy']['url'] = self.proxy_url_input.text().strip()
            
            # 保存配置文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True)
            
            # 更新用户设置
            self.user_settings["first_run_reminder"] = self.first_run_checkbox.isChecked()
            self.user_settings["show_regex_slot"] = self.regex_slot_checkbox.isChecked()
            self.user_settings["show_preset_slot"] = self.preset_slot_checkbox.isChecked()
            
            # 保存用户设置
            with open(self.user_settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_settings, f, ensure_ascii=False, indent=4)
            
            QMessageBox.information(self, "成功", "配置已保存")
            self.accept()
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            QMessageBox.critical(self, "错误", f"保存配置文件失败: {e}")
