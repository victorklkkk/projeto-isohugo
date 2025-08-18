# cogs/utils/config_manager.py
import json
import os
import logging

logger = logging.getLogger(__name__)
CONFIG_FILE = "verification_config.json"

def load_config():
    """Carrega as configurações do arquivo JSON"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(config):
    """Salva as configurações no arquivo JSON"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def get_server_config(guild_id: int):
    """Obtém a configuração de um servidor específico"""
    config = load_config()
    return config.get(str(guild_id), {})

def save_server_config(guild_id: int, server_config: dict):
    """Salva a configuração de um servidor específico"""
    config = load_config()
    config[str(guild_id)] = server_config
    save_config(config)