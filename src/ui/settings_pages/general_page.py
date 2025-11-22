from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QToolButton, QFileDialog, QFrame, \
    QScrollArea
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
import os
import subprocess
import platform
from src.core.config_manager import ConfigManager


class GeneralPage(QWidget):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.widgets = {}  # 存储控件引用
        self.init_ui()

    def init_ui(self):
        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #F5F5F7; border: none; }")

        # Container Widget
        container = QWidget()
        container.setObjectName("Container")
        container.setStyleSheet("#Container { background-color: #F5F5F7; }")
        
        content_layout = QVBoxLayout(container)
        content_layout.setAlignment(Qt.AlignTop)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(20)

        # --- Card 1: Illegal Characters ---
        card_illegal = self.create_card("非法字符处理")
        layout_illegal = card_illegal.layout()
        
        lbl_desc = QLabel("生成文件名时，以下字符将被自动替换为连字符 '-':")
        lbl_desc.setStyleSheet("color: #666; font-size: 13px; margin-bottom: 5px;")
        layout_illegal.addWidget(lbl_desc)
        
        chars = self.settings.get('illegal_chars', [])
        self.widgets['illegal_chars'] = QLineEdit(" ".join(chars))
        self.widgets['illegal_chars'].setObjectName("InputBox")
        layout_illegal.addWidget(self.widgets['illegal_chars'])
        
        content_layout.addWidget(card_illegal)

        # --- Card 2: Session Paths ---
        card_paths = self.create_card("上次会话路径 (Session Paths)")
        layout_paths = card_paths.layout()
        layout_paths.setSpacing(15)

        last_session = self.settings.get('last_session', {})

        def add_path_row(label_text, key, is_file=False):
            v_box = QVBoxLayout()
            v_box.setSpacing(5)
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-weight: 500; color: #333; font-size: 13px;")
            v_box.addWidget(lbl)
            
            h_box = QHBoxLayout()
            le = QLineEdit(last_session.get(key, ''))
            le.setObjectName("InputBox")
            
            btn = QToolButton()
            btn.setText("...")
            btn.setObjectName("BrowseButton")
            btn.setCursor(Qt.PointingHandCursor)
            
            if is_file:
                btn.clicked.connect(lambda: self.browse_file(le, "CSV (*.csv)"))
            else:
                btn.clicked.connect(lambda: self.browse_dir(le))
            
            h_box.addWidget(le)
            h_box.addWidget(btn)
            v_box.addLayout(h_box)
            self.widgets[key] = le
            layout_paths.addLayout(v_box)

        add_path_row("默认 CSV 数据表:", 'excel_path', is_file=True)
        add_path_row("Regular 默认输出文件夹:", 'regular_output_dir')
        add_path_row("Issue 默认输出文件夹:", 'issue_output_dir')
        
        content_layout.addWidget(card_paths)

        # --- Card 3: Configuration File ---
        card_config = self.create_card("配置文件位置")
        layout_config = card_config.layout()
        
        config_path = os.path.abspath(ConfigManager.SETTINGS_FILE)
        h_config = QHBoxLayout()
        
        le_config = QLineEdit(config_path)
        le_config.setObjectName("InputBox")
        le_config.setReadOnly(True)
        le_config.setStyleSheet("color: #666; background-color: #F0F0F5;") # Read-only style
        
        btn_open_config = QToolButton()
        btn_open_config.setText("📂") 
        btn_open_config.setToolTip("打开文件位置")
        btn_open_config.setObjectName("BrowseButton")
        btn_open_config.setCursor(Qt.PointingHandCursor)
        btn_open_config.clicked.connect(lambda: self.open_config_location(config_path))
        
        h_config.addWidget(le_config)
        h_config.addWidget(btn_open_config)
        layout_config.addLayout(h_config)
        
        content_layout.addWidget(card_config)

        content_layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        self.apply_styles()

    def create_card(self, title):
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_title = QLabel(title)
        lbl_title.setObjectName("CardTitle")
        layout.addWidget(lbl_title)
        
        # Add a small separator or spacing
        layout.addSpacing(10)
        
        return card

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            }
            
            QFrame#Card {
                background-color: #FFFFFF;
                border-radius: 10px;
                border: 1px solid #E5E5E5;
            }
            
            QLabel#CardTitle {
                font-size: 16px;
                font-weight: 700;
                color: #1D1D1F;
                margin-bottom: 5px;
            }
            
            QLineEdit#InputBox {
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                background-color: #FFFFFF;
            }
            QLineEdit#InputBox:focus {
                border: 1px solid #007AFF;
            }
            
            QToolButton#BrowseButton {
                background-color: #F2F2F7;
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                padding: 5px 10px;
                font-weight: 600;
                color: #333;
            }
            QToolButton#BrowseButton:hover {
                background-color: #E5E5EA;
            }
            QToolButton#BrowseButton:pressed {
                background-color: #D1D1D6;
            }
        """)

    def browse_file(self, line_edit, filter_):
        path, _ = QFileDialog.getOpenFileName(self, "Select File", line_edit.text(), filter_)
        if path: line_edit.setText(path)

    def browse_dir(self, line_edit):
        path = QFileDialog.getExistingDirectory(self, "Select Directory", line_edit.text())
        if path: line_edit.setText(path)

    def open_config_location(self, path):
        """
        打开配置文件所在位置并选中文件 (支持 Windows/macOS)
        """
        if not os.path.exists(path):
            return

        system_name = platform.system()

        if system_name == "Windows":
            # Windows: explorer /select,path
            try:
                subprocess.Popen(f'explorer /select,"{path}"')
            except Exception as e:
                print(f"Error opening explorer: {e}")
                # Fallback
                QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path)))
        
        elif system_name == "Darwin":
            # macOS: open -R path
            try:
                subprocess.call(["open", "-R", path])
            except Exception as e:
                print(f"Error opening finder: {e}")
                # Fallback
                QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path)))
        
        else:
            # Linux/Other: Try to open parent directory
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path)))

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