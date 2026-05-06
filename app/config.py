import os
import json
import logging
from filelock import FileLock

logger = logging.getLogger("UniversalAdapter")

CONFIG_DIR = "data"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
LOCK_FILE = os.path.join(CONFIG_DIR, "config.lock")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change_me_in_prod").strip()

DEFAULT_CONFIG = {
    "drivers": {
        "suchuang_async": {
            "name": "速创API (异步轮询)",
            "models": ["gpt-image-2", "nanobanana2"],
            "submit_urls": {
                "gpt-image-2": "https://api.wuyinkeji.com/api/async/image_gpt",
                "nanobanana2": "https://api.wuyinkeji.com/api/async/image_nanoBanana2"
            },
            "poll_url": "https://api.wuyinkeji.com/api/async/detail",
            "polling_interval": 3,
            "timeout": 120,
            "model_params": {
                "gpt-image-2": {
                    "size_mapping": {"1024x1024": "1:1", "1024x1792": "9:16", "default": "16:9"},
                    "size_field": "size",
                    "fixed_params": {},
                    "urls_format": "array"
                },
                "nanobanana2": {
                    "size_mapping": {"1024x1024": "1:1", "1024x1792": "9:16", "default": "16:9"},
                    "size_field": "aspectRatio",
                    "fixed_params": {"size": "1K"},
                    "urls_format": "string"
                }
            }
        }
    }
}

global_config_cache = None

def load_config():
    global global_config_cache
    if global_config_cache is not None:
        return global_config_cache

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                global_config_cache = json.load(f)
                return global_config_cache
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            
    global_config_cache = DEFAULT_CONFIG
    return global_config_cache

def save_config(config):
    global global_config_cache
    os.makedirs(CONFIG_DIR, exist_ok=True)
    lock = FileLock(LOCK_FILE, timeout=5)
    with lock:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    global_config_cache = config
