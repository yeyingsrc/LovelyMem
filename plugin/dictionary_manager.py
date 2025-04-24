import os
import json
import logging
from pathlib import Path
import fnmatch

logger = logging.getLogger(__name__)

class DictionaryItem:
    """字典项类，表示字典中的一个条目"""
    def __init__(self, name="", content="", description="", tags=None, type_name="通用", file_pattern="", is_exact_match=False):
        """
        初始化字典条目
        
        参数:
            name (str): 条目名称
            content (str): 条目内容
            description (str): 条目描述
            tags (list): 条目标签
            type_name (str): 条目类型名称
            file_pattern (str): 文件名匹配模式，支持通配符，如 "*.exe" 或 "config*"
            is_exact_match (bool): 是否为精确匹配，如设为True，则只匹配完整的词或数值
        """
        self.name = name                  # 条目名称
        self.content = content            # 条目内容
        self.description = description    # 条目描述
        self.tags = tags or []            # 标签列表
        self.type_name = type_name        # 类型名称（例如：命令行，正则表达式，通用等）
        self.file_pattern = file_pattern  # 文件名匹配模式
        self.is_exact_match = is_exact_match  # 是否精确匹配

    def to_dict(self):
        """将对象转换为字典，用于JSON序列化"""
        return {
            "name": self.name,
            "content": self.content,
            "description": self.description,
            "tags": self.tags,
            "type_name": self.type_name,
            "file_pattern": self.file_pattern,  # 保存文件名匹配模式
            "is_exact_match": self.is_exact_match  # 保存精确匹配设置
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建对象，用于从JSON反序列化"""
        return cls(
            name=data.get("name", ""),
            content=data.get("content", ""),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            type_name=data.get("type_name", "通用"),
            file_pattern=data.get("file_pattern", ""),  # 读取文件名匹配模式
            is_exact_match=data.get("is_exact_match", False)  # 读取精确匹配设置
        )

    def match_file(self, file_name):
        """
        检查文件名是否匹配该条目的文件模式
        
        参数:
            file_name (str): 要检查的文件名
            
        返回:
            bool: 如果文件名匹配或无模式限制则返回True，否则返回False
        """
        # 如果没有设置文件匹配模式，则对所有文件生效
        if not self.file_pattern:
            return True
            
        # 如果设置了多个模式（以英文逗号分隔），则只要匹配其中一个即可
        patterns = [p.strip() for p in self.file_pattern.split(',') if p.strip()]
        if not patterns:
            return True
            
        # 检查文件名是否匹配任一模式
        for pattern in patterns:
            if fnmatch.fnmatch(file_name, pattern):
                return True
                
        return False

class DictionaryManager:
    """字典管理器，负责字典的加载、保存和管理"""
    def __init__(self, dictionary_dir="db/dictionaries"):
        self.dictionary_dir = dictionary_dir
        self.dictionaries = {}  # 字典 {dictionary_name: {item_name: DictionaryItem}}
        self.ensure_directory_exists()
        self.load_all_dictionaries()
    
    def ensure_directory_exists(self):
        """确保字典目录存在"""
        os.makedirs(self.dictionary_dir, exist_ok=True)
    
    def get_dictionary_path(self, dictionary_name):
        """获取字典文件路径"""
        return os.path.join(self.dictionary_dir, f"{dictionary_name}.json")
    
    def load_dictionary(self, dictionary_name):
        """加载单个字典"""
        path = self.get_dictionary_path(dictionary_name)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                items = {}
                for item_data in data.get("items", []):
                    item = DictionaryItem.from_dict(item_data)
                    items[item.name] = item
                self.dictionaries[dictionary_name] = items
                logger.info(f"已加载字典: {dictionary_name}")
                return True
            except Exception as e:
                logger.error(f"加载字典 {dictionary_name} 时发生错误: {str(e)}")
                return False
        else:
            # 如果字典不存在，创建一个空字典
            self.dictionaries[dictionary_name] = {}
            logger.info(f"创建了新的空字典: {dictionary_name}")
            return True
    
    def load_all_dictionaries(self):
        """加载所有字典"""
        self.dictionaries.clear()
        if not os.path.exists(self.dictionary_dir):
            return
        
        for file in os.listdir(self.dictionary_dir):
            if file.endswith('.json'):
                dictionary_name = file[:-5]  # 移除 .json 后缀
                self.load_dictionary(dictionary_name)
    
    def save_dictionary(self, dictionary_name):
        """保存单个字典"""
        if dictionary_name not in self.dictionaries:
            logger.warning(f"尝试保存不存在的字典: {dictionary_name}")
            return False
        
        path = self.get_dictionary_path(dictionary_name)
        try:
            items = self.dictionaries[dictionary_name]
            data = {
                "name": dictionary_name,
                "items": [item.to_dict() for item in items.values()]
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f"已保存字典: {dictionary_name}")
            return True
        except Exception as e:
            logger.error(f"保存字典 {dictionary_name} 时发生错误: {str(e)}")
            return False
    
    def save_all_dictionaries(self):
        """保存所有字典"""
        for dictionary_name in self.dictionaries:
            self.save_dictionary(dictionary_name)
    
    def get_dictionary_names(self):
        """获取所有字典名称"""
        return list(self.dictionaries.keys())
    
    def create_dictionary(self, dictionary_name):
        """创建新字典"""
        if dictionary_name in self.dictionaries:
            logger.warning(f"字典已存在: {dictionary_name}")
            return False
        
        self.dictionaries[dictionary_name] = {}
        return self.save_dictionary(dictionary_name)
    
    def delete_dictionary(self, dictionary_name):
        """删除字典"""
        if dictionary_name not in self.dictionaries:
            logger.warning(f"尝试删除不存在的字典: {dictionary_name}")
            return False
        
        path = self.get_dictionary_path(dictionary_name)
        try:
            if os.path.exists(path):
                os.remove(path)
            del self.dictionaries[dictionary_name]
            logger.info(f"已删除字典: {dictionary_name}")
            return True
        except Exception as e:
            logger.error(f"删除字典 {dictionary_name} 时发生错误: {str(e)}")
            return False
    
    def add_item(self, dictionary_name, item):
        """向字典添加条目"""
        if dictionary_name not in self.dictionaries:
            logger.warning(f"尝试向不存在的字典添加条目: {dictionary_name}")
            return False
        
        self.dictionaries[dictionary_name][item.name] = item
        return self.save_dictionary(dictionary_name)
    
    def update_item(self, dictionary_name, old_name, item):
        """更新字典中的条目"""
        if dictionary_name not in self.dictionaries:
            logger.warning(f"尝试更新不存在的字典中的条目: {dictionary_name}")
            return False
        
        # 如果名称已更改，删除旧条目并添加新条目
        if old_name != item.name and old_name in self.dictionaries[dictionary_name]:
            del self.dictionaries[dictionary_name][old_name]
        
        self.dictionaries[dictionary_name][item.name] = item
        return self.save_dictionary(dictionary_name)
    
    def delete_item(self, dictionary_name, item_name):
        """从字典中删除条目"""
        if dictionary_name not in self.dictionaries:
            logger.warning(f"尝试从不存在的字典中删除条目: {dictionary_name}")
            return False
        
        if item_name not in self.dictionaries[dictionary_name]:
            logger.warning(f"尝试删除不存在的条目: {dictionary_name}/{item_name}")
            return False
        
        del self.dictionaries[dictionary_name][item_name]
        return self.save_dictionary(dictionary_name)
    
    def get_item(self, dictionary_name, item_name):
        """获取字典中的条目"""
        if dictionary_name not in self.dictionaries:
            logger.warning(f"尝试从不存在的字典中获取条目: {dictionary_name}")
            return None
        
        return self.dictionaries[dictionary_name].get(item_name)
    
    def get_items(self, dictionary_name):
        """获取字典中的所有条目"""
        if dictionary_name not in self.dictionaries:
            logger.warning(f"尝试从不存在的字典中获取所有条目: {dictionary_name}")
            return []
        
        return list(self.dictionaries[dictionary_name].values())
    
    def search_items(self, query, dictionary_name=None):
        """搜索字典中的条目
        
        参数:
            query (str): 搜索关键词
            dictionary_name (str, optional): 字典名称，如果为None则搜索所有字典
            
        返回:
            list: 匹配的条目列表，每个元素是 (dictionary_name, item) 元组
        """
        results = []
        query = query.lower()
        
        if dictionary_name:
            # 搜索指定字典
            if dictionary_name in self.dictionaries:
                for item in self.dictionaries[dictionary_name].values():
                    if (query in item.name.lower() or 
                        query in item.content.lower() or 
                        query in item.description.lower() or
                        any(query in tag.lower() for tag in item.tags)):
                        results.append((dictionary_name, item))
        else:
            # 搜索所有字典
            for dict_name, items in self.dictionaries.items():
                for item in items.values():
                    if (query in item.name.lower() or 
                        query in item.content.lower() or 
                        query in item.description.lower() or
                        any(query in tag.lower() for tag in item.tags)):
                        results.append((dict_name, item))
        
        return results
