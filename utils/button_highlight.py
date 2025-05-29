from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, QRect, Qt, Property as pyqtProperty
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QPushButton, QGraphicsDropShadowEffect

class ButtonHighlighter:
    """
    工具类，用于为按钮添加高亮/闪烁效果
    支持多种效果类型：边框闪烁、颜色渐变、脉冲效果等
    """
    
    def __init__(self):
        self.highlighted_buttons = {}  # 保存正在高亮的按钮及其效果
        self.default_styles = {}       # 保存按钮的原始样式
    
    def _generate_random_color(self):
        """生成纯随机的高亮颜色"""
        import random
        
        # 生成更深的随机RGB颜色
        r = random.randint(30, 180)  # 使用更深的颜色范围
        g = random.randint(30, 180)
        b = random.randint(30, 180)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def highlight_button(self, button, effect_type="border", color=None, duration=2000, 
                        loop_count=-1, auto_stop=False, stop_after=30000):
        """
        为按钮添加高亮效果
        
        参数:
            button: QPushButton对象
            effect_type: 效果类型，可以是 "border", "glow", "color", "pulse"
            color: 高亮颜色，如果为None则使用随机颜色
            duration: 单次动画持续时间（毫秒）
            loop_count: 重复次数，-1为无限循环
            auto_stop: 是否自动停止高亮
            stop_after: 自动停止的时间（毫秒）
        """
        # 如果没有指定颜色，使用随机颜色
        if color is None:
            color = self._generate_random_color()
        
        # 使用按钮对象的id作为键
        button_id = id(button)
        
        # 保存原始样式
        if button not in self.default_styles:
            self.default_styles[button] = button.styleSheet()
        
        # 如果按钮已经被高亮，先停止之前的效果
        if button_id in self.highlighted_buttons:
            self.stop_highlight(button)
        
        # 初始化该按钮的高亮数据
        self.highlighted_buttons[button_id] = {
            "button": button  # 存储按钮对象的引用
        }
        
        # 根据效果类型添加相应的高亮效果
        if effect_type == "border":
            self._add_border_effect(button, color, duration, loop_count)
        elif effect_type == "glow":
            self._add_glow_effect(button, color, duration, loop_count)
        elif effect_type == "color":
            self._add_color_effect(button, color, duration, loop_count)
        elif effect_type == "pulse":
            self._add_pulse_effect(button, color, duration, loop_count)
        
        # 如果设置了自动停止
        if auto_stop and stop_after > 0:
            stop_timer = QTimer()
            stop_timer.setSingleShot(True)
            stop_timer.timeout.connect(lambda: self.stop_highlight(button))
            stop_timer.start(stop_after)
            self.highlighted_buttons[button_id]["stop_timer"] = stop_timer
    
    def stop_highlight(self, button):
        """停止按钮的高亮效果"""
        button_id = id(button)
        if button_id in self.highlighted_buttons:
            effect_data = self.highlighted_buttons[button_id]
            
            # 停止动画
            if "animation" in effect_data:
                effect_data["animation"].stop()
            
            # 移除阴影效果
            if "shadow" in effect_data:
                button.setGraphicsEffect(None)
            
            # 恢复原始样式
            if button in self.default_styles:
                button.setStyleSheet(self.default_styles[button])
            
            # 如果有定时器，停止定时器
            if "stop_timer" in effect_data:
                effect_data["stop_timer"].stop()
            
            # 从高亮按钮列表中移除
            del self.highlighted_buttons[button_id]
    
    def stop_all_highlights(self):
        """停止所有按钮的高亮效果"""
        # 创建复制以避免在遍历过程中修改字典
        button_ids = list(self.highlighted_buttons.keys())
        for button_id in button_ids:
            if "button" in self.highlighted_buttons[button_id]:
                self.stop_highlight(self.highlighted_buttons[button_id]["button"])
    
    def _add_border_effect(self, button, color, duration, loop_count):
        """添加边框闪烁效果"""
        # 创建样式列表
        border_width = 2
        styles = [
            f"border: {border_width}px solid {color}; border-radius: 5px;",
            f"border: {border_width}px solid transparent; border-radius: 5px;"
        ]
        
        # 设置初始样式
        original_style = self.default_styles[button]
        
        # 创建定时器
        timer = QTimer()
        current_style = 0
        
        def update_style():
            nonlocal current_style
            button.setStyleSheet(original_style + styles[current_style])
            current_style = (current_style + 1) % len(styles)
        
        timer.timeout.connect(update_style)
        timer.start(duration // 2)  # 闪烁速度为动画时长的一半
        
        # 保存效果信息
        button_id = id(button)
        self.highlighted_buttons[button_id]["effect_type"] = "border"
        self.highlighted_buttons[button_id]["timer"] = timer
    
    def _add_glow_effect(self, button, color, duration, loop_count):
        """添加发光效果"""
        # 创建阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setColor(QColor(color))
        shadow.setOffset(0, 0)
        shadow.setBlurRadius(20)
        button.setGraphicsEffect(shadow)
        
        # 创建动画
        animation = QPropertyAnimation(shadow, b"color")
        animation.setStartValue(QColor(color).lighter(150))
        animation.setEndValue(QColor(color).darker(150))
        animation.setDuration(duration)
        animation.setLoopCount(loop_count)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.start()
        
        # 保存效果信息
        button_id = id(button)
        self.highlighted_buttons[button_id]["effect_type"] = "glow"
        self.highlighted_buttons[button_id]["shadow"] = shadow
        self.highlighted_buttons[button_id]["animation"] = animation
    
    def _add_color_effect(self, button, color, duration, loop_count):
        """添加颜色渐变效果"""
        original_style = self.default_styles[button]
        
        # 创建颜色列表（更深的彩虹色渐变）
        colors = [
            "#CC0000",  # 深红
            "#CC5500",  # 深橙
            "#CCCC00",  # 深黄
            "#00CC00",  # 深绿
            "#0000CC",  # 深蓝
            "#330055",  # 深靛
            "#660099",  # 深紫
        ]
        
        # 创建定时器
        timer = QTimer()
        current_color = 0
        
        def update_color():
            nonlocal current_color
            button.setStyleSheet(original_style + f"background-color: {colors[current_color]}; color: white;")
            current_color = (current_color + 1) % len(colors)
        
        timer.timeout.connect(update_color)
        timer.start(duration // len(colors))
        
        # 保存效果信息
        button_id = id(button)
        self.highlighted_buttons[button_id]["effect_type"] = "color"
        self.highlighted_buttons[button_id]["timer"] = timer
    
    def _add_pulse_effect(self, button, color, duration, loop_count):
        """添加脉冲效果"""
        # 创建阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setColor(QColor(color))
        shadow.setOffset(0, 0)
        shadow.setBlurRadius(10)
        button.setGraphicsEffect(shadow)
        
        # 创建动画
        animation = QPropertyAnimation(shadow, b"blurRadius")
        animation.setStartValue(5)
        animation.setEndValue(20)
        animation.setDuration(duration // 2)
        animation.setLoopCount(loop_count * 2)  # 每次循环包括放大和缩小
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.start()
        
        # 保存效果信息
        button_id = id(button)
        self.highlighted_buttons[button_id]["effect_type"] = "pulse"
        self.highlighted_buttons[button_id]["shadow"] = shadow
        self.highlighted_buttons[button_id]["animation"] = animation

# 全局单例实例
button_highlighter = ButtonHighlighter()
