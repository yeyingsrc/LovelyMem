import json
import os
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QStandardItemModel, QStandardItem
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                             QPushButton, QSpinBox, QGridLayout, QGroupBox, 
                             QColorDialog, QLineEdit, QCheckBox, QScrollArea, 
                             QWidget, QFrame, QSplitter, QTreeView, QHeaderView,
                             QMessageBox, QMenu, QListWidget, QListWidgetItem)  

from utils.button_highlight import button_highlighter


class HighlightSettingsDialog(QDialog):
    """高亮设置对话框，用于配置和预览按钮高亮效果"""
    
    def __init__(self, parent=None, config_path=None, highlight_manager=None):
        super().__init__(parent)
        self.setWindowTitle("按钮高亮设置")
        self.resize(900, 700)  # 增大窗口大小以容纳更多内容
        
        # 保存配置路径和高亮管理器
        self.config_path = config_path
        self.highlight_manager = highlight_manager
        
        # 初始化当前选中的配置项
        self.current_section = "after_memory_import"  # 默认选择内存导入后的高亮设置
        self.current_item_index = -1  # 当前选中的配置项索引
        
        # 初始化配置数据
        self.config_data = {
            "after_memory_import": [],
            "after_profile_match": []
        }
        
        # 初始化当前设置
        self._current_effect = "border"
        self._current_color = "#FF5500"
        self._current_duration = 2000
        self._current_loop_count = -1  # -1为无限循环
        self._auto_stop = False
        self._stop_after = 30000
        self._current_area = ""
        self._current_group = ""
        self._current_button_text = ""
        
        # 创建界面
        self._create_ui()
        
        # 如果提供了配置文件路径，从文件加载配置
        if self.config_path and os.path.exists(self.config_path):
            try:
                self._load_config_from_file()
                self._refresh_config_list()  # 加载完配置后刷新列表
            except Exception as e:
                print(f"加载高亮配置失败: {str(e)}")
                QMessageBox.warning(self, "配置加载失败", f"无法加载高亮配置: {str(e)}")
        
        # 初始化预览按钮的高亮效果
        self._update_preview()
    
    def _create_ui(self):
        """创建完整的用户界面"""
        # 主布局为水平分隔器
        main_layout = QHBoxLayout(self)
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # 创建左侧配置区域
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self._create_config_area(left_layout)
        
        # 创建右侧预览和设置区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建测试按钮区域
        self._create_test_button_area(right_layout)
        
        # 创建效果预览区域
        self._create_preview_area(right_layout)
        
        # 创建属性设置区域
        self._create_settings_area(right_layout)
        
        # 将左右区域添加到分隔器中
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(right_widget)
        
        # 设置分隔比例，左侧稍小一点
        self.splitter.setSizes([300, 600])
        
    def _create_config_area(self, parent_layout):
        """创建左侧配置区域"""
        # 创建配置分类选择组件
        section_group = QGroupBox("配置分类")
        section_layout = QVBoxLayout()
        section_group.setLayout(section_layout)
        
        self.section_combo = QComboBox()
        self.section_combo.addItem("内存导入后高亮 (after_memory_import)")
        self.section_combo.addItem("Profile匹配后高亮 (after_profile_match)")
        self.section_combo.currentIndexChanged.connect(self._on_section_changed)
        section_layout.addWidget(self.section_combo)
        
        parent_layout.addWidget(section_group)
        
        # 创建配置项列表
        config_group = QGroupBox("配置项列表")
        config_layout = QVBoxLayout()
        config_group.setLayout(config_layout)
        
        self.config_list = QListWidget()
        self.config_list.itemClicked.connect(self._on_config_item_clicked)
        config_layout.addWidget(self.config_list)
        
        # 添加操作按钮
        buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("新增")
        add_button.clicked.connect(self._add_config_item)
        buttons_layout.addWidget(add_button)
        
        edit_button = QPushButton("编辑")
        edit_button.clicked.connect(self._edit_config_item)
        buttons_layout.addWidget(edit_button)
        
        delete_button = QPushButton("删除")
        delete_button.clicked.connect(self._delete_config_item)
        buttons_layout.addWidget(delete_button)
        
        config_layout.addLayout(buttons_layout)
        
        parent_layout.addWidget(config_group)
        parent_layout.setStretch(1, 3)  # 列表比选择器更大
        
        # 添加配置项编辑组件
        edit_group = QGroupBox("编辑配置项")
        edit_layout = QGridLayout()
        edit_group.setLayout(edit_layout)
        
        # 区域设置
        edit_layout.addWidget(QLabel("区域:"), 0, 0)
        self.area_combo = QComboBox()
        self.area_combo.addItems(["MemProcFS", "Vol2", "Vol3", "QuickCheck"])
        edit_layout.addWidget(self.area_combo, 0, 1)
        
        # 组名设置
        edit_layout.addWidget(QLabel("组名:"), 1, 0)
        self.group_edit = QLineEdit()
        edit_layout.addWidget(self.group_edit, 1, 1)
        
        # 按钮文本设置
        edit_layout.addWidget(QLabel("按钮文本:"), 2, 0)
        self.button_text_edit = QLineEdit()
        edit_layout.addWidget(self.button_text_edit, 2, 1)
        
        # 操作按钮
        buttons_layout2 = QHBoxLayout()
        
        self.apply_edit_button = QPushButton("应用编辑")
        self.apply_edit_button.clicked.connect(self._apply_config_item_edit)
        buttons_layout2.addWidget(self.apply_edit_button)
        
        self.cancel_edit_button = QPushButton("取消")
        self.cancel_edit_button.clicked.connect(self._cancel_config_item_edit)
        buttons_layout2.addWidget(self.cancel_edit_button)
        
        edit_layout.addLayout(buttons_layout2, 3, 0, 1, 2)
        
        parent_layout.addWidget(edit_group)
        
        # 添加保存和放弃按钮
        save_layout = QHBoxLayout()
        
        save_all_button = QPushButton("保存所有配置")
        save_all_button.clicked.connect(self._save_all_config)
        save_layout.addWidget(save_all_button)
        
        discard_button = QPushButton("放弃更改")
        discard_button.clicked.connect(self._discard_changes)
        save_layout.addWidget(discard_button)
        
        parent_layout.addLayout(save_layout)
        
    def _create_test_button_area(self, parent_layout):
        """创建测试按钮区域"""
        test_group = QGroupBox("测试区域")
        test_layout = QVBoxLayout()
        test_group.setLayout(test_layout)
        
        # 添加说明标签
        instruction_label = QLabel("点击下面的按钮可以测试当前高亮效果")
        instruction_label.setAlignment(Qt.AlignCenter)
        test_layout.addWidget(instruction_label)
        
        # 添加测试按钮
        test_button = QPushButton("测试高亮效果")
        test_button.setMinimumHeight(40)
        test_button.clicked.connect(self._apply_test_highlight)
        test_layout.addWidget(test_button)
        self.test_button = test_button
        
        parent_layout.addWidget(test_group)
        
    def _create_preview_area(self, parent_layout):
        """创建预览区域，用于显示不同高亮效果的演示"""
        preview_group = QGroupBox("效果预览")
        preview_layout = QGridLayout()
        preview_group.setLayout(preview_layout)
        
        # 创建四个不同效果的预览按钮
        self.preview_buttons = {}
        effects = [
            ("border", "边框闪烁", 0, 0),
            ("glow", "发光效果", 0, 1),
            ("color", "颜色渐变", 1, 0),
            ("pulse", "脉冲效果", 1, 1)
        ]
        
        for effect_type, effect_name, row, col in effects:
            btn = QPushButton(effect_name)
            btn.setMinimumHeight(60)
            btn.setMinimumWidth(120)
            self.preview_buttons[effect_type] = btn
            preview_layout.addWidget(btn, row, col)
            
            # 为每个按钮添加点击事件，点击后应用相应效果
            btn.clicked.connect(lambda checked=False, e=effect_type: self._set_current_effect(e))
        
        parent_layout.addWidget(preview_group)
        parent_layout.setStretch(1, 5)  # 设置预览区域比例更大
        
    def _create_settings_area(self, parent_layout):
        """创建设置区域，用于调整高亮效果的属性"""
        settings_group = QGroupBox("效果属性设置")
        settings_layout = QGridLayout()
        settings_group.setLayout(settings_layout)
        
        # 效果类型选择
        settings_layout.addWidget(QLabel("效果类型:"), 0, 0)
        effect_combo = QComboBox()
        effect_combo.addItems(["边框闪烁", "发光效果", "颜色渐变", "脉冲效果"])
        effect_combo.currentIndexChanged.connect(self._on_effect_type_changed)
        self.effect_combo = effect_combo
        settings_layout.addWidget(effect_combo, 0, 1)
        
        # 颜色选择
        settings_layout.addWidget(QLabel("颜色:"), 1, 0)
        color_layout = QHBoxLayout()
        self.color_preview = QFrame()
        self.color_preview.setMinimumWidth(30)
        self.color_preview.setMinimumHeight(20)
        self.color_preview.setStyleSheet(f"background-color: {self._current_color};")
        color_layout.addWidget(self.color_preview)
        
        self.color_edit = QLineEdit(self._current_color)
        self.color_edit.setMaximumWidth(80)
        self.color_edit.textChanged.connect(self._on_color_text_changed)
        color_layout.addWidget(self.color_edit)
        
        color_button = QPushButton("选择颜色")
        color_button.clicked.connect(self._show_color_dialog)
        color_layout.addWidget(color_button)
        settings_layout.addLayout(color_layout, 1, 1)
        
        # 动画持续时间
        settings_layout.addWidget(QLabel("动画持续时间(毫秒):"), 2, 0)
        duration_spin = QSpinBox()
        duration_spin.setRange(100, 10000)
        duration_spin.setSingleStep(100)
        duration_spin.setValue(self._current_duration)
        duration_spin.valueChanged.connect(self._on_duration_changed)
        self.duration_spin = duration_spin
        settings_layout.addWidget(duration_spin, 2, 1)
        
        # 循环次数
        settings_layout.addWidget(QLabel("循环次数(-1为无限循环):"), 3, 0)
        loop_spin = QSpinBox()
        loop_spin.setRange(-1, 100)
        loop_spin.setValue(self._current_loop_count)
        loop_spin.valueChanged.connect(self._on_loop_count_changed)
        self.loop_spin = loop_spin
        settings_layout.addWidget(loop_spin, 3, 1)
        
        # 自动停止
        auto_stop_check = QCheckBox("自动停止")
        auto_stop_check.setChecked(self._auto_stop)
        auto_stop_check.stateChanged.connect(self._on_auto_stop_changed)
        self.auto_stop_check = auto_stop_check
        settings_layout.addWidget(auto_stop_check, 4, 0)
        
        # 停止时间
        settings_layout.addWidget(QLabel("停止时间(毫秒):"), 5, 0)
        stop_after_spin = QSpinBox()
        stop_after_spin.setRange(1000, 300000)  # 1秒到5分钟
        stop_after_spin.setSingleStep(1000)
        stop_after_spin.setValue(self._stop_after)
        stop_after_spin.valueChanged.connect(self._on_stop_after_changed)
        stop_after_spin.setEnabled(self._auto_stop)
        self.stop_after_spin = stop_after_spin
        settings_layout.addWidget(stop_after_spin, 5, 1)
        
        # 添加应用按钮和保存配置按钮
        apply_layout = QHBoxLayout()
        apply_button = QPushButton("应用到所有预览")
        apply_button.clicked.connect(self._update_preview)
        apply_layout.addWidget(apply_button)
        
        reset_button = QPushButton("重置")
        reset_button.clicked.connect(self._reset_settings)
        apply_layout.addWidget(reset_button)
        
        if self.config_path:
            save_button = QPushButton("保存配置")
            save_button.clicked.connect(self._save_config)
            apply_layout.addWidget(save_button)
            
        settings_layout.addLayout(apply_layout, 6, 0, 1, 2)
        
        parent_layout.addWidget(settings_group)
        
    def _apply_test_highlight(self):
        """向测试按钮应用当前高亮效果"""
        # 先停止之前的高亮效果
        button_highlighter.stop_highlight(self.test_button)
        
        # 应用新的高亮效果
        effect_map = {
            "边框闪烁": "border",
            "发光效果": "glow",
            "颜色渐变": "color",
            "脉冲效果": "pulse"
        }
        effect_type = effect_map[self.effect_combo.currentText()]
        
        button_highlighter.highlight_button(
            self.test_button,
            effect_type=effect_type,
            color=self._current_color,
            duration=self._current_duration,
            loop_count=self._current_loop_count,
            auto_stop=self._auto_stop,
            stop_after=self._stop_after
        )
    
    def _update_preview(self):
        """更新所有预览按钮的高亮效果"""
        # 停止所有按钮的高亮效果
        for button in self.preview_buttons.values():
            button_highlighter.stop_highlight(button)
        
        # 为每个预览按钮应用对应的高亮效果
        for effect_type, button in self.preview_buttons.items():
            button_highlighter.highlight_button(
                button,
                effect_type=effect_type,
                color=self._current_color,
                duration=self._current_duration,
                loop_count=self._current_loop_count,
                auto_stop=self._auto_stop,
                stop_after=self._stop_after
            )
    
    def _set_current_effect(self, effect_type):
        """设置当前效果类型"""
        self._current_effect = effect_type
        effect_index_map = {
            "border": 0,
            "glow": 1,
            "color": 2,
            "pulse": 3
        }
        self.effect_combo.setCurrentIndex(effect_index_map[effect_type])
        # 更新测试按钮的高亮效果
        self._apply_test_highlight()
    
    def _on_effect_type_changed(self, index):
        """效果类型变化时的回调"""
        effect_map = {
            0: "border",
            1: "glow",
            2: "color",
            3: "pulse"
        }
        self._current_effect = effect_map[index]
        # 更新测试按钮的高亮效果
        self._apply_test_highlight()
    
    def _show_color_dialog(self):
        """显示颜色选择对话框"""
        color = QColorDialog.getColor(QColor(self._current_color), self, "选择高亮颜色")
        if color.isValid():
            self._current_color = color.name()
            self.color_edit.setText(self._current_color)
            self.color_preview.setStyleSheet(f"background-color: {self._current_color};")
            self._apply_test_highlight()
    
    def _on_color_text_changed(self, text):
        """颜色文本框变化时的回调"""
        # 检查是否是有效的颜色格式
        try:
            color = QColor(text)
            if color.isValid():
                self._current_color = text
                self.color_preview.setStyleSheet(f"background-color: {self._current_color};")
                self._apply_test_highlight()
        except:
            pass
    
    def _on_duration_changed(self, value):
        """动画持续时间变化时的回调"""
        self._current_duration = value
        self._apply_test_highlight()
    
    def _on_loop_count_changed(self, value):
        """循环次数变化时的回调"""
        self._current_loop_count = value
        self._apply_test_highlight()
    
    def _on_auto_stop_changed(self, state):
        """自动停止状态变化时的回调"""
        self._auto_stop = (state == Qt.Checked)
        self.stop_after_spin.setEnabled(self._auto_stop)
        self._apply_test_highlight()
    
    def _on_stop_after_changed(self, value):
        """停止时间变化时的回调"""
        self._stop_after = value
        if self._auto_stop:
            self._apply_test_highlight()
    
    def _reset_settings(self):
        """重置所有设置到默认值"""
        self.effect_combo.setCurrentIndex(0)
        self._current_color = "#FF5500"
        self.color_edit.setText(self._current_color)
        self.color_preview.setStyleSheet(f"background-color: {self._current_color};")
        self._current_duration = 2000
        self.duration_spin.setValue(self._current_duration)
        self._current_loop_count = -1
        self.loop_spin.setValue(self._current_loop_count)
        self._auto_stop = False
        self.auto_stop_check.setChecked(False)
        self._stop_after = 30000
        self.stop_after_spin.setValue(self._stop_after)
        self._update_preview()
    
    def _load_config_from_file(self):
        """从配置文件加载高亮设置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 保存整个配置数据
            if 'after_memory_import' in config:
                self.config_data['after_memory_import'] = config['after_memory_import']
            if 'after_profile_match' in config:
                self.config_data['after_profile_match'] = config['after_profile_match']
                
            # 从配置中获取第一个高亮项的属性作为默认值
            if 'after_memory_import' in config and len(config['after_memory_import']) > 0:
                highlight_item = config['after_memory_import'][0]
                
                # 更新当前设置
                self._current_effect = highlight_item.get('effect', 'border')
                self._current_color = highlight_item.get('color', '#FF5500')
                self._current_duration = highlight_item.get('duration', 2000)
                self._auto_stop = highlight_item.get('auto_stop', False)
                self._stop_after = highlight_item.get('stop_after', 30000)
                
                # 更新界面控件
                effect_index_map = {
                    "border": 0,
                    "glow": 1,
                    "color": 2,
                    "pulse": 3
                }
                self.effect_combo.setCurrentIndex(effect_index_map.get(self._current_effect, 0))
                self.color_edit.setText(self._current_color)
                self.color_preview.setStyleSheet(f"background-color: {self._current_color};")
                self.duration_spin.setValue(self._current_duration)
                self.auto_stop_check.setChecked(self._auto_stop)
                self.stop_after_spin.setValue(self._stop_after)
                self.stop_after_spin.setEnabled(self._auto_stop)
                
                print(f"已从配置文件加载高亮设置")
        except Exception as e:
            print(f"加载配置文件时出错: {str(e)}")
    
    def _save_config(self):
        """将当前选中项的设置应用到所有配置项并保存到配置文件"""
        if not self.config_path:
            QMessageBox.warning(self, "错误", "没有指定配置文件路径")
            return
        
        try:
            # 将当前设置应用到所有配置项
            for section in ['after_memory_import', 'after_profile_match']:
                for item in self.config_data[section]:
                    item['effect'] = self._current_effect
                    item['color'] = self._current_color
                    item['duration'] = self._current_duration
                    item['loop_count'] = self._current_loop_count
                    item['auto_stop'] = self._auto_stop
                    item['stop_after'] = self._stop_after
            
            # 保存到文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
            
            # 如果有高亮管理器，重新加载配置
            if self.highlight_manager:
                self.highlight_manager.highlight_config = self.highlight_manager._load_config()
            
            # 显示保存成功提示
            QMessageBox.information(self, "保存成功", "当前设置已应用到所有配置项并保存到文件")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"保存配置时出错: {str(e)}")
    
    # 配置列表管理相关方法
    def _on_section_changed(self, index):
        """配置分类变更时的回调"""
        sections = ["after_memory_import", "after_profile_match"]
        self.current_section = sections[index]
        self.current_item_index = -1  # 重置选中项
        self._refresh_config_list()
        
    def _add_config_item(self):
        """添加新的配置项"""
        # 准备新的配置项
        new_item = {
            'area': self.area_combo.currentText(),
            'group': self.group_edit.text(),
            'button_text': self.button_text_edit.text(),
            'effect': self._current_effect,
            'color': self._current_color,
            'duration': self._current_duration,
            'loop_count': self._current_loop_count,
            'auto_stop': self._auto_stop,
            'stop_after': self._stop_after
        }
        
        # 验证必要字段
        if not new_item['area'] or not new_item['group'] or not new_item['button_text']:
            QMessageBox.warning(self, "错误", "区域、组名和按钮文本不能为空")
            return
        
        # 添加到当前配置分类
        self.config_data[self.current_section].append(new_item)
        
        # 刷新列表并选中新项
        self._refresh_config_list()
        self.current_item_index = len(self.config_data[self.current_section]) - 1
        self.config_list.setCurrentRow(self.current_item_index)
        
        QMessageBox.information(self, "成功", "新配置项添加成功")
    
    def _edit_config_item(self):
        """编辑当前选中的配置项"""
        if self.current_item_index < 0 or self.current_item_index >= len(self.config_data.get(self.current_section, [])):
            QMessageBox.warning(self, "错误", "请先选择要编辑的配置项")
            return
        
        # 选中项已在 _on_config_item_clicked 中加载到编辑区域
        # 只需要提示用户可以编辑了
        QMessageBox.information(self, "编辑模式", "您现在可以编辑所选配置项的属性，完成后点击'应用编辑'按钮保存更改")
    
    def _delete_config_item(self):
        """删除当前选中的配置项"""
        if self.current_item_index < 0 or self.current_item_index >= len(self.config_data.get(self.current_section, [])):
            QMessageBox.warning(self, "错误", "请先选择要删除的配置项")
            return
        
        # 询问用户是否确认删除
        reply = QMessageBox.question(self, "确认删除", "确定要删除选中的配置项吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # 从列表中移除
            del self.config_data[self.current_section][self.current_item_index]
            
            # 重置选中项并刷新列表
            self.current_item_index = -1
            self._refresh_config_list()
            
            # 清空编辑区域
            self.area_combo.setCurrentIndex(0)
            self.group_edit.setText("")
            self.button_text_edit.setText("")
            
            QMessageBox.information(self, "成功", "配置项已删除")
    
    def _apply_config_item_edit(self):
        """应用编辑更改到当前选中的配置项"""
        if self.current_item_index < 0 or self.current_item_index >= len(self.config_data.get(self.current_section, [])):
            # 如果没有选中项，就创建新的
            self._add_config_item()
            return
        
        # 更新配置项
        edited_item = {
            'area': self.area_combo.currentText(),
            'group': self.group_edit.text(),
            'button_text': self.button_text_edit.text(),
            'effect': self._current_effect,
            'color': self._current_color,
            'duration': self._current_duration,
            'loop_count': self._current_loop_count,
            'auto_stop': self._auto_stop,
            'stop_after': self._stop_after
        }
        
        # 验证必要字段
        if not edited_item['area'] or not edited_item['group'] or not edited_item['button_text']:
            QMessageBox.warning(self, "错误", "区域、组名和按钮文本不能为空")
            return
        
        # 更新配置
        self.config_data[self.current_section][self.current_item_index] = edited_item
        
        # 刷新列表
        self._refresh_config_list()
        self.config_list.setCurrentRow(self.current_item_index)
        
        QMessageBox.information(self, "成功", "配置项已更新")
    
    def _cancel_config_item_edit(self):
        """取消编辑"""
        # 如果有选中项，重新加载其数据
        if self.current_item_index >= 0 and self.current_item_index < len(self.config_data.get(self.current_section, [])):
            item = self.config_list.item(self.current_item_index)
            if item:
                self._on_config_item_clicked(item)
        else:
            # 否则清空编辑区域
            self.area_combo.setCurrentIndex(0)
            self.group_edit.setText("")
            self.button_text_edit.setText("")
        
        QMessageBox.information(self, "取消", "已取消编辑")
    
    def _save_all_config(self):
        """将所有配置保存到配置文件"""
        if not self.config_path:
            QMessageBox.warning(self, "错误", "没有指定配置文件路径")
            return
        
        try:
            # 保存到文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
            
            # 如果有高亮管理器，重新加载配置
            if self.highlight_manager:
                self.highlight_manager.highlight_config = self.highlight_manager._load_config()
            
            QMessageBox.information(self, "成功", "所有配置已成功保存到文件")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"保存配置时出错: {str(e)}")
    
    def _discard_changes(self):
        """放弃所有未保存的更改"""
        reply = QMessageBox.question(self, "确认放弃", "确定要放弃所有未保存的更改吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # 重新加载配置
            if self.config_path and os.path.exists(self.config_path):
                try:
                    self._load_config_from_file()
                    self._refresh_config_list()
                    self.current_item_index = -1  # 重置选中项
                    
                    # 清空编辑区域
                    self.area_combo.setCurrentIndex(0)
                    self.group_edit.setText("")
                    self.button_text_edit.setText("")
                    
                    QMessageBox.information(self, "成功", "已重新加载配置文件")
                except Exception as e:
                    QMessageBox.warning(self, "加载失败", f"重新加载配置时出错: {str(e)}")

    
    def _refresh_config_list(self):
        """刷新配置项列表"""
        self.config_list.clear()
        section_items = self.config_data.get(self.current_section, [])
        
        for i, item in enumerate(section_items):
            area = item.get('area', '')
            group = item.get('group', '')
            button_text = item.get('button_text', '')
            display_text = f"{area} - {group} - {button_text}"
            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.UserRole, i)  # 存储索引
            self.config_list.addItem(list_item)
    
    def _on_config_item_clicked(self, item):
        """配置项被点击时的回调"""
        index = item.data(Qt.UserRole)
        self.current_item_index = index
        
        # 加载选中项的数据
        if 0 <= index < len(self.config_data.get(self.current_section, [])):
            config_item = self.config_data[self.current_section][index]
            
            # 更新编辑区域
            area = config_item.get('area', '')
            group = config_item.get('group', '')
            button_text = config_item.get('button_text', '')
            
            self._current_area = area
            self._current_group = group
            self._current_button_text = button_text
            
            # 更新UI
            area_index = self.area_combo.findText(area)
            if area_index >= 0:
                self.area_combo.setCurrentIndex(area_index)
            self.group_edit.setText(group)
            self.button_text_edit.setText(button_text)
            
            # 更新效果设置
            self._current_effect = config_item.get('effect', 'border')
            self._current_color = config_item.get('color', '#FF5500')
            self._current_duration = config_item.get('duration', 2000)
            self._current_loop_count = config_item.get('loop_count', -1)
            self._auto_stop = config_item.get('auto_stop', False)
            self._stop_after = config_item.get('stop_after', 30000)
            
            # 更新UI控件
            effect_index_map = {
                "border": 0,
                "glow": 1,
                "color": 2,
                "pulse": 3
            }
            self.effect_combo.setCurrentIndex(effect_index_map.get(self._current_effect, 0))
            self.color_edit.setText(self._current_color)
            self.color_preview.setStyleSheet(f"background-color: {self._current_color};")
            self.duration_spin.setValue(self._current_duration)
            self.loop_spin.setValue(self._current_loop_count)
            self.auto_stop_check.setChecked(self._auto_stop)
            self.stop_after_spin.setValue(self._stop_after)
            self.stop_after_spin.setEnabled(self._auto_stop)
            
            # 更新预览
            self._update_preview()
    
    def closeEvent(self, event):
        """对话框关闭时停止所有高亮效果"""
        button_highlighter.stop_all_highlights()
        super().closeEvent(event)