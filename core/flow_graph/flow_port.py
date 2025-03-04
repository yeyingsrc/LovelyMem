from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QRadialGradient
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QObject, Slot
from enum import Enum


class PortType(Enum):
    """端口类型枚举"""
    Input = 1   # 输入端口
    Output = 2  # 输出端口


class FlowPort(QGraphicsItem):
    """
    流程图的端口类：表示节点上的连接点
    """
    RADIUS = 8  # 端口半径
    
    def __init__(self, parent_node, name="", port_type=PortType.Input, port_index=0):
        super().__init__(parent_node)
        
        # 设置属性
        self.parent_node = parent_node
        self.name = name
        self.port_type = port_type
        self.port_index = port_index
        
        # 连接的边列表
        self.edges = set()
        
        # 设置可接受悬停事件
        self.setAcceptHoverEvents(True)
        
        # 初始化外观
        self.radius = self.RADIUS
        self.hovered = False
        
        # 输入端口为蓝色，输出端口为红色
        if port_type == PortType.Input:
            self.color = QColor(51, 102, 204)  # 蓝色
        else:
            self.color = QColor(204, 51, 51)   # 红色
        
        # 设置工具提示
        self.setToolTip(name)
    
    def boundingRect(self):
        """定义端口的边界矩形"""
        return QRectF(-self.radius, -self.radius, 
                     2 * self.radius, 2 * self.radius)
    
    def paint(self, painter, option, widget):
        """绘制端口"""
        # 创建径向渐变填充
        gradient = QRadialGradient(0, 0, self.radius)
        if self.hovered:
            gradient.setColorAt(0, self.color.lighter(150))
            gradient.setColorAt(1, self.color)
            pen = QPen(self.color.lighter(150), 2)
        else:
            gradient.setColorAt(0, self.color.lighter(130))
            gradient.setColorAt(1, self.color)
            pen = QPen(self.color, 1.5)
        
        # 设置画笔和画刷
        painter.setPen(pen)
        painter.setBrush(QBrush(gradient))
        
        # 绘制圆形端口
        painter.drawEllipse(QPointF(0, 0), self.radius, self.radius)
    
    def hoverEnterEvent(self, event):
        """处理鼠标悬停进入事件"""
        self.hovered = True
        self.update()
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """处理鼠标悬停离开事件"""
        self.hovered = False
        self.update()
        super().hoverLeaveEvent(event)
    
    def add_edge(self, edge):
        """添加边到此端口"""
        self.edges.add(edge)
    
    def remove_edge(self, edge):
        """从此端口移除边"""
        if edge in self.edges:
            self.edges.remove(edge)
    
    def get_connection_pos(self):
        """获取连接点的位置"""
        # 返回场景坐标系中的位置
        return self.mapToScene(QPointF(0, 0))
    
    def can_connect(self, other_port):
        """检查是否可以与另一个端口连接"""
        # 不能连接到自己节点上的端口
        if self.parent_node == other_port.parent_node:
            return False
        
        # 检查端口类型是否匹配（输出连接到输入）
        if self.port_type == other_port.port_type:
            return False
        
        # 输入端口只能连接一条边
        if self.port_type == PortType.Input and len(self.edges) > 0:
            return False
        
        # 如果是输入端口，确保另一个是输出端口
        if self.port_type == PortType.Input:
            return other_port.port_type == PortType.Output
        else:  # 如果是输出端口，确保另一个是输入端口
            return other_port.port_type == PortType.Input
