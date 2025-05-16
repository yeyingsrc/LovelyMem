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
        print("[调试] highlight_after_memory_import 被调用")
        if not self.highlight_config or 'after_memory_import' not in self.highlight_config:
            print("[调试] 没有找到高亮配置或 after_memory_import 节点")
            return
        
        buttons_to_highlight = self.highlight_config['after_memory_import']
        print(f"[调试] 需要高亮的按钮数量: {len(buttons_to_highlight)}")
        for btn_config in buttons_to_highlight:
            print(f"[调试] 正在尝试高亮: {btn_config.get('area')}/{btn_config.get('group')}/{btn_config.get('button_text')}")
            self._highlight_button(btn_config)
    
    def highlight_after_profile_match(self):
        """在Profile匹配成功后高亮指定按钮"""
        print("[调试] highlight_after_profile_match 被调用")
        if not self.highlight_config or 'after_profile_match' not in self.highlight_config:
            print("[调试] 没有找到高亮配置或 after_profile_match 节点")
            return
        
        buttons_to_highlight = self.highlight_config['after_profile_match']
        print(f"[调试] Profile匹配后需要高亮的按钮数量: {len(buttons_to_highlight)}")
        for btn_config in buttons_to_highlight:
            print(f"[调试] 正在尝试高亮: {btn_config.get('area')}/{btn_config.get('group')}/{btn_config.get('button_text')}")
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
            print(f"[调试] 找不到区域: {area}")
            return
        else:
            print(f"[调试] 成功获取区域: {area}")
        
        # 找到该区域中指定组名的按钮组
        button_found = False
        if area == 'MemProcFS':
            from ui.memprocfs_area import CollapsibleButtonGroup
            print(f"[调试] 导入 MemProcFS 的 CollapsibleButtonGroup 成功")
        elif area == 'Vol2':
            from ui.vol2_area import CollapsibleButtonGroup
            print(f"[调试] 导入 Vol2 的 CollapsibleButtonGroup 成功")
        elif area == 'Vol3':
            from ui.vol3_area import CollapsibleButtonGroup
            print(f"[调试] 导入 Vol3 的 CollapsibleButtonGroup 成功")
        elif area == 'QuickCheck':
            from ui.quick_check_area import CollapsibleButtonGroup
            print(f"[调试] 导入 QuickCheck 的 CollapsibleButtonGroup 成功")
        else:
            print(f"[调试] 不支持的区域: {area}")
            return
        
        # 遍历该区域中的所有按钮组
        groups = area_widget.findChildren(CollapsibleButtonGroup)
        print(f"[调试] 找到 {len(groups)} 个 CollapsibleButtonGroup")
        for group in groups:
            print(f"[调试] 检查组名: {group.title} 是否匹配 {group_name}")
            if group.title == group_name:
                print(f"[调试] 找到匹配的组: {group_name}, 包含 {len(group.buttons)} 个按钮")
                # 遍历该组中的所有按钮
                for button in group.buttons:
                    print(f"[调试] 检查按钮: {button.text()} 是否匹配 {button_text}")
                    if isinstance(button, QPushButton) and button.text() == button_text:
                        print(f"[调试] 找到匹配的按钮: {button_text}, 开始添加高亮效果")
                        # 高亮该按钮
                        button_highlighter.highlight_button(
                            button,
                            effect_type=btn_config.get('effect', 'border'),
                            color=btn_config.get('color', '#FF5500'),
                            duration=btn_config.get('duration', 2000),
                            loop_count=-1,
                            auto_stop=btn_config.get('auto_stop', False),
                            stop_after=btn_config.get('stop_after', 30000)
                        )
                        button_found = True
                        print(f"[调试] 成功添加高亮效果到按钮: {button_text}")
                        break
            if button_found:
                break
        if not button_found:
            print(f"[调试] 未能找到匹配的按钮: {area}/{group_name}/{button_text}")
    
    def _get_area_widget(self, area):
        """获取指定区域的控件"""
        print(f"[调试] 尝试获取区域: {area}")
        if area == 'MemProcFS':
            print(f"[调试] 检查main_window是否有memprocfs_area: {hasattr(self.main_window, 'memprocfs_area')}")
            return self.main_window.memprocfs_area if hasattr(self.main_window, 'memprocfs_area') else None
        elif area == 'Vol2':
            print(f"[调试] 检查main_window是否有vol2_area: {hasattr(self.main_window, 'vol2_area')}")
            return self.main_window.vol2_area if hasattr(self.main_window, 'vol2_area') else None
        elif area == 'Vol3':
            print(f"[调试] 检查main_window是否有vol3_area: {hasattr(self.main_window, 'vol3_area')}")
            return self.main_window.vol3_area if hasattr(self.main_window, 'vol3_area') else None
        elif area == 'QuickCheck':
            print(f"[调试] 检查main_window是否有quick_check_area: {hasattr(self.main_window, 'quick_check_area')}")
            return self.main_window.quick_check_area if hasattr(self.main_window, 'quick_check_area') else None
        print(f"[调试] 不支持的区域: {area}")
        return None
