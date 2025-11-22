from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget
from src.ui.components.visual_json_editor import VisualJsonEditor


class LibrariesPage(QWidget):
    def __init__(self, cp_map, issue_map, orient_map, parent=None):
        super().__init__(parent)
        # 这里我们直接持有引用，因为 VisualJsonEditor 是直接修改字典对象的
        self.cp_map = cp_map
        self.issue_map = issue_map
        self.orient_map = orient_map
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        tabs = QTabWidget()

        # Tab 1
        self.editor_cp = VisualJsonEditor(self.cp_map, mode='nested')
        tabs.addTab(self.editor_cp, "节点库 (CP Map)")

        # Tab 2
        self.editor_issue = VisualJsonEditor(self.issue_map, mode='flat')
        tabs.addTab(self.editor_issue, "问题库 (Issue Map)")

        # Tab 3
        self.editor_orient = VisualJsonEditor(self.orient_map, mode='flat')
        tabs.addTab(self.editor_orient, "方向库 (Orient Map)")

        layout.addWidget(tabs)

        note = QLabel("注意：所有修改仅在内存中生效，只有点击右下角【保存全部配置】后才会写入文件。")
        note.setStyleSheet("color: #d32f2f; font-weight: bold;")
        layout.addWidget(note)

    # 这个页面不需要 save_data 方法，因为数据是引用修改的，
    # 主对话框的 save_all_settings 会直接拿最新的 map 去保存