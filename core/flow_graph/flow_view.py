from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QMouseEvent


class FlowView(QGraphicsView):
    """
    流程图视图：负责处理用户的交互和视图的显示
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置视图属性
        self.setRenderHint(QPainter.RenderHint.Antialiasing)  # 抗锯齿
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)  # 文字抗锯齿
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)  # 平滑像素变换
        
        # 设置拖拽模式
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        # 允许鼠标跟踪
        self.setMouseTracking(True)
        
        # 设置视口更新模式
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        
        # 设置背景颜色为白色
        self.setBackgroundBrush(Qt.GlobalColor.white)
        
        # 初始化缩放级别
        self.zoom_level = 1.0
        
        # 设置视图缩放范围
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # 保存当前平移开始位置
        self.last_pan_point = QPointF()
        self.panning = False
    
    def wheelEvent(self, event):
        """
        处理鼠标滚轮事件，用于缩放视图
        """
        # 调整缩放步长
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        
        # 获取当前缩放
        old_pos = self.mapToScene(event.position().toPoint())
        
        # 根据滚轮方向放大或缩小
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        
        # 限制缩放范围
        new_zoom = self.zoom_level * zoom_factor
        if 0.2 <= new_zoom <= 5.0:
            self.zoom_level = new_zoom
            self.scale(zoom_factor, zoom_factor)
            
            # 调整视图位置，确保滚轮下的点不移动
            new_pos = self.mapToScene(event.position().toPoint())
            delta = new_pos - old_pos
            self.translate(delta.x(), delta.y())
        
        event.accept()
    
    def mousePressEvent(self, event):
        """
        处理鼠标按下事件
        """
        # 检查是否为中键或右键+Alt
        if event.button() == Qt.MouseButton.MiddleButton or (event.button() == Qt.MouseButton.RightButton and event.modifiers() & Qt.KeyboardModifier.AltModifier):
            # 开始平移操作
            self.panning = True
            self.last_pan_point = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """
        处理鼠标移动事件
        """
        # 如果正在平移，处理平移逻辑
        if self.panning:
            delta = event.position() - self.last_pan_point
            self.last_pan_point = event.position()
            
            # 执行平移
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """
        处理鼠标释放事件
        """
        # 结束平移操作
        if self.panning:
            self.panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        
        super().mouseReleaseEvent(event)
    
    def keyPressEvent(self, event):
        """
        处理键盘按键事件
        """
        # 按空格键切换拖拽模式
        if event.key() == Qt.Key.Key_Space:
            if self.dragMode() == QGraphicsView.DragMode.RubberBandDrag:
                self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            else:
                self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            event.accept()
            return
        
        # 删除选中项
        if event.key() == Qt.Key.Key_Delete and self.scene():
            # 获取所有选中的项并删除它们
            selected_items = [item for item in self.scene().items() if item.isSelected()]
            for item in selected_items:
                self.scene().removeItem(item)
            event.accept()
            return
        
        super().keyPressEvent(event)
    
    def contextMenuEvent(self, event):
        """
        处理右键菜单事件
        """
        # 如果场景存在，则通知场景处理右键菜单
        if self.scene():
            # 直接将事件传递给场景
            self.scene().contextMenuEvent(event)
        else:
            super().contextMenuEvent(event)
