from PySide6.QtWidgets import (QGraphicsScene, QMenu, QMessageBox, 
                               QInputDialog, QGraphicsSceneMouseEvent)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QTransform
from PySide6.QtCore import Qt, QPointF, Signal, QRectF

from core.flow_graph.flow_node import FlowNode
from core.flow_graph.flow_edge import FlowEdge
from core.flow_graph.flow_port import FlowPort, PortType


class FlowScene(QGraphicsScene):
    """
    流程图场景：管理所有流程图元素（节点、边）
    处理用户交互（创建、连接、删除）
    """
    # 信号
    node_created = Signal(FlowNode)
    node_deleted = Signal(FlowNode)
    edge_created = Signal(FlowEdge)
    edge_deleted = Signal(FlowEdge)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置场景范围（可以根据需要调整）
        self.setSceneRect(QRectF(-2000, -2000, 4000, 4000))
        
        # 设置背景色
        self.setBackgroundBrush(QColor(245, 245, 245))
        
        # 跟踪鼠标状态
        self.mouse_down_pos = QPointF(0, 0)
        
        # 跟踪正在创建的边
        self.temp_edge = None
        self.connection_port = None
        
        # 节点和边的集合（方便快速查找）
        self.nodes = {}  # id -> node
        self.edges = {}  # id -> edge
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件"""
        # 保存鼠标按下位置
        self.mouse_down_pos = event.scenePos()
        
        # 检查是否点击了端口
        item = self.itemAt(event.scenePos(), QTransform())
        if isinstance(item, FlowPort):
            # 记录连接起始端口
            self.connection_port = item
            
            # 创建临时边
            self.temp_edge = FlowEdge()
            self.addItem(self.temp_edge)
            
            # 设置边的起点为端口位置，终点为鼠标位置
            self.temp_edge.set_temporary_points(
                item.get_connection_pos(),
                event.scenePos()
            )
            
            # 事件已处理
            event.accept()
            return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件"""
        # 更新临时边的终点
        if self.temp_edge and self.connection_port:
            self.temp_edge.set_temporary_points(
                self.connection_port.get_connection_pos(),
                event.scenePos()
            )
            event.accept()
            return
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        # 检查是否需要完成连接
        if self.temp_edge and self.connection_port:
            # 查找目标端口
            item = self.itemAt(event.scenePos(), QTransform())
            
            # 清理临时边
            self.removeItem(self.temp_edge)
            self.temp_edge = None
            
            # 如果找到了端口并且可以连接
            if isinstance(item, FlowPort) and item != self.connection_port:
                source_port = None
                target_port = None
                
                # 确定源端口和目标端口
                if self.connection_port.port_type == PortType.Output and item.port_type == PortType.Input:
                    source_port = self.connection_port
                    target_port = item
                elif self.connection_port.port_type == PortType.Input and item.port_type == PortType.Output:
                    source_port = item
                    target_port = self.connection_port
                
                # 检查是否可以建立连接
                if source_port and target_port and source_port.can_connect(target_port):
                    # 创建实际的边
                    edge = FlowEdge(source_port, target_port)
                    self.addItem(edge)
                    
                    # 保存边并发出信号
                    self.edges[edge.id] = edge
                    self.edge_created.emit(edge)
            
            # 清除连接状态
            self.connection_port = None
            event.accept()
            return
        
        super().mouseReleaseEvent(event)
    
    def contextMenuEvent(self, event):
        """处理右键菜单事件"""
        # 创建菜单
        menu = QMenu()
        
        # 获取场景位置
        if hasattr(event, 'scenePos'):
            # 如果是QGraphicsSceneContextMenuEvent
            scene_pos = event.scenePos()
        else:
            # 如果是从view传来的QContextMenuEvent
            scene_pos = self.views()[0].mapToScene(event.pos())
        
        # 查找点击位置的项
        item = self.itemAt(scene_pos, QTransform())
        
        # 检查是否点击了节点或其子项
        node_item = None
        if isinstance(item, FlowNode):
            node_item = item
        elif isinstance(item, FlowPort) and item.parentItem() and isinstance(item.parentItem(), FlowNode):
            node_item = item.parentItem()
        elif item and item.parentItem() and isinstance(item.parentItem(), FlowNode):
            node_item = item.parentItem()
        
        if node_item:
            # 如果点击的是节点或者节点上的组件，弹出节点菜单
            # 添加节点相关的菜单项
            delete_action = menu.addAction("删除节点")
            rename_action = menu.addAction("重命名")
            
            # 显示菜单并获取用户选择
            # 使用globalPos
            if hasattr(event, 'globalPos'):
                pos = event.globalPos()
            else:
                # 如果是QGraphicsSceneContextMenuEvent
                pos = event.screenPos()
                
            action = menu.exec_(pos)
            
            # 处理用户选择
            if action == delete_action:
                # 删除节点及其连接
                # 先删除所有连接
                ports = node_item.input_ports + node_item.output_ports
                for port in ports:
                    for edge in list(port.edges):
                        if edge.id in self.edges:
                            del self.edges[edge.id]
                        self.removeItem(edge)
                
                # 再删除节点
                if node_item.id in self.nodes:
                    del self.nodes[node_item.id]
                self.removeItem(node_item)
                
                # 发送信号通知节点已删除
                self.node_deleted.emit(node_item)
                
                event.accept()
                return
            elif action == rename_action:
                # 重命名功能可以后续实现
                pass
        else:
            # 如果点击的是空白区域，弹出创建节点菜单
            create_node_action = menu.addAction("创建节点")
            
            # 显示菜单并获取用户选择
            if hasattr(event, 'globalPos'):
                pos = event.globalPos()
            else:
                # 如果是QGraphicsSceneContextMenuEvent
                pos = event.screenPos()
                
            action = menu.exec_(pos)
            
            # 处理用户选择
            if action == create_node_action:
                self.create_node_at(scene_pos)
                event.accept()
                return
    
    def create_node_at(self, pos, title="新节点"):
        """在指定位置创建节点"""
        # 创建节点
        node = FlowNode(title)
        
        # 设置节点位置
        node.setPos(pos)
        
        # 添加到场景
        self.addItem(node)
        
        # 保存节点并发出信号
        self.nodes[node.id] = node
        self.node_created.emit(node)
        
        return node
    
    def create_task_node(self, pos, area, task_name):
        """创建任务节点"""
        node = self.create_node_at(pos, task_name)
        node.set_task(area, task_name)
        return node
    
    def clear(self):
        """清空场景"""
        # 清除所有项
        super().clear()
        
        # 重置集合
        self.nodes = {}
        self.edges = {}
        
        # 重置状态
        self.temp_edge = None
        self.connection_port = None
    
    def get_execution_sequence(self):
        """获取执行序列"""
        # 首先查找开始节点
        start_node = None
        for node in self.nodes.values():
            if node.is_start_node:
                start_node = node
                break
        
        # 如果没有指定开始节点，则尝试找到没有输入连接的节点作为开始节点
        if not start_node:
            for node in self.nodes.values():
                # 检查是否有输入连接
                has_input = False
                for port in node.input_ports:
                    if port.edges:
                        has_input = True
                        break
                
                if not has_input:
                    start_node = node
                    break
        
        # 如果仍然没有找到开始节点，返回空列表
        if not start_node:
            return []
        
        # 从开始节点开始，按照连接顺序构建执行序列
        visited = set()
        execution_sequence = []
        
        def visit_node(node):
            if node.id in visited:
                return
            
            visited.add(node.id)
            
            # 添加当前节点的任务
            if node.area and node.task:
                execution_sequence.append({
                    "area": node.area,
                    "task": node.task
                })
            
            # 遍历所有输出端口，找到连接的下一个节点
            for port in node.output_ports:
                for edge in port.edges:
                    if edge.target_port and edge.target_port.parent_node:
                        visit_node(edge.target_port.parent_node)
        
        # 从开始节点开始遍历
        visit_node(start_node)
        
        return execution_sequence
    
    def serialize(self):
        """序列化场景数据"""
        # 序列化所有节点
        nodes_data = []
        for node in self.nodes.values():
            nodes_data.append(node.serialize())
        
        # 序列化所有边
        edges_data = []
        for edge in self.edges.values():
            edge_data = edge.serialize()
            if edge_data:
                edges_data.append(edge_data)
        
        # 返回完整的场景数据
        return {
            "nodes": nodes_data,
            "edges": edges_data
        }
    
    def deserialize(self, data):
        """从序列化数据恢复场景"""
        # 清空当前场景
        self.clear()
        
        # 重建所有节点
        nodes_map = {}  # 映射ID到新节点
        
        for node_data in data.get("nodes", []):
            # 创建节点
            node = FlowNode()
            node.deserialize(node_data)
            
            # 添加到场景
            self.addItem(node)
            self.nodes[node.id] = node
            nodes_map[node.id] = node
        
        # 重建所有边
        for edge_data in data.get("edges", []):
            # 获取源节点和端口
            source_node_id = edge_data.get("source_node_id")
            source_port_index = edge_data.get("source_port_index", 0)
            
            # 获取目标节点和端口
            target_node_id = edge_data.get("target_node_id")
            target_port_index = edge_data.get("target_port_index", 0)
            
            # 检查节点是否存在
            if (source_node_id in nodes_map and 
                target_node_id in nodes_map):
                
                source_node = nodes_map[source_node_id]
                target_node = nodes_map[target_node_id]
                
                # 检查端口索引是否有效
                if (0 <= source_port_index < len(source_node.output_ports) and
                    0 <= target_port_index < len(target_node.input_ports)):
                    
                    source_port = source_node.output_ports[source_port_index]
                    target_port = target_node.input_ports[target_port_index]
                    
                    # 创建边
                    edge = FlowEdge(source_port, target_port)
                    self.addItem(edge)
                    self.edges[edge.id] = edge
    
    def dragEnterEvent(self, event):
        """处理拖拽进入事件"""
        # 检查是否包含任务数据
        if event.mimeData().hasFormat("application/x-task-area") and event.mimeData().hasFormat("application/x-task-name"):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)
    
    def dropEvent(self, event):
        """处理拖拽放置事件"""
        # 检查是否包含任务数据
        if event.mimeData().hasFormat("application/x-task-area") and event.mimeData().hasFormat("application/x-task-name"):
            # 获取任务信息
            area = event.mimeData().data("application/x-task-area").data().decode()
            task_name = event.mimeData().data("application/x-task-name").data().decode()
            
            # 在放置位置创建任务节点
            self.create_task_node(event.scenePos(), area, task_name)
            
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
