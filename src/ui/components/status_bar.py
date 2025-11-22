from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

class StatusBar(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StatusBar")
        self.setFixedHeight(30)
        self.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.setContentsMargins(10, 0, 0, 0)
        self.update_status(0, 0, "Ready")

    def update_status(self, total, checked_out, msg):
        text = f"  状态: {msg}  |  已加载: {total} 张          提示：双击可修改【原文件名】，【标准CP】，【标准方向/issue】列的值"
        self.setText(text)