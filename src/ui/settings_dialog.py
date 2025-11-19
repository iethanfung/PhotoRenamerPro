import os
import sys
from PySide6.QtWidgets import (
    QDialog, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QStackedWidget,
    QPushButton, QLabel, QLineEdit, QFrame, QGridLayout, QTabWidget, QScrollArea,
    QListWidgetItem, QApplication
)
from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtGui import QDesktopServices
from src.core.config_manager import ConfigManager


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings - Photo Renamer Pro")
        self.resize(900, 650)
        self.setModal(True)

        self.current_settings = ConfigManager.load_settings()

        # 存储控件引用
        self.widgets = {
            'excel_map': {},
            'reg_template': {},  # 存 Regular 的 input 和 label
            'issue_template': {},  # 存 Issue 的 input 和 label
            'parsed_map': {}
        }

        # 模拟数据用于预览
        self.mock_data = {
            "Build": "P1", "Config": "R1", "Rel_No": "0065",
            "SN": "SN123456", "Mode": "Stow", "WF": "2",
            "Test": "1mG"
        }

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)

        self.add_sidebar_item("⚙️  通用设置", 0)
        self.add_sidebar_item("🏷️  命名模板", 1)
        self.add_sidebar_item("🔀  数据映射", 2)
        self.add_sidebar_item("📚  别名库", 3)

        self.sidebar.currentRowChanged.connect(self.change_page)
        main_layout.addWidget(self.sidebar)

        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.pages = QStackedWidget()
        self.pages.addWidget(self.create_general_page())
        self.pages.addWidget(self.create_templates_page())
        self.pages.addWidget(self.create_mapping_page())
        self.pages.addWidget(self.create_libraries_page())

        content_layout.addWidget(self.pages)

        btn_bar = QHBoxLayout()
        btn_bar.setContentsMargins(20, 10, 20, 20)
        btn_bar.addStretch()

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setFixedWidth(100)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("保存配置")
        self.btn_save.setObjectName("PrimaryButton")
        self.btn_save.setFixedWidth(120)
        self.btn_save.clicked.connect(self.save_settings)

        btn_bar.addWidget(self.btn_cancel)
        btn_bar.addWidget(self.btn_save)

        content_layout.addLayout(btn_bar)
        main_layout.addWidget(content_container)

        self.sidebar.setCurrentRow(0)
        self.apply_styles()

    def add_sidebar_item(self, text, index):
        item = QListWidgetItem(text)
        item.setSizeHint(QSize(0, 50))
        self.sidebar.addItem(item)

    def change_page(self, index):
        self.pages.setCurrentIndex(index)

    def create_general_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        layout.addWidget(QLabel("<h3>非法字符处理</h3>"))
        desc = QLabel("生成文件名时，以下字符将被自动替换为连字符 '-':")
        desc.setStyleSheet("color: #666;")
        layout.addWidget(desc)

        chars = self.current_settings.get('illegal_chars', [])
        chars_str = " ".join(chars)

        self.widgets['illegal_chars'] = QLineEdit(chars_str)
        self.widgets['illegal_chars'].setObjectName("InputBox")
        layout.addWidget(self.widgets['illegal_chars'])

        layout.addSpacing(20)
        layout.addWidget(QLabel("<h3>配置文件位置</h3>"))

        path_frame = QFrame()
        path_frame.setObjectName("InfoFrame")
        h = QHBoxLayout(path_frame)

        config_path = os.path.abspath(ConfigManager.SETTINGS_FILE)
        lbl_path = QLineEdit(os.path.dirname(config_path))
        lbl_path.setReadOnly(True)
        lbl_path.setStyleSheet("background: transparent; border: none; color: #555;")

        btn_open = QPushButton("打开文件夹")
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(config_path))))

        h.addWidget(lbl_path)
        h.addWidget(btn_open)
        layout.addWidget(path_frame)

        layout.addStretch()
        return page

    def create_templates_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        tabs = QTabWidget()

        tab_reg = QWidget()
        self.setup_template_tab(tab_reg, 'regular_photo', is_issue=False)
        tabs.addTab(tab_reg, "Regular Photo (标准照)")

        tab_issue = QWidget()
        self.setup_template_tab(tab_issue, 'issue_photo', is_issue=True)
        tabs.addTab(tab_issue, "Issue Photo (问题照)")

        layout.addWidget(tabs)
        return page

    def setup_template_tab(self, parent, config_key, is_issue):
        layout = QVBoxLayout(parent)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        data = self.current_settings.get(config_key, {})
        store = self.widgets['issue_template'] if is_issue else self.widgets['reg_template']

        # 文件名模板
        layout.addWidget(QLabel("<b>文件名模板 (File Name Pattern):</b>"))
        edit_name = QLineEdit(data.get('template_name', ''))
        edit_name.setObjectName("InputBox")
        store['name'] = edit_name
        layout.addWidget(edit_name)

        # 文件夹模板
        layout.addWidget(QLabel("<b>文件夹路径模板 (Folder Structure):</b>"))
        edit_folder = QLineEdit(data.get('template_folder', ''))
        edit_folder.setObjectName("InputBox")
        store['folder'] = edit_folder
        layout.addWidget(edit_folder)

        # 🔥🔥🔥 实时预览连接 🔥🔥🔥
        edit_name.textChanged.connect(lambda: self.update_preview(is_issue))
        edit_folder.textChanged.connect(lambda: self.update_preview(is_issue))

        # 变量胶囊
        layout.addSpacing(10)
        layout.addWidget(QLabel("点击下方标签插入变量:"))

        chips_layout = QHBoxLayout()
        chips_layout.setAlignment(Qt.AlignLeft)
        chips_layout.setSpacing(8)

        tags = ["{Build}", "{Config}", "{Rel_No}", "{SN}", "{Mode}", "{WF}", "{Test}"]
        if is_issue:
            tags += ["{CP}", "{Issue}"]
        else:
            tags += ["{CP}", "{O}"]

        for tag in tags:
            btn = QPushButton(tag)
            btn.setObjectName("TagChip")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, t=tag, e=edit_name: e.insert(t))
            chips_layout.addWidget(btn)

        layout.addLayout(chips_layout)
        layout.addStretch()

        # 预览区
        preview = QFrame()
        preview.setObjectName("PreviewBox")
        pl = QVBoxLayout(preview)
        pl.addWidget(QLabel("预览示例 (实时):"))

        # 占位 Label，后续 update_preview 会更新它们
        lbl_name_preview = QLabel()
        lbl_name_preview.setStyleSheet("font-family: monospace; color: #333; font-weight: bold;")
        store['lbl_name'] = lbl_name_preview  # 存起来

        lbl_folder_preview = QLabel()
        lbl_folder_preview.setStyleSheet("color: #666;")
        store['lbl_folder'] = lbl_folder_preview  # 存起来

        # 图标
        h_name = QHBoxLayout()
        h_name.addWidget(QLabel("📄"))
        h_name.addWidget(lbl_name_preview)
        h_name.addStretch()

        h_folder = QHBoxLayout()
        h_folder.addWidget(QLabel("📂"))
        h_folder.addWidget(lbl_folder_preview)
        h_folder.addStretch()

        pl.addLayout(h_name)
        pl.addLayout(h_folder)
        layout.addWidget(preview)

        # 初始化一次预览
        self.update_preview(is_issue)

    # 🔥🔥🔥 核心：更新预览逻辑 🔥🔥🔥
    def update_preview(self, is_issue):
        store = self.widgets['issue_template'] if is_issue else self.widgets['reg_template']

        name_tmpl = store['name'].text()
        folder_tmpl = store['folder'].text()

        # 准备当次预览数据
        preview_data = self.mock_data.copy()
        if is_issue:
            preview_data.update({"CP": "20Cycles", "Issue": "Crack"})
        else:
            preview_data.update({"CP": "25Drop", "O": "O1", "Orient": "O1"})

        # 简单替换
        preview_name = name_tmpl
        preview_folder = folder_tmpl

        for k, v in preview_data.items():
            preview_name = preview_name.replace(f"{{{k}}}", v)
            preview_folder = preview_folder.replace(f"{{{k}}}", v)

        # 加上假后缀
        preview_name += ".jpg"

        # 更新 UI
        store['lbl_name'].setText(preview_name)
        store['lbl_folder'].setText(preview_folder)

    def create_mapping_page(self):
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        layout.addWidget(QLabel("<h3>1. Excel 表头映射</h3>"))
        layout.addWidget(QLabel("请将左侧的系统标准名称映射到您 Excel 表格中实际的列头名称。"))

        grid = QGridLayout()
        grid.setSpacing(15)

        sys_fields = [
            ("Rel_No (机台号)", "Rel_No"),
            ("Test (测试项目)", "Test"),
            ("SN (序列号)", "SN"),
            ("Build (阶段)", "Build"),
            ("Config (配置)", "Config"),
            ("Mode (模式)", "Mode"),
            ("WF (Waterfall)", "WF")
        ]

        current_map = self.current_settings.get('excel_header_map', {})

        row, col = 0, 0
        for label_text, key in sys_fields:
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-weight: bold; color: #444;")

            edit = QLineEdit(current_map.get(key, ""))
            edit.setObjectName("InputBox")
            edit.setPlaceholderText(f"Excel列名 e.g. {key}")

            self.widgets['excel_map'][key] = edit

            grid.addWidget(lbl, row, col)
            grid.addWidget(edit, row + 1, col)

            col += 1
            if col > 1:
                col = 0
                row += 2

        layout.addLayout(grid)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background: #E0E0E0; margin: 10px 0;")
        layout.addWidget(line)

        layout.addWidget(QLabel("<h3>2. 解析变量映射</h3>"))
        layout.addWidget(QLabel("定义解析出的数据在模板中的标签名。"))

        p_grid = QGridLayout()
        p_grid.setSpacing(10)

        reg_map = self.current_settings.get('regular_photo', {}).get('parsed_data_map', {})
        issue_map = self.current_settings.get('issue_photo', {}).get('parsed_data_map', {})

        def add_parse_row(r, label, internal_key, current_val, store_key):
            l = QLabel(f"系统解析: {label}")
            arrow = QLabel("➜")
            w = QWidget()
            hl = QHBoxLayout(w)
            hl.setContentsMargins(0, 0, 0, 0)
            lb = QLabel("{")
            lb.setStyleSheet("color: #007AFF; font-size: 16px; font-weight: bold;")
            le = QLineEdit(current_val)
            le.setObjectName("InputBox")
            le.setFixedWidth(80)
            rb = QLabel("}")
            rb.setStyleSheet("color: #007AFF; font-size: 16px; font-weight: bold;")
            hl.addWidget(lb)
            hl.addWidget(le)
            hl.addWidget(rb)
            hl.addStretch()
            self.widgets['parsed_map'][store_key] = le
            p_grid.addWidget(l, r, 0)
            p_grid.addWidget(arrow, r, 1)
            p_grid.addWidget(w, r, 2)

        add_parse_row(0, "节点 (Checkpoint)", "CP", reg_map.get('CP', 'CP'), 'CP')
        add_parse_row(1, "方向 (Orientation)", "Orient", reg_map.get('O', 'Orient'), 'O')
        add_parse_row(2, "问题描述 (Issue)", "Issue", issue_map.get('Issue', 'Issue'), 'Issue')

        layout.addLayout(p_grid)
        layout.addStretch()

        scroll.setWidget(container)
        wrapper = QVBoxLayout(page)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(scroll)
        return page

    def create_libraries_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        layout.addWidget(QLabel("<h3>JSON 知识库管理</h3>"))
        layout.addWidget(QLabel("此处存储了节点别名和问题关键词的映射关系。"))

        btn_cp = QPushButton("📝 打开节点映射文件 (cp_map.json)")
        btn_cp.setFixedWidth(300)
        btn_cp.clicked.connect(lambda: self.open_json(ConfigManager.CP_MAP_FILE))

        btn_issue = QPushButton("📝 打开问题映射文件 (issue_map.json)")
        btn_issue.setFixedWidth(300)
        btn_issue.clicked.connect(lambda: self.open_json(ConfigManager.ISSUE_MAP_FILE))

        layout.addWidget(btn_cp)
        layout.addWidget(btn_issue)
        layout.addStretch()
        return page

    def open_json(self, path):
        url = QUrl.fromLocalFile(os.path.abspath(path))
        QDesktopServices.openUrl(url)

    def save_settings(self):
        raw_chars = self.widgets['illegal_chars'].text()
        self.current_settings['illegal_chars'] = raw_chars.split()

        self.current_settings['regular_photo']['template_name'] = self.widgets['reg_template']['name'].text()
        self.current_settings['regular_photo']['template_folder'] = self.widgets['reg_template']['folder'].text()

        self.current_settings['issue_photo']['template_name'] = self.widgets['issue_template']['name'].text()
        self.current_settings['issue_photo']['template_folder'] = self.widgets['issue_template']['folder'].text()

        for key, widget in self.widgets['excel_map'].items():
            self.current_settings['excel_header_map'][key] = widget.text()

        self.current_settings['regular_photo']['parsed_data_map']['CP'] = self.widgets['parsed_map']['CP'].text()
        self.current_settings['regular_photo']['parsed_data_map']['O'] = self.widgets['parsed_map']['O'].text()

        self.current_settings['issue_photo']['parsed_data_map']['CP'] = self.widgets['parsed_map']['CP'].text()
        self.current_settings['issue_photo']['parsed_data_map']['Issue'] = self.widgets['parsed_map']['Issue'].text()

        ConfigManager.save_settings(self.current_settings)
        self.accept()

    def apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }

            /* Sidebar */
            QListWidget#Sidebar {
                background-color: #F5F5F7;
                border: none;
                border-right: 1px solid #E5E5E5;
                outline: none;
                padding-top: 15px;
            }
            QListWidget::item {
                padding-left: 15px;
                color: #333;
                border-radius: 8px;
                margin: 4px 10px;
                font-size: 13px;
                font-weight: 500;
                height: 40px;
            }
            QListWidget::item:selected {
                background-color: #E0E0E0;
                color: #000;
            }
            QListWidget::item:hover {
                background-color: #EBEBEB;
            }

            /* Inputs */
            QLineEdit#InputBox {
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 13px;
                background-color: #FFFFFF;
                min-height: 20px;
            }
            QLineEdit#InputBox:focus { border: 2px solid #007AFF; }

            /* Preview Box */
            QFrame#InfoFrame {
                background-color: #F9F9F9;
                border: 1px solid #E5E5E5;
                border-radius: 6px;
            }
            QFrame#PreviewBox {
                background-color: #F2F7FF;
                border: 1px dashed #007AFF;
                border-radius: 6px;
                padding: 15px;
                color: #555;
            }

            /* Chips */
            QPushButton#TagChip {
                background-color: #E3F2FD;
                color: #007AFF;
                border: none;
                border-radius: 12px;
                padding: 5px 12px;
                font-weight: bold;
            }
            QPushButton#TagChip:hover { background-color: #BBDEFB; }

            /* Primary Button */
            QPushButton#PrimaryButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton#PrimaryButton:hover { background-color: #006AD6; }

            /* Tabs */
            QTabWidget::pane { border: 1px solid #E5E5E5; border-radius: 6px; top: -1px; }
            QTabBar::tab {
                background: #F5F5F7; 
                border: 1px solid #E5E5E5;
                padding: 8px 15px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected { background: #FFFFFF; border-bottom-color: #FFFFFF; }
        """)