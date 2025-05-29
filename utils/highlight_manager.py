import json
import os
from PySide6.QtWidgets import QPushButton, QWidget

from utils.button_highlight import button_highlighter


class ButtonHighlightManager:
    """
    按钮高亮管理器，用于在特定事件后高亮指定按钮
    """
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.config_path = os.path.join('config', 'highlight_buttons.json')
        self.highlight_config = self._load_config()
    
    def _load_config(self):
        """加载高亮按钮配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载按钮高亮配置失败: {str(e)}")
                return {}
        return {}
    
    def highlight_after_memory_import(self):
        """内存导入后高亮指定按钮"""
        if not self.highlight_config or 'after_memory_import' not in self.highlight_config:
            return
        
        buttons_to_highlight = self.highlight_config['after_memory_import']
        for btn_config in buttons_to_highlight:
            self._highlight_button(btn_config)
    
    def highlight_after_profile_match(self):
        """在Profile匹配成功后高亮指定按钮"""
        if not self.highlight_config or 'after_profile_match' not in self.highlight_config:
            return
        
        buttons_to_highlight = self.highlight_config['after_profile_match']
        for btn_config in buttons_to_highlight:
            self._highlight_button(btn_config)
    
    def stop_all_highlights(self):
        """停止所有按钮高亮效果"""
        button_highlighter.stop_all_highlights()
    
    def _highlight_button(self, btn_config):
        """根据配置高亮指定按钮"""
        area = btn_config.get('area')
        group_name = btn_config.get('group')
        button_text = btn_config.get('button_text')
        
        # 获取对应区域
        area_widget = self._get_area_widget(area)
        if not area_widget:
            return
        
        # 找到该区域中指定组名的按钮组
        button_found = False
        if area == 'MemProcFS':
            from ui.memprocfs_area import CollapsibleButtonGroup
        elif area == 'Vol2':
            from ui.vol2_area import CollapsibleButtonGroup
        elif area == 'Vol3':
            from ui.vol3_area import CollapsibleButtonGroup
        elif area == 'QuickCheck':
            from ui.quick_check_area import CollapsibleButtonGroup
        else:
            return
        
        # 遍历该区域中的所有按钮组
        groups = area_widget.findChildren(CollapsibleButtonGroup)
        for group in groups:
            if group.title == group_name:
                # 遍历该组中的所有按钮
                for button in group.buttons:
                    if isinstance(button, QPushButton) and button.text() == button_text:
                        # 高亮该按钮
                        button_highlighter.highlight_button(
                            button,
                            effect_type=btn_config.get('effect', 'border'),
                            color=btn_config.get('color'),  # 如果为None，会使用随机颜色
                            duration=btn_config.get('duration', 2000),
                            loop_count=-1,
                            auto_stop=btn_config.get('auto_stop', False),
                            stop_after=btn_config.get('stop_after', 30000)
                        )
                        button_found = True
                        break
            if button_found:
                break
    
    def _get_area_widget(self, area):
        """获取指定区域的控件"""
        if area == 'MemProcFS':
            return self.main_window.memprocfs_area if hasattr(self.main_window, 'memprocfs_area') else None
        elif area == 'Vol2':
            return self.main_window.vol2_area if hasattr(self.main_window, 'vol2_area') else None
        elif area == 'Vol3':
            return self.main_window.vol3_area if hasattr(self.main_window, 'vol3_area') else None
        elif area == 'QuickCheck':
            return self.main_window.quick_check_area if hasattr(self.main_window, 'quick_check_area') else None
        return None
