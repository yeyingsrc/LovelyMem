import json
import os
import yaml

BASE_CONFIG_FILE = 'config/base_config.yaml'
USER_CONFIG_FILE = 'config/user_settings.json'

def load_base_config():
    if os.path.exists(BASE_CONFIG_FILE):
        with open(BASE_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}

def load_user_config():
    if os.path.exists(USER_CONFIG_FILE):
        with open(USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def deep_update(d, u):
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = deep_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def load_config():
    base_config = load_base_config()
    user_config = load_user_config()
    # 深度合并配置，用户配置优先级更高
    return deep_update(base_config, user_config)

def save_config(config):
    # 加载现有的用户配置
    existing_user_config = load_user_config()
    # 深度更新现有配置
    updated_config = deep_update(existing_user_config, config)
    # 保存更新后的配置
    with open(USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(updated_config, f, ensure_ascii=False, indent=4)

def save_theme(theme_name):
    config = load_user_config()
    config['theme'] = theme_name
    save_config({'theme': theme_name})

def get_saved_theme():
    config = load_config()
    return config.get('theme', '默认')  # 如果没有保存的主题，返回默认主题
