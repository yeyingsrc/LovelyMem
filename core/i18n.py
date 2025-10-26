"""
国际化(i18n)模块
提供多语言支持功能
"""
import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class I18n:
    """国际化管理类"""
    
    def __init__(self):
        self.current_language = "zh_CN"  # 默认语言
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.locales_dir = os.path.join(os.getcwd(), "config", "locales")
        self.fallback_language = "zh_CN"  # 回退语言

        # 确保 locales 目录存在
        os.makedirs(self.locales_dir, exist_ok=True)

        # 加载当前语言
        self._load_language_from_settings()

        # 加载翻译文件
        self.load_language(self.current_language)

        # 如果当前语言不是回退语言，也加载回退语言
        if self.current_language != self.fallback_language:
            self.load_language(self.fallback_language)
        
    def _load_language_from_settings(self):
        """从用户设置中加载语言配置"""
        try:
            settings_file = os.path.join(os.getcwd(), "config", "user_settings.json")
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.current_language = settings.get("language", "zh_CN")
        except Exception as e:
            logger.warning(f"加载语言设置失败: {e}")
            self.current_language = "zh_CN"
    
    def load_language(self, language_code: str) -> bool:
        """
        加载指定语言的翻译文件
        
        Args:
            language_code: 语言代码，如 'zh_CN', 'en_US'
            
        Returns:
            bool: 加载是否成功
        """
        try:
            locale_file = os.path.join(self.locales_dir, f"{language_code}.json")
            
            if not os.path.exists(locale_file):
                logger.warning(f"语言文件不存在: {locale_file}")
                return False
            
            with open(locale_file, 'r', encoding='utf-8') as f:
                self.translations[language_code] = json.load(f)
            
            logger.info(f"成功加载语言: {language_code}")
            return True
            
        except Exception as e:
            logger.error(f"加载语言文件失败 {language_code}: {e}")
            return False
    
    def set_language(self, language_code: str) -> bool:
        """
        设置当前语言
        
        Args:
            language_code: 语言代码
            
        Returns:
            bool: 设置是否成功
        """
        # 如果语言未加载，先加载
        if language_code not in self.translations:
            if not self.load_language(language_code):
                return False
        
        # 同时加载回退语言
        if self.fallback_language not in self.translations:
            self.load_language(self.fallback_language)
        
        self.current_language = language_code
        
        # 保存到用户设置
        self._save_language_to_settings(language_code)
        
        return True
    
    def _save_language_to_settings(self, language_code: str):
        """保存语言设置到用户配置文件"""
        try:
            settings_file = os.path.join(os.getcwd(), "config", "user_settings.json")
            
            # 读取现有设置
            settings = {}
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            # 更新语言设置
            settings["language"] = language_code
            
            # 保存设置
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
                
        except Exception as e:
            logger.error(f"保存语言设置失败: {e}")
    
    def get(self, key: str, **kwargs) -> str:
        """
        获取翻译文本
        
        Args:
            key: 翻译键，支持点号分隔的嵌套键，如 'menu.file.open'
            **kwargs: 用于格式化字符串的参数
            
        Returns:
            str: 翻译后的文本，如果找不到则返回键本身
        """
        # 尝试从当前语言获取翻译
        translation = self._get_nested_value(
            self.translations.get(self.current_language, {}), 
            key
        )
        
        # 如果当前语言没有，尝试从回退语言获取
        if translation is None and self.current_language != self.fallback_language:
            translation = self._get_nested_value(
                self.translations.get(self.fallback_language, {}), 
                key
            )
        
        # 如果还是没有，返回键本身
        if translation is None:
            logger.debug(f"翻译键未找到: {key}")
            translation = key
        
        # 如果有参数，进行格式化
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except Exception as e:
                logger.warning(f"翻译文本格式化失败 {key}: {e}")
        
        return translation
    
    def _get_nested_value(self, data: Dict, key: str) -> Optional[str]:
        """
        从嵌套字典中获取值
        
        Args:
            data: 字典数据
            key: 点号分隔的键，如 'menu.file.open'
            
        Returns:
            Optional[str]: 找到的值，如果不存在返回 None
        """
        keys = key.split('.')
        value = data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        
        return value if isinstance(value, str) else None
    
    def get_available_languages(self) -> Dict[str, str]:
        """
        获取所有可用的语言
        
        Returns:
            Dict[str, str]: 语言代码到语言名称的映射
        """
        languages = {}
        
        try:
            if os.path.exists(self.locales_dir):
                for filename in os.listdir(self.locales_dir):
                    if filename.endswith('.json'):
                        lang_code = filename[:-5]  # 移除 .json 后缀
                        
                        # 尝试从翻译文件中获取语言名称
                        if lang_code not in self.translations:
                            self.load_language(lang_code)
                        
                        lang_name = self._get_nested_value(
                            self.translations.get(lang_code, {}),
                            "_meta.language_name"
                        )
                        
                        if lang_name:
                            languages[lang_code] = lang_name
                        else:
                            languages[lang_code] = lang_code
                            
        except Exception as e:
            logger.error(f"获取可用语言列表失败: {e}")
        
        return languages
    
    def get_current_language(self) -> str:
        """获取当前语言代码"""
        return self.current_language


# 创建全局实例
_i18n_instance = None


def get_i18n() -> I18n:
    """获取 i18n 实例（单例模式）"""
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18n()
    return _i18n_instance


def t(key: str, **kwargs) -> str:
    """
    翻译函数的快捷方式
    
    Args:
        key: 翻译键
        **kwargs: 格式化参数
        
    Returns:
        str: 翻译后的文本
    """
    return get_i18n().get(key, **kwargs)


def set_language(language_code: str) -> bool:
    """
    设置当前语言的快捷方式
    
    Args:
        language_code: 语言代码
        
    Returns:
        bool: 设置是否成功
    """
    return get_i18n().set_language(language_code)


def get_available_languages() -> Dict[str, str]:
    """获取可用语言列表的快捷方式"""
    return get_i18n().get_available_languages()


def get_current_language() -> str:
    """获取当前语言的快捷方式"""
    return get_i18n().get_current_language()

