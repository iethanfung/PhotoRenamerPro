from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton, QFrame, QTabWidget
from PySide6.QtCore import Qt, QEvent


class TemplatesPage(QWidget):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.widgets = {
            'reg_template': {},
            'issue_template': {}
        }

        # 🔥 内部标准 Mock 数据 (Key 是 sys_id)
        self.internal_mock_data = {
            "Build": "P1", "Config": "R1", "Rel_No": "0065",
            "SN": "SN123456", "Mode": "Stow", "WF": "2", "Test": "1mG",
            "__CP__": "25Drop",
            "__O__": "O1",
            "__Issue__": "Crack"
        }

        # 🔥 2. 暂存当前的变量名映射 (默认值)
        self.current_parsed_vars = {
            'CP': 'CP',
            'O': 'Orient',
            'Issue': 'Issue'
        }

        self.current_sys_id_map = {}  # 存储 sys_id -> user_key

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        tabs = QTabWidget()
        tab_reg = QWidget()
        self.setup_template_tab(tab_reg, 'regular_photo', is_issue=False)
        tabs.addTab(tab_reg, "Regular Photo (标准照)")

        tab_issue = QWidget()
        self.setup_template_tab(tab_issue, 'issue_photo', is_issue=True)
        tabs.addTab(tab_issue, "Issue Photo (问题照)")

        layout.addWidget(tabs)

    def setup_template_tab(self, parent, config_key, is_issue):
        layout = QVBoxLayout(parent)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        data = self.settings.get(config_key, {})
        store = self.widgets['issue_template'] if is_issue else self.widgets['reg_template']

        edit_name = QLineEdit(data.get('template_name', ''))
        edit_folder = QLineEdit(data.get('template_folder', ''))
        
        # 默认焦点在 name 输入框
        store['current_edit'] = edit_name

        layout.addWidget(QLabel("<b>文件名模板:</b>"))
        edit_name.setObjectName("InputBox")
        store['name'] = edit_name
        edit_name.installEventFilter(self)
        layout.addWidget(edit_name)

        layout.addWidget(QLabel("<b>文件夹路径模板:</b>"))
        edit_folder.setObjectName("InputBox")
        store['folder'] = edit_folder
        edit_folder.installEventFilter(self)
        layout.addWidget(edit_folder)

        edit_name.textChanged.connect(lambda: self.update_preview(is_issue))
        edit_folder.textChanged.connect(lambda: self.update_preview(is_issue))

        layout.addSpacing(10)
        layout.addWidget(QLabel("可用变量 (点击插入):"))

        store['chips_container'] = QWidget()
        store['chips_layout'] = QHBoxLayout(store['chips_container'])
        store['chips_layout'].setAlignment(Qt.AlignLeft)
        store['chips_layout'].setContentsMargins(0, 0, 0, 0)
        store['chips_layout'].setSpacing(8)
        layout.addWidget(store['chips_container'])

        layout.addStretch()

        preview = QFrame()
        preview.setObjectName("PreviewBox")
        pl = QVBoxLayout(preview)
        pl.addWidget(QLabel("实时预览:"))
        lbl_name = QLabel()
        lbl_name.setStyleSheet("font-family: monospace; font-weight: bold;")
        store['lbl_name'] = lbl_name
        lbl_folder = QLabel()
        lbl_folder.setStyleSheet("color: #666;")
        store['lbl_folder'] = lbl_folder
        pl.addWidget(lbl_name)
        pl.addWidget(lbl_folder)
        layout.addWidget(preview)

        # 初始时调用一次预览
        self.update_preview(is_issue)

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.FocusIn:
            # 检查是哪个 tab 的输入框
            if source in [self.widgets['reg_template'].get('name'), self.widgets['reg_template'].get('folder')]:
                self.widgets['reg_template']['current_edit'] = source
            elif source in [self.widgets['issue_template'].get('name'), self.widgets['issue_template'].get('folder')]:
                self.widgets['issue_template']['current_edit'] = source
        return super().eventFilter(source, event)

    def insert_tag(self, store, tag):
        edit = store.get('current_edit')
        if edit:
            edit.insert(tag)
            edit.setFocus()

    def refresh_chips(self, mapping_keys, parsed_vars, sys_id_map):
        """由主对话框调用,传入最新的  Keys 和 Parsed Vars"""
        # 🔥 3. 更新暂存的映射关系
        self.current_sys_id_map = sys_id_map
        self.current_parsed_vars = parsed_vars

        self._rebuild_chips(self.widgets['reg_template'], mapping_keys, parsed_vars, is_issue=False)
        self._rebuild_chips(self.widgets['issue_template'], mapping_keys, parsed_vars, is_issue=True)

        # 🔥 4. 刷新预览
        self.update_preview(is_issue=False)
        self.update_preview(is_issue=True)

    def _rebuild_chips(self, store, mapping_keys, parsed_vars, is_issue):
        layout = store['chips_layout']
        while layout.count():
            child = layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        tags = mapping_keys.copy()

        cp_tag = parsed_vars.get('CP', 'CP')
        if is_issue:
            issue_tag = parsed_vars.get('Issue', 'Issue')
            tags += [cp_tag, issue_tag]
        else:
            orient_tag = parsed_vars.get('O', 'Orient')
            tags += [cp_tag, orient_tag]

        for tag in tags:
            clean_tag = tag.replace("{", "").replace("}", "")
            label = f"{{{clean_tag}}}"

            btn = QPushButton(label)
            btn.setObjectName("TagChip")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, t=label, s=store: self.insert_tag(s, t))
            layout.addWidget(btn)

    def update_preview(self, is_issue):
        store = self.widgets['issue_template'] if is_issue else self.widgets['reg_template']
        name_tmpl = store['name'].text()
        folder_tmpl = store['folder'].text()

        # 🔥🔥🔥 动态构建预览数据 🔥🔥🔥
        preview_data = {}

        # 1. 映射 CSV 变量
        # 遍历内部 mock 数据，查看是否有对应的 User Key
        for sys_id, val in self.internal_mock_data.items():
            if sys_id in self.current_sys_id_map:
                user_key = self.current_sys_id_map[sys_id]
                preview_data[user_key] = val
            elif not sys_id.startswith("__"):
                # 如果用户删了这个映射，或者这是个未映射的标准字段，暂且保留原名作为 key
                preview_data[sys_id] = val

        # 2. 映射解析变量
        user_cp_key = self.current_parsed_vars.get('CP', 'CP')
        user_orient_key = self.current_parsed_vars.get('O', 'Orient')
        user_issue_key = self.current_parsed_vars.get('Issue', 'Issue')

        preview_data[user_cp_key] = self.internal_mock_data["__CP__"]

        if is_issue:
            preview_data[user_issue_key] = self.internal_mock_data["__Issue__"]
        else:
            preview_data[user_orient_key] = self.internal_mock_data["__O__"]

        # 执行替换
        for k, v in preview_data.items():
            name_tmpl = name_tmpl.replace(f"{{{k}}}", v)
            folder_tmpl = folder_tmpl.replace(f"{{{k}}}", v)

        store['lbl_name'].setText("📄 " + name_tmpl + ".jpg")
        store['lbl_folder'].setText("📂 " + folder_tmpl)

    def save_data(self):
        self.settings['regular_photo']['template_name'] = self.widgets['reg_template']['name'].text()
        self.settings['regular_photo']['template_folder'] = self.widgets['reg_template']['folder'].text()
        self.settings['issue_photo']['template_name'] = self.widgets['issue_template']['name'].text()
        self.settings['issue_photo']['template_folder'] = self.widgets['issue_template']['folder'].text()