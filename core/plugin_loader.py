"""
统一插件加载模块

消除 memory_workbench.py 和 file_slot.py 中重复的插件加载逻辑。
"""
import os
import sys
import logging
import traceback
import importlib.util
from core.paths import EXTENSIONS_DIR

logger = logging.getLogger(__name__)


def load_plugins(plugin_dir=None):
    """
    从指定目录加载所有插件。
    
    Args:
        plugin_dir: 插件目录路径，默认为 EXTENSIONS_DIR
    
    Returns:
        dict: 按分类组织的插件字典
              {category: {title: {"module": module, "info": plugin_info, "file_path": path}}}
    """
    if plugin_dir is None:
        plugin_dir = str(EXTENSIONS_DIR)
    
    plugins = {}
    
    if not os.path.exists(plugin_dir):
        logger.warning(f"插件目录不存在: {plugin_dir}")
        return plugins
    
    for root, dirs, files in os.walk(plugin_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                _load_single_plugin(file_path, plugins)
    
    logger.info(f"已加载 {sum(len(v) for v in plugins.values())} 个插件，分 {len(plugins)} 个类别")
    return plugins


def _load_single_plugin(file_path, plugins):
    """
    加载单个插件文件。
    
    Args:
        file_path: 插件文件路径
        plugins: 插件字典（会原地修改）
    """
    try:
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            logger.warning(f"无法创建模块 spec: {file_path}")
            return
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        if hasattr(module, "plugin_info"):
            info = module.plugin_info
            category = info.get("category", "其他")
            title = info.get("title", module_name)
            
            if category not in plugins:
                plugins[category] = {}
            
            plugins[category][title] = {
                "module": module,
                "info": info,
                "file_path": file_path
            }
            logger.debug(f"成功加载插件: {title} [{category}]")
        else:
            logger.debug(f"跳过无 plugin_info 的文件: {file_path}")
            
    except Exception as e:
        logger.error(f"加载插件 {file_path} 时出错: {e}")
        logger.debug(traceback.format_exc())


def execute_plugin(file_path, plugin_data):
    """
    执行插件。
    
    Args:
        file_path: 要处理的文件路径
        plugin_data: 插件数据字典
    
    Raises:
        ValueError: 如果插件缺少 run 函数
        Exception: 插件执行中的其他错误
    """
    # 确定插件文件路径
    if isinstance(plugin_data, dict) and "file_path" in plugin_data:
        plugin_file_path = plugin_data["file_path"]
    elif isinstance(plugin_data, dict) and "module" in plugin_data:
        plugin_file_path = plugin_data["module"].__file__
    else:
        plugin_file_path = plugin_data.__file__
    
    # 确定模块名称
    if isinstance(plugin_data, dict) and "module" in plugin_data:
        module_name = plugin_data["module"].__name__
    else:
        module_name = plugin_data.__name__
    
    logger.debug(f"执行插件: {module_name}, 文件: {file_path}")
    
    # 重新加载模块（确保使用最新代码）
    spec = importlib.util.spec_from_file_location(module_name, plugin_file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    
    # 执行插件的 run 函数
    if hasattr(module, "run"):
        module.run(file_path)
    else:
        raise ValueError(f"插件 {module_name} 缺少 run 函数")
    
    title = "未知插件"
    if isinstance(plugin_data, dict) and "info" in plugin_data:
        title = plugin_data["info"].get("title", module_name)
    
    logger.info(f"成功执行插件: {title}")
