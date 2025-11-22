import os
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QStackedWidget,
    QPushButton, QListWidgetItem, QMessageBox, QWidget
)
from PySide6.QtCore import Qt, QSize
from src.core.config_manager import ConfigManager

# 导入拆分后的页面
from src.ui.settings_pages.general_page import GeneralPage
from src.ui.settings_pages.templates_page import TemplatesPage
from src.ui.settings_pages.mapping_page import MappingPage
from src.ui.settings_pages.libraries_page import LibrariesPage


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置 - Photo Renamer Pro")
        self.resize(1000, 750)
        self.setModal(True)

        # 1. 加载数据 (引用)
        self.current_settings = ConfigManager.load_settings()
        self.cp_map = ConfigManager.load_cp_map()
        self.issue_map = ConfigManager.load_issue_map()
        self.orient_map = ConfigManager.load_orient_map()

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)

        self.add_sidebar_item("⚙️  通用设置")
        self.add_sidebar_item("🏷️  命名模板")
        self.add_sidebar_item("🔀  CSV 映射")
        self.add_sidebar_item("📚  别名库管理")

        self.sidebar.currentRowChanged.connect(self.change_page)
        main_layout.addWidget(self.sidebar)

        # Content
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.pages = QStackedWidget()

        # 🔥 初始化各个页面 🔥
        self.general_page = GeneralPage(self.current_settings)
        self.templates_page = TemplatesPage(self.current_settings)
        self.mapping_page = MappingPage(self.current_settings)
        self.libraries_page = LibrariesPage(self.cp_map, self.issue_map, self.orient_map)

        self.pages.addWidget(self.general_page)
        self.pages.addWidget(self.templates_page)
        self.pages.addWidget(self.mapping_page)
        self.pages.addWidget(self.libraries_page)

        content_layout.addWidget(self.pages)

        # Buttons
        btn_bar = QHBoxLayout()
        btn_bar.setContentsMargins(20, 10, 20, 20)
        btn_bar.addStretch()
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setFixedWidth(100)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("保存全部配置")
        self.btn_save.setObjectName("PrimaryButton")
        self.btn_save.setFixedWidth(150)
        self.btn_save.clicked.connect(self.save_all_settings)

        btn_bar.addWidget(self.btn_cancel)
        btn_bar.addWidget(self.btn_save)

        content_layout.addLayout(btn_bar)
        main_layout.addWidget(content_container)

        self.sidebar.setCurrentRow(0)
        self.apply_styles()

    def add_sidebar_item(self, text):
        item = QListWidgetItem(text)
        item.setSizeHint(QSize(0, 50))
        self.sidebar.addItem(item)

    def change_page(self, index):
        self.pages.setCurrentIndex(index)
        # 🔥 联动：当切到模板页时，从 Mapping 页获取最新 Key 刷新胶囊 🔥
        if index == 1:
            # 1. 获取 CSV 映射的 Key
            csv_keys = self.mapping_page.get_current_keys()
            # 2. 获取 解析变量的 Key (如 "哈哈")
            parsed_keys = self.mapping_page.get_parsed_vars()
            # 3. 获取 sys_id 映射
            sys_id_map = self.mapping_page.get_sys_id_map()

            # 4. 刷新模板页的胶囊按钮
            self.templates_page.refresh_chips(csv_keys, parsed_keys, sys_id_map)

    def save_all_settings(self):
        # 1. 通知各个页面把界面数据写回 self.current_settings
        self.general_page.save_data()
        self.templates_page.save_data()
        self.mapping_page.save_data()
        # libraries_page 保存逻辑可能不同，这里假设它实时保存或不需要显式调用 save_data

        # 2. 保存文件
        ConfigManager.save_settings(self.current_settings)
        ConfigManager.save_cp_map(self.cp_map)
        ConfigManager.save_issue_map(self.issue_map)
        ConfigManager.save_orient_map(self.orient_map)

        QMessageBox.information(self, "成功", "所有配置已成功保存！")
        self.accept()

    def apply_styles(self):
        self.setStyleSheet("""
                    /* 全局设置 */
                    QDialog { 
                        background-color: #FFFFFF; 
                    }

                    /* 侧边栏：通透、现代 */
                    QListWidget#Sidebar {
                        background-color: #F2F2F7; /* macOS 侧边栏底色 */
                        border: none;
                        outline: none;
                        padding-top: 20px;
                        padding-left: 10px;
                        padding-right: 10px;
                    }
                    QListWidget::item {
                        color: #333333;
                        border-radius: 8px;
                        margin-bottom: 5px;
                        padding: 8px 10px;
                        font-size: 13px;
                        font-weight: 500;
                        height: 36px;
                    }
                    QListWidget::item:selected {
                        background-color: #FFFFFF; /* 选中项变白，这是现代设计趋势 */
                        color: #000000;
                        border: 1px solid #E5E5E5;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                    }
                    QListWidget::item:hover:!selected {
                        background-color: #EAEAEA;
                    }

                    /* 标题文字 */
                    QLabel#H3 {
                        font-size: 15px;
                        font-weight: 700;
                        color: #1D1D1F;
                        margin-bottom: 5px;
                    }
                    QLabel#DescLabel {
                        color: #86868B;
                        font-size: 12px;
                        margin-bottom: 10px;
                    }

                    /* 输入框：圆润、微边框 */
                    QLineEdit#InputBox {
                        border: 1px solid #D1D1D6;
                        border-radius: 8px;
                        padding: 8px 12px; /* 更大的内边距 */
                        font-size: 13px;
                        background-color: #FFFFFF;
                        selection-background-color: #007AFF;
                    }
                    QLineEdit#InputBox:focus {
                        border: 1px solid #007AFF;
                        background-color: #FFFFFF;
                    }
                    QLineEdit#InputBox:hover {
                        background-color: #FAFAFA;
                    }

                    /* 按钮系统 */
                    /* 主按钮 (Primary) - 蓝色 */
                    QPushButton#PrimaryButton {
                        background-color: #007AFF;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 8px 20px;
                        font-weight: 600;
                        font-size: 13px;
                    }
                    QPushButton#PrimaryButton:hover {
                        background-color: #0062CC;
                    }
                    QPushButton#PrimaryButton:pressed {
                        background-color: #0051A8;
                    }

                    /* 次级按钮 (Secondary) - 浅灰 */
                    QPushButton#SecondaryButton {
                        background-color: #F2F2F7;
                        color: #007AFF;
                        border: none;
                        border-radius: 8px;
                        padding: 6px 15px;
                        font-weight: 600;
                    }
                    QPushButton#SecondaryButton:hover {
                        background-color: #E5E5EA;
                    }

                    /* 普通按钮 */
                    QPushButton {
                        background-color: #FFFFFF;
                        border: 1px solid #D1D1D6;
                        border-radius: 8px;
                        color: #333;
                        padding: 6px 15px;
                    }
                    QPushButton:hover {
                        background-color: #F9F9F9;
                        border-color: #C7C7CC;
                    }

                    /* 删除按钮 (垃圾桶) */
                    QToolButton#DeleteButton {
                        background-color: transparent;
                        border: none;
                        border-radius: 6px;
                        font-size: 14px;
                    }
                    QToolButton#DeleteButton:hover {
                        background-color: #FFF1F0; /* 浅红背景 */
                        border: 1px solid #FFCCC7;
                    }

                    /* 胶囊标签 (Tags) */
                    QPushButton#TagChip {
                        background-color: #EBF3FF;
                        color: #007AFF;
                        border: none;
                        border-radius: 14px; /* 更圆 */
                        padding: 5px 12px;
                        font-weight: 600;
                        font-size: 12px;
                    }
                    QPushButton#TagChip:hover {
                        background-color: #DCE9FF;
                    }

                    /* 预览区域 */
                    QFrame#PreviewBox {
                        background-color: #F5F5F7;
                        border: none;
                        border-radius: 10px;
                        padding: 20px;
                    }

                    /* 分割线 */
                    QFrame#Separator {
                        background-color: #F0F0F0;
                        max-height: 1px;
                    }

                    /* 滚动条 (尝试美化) */
                    QScrollBar:vertical {
                        border: none;
                        background: transparent;
                        width: 8px;
                        margin: 0px;
                    }
                    QScrollBar::handle:vertical {
                        background: #C1C1C1;
                        min-height: 20px;
                        border-radius: 4px;
                    }
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                        height: 0px;
                    }
                """)