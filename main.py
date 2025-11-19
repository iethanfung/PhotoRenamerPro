import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QIcon  # 引入 QIcon
from src.ui.main_window import MainWindow
from src.utils.logger import setup_logger
from src.core.config_manager import ConfigManager
from src.utils.constants import ASSETS_DIR  # 引入资源路径常量


def main():
    # 1. 初始化日志
    setup_logger()

    # 2. 确保配置存在
    ConfigManager.ensure_defaults()

    # 3. 启动应用
    app = QApplication(sys.argv)
    app.setApplicationName("Photo Renamer Pro")

    # 🔥🔥🔥 修复点：加载图标 🔥🔥🔥
    icon_name = "app_icon.icns" if sys.platform == "darwin" else "app_icon.ico"
    icon_path = os.path.join(ASSETS_DIR, 'icons', icon_name)

    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
        # Mac 上的 Dock 图标通常由打包工具处理，但运行时设置这个也没坏处
    else:
        print(f"Warning: Icon not found at {icon_path}")

    # 设置全局字体
    font = QFont("SF Pro Text", 10)
    font.setStyleHint(QFont.System)
    if sys.platform == "win32":
        font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()