from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtGui import QPainter, QPen, QPainterPath, QColor
from PySide6.QtCore import Qt, QPointF, QUuid

from core.flow_graph.flow_port import PortType


class FlowEdge(QGraphicsPathItem):
    """
    流程图边：表示节点之间的连接线
    """
    
    def __init__(self, source_port=None, target_port=None, parent=None):
        super().__init__(parent)
        
        # 基本属性
        self.id = str(QUuid.createUuid())
        self.source_port = source_port
        self.target_port = target_port
        
        # 临时线条的起点和终点（用于拖拽创建连接）
        self.start_pos = QPointF(0, 0)
        self.end_pos = QPointF(0, 0)
        
        # 是否是临时线
        self.is_temporary = False
        
        # 设置可选择
        self.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemIsSelectable)
        
        # 设置外观
        self.pen_width = 2.0
        self.normal_color = QColor(80, 100, 120)
        self.selected_color = QColor(200, 150, 50)
        self.temp_color = QColor(100, 100, 100)
        
        # 设置画笔
        self.setPen(QPen(self.normal_color, self.pen_width, 
                        Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        
        # 设置Z值，确保线条在节点下方
        self.setZValue(-1)
        
        # 如果提供了端口，则连接
        if source_port and target_port:
            self.connect(source_port, target_port)
    
    def connect(self, source_port, target_port):
        """
        连接两个端口
        
        Args:
            source_port: 源端口（输出端口）
            target_port: 目标端口（输入端口）
        """
        # 验证端口类型
        if (source_port.port_type == PortType.Output and
            target_port.port_type == PortType.Input):
            
            # 设置端口
            self.source_port = source_port
            self.target_port = target_port
            
            # 将边添加到两个端口
            source_port.add_edge(self)
            target_port.add_edge(self)
            
            # 更新线条位置
            self.update_position()
            
            # 设置为非临时
            self.is_temporary = False
        else:
            raise ValueError("无效的端口连接：源端口必须是输出端口，目标端口必须是输入端口")
    
    def disconnect(self):
        """断开连接"""
        # 从端口中移除此边
        if self.source_port:
            self.source_port.remove_edge(self)
        if self.target_port:
            self.target_port.remove_edge(self)
        
        # 清除引用
        self.source_port = None
        self.target_port = None
    
    def paint(self, painter, option, widget):
        """绘制边"""
        # 设置抗锯齿
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 根据选择状态和临时状态设置画笔
        if self.isSelected():
            pen = QPen(self.selected_color, self.pen_width)
        elif self.is_temporary:
            pen = QPen(self.temp_color, self.pen_width, Qt.PenStyle.DashLine)
        else:
            pen = QPen(self.normal_color, self.pen_width)
        
        painter.setPen(pen)
        
        # 绘制路径
        painter.drawPath(self.path())
    
    def update_position(self):
        """更新连接线的位置"""
        if self.is_temporary:
            # 临时线条使用起点和终点
            self._create_path(self.start_pos, self.end_pos)
        elif self.source_port and self.target_port:
            # 获取源端口和目标端口的场景坐标位置
            source_pos = self.source_port.get_connection_pos()
            target_pos = self.target_port.get_connection_pos()
            
            # 创建贝塞尔曲线路径
            self._create_path(source_pos, target_pos)
    
    def _create_path(self, source_pos, target_pos):
        """
        创建两点之间的贝塞尔曲线路径
        
        Args:
            source_pos: 起点位置
            target_pos: 终点位置
        """
        # 计算控制点
        dx = target_pos.x() - source_pos.x()
        control_distance = abs(dx) * 0.5
        
        # 创建路径
        path = QPainterPath()
        path.moveTo(source_pos)
        
        # 二次贝塞尔曲线使用两个控制点
        c1 = QPointF(source_pos.x() + control_distance, source_pos.y())
        c2 = QPointF(target_pos.x() - control_distance, target_pos.y())
        
        # 绘制贝塞尔曲线
        path.cubicTo(c1, c2, target_pos)
        
        # 设置路径
        self.setPath(path)
    
    def set_temporary_points(self, start_pos, end_pos):
        """设置临时线条的起点和终点"""
        self.is_temporary = True
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.update_position()
    
    def serialize(self):
        """序列化边数据"""
        if not self.source_port or not self.target_port:
            return None
        
        return {
            "id": self.id,
            "source_node_id": self.source_port.parent_node.id,
            "source_port_index": self.source_port.port_index,
            "target_node_id": self.target_port.parent_node.id,
            "target_port_index": self.target_port.port_index
        }
