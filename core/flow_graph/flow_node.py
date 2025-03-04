from PySide6.QtWidgets import (QGraphicsItem, QGraphicsObject, QGraphicsProxyWidget,
                               QGraphicsSceneMouseEvent, QMenu, QGraphicsTextItem, QLabel)
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath, QCursor
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, Slot, QUuid

from core.flow_graph.flow_port import FlowPort, PortType


class FlowNode(QGraphicsObject):
    """
    流程图节点类：表示任务流程中的一个节点
    """
    # 信号
    position_changed = Signal(QPointF)  # 节点位置变化信号
    data_changed = Signal()  # 节点数据变化信号
    
    # 节点默认样式
    DEFAULT_WIDTH = 180
    DEFAULT_HEIGHT = 120  # 再增加一点高度
    TITLE_HEIGHT = 25
    PORT_RADIUS = 8
    
    def __init__(self, title="节点", parent=None):
        super().__init__(parent)
        
        # 基本属性
        self.id = str(QUuid.createUuid())
        self.title = title
        self.node_width = self.DEFAULT_WIDTH
        self.node_height = self.DEFAULT_HEIGHT
        
        # 设置可选择、可移动
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        # 接受悬停事件
        self.setAcceptHoverEvents(True)
        
        # 外观
        self.title_color = QColor(100, 100, 200)
        self.title_font = QFont("Arial", 10, QFont.Bold)
        self.border_pen = QPen(QColor(100, 100, 100), 2)
        self.selected_pen = QPen(QColor(200, 150, 50), 3)
        self.brush = QBrush(QColor(240, 240, 240))
        
        # 端口列表
        self.input_ports = []  # 输入端口
        self.output_ports = []  # 输出端口
        
        # 创建标题
        self.title_item = QGraphicsTextItem(self)
        self.title_item.setPlainText(title)
        self.title_item.setFont(self.title_font)
        self.title_item.setDefaultTextColor(Qt.GlobalColor.white)
        self.title_item.setPos(5, 2)
        
        # 创建默认端口
        self.add_input_port("输入")
        self.add_output_port("输出")
        
        # 内部数据
        self.data = {}
        self.area = ""  # 区域（MemProcFS、Vol2等）
        self.task = ""  # 任务名称
        
        # 开始节点标志
        self.is_start_node = False
    
    def boundingRect(self):
        """定义节点的边界矩形"""
        return QRectF(0, 0, self.node_width, self.node_height)
    
    def paint(self, painter, option, widget):
        """绘制节点"""
        # 绘制阴影
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 30))
        painter.drawRoundedRect(3, 3, self.node_width, self.node_height, 10, 10)
        
        # 设置节点边框和填充
        if self.isSelected():
            painter.setPen(self.selected_pen)
        else:
            painter.setPen(self.border_pen)
            
        # 如果是开始节点，使用特殊的填充颜色
        if self.is_start_node:
            painter.setBrush(QBrush(QColor(200, 255, 200)))  # 浅绿色
        else:
            painter.setBrush(self.brush)
        
        # 绘制主体
        painter.drawRoundedRect(0, 0, self.node_width, self.node_height, 10, 10)
        
        # 绘制标题栏
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.node_width, self.TITLE_HEIGHT, 10, 10)
        path.addRect(0, self.TITLE_HEIGHT / 2, self.node_width, self.TITLE_HEIGHT / 2)
        
        # 如果是开始节点，使用特殊的标题颜色
        if self.is_start_node:
            painter.fillPath(path, QColor(50, 150, 50))  # 深绿色
        else:
            painter.fillPath(path, self.title_color)
        
        # 绘制任务信息
        if self.area and self.task:
            # 绘制区域名称（在标题栏下方）
            painter.setPen(Qt.GlobalColor.black)
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            area_rect = QRectF(10, self.TITLE_HEIGHT + 5, 
                              self.node_width - 20, 20)
            painter.drawText(area_rect, Qt.AlignmentFlag.AlignCenter, self.area)
            
            # 绘制任务名称（在区域名称下方）
            painter.setFont(QFont("Arial", 9))
            task_rect = QRectF(10, self.TITLE_HEIGHT + 25, 
                              self.node_width - 20, self.node_height - self.TITLE_HEIGHT - 35)
            painter.drawText(task_rect, Qt.AlignmentFlag.AlignCenter, self.task)
    
    def add_input_port(self, name=""):
        """添加输入端口"""
        port = FlowPort(self, name, PortType.Input, len(self.input_ports))
        self.input_ports.append(port)
        self._update_port_positions()
        return port
    
    def add_output_port(self, name=""):
        """添加输出端口"""
        port = FlowPort(self, name, PortType.Output, len(self.output_ports))
        self.output_ports.append(port)
        self._update_port_positions()
        return port
    
    def _update_port_positions(self):
        """更新所有端口位置"""
        # 计算输入端口位置
        input_count = len(self.input_ports)
        for i, port in enumerate(self.input_ports):
            x = self.PORT_RADIUS + 5  # 靠左侧放置
            
            # 将端口放在节点的上下两侧，避开中间的文本区域
            if i < input_count / 2:
                # 上半部分
                y = self.TITLE_HEIGHT + (i + 1) * (self.node_height / 2 - self.TITLE_HEIGHT) / (input_count / 2 + 1)
            else:
                # 下半部分
                idx = i - int(input_count / 2)
                y = self.node_height / 2 + idx * (self.node_height / 2) / (input_count - int(input_count / 2) + 1)
            
            port.setPos(x, y)
        
        # 计算输出端口位置
        output_count = len(self.output_ports)
        for i, port in enumerate(self.output_ports):
            x = self.node_width - self.PORT_RADIUS - 5  # 靠右侧放置
            
            # 将端口放在节点的上下两侧，避开中间的文本区域
            if i < output_count / 2:
                # 上半部分
                y = self.TITLE_HEIGHT + (i + 1) * (self.node_height / 2 - self.TITLE_HEIGHT) / (output_count / 2 + 1)
            else:
                # 下半部分
                idx = i - int(output_count / 2)
                y = self.node_height / 2 + idx * (self.node_height / 2) / (output_count - int(output_count / 2) + 1)
            
            port.setPos(x, y)
    
    def itemChange(self, change, value):
        """处理项目变化事件"""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # 发出位置变化信号
            self.position_changed.emit(value)
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # 节点移动后，更新连接的边
            for port in self.input_ports + self.output_ports:
                for edge in port.edges:
                    edge.update_position()
        
        return super().itemChange(change, value)
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件"""
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            # 将节点置于顶层
            self.setZValue(1)
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        super().mouseReleaseEvent(event)
        # 重置Z值
        self.setZValue(0)
    
    def contextMenuEvent(self, event):
        """处理右键菜单事件"""
        menu = QMenu()
        
        # 添加菜单项
        delete_action = menu.addAction("删除节点")
        rename_action = menu.addAction("重命名")
        
        # 添加设置/取消开始节点的菜单项
        if self.is_start_node:
            start_action = menu.addAction("取消设为开始节点")
        else:
            start_action = menu.addAction("设为开始节点")
        
        # 显示菜单并获取用户选择
        if hasattr(event, 'screenPos'):
            pos = event.screenPos()
        else:
            pos = event.globalPos()
            
        action = menu.exec_(pos)
        
        # 处理用户选择
        if action == delete_action:
            # 删除节点及其连接
            if self.scene():
                # 先删除所有连接
                ports = self.input_ports + self.output_ports
                for port in ports:
                    for edge in list(port.edges):
                        if hasattr(self.scene(), 'edges') and edge.id in self.scene().edges:
                            del self.scene().edges[edge.id]
                        self.scene().removeItem(edge)
                
                # 再删除节点
                if hasattr(self.scene(), 'nodes') and self.id in self.scene().nodes:
                    del self.scene().nodes[self.id]
                self.scene().removeItem(self)
                
                # 发送信号通知节点已删除
                if hasattr(self.scene(), 'node_deleted'):
                    self.scene().node_deleted.emit(self)
                
                event.accept()
                return
        elif action == rename_action:
            # 重命名功能可以后续实现
            pass
        elif action == start_action:
            # 设置或取消开始节点
            if self.scene():
                # 如果设置为开始节点，先取消其他节点的开始节点状态
                if not self.is_start_node:
                    for node in self.scene().nodes.values():
                        if node.is_start_node:
                            node.is_start_node = False
                            node.update()
                
                # 切换当前节点的开始节点状态
                self.is_start_node = not self.is_start_node
                self.update()
                
                event.accept()
                return
        
        super().contextMenuEvent(event)
    
    def set_task(self, area, task_name):
        """设置节点的任务内容"""
        self.area = area
        self.task = task_name
        self.data["area"] = area
        self.data["task"] = task_name
        
        # 更新标题
        self.title = task_name
        self.title_item.setPlainText(task_name)
        
        # 通知数据变化
        self.data_changed.emit()
        self.update()
    
    def get_connected_nodes(self):
        """获取所有连接到此节点的其他节点"""
        connected_nodes = set()
        
        # 检查输入端口连接的节点
        for port in self.input_ports:
            for edge in port.edges:
                source_port = edge.source_port
                if source_port and source_port.parent_node != self:
                    connected_nodes.add(source_port.parent_node)
        
        # 检查输出端口连接的节点
        for port in self.output_ports:
            for edge in port.edges:
                target_port = edge.target_port
                if target_port and target_port.parent_node != self:
                    connected_nodes.add(target_port.parent_node)
        
        return list(connected_nodes)
    
    def serialize(self):
        """序列化节点数据"""
        # 获取端口连接信息
        input_connections = []
        for i, port in enumerate(self.input_ports):
            for edge in port.edges:
                if edge.source_port and edge.source_port.parent_node:
                    input_connections.append({
                        "source_node_id": edge.source_port.parent_node.id,
                        "source_port_index": edge.source_port.parent_node.output_ports.index(edge.source_port),
                        "target_port_index": i
                    })
        
        # 返回节点数据
        return {
            "id": self.id,
            "title": self.title,
            "pos_x": self.pos().x(),
            "pos_y": self.pos().y(),
            "area": self.area,
            "task": self.task,
            "is_start_node": self.is_start_node,
            "input_connections": input_connections
        }
    
    def deserialize(self, data):
        """从序列化数据恢复节点"""
        # 恢复基本属性
        self.id = data.get("id", str(QUuid.createUuid()))
        self.title = data.get("title", "节点")
        self.setPos(data.get("pos_x", 0), data.get("pos_y", 0))
        
        # 恢复任务信息
        self.area = data.get("area", "")
        self.task = data.get("task", "")
        
        # 恢复开始节点状态
        self.is_start_node = data.get("is_start_node", False)
