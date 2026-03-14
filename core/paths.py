"""
统一路径管理模块

所有路径基于 APP_ROOT 构建，消除对 os.getcwd() 的依赖。
"""
import os
from pathlib import Path

# 项目根目录 = core/ 的上级目录
APP_ROOT = Path(__file__).resolve().parent.parent

# 常用目录
CONFIG_DIR = APP_ROOT / "config"
DB_DIR = APP_ROOT / "db"
OUTPUT_DIR = APP_ROOT / "output"
PACKED_DIR = APP_ROOT / "packed_files"
RES_DIR = APP_ROOT / "res"
PLUGIN_DIR = APP_ROOT / "plugin"
EXTENSIONS_DIR = APP_ROOT / "extensions"
LOGS_DIR = APP_ROOT / "logs"

# 常用配置文件
BASE_CONFIG_FILE = CONFIG_DIR / "base_config.yaml"
USER_SETTINGS_FILE = CONFIG_DIR / "user_settings.json"
STYLE_CONFIG_FILE = CONFIG_DIR / "style.json"
HIGHLIGHT_BUTTONS_FILE = CONFIG_DIR / "highlight_buttons.json"
TOPIC_KEYWORDS_FILE = CONFIG_DIR / "topic_analysis_keywords.yaml"
TOPIC_PROMPT_FILE = CONFIG_DIR / "topic_analysis_prompt.txt"

# 数据库文件
PRESETS_DB = DB_DIR / "presets.db"
FAVORITES_DB = DB_DIR / "favorites.db"
DEFAULT_REGEX_DB = DB_DIR / "default_regex.db"
USER_REGEX_DB = DB_DIR / "user_regex.db"

# 资源文件
LOGO_ICO = RES_DIR / "logo.ico"
LOGO_64 = RES_DIR / "logo_64.png"
LOGO_200 = RES_DIR / "logo_200.png"


def ensure_directories():
    """确保所有必要的目录存在"""
    for directory in [CONFIG_DIR, DB_DIR, OUTPUT_DIR, PACKED_DIR, LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
