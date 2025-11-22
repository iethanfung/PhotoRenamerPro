from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QToolButton, QFileDialog, QFrame, \
    QScrollArea
from PySide6.QtCore import Qt


class GeneralPage(QWidget):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.widgets = {}  # 存储控件引用
        self.init_ui()

    def init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        layout.addWidget(QLabel("<h3>非法字符处理</h3>"))
        layout.addWidget(QLabel("生成文件名时，以下字符将被自动替换为连字符 '-':"))
        chars = self.settings.get('illegal_chars', [])
        self.widgets['illegal_chars'] = QLineEdit(" ".join(chars))
        self.widgets['illegal_chars'].setObjectName("InputBox")
        layout.addWidget(self.widgets['illegal_chars'])

        layout.addSpacing(10)
        layout.addWidget(QLabel("<h3>上次会话路径 (Session Paths)</h3>"))

        last_session = self.settings.get('last_session', {})

        # Helper
        def add_path_row(label, key, is_file=False):
            layout.addWidget(QLabel(label))
            h = QHBoxLayout()
            le = QLineEdit(last_session.get(key, ''))
            le.setObjectName("InputBox")
            btn = QToolButton()
            btn.setText("...")
            if is_file:
                btn.clicked.connect(lambda: self.browse_file(le, "CSV (*.csv)"))
            else:
                btn.clicked.connect(lambda: self.browse_dir(le))
            h.addWidget(le)
            h.addWidget(btn)
            layout.addLayout(h)
            self.widgets[key] = le

        add_path_row("默认 CSV 数据表:", 'excel_path', is_file=True)
        add_path_row("Regular 默认输出文件夹:", 'regular_output_dir')
        add_path_row("Issue 默认输出文件夹:", 'issue_output_dir')

        layout.addStretch()

        scroll.setWidget(container)
        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(scroll)

    def browse_file(self, line_edit, filter_):
        path, _ = QFileDialog.getOpenFileName(self, "Select File", line_edit.text(), filter_)
        if path: line_edit.setText(path)

    def browse_dir(self, line_edit):
        path = QFileDialog.getExistingDirectory(self, "Select Directory", line_edit.text())
        if path: line_edit.setText(path)

    def save_data(self):
        """将界面数据写回 settings 字典"""
        # 1. Illegal Chars
        raw_chars = self.widgets['illegal_chars'].text()
        self.settings['illegal_chars'] = raw_chars.split()

        # 2. Session Paths
        if 'last_session' not in self.settings: self.settings['last_session'] = {}
        self.settings['last_session']['excel_path'] = self.widgets['excel_path'].text()
        self.settings['last_session']['regular_output_dir'] = self.widgets['regular_output_dir'].text()
        self.settings['last_session']['issue_output_dir'] = self.widgets['issue_output_dir'].text()