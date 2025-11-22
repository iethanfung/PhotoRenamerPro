from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QGridLayout,
    QLineEdit, QHBoxLayout, QToolButton, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt


class MappingPage(QWidget):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.mapping_rows = []
        self.widgets = {'parsed_map': {}}
        self.init_ui()

    def init_ui(self):
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self.content_layout = QVBoxLayout(container)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)  # 增加间距，更透气

        # 标题区
        title_box = QVBoxLayout()
        title_box.setSpacing(5)
        lbl_title = QLabel("CSV 表头映射")
        lbl_title.setObjectName("H3")  # 用于 CSS 样式
        lbl_desc = QLabel("定义变量名 (Key) 与 CSV 列头 (Header) 的对应关系。")
        lbl_desc.setObjectName("DescLabel")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_desc)
        self.content_layout.addLayout(title_box)

        # 动态行容器
        self.rows_container = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(0, 10, 0, 10)
        self.rows_layout.setSpacing(12)  # 行间距增加
        self.content_layout.addWidget(self.rows_container)

        # 加载现有映射
        current_map = self.settings.get('excel_header_map', {})
        priority_keys = ["Rel_No", "Test", "SN", "Build", "Config", "Mode", "WF"]
        existing_keys = list(current_map.keys())

        for pk in priority_keys:
            if pk in existing_keys:
                self.add_mapping_row(pk, current_map[pk])
                existing_keys.remove(pk)
        for k in existing_keys:
            self.add_mapping_row(k, current_map[k])

        # 新增按钮
        btn_add = QPushButton("＋ 新增映射字段")
        btn_add.setObjectName("SecondaryButton")  # 设为次级按钮样式
        btn_add.clicked.connect(lambda: self.add_mapping_row("", ""))
        self.content_layout.addWidget(btn_add)

        # 分割线
        line = QFrame()
        line.setObjectName("Separator")  # 用于 CSS
        line.setFrameShape(QFrame.HLine)
        self.content_layout.addWidget(line)

        # 解析变量映射
        lbl_sec2 = QLabel("解析变量映射 (Fixed)")
        lbl_sec2.setObjectName("H3")
        self.content_layout.addWidget(lbl_sec2)

        p_grid = QGridLayout()
        p_grid.setSpacing(15)
        reg_map = self.settings.get('regular_photo', {}).get('parsed_data_map', {})
        issue_map = self.settings.get('issue_photo', {}).get('parsed_data_map', {})

        self.add_static_row(p_grid, 0, "节点 (CP)", reg_map.get('CP', 'CP'), 'CP')
        self.add_static_row(p_grid, 1, "方向 (Orient)", reg_map.get('O', 'Orient'), 'O')
        self.add_static_row(p_grid, 2, "问题 (Issue)", issue_map.get('Issue', 'Issue'), 'Issue')

        self.content_layout.addLayout(p_grid)
        self.content_layout.addStretch()

        scroll.setWidget(container)
        page_layout.addWidget(scroll)

    def add_static_row(self, grid, r, label, val, key):
        l = QLabel(label)
        l.setStyleSheet("font-weight: 500; color: #333;")
        grid.addWidget(l, r, 0)

        grid.addWidget(QLabel("➜"), r, 1)

        le = QLineEdit(val)
        le.setObjectName("InputBox")
        le.setFixedWidth(120)
        self.widgets['parsed_map'][key] = le

        # 包装一下显得更好看
        wrapper = QWidget()
        wl = QHBoxLayout(wrapper)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.addWidget(QLabel("{"))
        wl.addWidget(le)
        wl.addWidget(QLabel("}"))
        wl.addStretch()

        grid.addWidget(wrapper, r, 2)

    def add_mapping_row(self, key_text, value_text):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)

        # Key
        edt_key = QLineEdit(key_text)
        edt_key.setPlaceholderText("变量名")
        edt_key.setObjectName("InputBox")

        lbl_arrow = QLabel("➜")
        lbl_arrow.setStyleSheet("color: #999; font-weight: bold;")

        # Value
        edt_val = QLineEdit(value_text)
        edt_val.setPlaceholderText("CSV 列头名")
        edt_val.setObjectName("InputBox")

        # 删除按钮
        btn_del = QToolButton()
        btn_del.setText("🗑️")  # 或者使用图标
        btn_del.setObjectName("DeleteButton")  # 🔥 用于 CSS 样式
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setToolTip("删除此映射")

        row_layout.addWidget(edt_key, 3)
        row_layout.addWidget(lbl_arrow)
        row_layout.addWidget(edt_val, 3)
        row_layout.addWidget(btn_del)

        row_data = {'widget': row_widget, 'key': edt_key, 'value': edt_val}
        self.mapping_rows.append(row_data)

        btn_del.clicked.connect(lambda: self.delete_mapping_row(row_data))
        self.rows_layout.addWidget(row_widget)

    # 🔥🔥🔥 修复点：增加删除确认 🔥🔥🔥
    def delete_mapping_row(self, row_data):
        key_name = row_data['key'].text().strip()
        if not key_name: key_name = "此空行"

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除映射 '{key_name}' 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.rows_layout.removeWidget(row_data['widget'])
            row_data['widget'].deleteLater()
            if row_data in self.mapping_rows:
                self.mapping_rows.remove(row_data)

    def get_current_keys(self):
        keys = []
        for row in self.mapping_rows:
            k = row['key'].text().strip()
            if k: keys.append(k)
        return keys

    def get_parsed_vars(self):
        return {
            'CP': self.widgets['parsed_map']['CP'].text().strip() or "CP",
            'O': self.widgets['parsed_map']['O'].text().strip() or "Orient",
            'Issue': self.widgets['parsed_map']['Issue'].text().strip() or "Issue"
        }

    def save_data(self):
        new_map = {}
        for row_data in self.mapping_rows:
            k = row_data['key'].text().strip()
            v = row_data['value'].text().strip()
            if k and v: new_map[k] = v
        self.settings['excel_header_map'] = new_map

        self.settings['regular_photo']['parsed_data_map']['CP'] = self.widgets['parsed_map']['CP'].text()
        self.settings['regular_photo']['parsed_data_map']['O'] = self.widgets['parsed_map']['O'].text()
        self.settings['issue_photo']['parsed_data_map']['CP'] = self.widgets['parsed_map']['CP'].text()
        self.settings['issue_photo']['parsed_data_map']['Issue'] = self.widgets['parsed_map']['Issue'].text()