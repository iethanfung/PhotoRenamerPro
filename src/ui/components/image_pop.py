from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor


class ImagePop(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint)
        # 1. 设置主窗口背景透明，以便显示圆角和阴影
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # 2. 主布局 (留出 Margin 给阴影显示，否则阴影会被切掉)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)

        # 3. 卡片容器 (真正的白色背景区域)
        self.container = QFrame()
        self.container.setObjectName("PopCard")
        self.container.setStyleSheet("""
            QFrame#PopCard {
                background-color: #FFFFFF;
                border: 1px solid #E5E5E5;
                border-radius: 12px;
            }
        """)

        # 4. 添加 macOS 风格的柔和阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)  # 阴影模糊度
        shadow.setXOffset(0)
        shadow.setYOffset(5)  # 阴影向下偏移
        shadow.setColor(QColor(0, 0, 0, 40))  # 半透明黑色
        self.container.setGraphicsEffect(shadow)

        # 5. 卡片内部布局
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(10, 10, 10, 10)
        self.container_layout.setSpacing(8)

        # 图片标签
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)
        # 让图片圆角需要 mask，这里简单处理：不设背景色即可
        self.img_label.setStyleSheet("background: transparent; border: none;")
        self.container_layout.addWidget(self.img_label)

        # 文字标签 (路径)
        self.text_label = QLabel()
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet("""
            color: #8E8E93;  /* Apple System Gray */
            font-size: 11px;
            font-family: "SF Pro Text", "Segoe UI", sans-serif;
            border: none;
            background: transparent;
            padding-top: 4px;
        """)
        self.text_label.setMaximumWidth(320)  # 限制文字最大宽度
        self.container_layout.addWidget(self.text_label)

        self.layout.addWidget(self.container)

    def set_content(self, pixmap: QPixmap, path_text: str):
        """同时设置图片和文字"""
        # 基础尺寸 (包含 Margin)
        base_margin = 30
        content_width = 0
        content_height = 0

        if pixmap:
            # 限制图片最大尺寸，保持比例
            # macOS 风格通常图片比较精致，不要太大
            max_w, max_h = 360, 360
            scaled = pixmap.scaled(max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_label.setPixmap(scaled)
            self.img_label.setVisible(True)

            content_width = max(content_width, scaled.width())
            content_height += scaled.height()
        else:
            self.img_label.setVisible(False)

        if path_text:
            self.text_label.setText(path_text)
            self.text_label.setVisible(True)
            # 估算文字高度
            content_height += 50
            content_width = max(content_width, 220)  # 保证最小宽度
        else:
            self.text_label.setVisible(False)

        # 调整窗口大小 (内容 + 内边距 + 阴影外边距)
        self.resize(content_width + base_margin, content_height + base_margin)