from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap


class ImagePop(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel()
        self.label.setStyleSheet("""
            background-color: white;
            border: 1px solid #CCCCCC;
            border-radius: 8px;
            padding: 4px;
        """)
        self.layout.addWidget(self.label)

        # Shadow effect (optional, needs QGraphicsEffect)

    def set_image(self, pixmap: QPixmap):
        if pixmap:
            scaled = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.label.setPixmap(scaled)
            self.resize(scaled.size() + QSize(10, 10))