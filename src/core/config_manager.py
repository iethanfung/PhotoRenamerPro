import json
import os
from src.utils.constants import CONFIG_DIR, DEFAULT_SETTINGS, DEFAULT_CP_MAP, DEFAULT_ISSUE_MAP
from loguru import logger


class ConfigManager:
    SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
    CP_MAP_FILE = os.path.join(CONFIG_DIR, "cp_map.json")
    ISSUE_MAP_FILE = os.path.join(CONFIG_DIR, "issue_map.json")
    # 🔥 新增：方向映射文件
    ORIENT_MAP_FILE = os.path.join(CONFIG_DIR, "orient_map.json")

    @classmethod
    def ensure_defaults(cls):
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)

        cls._create_if_missing(cls.SETTINGS_FILE, DEFAULT_SETTINGS)
        cls._create_if_missing(cls.CP_MAP_FILE, DEFAULT_CP_MAP)
        cls._create_if_missing(cls.ISSUE_MAP_FILE, DEFAULT_ISSUE_MAP)
        # orient_map 如果没有，可以先创建一个空的或默认的，防止报错
        cls._create_if_missing(cls.ORIENT_MAP_FILE, {})

    @staticmethod
    def _create_if_missing(path, content):
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_settings(cls):
        with open(cls.SETTINGS_FILE, 'r', encoding='utf-8') as f: return json.load(f)

    @classmethod
    def save_settings(cls, data):
        with open(cls.SETTINGS_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_cp_map(cls):
        with open(cls.CP_MAP_FILE, 'r', encoding='utf-8') as f: return json.load(f)

    @classmethod
    def save_cp_map(cls, data):
        with open(cls.CP_MAP_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_issue_map(cls):
        with open(cls.ISSUE_MAP_FILE, 'r', encoding='utf-8') as f: return json.load(f)

    @classmethod
    def save_issue_map(cls, data):
        with open(cls.ISSUE_MAP_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_orient_map(cls):
        if os.path.exists(cls.ORIENT_MAP_FILE):
            with open(cls.ORIENT_MAP_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        return {}  # 返回空字典兜底

    @classmethod
    def save_orient_map(cls, data):
        with open(cls.ORIENT_MAP_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2, ensure_ascii=False)