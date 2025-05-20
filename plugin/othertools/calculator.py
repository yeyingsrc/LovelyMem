import sys
import os
import re
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                              QPushButton, QLabel, QLineEdit, QApplication, 
                              QTabWidget, QGroupBox, QRadioButton, QButtonGroup,
                              QComboBox, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QRegularExpression
from PySide6.QtGui import QFont, QRegularExpressionValidator

# 添加项目根目录到系统路径，确保可以导入ui.styles
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class Calculator(QWidget):
    """偏移量和十六进制计算器"""
    
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.setWindowTitle("偏移量和十六进制计算器")
        self.resize(800, 450)  # 16:9比例
        self.main_window = main_window
        
        # 如果传入了主窗口，则连接样式更新信号
        if self.main_window and hasattr(self.main_window, 'style_updated_signal'):
            self.main_window.style_updated_signal.connect(self.update_style)
        
        # 初始化UI
        self.setup_ui()
        
        # 应用当前样式
        self.update_style()
        
    def setup_ui(self):
        """设置界面"""
        main_layout = QVBoxLayout(self)
        
        # 添加标题标签
        self.title_label = QLabel("偏移量和十六进制计算器")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(self.title_label)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 创建偏移量计算页面
        self.offset_tab = QWidget()
        self.setup_offset_tab()
        self.tab_widget.addTab(self.offset_tab, "偏移量计算")
        
        # 创建十六进制计算页面
        self.hex_tab = QWidget()
        self.setup_hex_tab()
        self.tab_widget.addTab(self.hex_tab, "十六进制计算")
        
        # 创建进制转换页面
        self.convert_tab = QWidget()
        self.setup_convert_tab()
        self.tab_widget.addTab(self.convert_tab, "进制转换")
        
        # 创建内存取证常用计算页面
        self.forensic_tab = QWidget()
        self.setup_forensic_tab()
        self.tab_widget.addTab(self.forensic_tab, "内存取证工具")
        
        # 创建PE文件结构分析页面
        self.pe_tab = QWidget()
        self.setup_pe_tab()
        self.tab_widget.addTab(self.pe_tab, "PE文件分析")
        
        main_layout.addWidget(self.tab_widget)
    
    def setup_offset_tab(self):
        """设置偏移量计算标签页"""
        layout = QHBoxLayout(self.offset_tab)
        
        # 左侧输入区域
        input_group = QGroupBox("地址输入")
        input_layout = QGridLayout(input_group)
        
        # 基数选择
        self.offset_base_label = QLabel("基数:")
        self.hex_radio = QRadioButton("十六进制")
        self.dec_radio = QRadioButton("十进制")
        self.hex_radio.setChecked(True)
        
        # 创建按钮组
        self.base_group = QButtonGroup(self)
        self.base_group.addButton(self.hex_radio, 16)
        self.base_group.addButton(self.dec_radio, 10)
        self.base_group.idClicked.connect(self.base_changed)
        
        input_layout.addWidget(self.offset_base_label, 0, 0)
        input_layout.addWidget(self.hex_radio, 0, 1)
        input_layout.addWidget(self.dec_radio, 0, 2)
        
        # 起始地址
        self.start_addr_label = QLabel("起始地址:")
        self.start_addr_input = QLineEdit()
        self.start_addr_input.setPlaceholderText("例如: 0x1000")
        
        # 设置十六进制验证器
        hex_validator = QRegularExpressionValidator(QRegularExpression("0x[0-9A-Fa-f]+"))
        self.start_addr_input.setValidator(hex_validator)
        
        input_layout.addWidget(self.start_addr_label, 1, 0)
        input_layout.addWidget(self.start_addr_input, 1, 1, 1, 2)
        
        # 结束地址
        self.end_addr_label = QLabel("结束地址:")
        self.end_addr_input = QLineEdit()
        self.end_addr_input.setPlaceholderText("例如: 0x2000")
        self.end_addr_input.setValidator(hex_validator)
        
        input_layout.addWidget(self.end_addr_label, 2, 0)
        input_layout.addWidget(self.end_addr_input, 2, 1, 1, 2)
        
        # 计算按钮
        self.calc_offset_button = QPushButton("计算偏移量")
        self.calc_offset_button.clicked.connect(self.calculate_offset)
        input_layout.addWidget(self.calc_offset_button, 3, 0, 1, 3)
        
        # 右侧结果区域
        result_group = QGroupBox("计算结果")
        result_layout = QGridLayout(result_group)
        
        # 十六进制偏移量
        self.hex_offset_label = QLabel("十六进制偏移量:")
        self.hex_offset_result = QLineEdit()
        self.hex_offset_result.setReadOnly(True)
        
        result_layout.addWidget(self.hex_offset_label, 0, 0)
        result_layout.addWidget(self.hex_offset_result, 0, 1)
        
        # 十进制偏移量
        self.dec_offset_label = QLabel("十进制偏移量:")
        self.dec_offset_result = QLineEdit()
        self.dec_offset_result.setReadOnly(True)
        
        result_layout.addWidget(self.dec_offset_label, 1, 0)
        result_layout.addWidget(self.dec_offset_result, 1, 1)
        
        # 字节数
        self.bytes_label = QLabel("字节数:")
        self.bytes_result = QLineEdit()
        self.bytes_result.setReadOnly(True)
        
        result_layout.addWidget(self.bytes_label, 2, 0)
        result_layout.addWidget(self.bytes_result, 2, 1)
        
        # 常用偏移量参考
        reference_group = QGroupBox("常用偏移量参考")
        reference_layout = QGridLayout(reference_group)
        
        references = [
            ("BYTE", "1字节", "0x1"),
            ("WORD", "2字节", "0x2"),
            ("DWORD", "4字节", "0x4"),
            ("QWORD", "8字节", "0x8"),
            ("段", "16字节", "0x10"),
            ("页", "4KB", "0x1000"),
            ("大页", "2MB", "0x200000"),
            ("1GB页", "1GB", "0x40000000")
        ]
        
        for i, (name, desc, value) in enumerate(references):
            name_label = QLabel(name)
            desc_label = QLabel(desc)
            value_label = QLabel(value)
            
            reference_layout.addWidget(name_label, i, 0)
            reference_layout.addWidget(desc_label, i, 1)
            reference_layout.addWidget(value_label, i, 2)
        
        # 添加到主布局
        layout.addWidget(input_group, 1)
        right_layout = QVBoxLayout()
        right_layout.addWidget(result_group)
        right_layout.addWidget(reference_group)
        layout.addLayout(right_layout, 1)
    
    def setup_hex_tab(self):
        """设置十六进制计算标签页"""
        layout = QVBoxLayout(self.hex_tab)
        
        # 输入区域
        input_group = QGroupBox("十六进制计算")
        input_layout = QHBoxLayout(input_group)
        
        # 第一个操作数
        self.hex_input1_label = QLabel("操作数1:")
        self.hex_input1 = QLineEdit()
        self.hex_input1.setPlaceholderText("例如: 0xFF")
        
        # 设置十六进制验证器
        hex_validator = QRegularExpressionValidator(QRegularExpression("0x[0-9A-Fa-f]+"))
        self.hex_input1.setValidator(hex_validator)
        
        # 操作符
        self.hex_operator_label = QLabel("操作符:")
        self.hex_operator = QComboBox()
        self.hex_operator.addItems(["+", "-", "*", "/", "&", "|", "^", "<<", ">>"])
        
        # 第二个操作数
        self.hex_input2_label = QLabel("操作数2:")
        self.hex_input2 = QLineEdit()
        self.hex_input2.setPlaceholderText("例如: 0x0F")
        self.hex_input2.setValidator(hex_validator)
        
        # 计算按钮
        self.calc_hex_button = QPushButton("计算")
        self.calc_hex_button.clicked.connect(self.calculate_hex)
        
        input_layout.addWidget(self.hex_input1_label)
        input_layout.addWidget(self.hex_input1)
        input_layout.addWidget(self.hex_operator_label)
        input_layout.addWidget(self.hex_operator)
        input_layout.addWidget(self.hex_input2_label)
        input_layout.addWidget(self.hex_input2)
        input_layout.addWidget(self.calc_hex_button)
        
        # 结果区域
        result_group = QGroupBox("计算结果")
        result_layout = QGridLayout(result_group)
        
        # 十六进制结果
        self.hex_result_label = QLabel("十六进制结果:")
        self.hex_result = QLineEdit()
        self.hex_result.setReadOnly(True)
        
        result_layout.addWidget(self.hex_result_label, 0, 0)
        result_layout.addWidget(self.hex_result, 0, 1)
        
        # 十进制结果
        self.dec_result_label = QLabel("十进制结果:")
        self.dec_result = QLineEdit()
        self.dec_result.setReadOnly(True)
        
        result_layout.addWidget(self.dec_result_label, 1, 0)
        result_layout.addWidget(self.dec_result, 1, 1)
        
        # 二进制结果
        self.bin_result_label = QLabel("二进制结果:")
        self.bin_result = QLineEdit()
        self.bin_result.setReadOnly(True)
        
        result_layout.addWidget(self.bin_result_label, 2, 0)
        result_layout.addWidget(self.bin_result, 2, 1)
        
        # 位运算说明
        bit_op_group = QGroupBox("位运算说明")
        bit_op_layout = QGridLayout(bit_op_group)
        
        bit_operations = [
            ("&", "按位与", "两个位都为1时，结果才为1"),
            ("|", "按位或", "两个位都为0时，结果才为0"),
            ("^", "按位异或", "两个位相同为0，不同为1"),
            ("<<", "左移", "各二进位全部左移若干位"),
            (">>", "右移", "各二进位全部右移若干位")
        ]
        
        for i, (op, name, desc) in enumerate(bit_operations):
            op_label = QLabel(op)
            name_label = QLabel(name)
            desc_label = QLabel(desc)
            
            bit_op_layout.addWidget(op_label, i, 0)
            bit_op_layout.addWidget(name_label, i, 1)
            bit_op_layout.addWidget(desc_label, i, 2)
        
        # 添加到主布局
        layout.addWidget(input_group)
        layout.addWidget(result_group)
        layout.addWidget(bit_op_group)
    
    def setup_convert_tab(self):
        """设置进制转换标签页"""
        layout = QVBoxLayout(self.convert_tab)
        
        # 输入区域
        input_group = QGroupBox("输入数值")
        input_layout = QHBoxLayout(input_group)
        
        # 输入基数
        self.input_base_label = QLabel("输入基数:")
        self.input_base = QComboBox()
        self.input_base.addItems(["二进制", "八进制", "十进制", "十六进制"])
        self.input_base.setCurrentIndex(3)  # 默认十六进制
        self.input_base.currentIndexChanged.connect(self.input_base_changed)
        
        # 输入值
        self.convert_input_label = QLabel("输入值:")
        self.convert_input = QLineEdit()
        self.convert_input.setPlaceholderText("例如: 0xFF")
        
        # 设置十六进制验证器
        hex_validator = QRegularExpressionValidator(QRegularExpression("0x[0-9A-Fa-f]+"))
        self.convert_input.setValidator(hex_validator)
        
        # 转换按钮
        self.convert_button = QPushButton("转换")
        self.convert_button.clicked.connect(self.convert_base)
        
        input_layout.addWidget(self.input_base_label)
        input_layout.addWidget(self.input_base)
        input_layout.addWidget(self.convert_input_label)
        input_layout.addWidget(self.convert_input)
        input_layout.addWidget(self.convert_button)
        
        # 结果区域
        result_group = QGroupBox("转换结果")
        result_layout = QGridLayout(result_group)
        
        # 二进制结果
        self.bin_convert_label = QLabel("二进制:")
        self.bin_convert_result = QLineEdit()
        self.bin_convert_result.setReadOnly(True)
        
        result_layout.addWidget(self.bin_convert_label, 0, 0)
        result_layout.addWidget(self.bin_convert_result, 0, 1)
        
        # 八进制结果
        self.oct_convert_label = QLabel("八进制:")
        self.oct_convert_result = QLineEdit()
        self.oct_convert_result.setReadOnly(True)
        
        result_layout.addWidget(self.oct_convert_label, 1, 0)
        result_layout.addWidget(self.oct_convert_result, 1, 1)
        
        # 十进制结果
        self.dec_convert_label = QLabel("十进制:")
        self.dec_convert_result = QLineEdit()
        self.dec_convert_result.setReadOnly(True)
        
        result_layout.addWidget(self.dec_convert_label, 2, 0)
        result_layout.addWidget(self.dec_convert_result, 2, 1)
        
        # 十六进制结果
        self.hex_convert_label = QLabel("十六进制:")
        self.hex_convert_result = QLineEdit()
        self.hex_convert_result.setReadOnly(True)
        
        result_layout.addWidget(self.hex_convert_label, 3, 0)
        result_layout.addWidget(self.hex_convert_result, 3, 1)
        
        # 添加到主布局
        layout.addWidget(input_group)
        layout.addWidget(result_group)
        layout.addStretch()
    
    def base_changed(self, base_id):
        """处理基数变化"""
        if base_id == 16:
            # 十六进制
            hex_validator = QRegularExpressionValidator(QRegularExpression("0x[0-9A-Fa-f]+"))
            self.start_addr_input.setValidator(hex_validator)
            self.end_addr_input.setValidator(hex_validator)
            self.start_addr_input.setPlaceholderText("例如: 0x1000")
            self.end_addr_input.setPlaceholderText("例如: 0x2000")
        else:
            # 十进制
            dec_validator = QRegularExpressionValidator(QRegularExpression("[0-9]+"))
            self.start_addr_input.setValidator(dec_validator)
            self.end_addr_input.setValidator(dec_validator)
            self.start_addr_input.setPlaceholderText("例如: 4096")
            self.end_addr_input.setPlaceholderText("例如: 8192")
        
        # 清空输入框
        self.start_addr_input.clear()
        self.end_addr_input.clear()
    
    def input_base_changed(self, index):
        """处理进制转换输入基数变化"""
        self.convert_input.clear()
        
        if index == 0:  # 二进制
            bin_validator = QRegularExpressionValidator(QRegularExpression("0b[01]+"))
            self.convert_input.setValidator(bin_validator)
            self.convert_input.setPlaceholderText("例如: 0b1010")
        elif index == 1:  # 八进制
            oct_validator = QRegularExpressionValidator(QRegularExpression("0o[0-7]+"))
            self.convert_input.setValidator(oct_validator)
            self.convert_input.setPlaceholderText("例如: 0o777")
        elif index == 2:  # 十进制
            dec_validator = QRegularExpressionValidator(QRegularExpression("[0-9]+"))
            self.convert_input.setValidator(dec_validator)
            self.convert_input.setPlaceholderText("例如: 255")
        else:  # 十六进制
            hex_validator = QRegularExpressionValidator(QRegularExpression("0x[0-9A-Fa-f]+"))
            self.convert_input.setValidator(hex_validator)
            self.convert_input.setPlaceholderText("例如: 0xFF")
    
    def calculate_offset(self):
        """计算偏移量"""
        try:
            # 获取基数
            base = self.base_group.checkedId()
            
            # 获取起始和结束地址
            start_text = self.start_addr_input.text()
            end_text = self.end_addr_input.text()
            
            if not start_text or not end_text:
                return
            
            # 转换为整数
            if base == 16:
                start_addr = int(start_text, 16)
                end_addr = int(end_text, 16)
            else:
                start_addr = int(start_text)
                end_addr = int(end_text)
            
            # 计算偏移量
            offset = end_addr - start_addr
            
            # 显示结果
            self.hex_offset_result.setText(hex(offset))
            self.dec_offset_result.setText(str(offset))
            self.bytes_result.setText(str(offset))
            
        except Exception as e:
            self.hex_offset_result.setText("错误")
            self.dec_offset_result.setText("错误")
            self.bytes_result.setText("错误")
    
    def calculate_hex(self):
        """计算十六进制运算"""
        try:
            # 获取操作数
            input1_text = self.hex_input1.text()
            input2_text = self.hex_input2.text()
            operator = self.hex_operator.currentText()
            
            if not input1_text or not input2_text:
                return
            
            # 转换为整数
            num1 = int(input1_text, 16)
            num2 = int(input2_text, 16)
            
            # 执行运算
            if operator == "+":
                result = num1 + num2
            elif operator == "-":
                result = num1 - num2
            elif operator == "*":
                result = num1 * num2
            elif operator == "/":
                result = num1 // num2
            elif operator == "&":
                result = num1 & num2
            elif operator == "|":
                result = num1 | num2
            elif operator == "^":
                result = num1 ^ num2
            elif operator == "<<":
                result = num1 << num2
            elif operator == ">>":
                result = num1 >> num2
            
            # 显示结果
            self.hex_result.setText(hex(result))
            self.dec_result.setText(str(result))
            self.bin_result.setText(bin(result))
            
        except Exception as e:
            self.hex_result.setText("错误")
            self.dec_result.setText("错误")
            self.bin_result.setText("错误")
    
    def convert_base(self):
        """进制转换"""
        try:
            # 获取输入基数和值
            base_index = self.input_base.currentIndex()
            input_text = self.convert_input.text()
            
            if not input_text:
                return
            
            # 转换为整数
            if base_index == 0:  # 二进制
                value = int(input_text, 2)
            elif base_index == 1:  # 八进制
                value = int(input_text, 8)
            elif base_index == 2:  # 十进制
                value = int(input_text)
            else:  # 十六进制
                value = int(input_text, 16)
            
            # 显示结果
            self.bin_convert_result.setText(bin(value))
            self.oct_convert_result.setText(oct(value))
            self.dec_convert_result.setText(str(value))
            self.hex_convert_result.setText(hex(value))
            
        except Exception as e:
            self.bin_convert_result.setText("错误")
            self.oct_convert_result.setText("错误")
            self.dec_convert_result.setText("错误")
            self.hex_convert_result.setText("错误")
    
    def setup_forensic_tab(self):
        """设置内存取证常用计算标签页"""
        layout = QVBoxLayout(self.forensic_tab)
        
        # 时间戳转换组
        timestamp_group = QGroupBox("时间戳转换")
        timestamp_layout = QGridLayout(timestamp_group)
        
        # UNIX时间戳输入
        self.unix_timestamp_label = QLabel("UNIX时间戳:")
        self.unix_timestamp_input = QLineEdit()
        self.unix_timestamp_input.setPlaceholderText("例如: 1621234567")
        
        # 转换按钮
        self.convert_timestamp_button = QPushButton("转换")
        self.convert_timestamp_button.clicked.connect(self.convert_timestamp)
        
        # 结果显示
        self.timestamp_result_label = QLabel("转换结果:")
        self.timestamp_result = QLineEdit()
        self.timestamp_result.setReadOnly(True)
        
        # 当前时间戳按钮
        self.current_timestamp_button = QPushButton("获取当前时间戳")
        self.current_timestamp_button.clicked.connect(self.get_current_timestamp)
        
        timestamp_layout.addWidget(self.unix_timestamp_label, 0, 0)
        timestamp_layout.addWidget(self.unix_timestamp_input, 0, 1)
        timestamp_layout.addWidget(self.convert_timestamp_button, 0, 2)
        timestamp_layout.addWidget(self.timestamp_result_label, 1, 0)
        timestamp_layout.addWidget(self.timestamp_result, 1, 1, 1, 2)
        timestamp_layout.addWidget(self.current_timestamp_button, 2, 0, 1, 3)
        
        # 内存地址计算组
        memory_group = QGroupBox("内存地址计算")
        memory_layout = QGridLayout(memory_group)
        
        # 虚拟地址输入
        self.virtual_addr_label = QLabel("虚拟地址:")
        self.virtual_addr_input = QLineEdit()
        self.virtual_addr_input.setPlaceholderText("例如: 0x7FFE0000")
        
        # 页大小选择
        self.page_size_label = QLabel("页大小:")
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["4KB (0x1000)", "2MB (0x200000)", "1GB (0x40000000)"])
        
        # 计算按钮
        self.calc_memory_button = QPushButton("计算")
        self.calc_memory_button.clicked.connect(self.calculate_memory_address)
        
        # 结果显示
        self.page_number_label = QLabel("页号:")
        self.page_number_result = QLineEdit()
        self.page_number_result.setReadOnly(True)
        
        self.page_offset_label = QLabel("页内偏移:")
        self.page_offset_result = QLineEdit()
        self.page_offset_result.setReadOnly(True)
        
        memory_layout.addWidget(self.virtual_addr_label, 0, 0)
        memory_layout.addWidget(self.virtual_addr_input, 0, 1, 1, 2)
        memory_layout.addWidget(self.page_size_label, 1, 0)
        memory_layout.addWidget(self.page_size_combo, 1, 1, 1, 2)
        memory_layout.addWidget(self.calc_memory_button, 2, 0, 1, 3)
        memory_layout.addWidget(self.page_number_label, 3, 0)
        memory_layout.addWidget(self.page_number_result, 3, 1, 1, 2)
        memory_layout.addWidget(self.page_offset_label, 4, 0)
        memory_layout.addWidget(self.page_offset_result, 4, 1, 1, 2)
        
        # 哈希计算组
        hash_group = QGroupBox("哈希值计算")
        hash_layout = QGridLayout(hash_group)
        
        # 输入文本
        self.hash_input_label = QLabel("输入文本:")
        self.hash_input = QLineEdit()
        self.hash_input.setPlaceholderText("输入要计算哈希的文本")
        
        # 哈希类型选择
        self.hash_type_label = QLabel("哈希类型:")
        self.hash_type_combo = QComboBox()
        self.hash_type_combo.addItems(["MD5", "SHA-1", "SHA-256", "SHA-512"])
        
        # 计算按钮
        self.calc_hash_button = QPushButton("计算哈希")
        self.calc_hash_button.clicked.connect(self.calculate_hash)
        
        # 结果显示
        self.hash_result_label = QLabel("哈希结果:")
        self.hash_result = QLineEdit()
        self.hash_result.setReadOnly(True)
        
        hash_layout.addWidget(self.hash_input_label, 0, 0)
        hash_layout.addWidget(self.hash_input, 0, 1, 1, 2)
        hash_layout.addWidget(self.hash_type_label, 1, 0)
        hash_layout.addWidget(self.hash_type_combo, 1, 1)
        hash_layout.addWidget(self.calc_hash_button, 1, 2)
        hash_layout.addWidget(self.hash_result_label, 2, 0)
        hash_layout.addWidget(self.hash_result, 2, 1, 1, 2)
        
        # 数据单位转换组
        unit_group = QGroupBox("数据单位转换")
        unit_layout = QGridLayout(unit_group)
        
        # 输入值
        self.unit_value_label = QLabel("数值:")
        self.unit_value_input = QLineEdit()
        self.unit_value_input.setPlaceholderText("例如: 1024")
        
        # 输入单位
        self.unit_from_label = QLabel("从:")
        self.unit_from_combo = QComboBox()
        self.unit_from_combo.addItems(["字节(B)", "千字节(KB)", "兆字节(MB)", "吉字节(GB)", "太字节(TB)"])
        
        # 输出单位
        self.unit_to_label = QLabel("到:")
        self.unit_to_combo = QComboBox()
        self.unit_to_combo.addItems(["字节(B)", "千字节(KB)", "兆字节(MB)", "吉字节(GB)", "太字节(TB)"])
        self.unit_to_combo.setCurrentIndex(2)  # 默认选择MB
        
        # 转换按钮
        self.convert_unit_button = QPushButton("转换")
        self.convert_unit_button.clicked.connect(self.convert_data_unit)
        
        # 结果显示
        self.unit_result_label = QLabel("转换结果:")
        self.unit_result = QLineEdit()
        self.unit_result.setReadOnly(True)
        
        unit_layout.addWidget(self.unit_value_label, 0, 0)
        unit_layout.addWidget(self.unit_value_input, 0, 1, 1, 3)
        unit_layout.addWidget(self.unit_from_label, 1, 0)
        unit_layout.addWidget(self.unit_from_combo, 1, 1)
        unit_layout.addWidget(self.unit_to_label, 1, 2)
        unit_layout.addWidget(self.unit_to_combo, 1, 3)
        unit_layout.addWidget(self.convert_unit_button, 2, 0, 1, 4)
        unit_layout.addWidget(self.unit_result_label, 3, 0)
        unit_layout.addWidget(self.unit_result, 3, 1, 1, 3)
        
        # 添加到主布局
        layout.addWidget(timestamp_group)
        layout.addWidget(memory_group)
        layout.addWidget(hash_group)
        layout.addWidget(unit_group)
        layout.addStretch()
    
    def convert_timestamp(self):
        """转换UNIX时间戳为可读时间"""
        try:
            timestamp = int(self.unix_timestamp_input.text())
            from datetime import datetime
            dt = datetime.fromtimestamp(timestamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            self.timestamp_result.setText(formatted_time)
        except Exception as e:
            self.timestamp_result.setText(f"错误: {str(e)}")
    
    def get_current_timestamp(self):
        """获取当前时间的UNIX时间戳"""
        from datetime import datetime
        current_timestamp = int(datetime.now().timestamp())
        self.unix_timestamp_input.setText(str(current_timestamp))
        self.convert_timestamp()
    
    def calculate_memory_address(self):
        """计算虚拟地址的页号和页内偏移"""
        try:
            # 获取虚拟地址
            virtual_addr = int(self.virtual_addr_input.text(), 16)
            
            # 获取页大小
            page_size_index = self.page_size_combo.currentIndex()
            if page_size_index == 0:
                page_size = 0x1000  # 4KB
            elif page_size_index == 1:
                page_size = 0x200000  # 2MB
            else:
                page_size = 0x40000000  # 1GB
            
            # 计算页号和页内偏移
            page_number = virtual_addr // page_size
            page_offset = virtual_addr % page_size
            
            # 显示结果
            self.page_number_result.setText(hex(page_number))
            self.page_offset_result.setText(hex(page_offset))
            
        except Exception as e:
            self.page_number_result.setText("错误")
            self.page_offset_result.setText(f"{str(e)}")
    
    def calculate_hash(self):
        """计算输入文本的哈希值"""
        try:
            import hashlib
            input_text = self.hash_input.text().encode('utf-8')
            hash_type = self.hash_type_combo.currentText()
            
            if hash_type == "MD5":
                hash_obj = hashlib.md5(input_text)
            elif hash_type == "SHA-1":
                hash_obj = hashlib.sha1(input_text)
            elif hash_type == "SHA-256":
                hash_obj = hashlib.sha256(input_text)
            elif hash_type == "SHA-512":
                hash_obj = hashlib.sha512(input_text)
            
            hash_result = hash_obj.hexdigest()
            self.hash_result.setText(hash_result)
            
        except Exception as e:
            self.hash_result.setText(f"错误: {str(e)}")
    
    def convert_data_unit(self):
        """转换数据单位"""
        try:
            # 获取输入值
            value = float(self.unit_value_input.text())
            
            # 获取单位转换系数
            units = ["字节(B)", "千字节(KB)", "兆字节(MB)", "吉字节(GB)", "太字节(TB)"]
            from_index = self.unit_from_combo.currentIndex()
            to_index = self.unit_to_combo.currentIndex()
            
            # 转换为字节
            bytes_value = value * (1024 ** from_index)
            
            # 转换为目标单位
            result = bytes_value / (1024 ** to_index)
            
            # 显示结果
            self.unit_result.setText(f"{result:.6f} {units[to_index]}")
            
        except Exception as e:
            self.unit_result.setText(f"错误: {str(e)}")
    
    def setup_pe_tab(self):
        """设置PE文件结构分析标签页"""
        layout = QVBoxLayout(self.pe_tab)
        
        # RVA和VA转换组
        rva_group = QGroupBox("RVA/VA转换")
        rva_layout = QGridLayout(rva_group)
        
        # 文件基址址址入
        self.image_base_label = QLabel("文件基址址:")
        self.image_base_input = QLineEdit()
        self.image_base_input.setPlaceholderText("例如: 0x400000")
        self.image_base_input.setText("0x400000")  # 默认值
        
        rva_layout.addWidget(self.image_base_label, 0, 0)
        rva_layout.addWidget(self.image_base_input, 0, 1, 1, 3)
        
        # RVA转VA
        self.rva_label = QLabel("RVA:")
        self.rva_input = QLineEdit()
        self.rva_input.setPlaceholderText("例如: 0x1000")
        self.rva_to_va_button = QPushButton("RVA转VA")
        self.rva_to_va_button.clicked.connect(self.convert_rva_to_va)
        
        rva_layout.addWidget(self.rva_label, 1, 0)
        rva_layout.addWidget(self.rva_input, 1, 1)
        rva_layout.addWidget(self.rva_to_va_button, 1, 2)
        
        # VA转RVA
        self.va_label = QLabel("VA:")
        self.va_input = QLineEdit()
        self.va_input.setPlaceholderText("例如: 0x401000")
        self.va_to_rva_button = QPushButton("VA转RVA")
        self.va_to_rva_button.clicked.connect(self.convert_va_to_rva)
        
        rva_layout.addWidget(self.va_label, 2, 0)
        rva_layout.addWidget(self.va_input, 2, 1)
        rva_layout.addWidget(self.va_to_rva_button, 2, 2)
        
        # 转换结果
        self.rva_va_result_label = QLabel("转换结果:")
        self.rva_va_result = QLineEdit()
        self.rva_va_result.setReadOnly(True)
        
        rva_layout.addWidget(self.rva_va_result_label, 3, 0)
        rva_layout.addWidget(self.rva_va_result, 3, 1, 1, 3)
        
        # 文件偏移计算组
        file_offset_group = QGroupBox("文件偏移计算")
        file_offset_layout = QGridLayout(file_offset_group)
        
        # 节表信息输入
        self.section_info_label = QLabel("节表信息:")
        file_offset_layout.addWidget(self.section_info_label, 0, 0, 1, 4)
        
        # 节表名称
        self.section_name_label = QLabel("节表名称:")
        self.section_name_input = QLineEdit()
        self.section_name_input.setPlaceholderText("例如: .text")
        
        file_offset_layout.addWidget(self.section_name_label, 1, 0)
        file_offset_layout.addWidget(self.section_name_input, 1, 1, 1, 3)
        
        # 节表RVA
        self.section_rva_label = QLabel("节表RVA:")
        self.section_rva_input = QLineEdit()
        self.section_rva_input.setPlaceholderText("例如: 0x1000")
        
        file_offset_layout.addWidget(self.section_rva_label, 2, 0)
        file_offset_layout.addWidget(self.section_rva_input, 2, 1, 1, 3)
        
        # 节表文件偏移
        self.section_file_offset_label = QLabel("节表文件偏移:")
        self.section_file_offset_input = QLineEdit()
        self.section_file_offset_input.setPlaceholderText("例如: 0x400")
        
        file_offset_layout.addWidget(self.section_file_offset_label, 3, 0)
        file_offset_layout.addWidget(self.section_file_offset_input, 3, 1, 1, 3)
        
        # RVA转文件偏移
        self.rva_to_offset_label = QLabel("RVA:")
        self.rva_to_offset_input = QLineEdit()
        self.rva_to_offset_input.setPlaceholderText("例如: 0x1200")
        self.rva_to_offset_button = QPushButton("RVA转文件偏移")
        self.rva_to_offset_button.clicked.connect(self.convert_rva_to_file_offset)
        
        file_offset_layout.addWidget(self.rva_to_offset_label, 4, 0)
        file_offset_layout.addWidget(self.rva_to_offset_input, 4, 1)
        file_offset_layout.addWidget(self.rva_to_offset_button, 4, 2, 1, 2)
        
        # 文件偏移转RVA
        self.offset_to_rva_label = QLabel("文件偏移:")
        self.offset_to_rva_input = QLineEdit()
        self.offset_to_rva_input.setPlaceholderText("例如: 0x600")
        self.offset_to_rva_button = QPushButton("文件偏移转RVA")
        self.offset_to_rva_button.clicked.connect(self.convert_file_offset_to_rva)
        
        file_offset_layout.addWidget(self.offset_to_rva_label, 5, 0)
        file_offset_layout.addWidget(self.offset_to_rva_input, 5, 1)
        file_offset_layout.addWidget(self.offset_to_rva_button, 5, 2, 1, 2)
        
        # 转换结果
        self.file_offset_result_label = QLabel("转换结果:")
        self.file_offset_result = QLineEdit()
        self.file_offset_result.setReadOnly(True)
        
        file_offset_layout.addWidget(self.file_offset_result_label, 6, 0)
        file_offset_layout.addWidget(self.file_offset_result, 6, 1, 1, 3)
        
        # PE文件结构参考组
        pe_reference_group = QGroupBox("PE文件结构参考")
        pe_reference_layout = QGridLayout(pe_reference_group)
        
        pe_headers = [
            ("字段", "偏移量", "大小", "说明"),
            ("DOS头", "0x0", "0x40", "MZ头部"),
            ("e_lfanew", "0x3C", "0x4", "PE头部偏移"),
            ("PE签名", "e_lfanew", "0x4", "PE\0\0"),
            ("FileHeader", "e_lfanew+0x4", "0x14", "文件头"),
            ("OptionalHeader", "e_lfanew+0x18", "变长", "可选头"),
            ("SectionTable", "OptionalHeader后", "N*0x28", "节表"),
            ("ImageBase", "OptionalHeader+0x18", "0x4/0x8", "映像基址"),
            ("SectionAlignment", "OptionalHeader+0x20", "0x4", "节对齐"),
            ("FileAlignment", "OptionalHeader+0x24", "0x4", "文件对齐"),
            ("DataDirectory", "OptionalHeader尾部", "16*0x8", "数据目录"),
        ]
        
        # 创建表格标题
        for col, title in enumerate(pe_headers[0]):
            label = QLabel(title)
            label.setStyleSheet("font-weight: bold;")
            pe_reference_layout.addWidget(label, 0, col)
        
        # 填充表格数据
        for row, (field, offset, size, desc) in enumerate(pe_headers[1:], 1):
            pe_reference_layout.addWidget(QLabel(field), row, 0)
            pe_reference_layout.addWidget(QLabel(offset), row, 1)
            pe_reference_layout.addWidget(QLabel(size), row, 2)
            pe_reference_layout.addWidget(QLabel(desc), row, 3)
        
        # 添加到主布局
        layout.addWidget(rva_group)
        layout.addWidget(file_offset_group)
        layout.addWidget(pe_reference_group)
        layout.addStretch()
    
    def convert_rva_to_va(self):
        """将RVA转换为VA"""
        try:
            # 获取基址址和RVA
            image_base = int(self.image_base_input.text(), 16)
            rva = int(self.rva_input.text(), 16)
            
            # 计算VA
            va = image_base + rva
            
            # 显示结果
            self.rva_va_result.setText(f"VA = {hex(va)}")
            
        except Exception as e:
            self.rva_va_result.setText(f"错误: {str(e)}")
    
    def convert_va_to_rva(self):
        """将VA转换为RVA"""
        try:
            # 获取基址址和VA
            image_base = int(self.image_base_input.text(), 16)
            va = int(self.va_input.text(), 16)
            
            # 计算RVA
            rva = va - image_base
            
            # 显示结果
            self.rva_va_result.setText(f"RVA = {hex(rva)}")
            
        except Exception as e:
            self.rva_va_result.setText(f"错误: {str(e)}")
    
    def convert_rva_to_file_offset(self):
        """将RVA转换为文件偏移"""
        try:
            # 获取节表信息和RVA
            section_rva = int(self.section_rva_input.text(), 16)
            section_file_offset = int(self.section_file_offset_input.text(), 16)
            rva = int(self.rva_to_offset_input.text(), 16)
            
            # 计算文件偏移
            # 文件偏移 = 节表文件偏移 + (RVA - 节表RVA)
            file_offset = section_file_offset + (rva - section_rva)
            
            # 显示结果
            self.file_offset_result.setText(f"文件偏移 = {hex(file_offset)}")
            
        except Exception as e:
            self.file_offset_result.setText(f"错误: {str(e)}")
    
    def convert_file_offset_to_rva(self):
        """将文件偏移转换为RVA"""
        try:
            # 获取节表信息和文件偏移
            section_rva = int(self.section_rva_input.text(), 16)
            section_file_offset = int(self.section_file_offset_input.text(), 16)
            file_offset = int(self.offset_to_rva_input.text(), 16)
            
            # 计算RVA
            # RVA = 节表RVA + (文件偏移 - 节表文件偏移)
            rva = section_rva + (file_offset - section_file_offset)
            
            # 显示结果
            self.file_offset_result.setText(f"RVA = {hex(rva)}")
            
        except Exception as e:
            self.file_offset_result.setText(f"错误: {str(e)}")
    
    def update_style(self):
        """更新样式以匹配当前主题"""
        try:
            # 导入样式变量
            from ui.styles import quick_check_style, background_color, text_color, button_bg_color, button_text_color, button_hover_color, border_color
            
            # 应用全局样式
            self.setStyleSheet(quick_check_style)
            
            # 更新标签样式
            self.title_label.setStyleSheet(f"font-size: 18px; font-weight: bold; margin: 10px; color: {text_color};")
            
            # 更新标签页样式
            tab_style = f"""
                QTabWidget::pane {{
                    border: 1px solid {border_color};
                    background-color: {background_color};
                }}
                QTabBar::tab {{
                    background-color: {button_bg_color};
                    color: {button_text_color};
                    border: 1px solid {border_color};
                    padding: 5px 10px;
                    margin-right: 2px;
                }}
                QTabBar::tab:selected {{
                    background-color: {button_hover_color};
                }}
            """
            self.tab_widget.setStyleSheet(tab_style)
            
            # 更新组框样式
            group_style = f"""
                QGroupBox {{
                    border: 1px solid {border_color};
                    border-radius: 3px;
                    margin-top: 10px;
                    font-weight: bold;
                    color: {text_color};
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px;
                }}
            """
            
            # 更新标签样式
            label_style = f"color: {text_color};"
            
            # 更新输入框样式
            input_style = f"""
                QLineEdit {{
                    background-color: {background_color};
                    color: {text_color};
                    border: 1px solid {border_color};
                    padding: 3px;
                    border-radius: 2px;
                }}
            """
            
            # 更新按钮样式
            button_style = f"""
                QPushButton {{
                    background-color: {button_bg_color};
                    color: {button_text_color};
                    border: 1px solid {border_color};
                    border-radius: 3px;
                    padding: 5px 10px;
                }}
                QPushButton:hover {{
                    background-color: {button_hover_color};
                }}
            """
            
            # 更新单选按钮样式
            radio_style = f"""
                QRadioButton {{
                    color: {text_color};
                }}
                QRadioButton::indicator {{
                    width: 13px;
                    height: 13px;
                }}
            """
            
            # 更新下拉框样式
            combo_style = f"""
                QComboBox {{
                    background-color: {button_bg_color};
                    color: {button_text_color};
                    border: 1px solid {border_color};
                    padding: 3px;
                    border-radius: 2px;
                }}
                QComboBox:hover {{
                    background-color: {button_hover_color};
                }}
                QComboBox QAbstractItemView {{
                    background-color: {background_color};
                    color: {text_color};
                    selection-background-color: {button_hover_color};
                }}
            """
            
            # 应用样式到所有组件
            for tab in [self.offset_tab, self.hex_tab, self.convert_tab, self.forensic_tab, self.pe_tab]:
                for child in tab.findChildren(QGroupBox):
                    child.setStyleSheet(group_style)
                
                for child in tab.findChildren(QLabel):
                    child.setStyleSheet(label_style)
                
                for child in tab.findChildren(QLineEdit):
                    child.setStyleSheet(input_style)
                
                for child in tab.findChildren(QPushButton):
                    child.setStyleSheet(button_style)
                
                for child in tab.findChildren(QRadioButton):
                    child.setStyleSheet(radio_style)
                
                for child in tab.findChildren(QComboBox):
                    child.setStyleSheet(combo_style)
        
        except Exception as e:
            print(f"样式更新错误: {str(e)}")

# 用于独立测试
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = Calculator()
    window.show()
    sys.exit(app.exec())
