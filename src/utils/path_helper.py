import os
import sys
from src.utils.constants import ASSETS_DIR

def get_asset_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和打包环境"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时目录
        return os.path.join(sys._MEIPASS, 'assets', relative_path)
    return os.path.join(ASSETS_DIR, relative_path)