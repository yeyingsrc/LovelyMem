from openai import AsyncOpenAI

import json
import os

CONFIG_FILE = "AItools/config.json"

# 默认配置
DEFAULT_CONFIG = {
    "api_key": "",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-chat"
}

def load_config():
    """加载配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

def save_config(config):
    """保存配置"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

# 加载配置
config = load_config()

# 初始化客户端
client = AsyncOpenAI(
    api_key=config["api_key"],
    base_url=config["base_url"],
)
