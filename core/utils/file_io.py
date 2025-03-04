import json
import os

def save_flow(filename, flow_scene):
    """
    保存流程图到文件
    
    Args:
        filename (str): 文件路径
        flow_scene (FlowScene): 流程图场景对象
    """
    # 创建目录（如果不存在）
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # 获取流程图数据
    flow_data = flow_scene.serialize()
    
    # 保存到文件
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(flow_data, f, ensure_ascii=False, indent=2)


def load_flow(filename, flow_scene):
    """
    从文件加载流程图
    
    Args:
        filename (str): 文件路径
        flow_scene (FlowScene): 流程图场景对象
    """
    # 检查文件是否存在
    if not os.path.exists(filename):
        raise FileNotFoundError(f"文件不存在: {filename}")
    
    # 从文件读取数据
    with open(filename, 'r', encoding='utf-8') as f:
        flow_data = json.load(f)
    
    # 重建流程图
    flow_scene.deserialize(flow_data)
