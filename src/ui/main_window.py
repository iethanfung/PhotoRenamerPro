import os
import shutil
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QHeaderView, QSizePolicy, QFileDialog, QMessageBox, QCheckBox, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, Slot
from src.ui.components.preview_table import PreviewTable
from src.ui.components.status_bar import StatusBar
from src.ui.models.photo_table_model import PhotoTableModel
from src.ui.settings_dialog import SettingsDialog
from src.core.config_manager import ConfigManager
from src.core.excel_engine import ExcelEngine
from src.core.parser_engine import ParserEngine
from src.core.file_processor import FileProcessor
from src.core.learner import Learner
from src.utils.constants import COLOR_GREEN, COLOR_YELLOW, COLOR_ORANGE, COLOR_RED


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photo Renamer Pro")
        self.resize(1300, 800)
        self.setAcceptDrops(True)

        self.settings = ConfigManager.load_settings()
        self.cp_map = ConfigManager.load_cp_map()
        self.issue_map = ConfigManager.load_issue_map()

        self.excel_engine = ExcelEngine()
        self.parser_engine = ParserEngine(self.excel_engine, self.settings, self.cp_map, self.issue_map)
        self.file_processor = FileProcessor(self.settings)

        self.init_ui()

        # --- 🔥🔥🔥 修复点：启动时恢复上次的会话状态 🔥🔥🔥 ---
        last_session = self.settings.get('last_session', {})

        # 1. 恢复 Excel
        last_excel = last_session.get('excel_path')
        if last_excel and os.path.exists(last_excel):
            self.load_excel(last_excel)

        # 2. 恢复 Regular 输出路径
        last_reg_out = last_session.get('regular_output_dir')
        if last_reg_out and os.path.exists(last_reg_out):
            self.btn_reg_dir.setText(f"📂 Reg Out: {os.path.basename(last_reg_out)}")
            self.btn_reg_dir.setToolTip(last_reg_out)  # 鼠标悬停显示全路径

        # 3. 恢复 Issue 输出路径
        last_issue_out = last_session.get('issue_output_dir')
        if last_issue_out and os.path.exists(last_issue_out):
            self.btn_issue_dir.setText(f"📂 Issue Out: {os.path.basename(last_issue_out)}")
            self.btn_issue_dir.setToolTip(last_issue_out)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Header ---
        header_widget = QWidget()
        header_widget.setObjectName("HeaderArea")
        header_widget.setFixedHeight(140)
        header_layout = QHBoxLayout(header_widget)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.btn_excel = QPushButton("📄 Load Excel")
        self.btn_excel.clicked.connect(self.browse_excel)
        self.btn_reg_dir = QPushButton("📂 Regular Output Dir")
        self.btn_reg_dir.clicked.connect(lambda: self.browse_output('regular'))
        self.btn_issue_dir = QPushButton("📂 Issue Output Dir")
        self.btn_issue_dir.clicked.connect(lambda: self.browse_output('issue'))

        for btn in [self.btn_excel, self.btn_reg_dir, self.btn_issue_dir]:
            btn.setObjectName("ConfigButton")
            left_layout.addWidget(btn)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        top_btns = QHBoxLayout()
        self.btn_settings = QPushButton("⚙️ Settings")
        self.btn_settings.clicked.connect(self.open_settings)
        self.btn_clear = QPushButton("🗑️ Clear List")
        self.btn_clear.clicked.connect(self.clear_table)
        top_btns.addWidget(self.btn_settings)
        top_btns.addWidget(self.btn_clear)

        self.btn_start = QPushButton("▶ Start Rename")
        self.btn_start.setObjectName("BigStartButton")
        self.btn_start.clicked.connect(self.execute_rename)

        right_layout.addLayout(top_btns)
        right_layout.addWidget(self.btn_start)

        header_layout.addWidget(left_panel, 3)
        header_layout.addWidget(right_panel, 1)
        main_layout.addWidget(header_widget)

        # --- Table ---
        self.table = PreviewTable()
        self.model = PhotoTableModel()
        self.table.setModel(self.model)
        self.model.dataChanged.connect(self.on_data_changed)

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Interactive)
        h.setStretchLastSection(True)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 150)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 60)
        self.table.setColumnWidth(7, 80)
        self.table.setColumnWidth(8, 250)

        main_layout.addWidget(self.table)
        self.status_bar = StatusBar()
        main_layout.addWidget(self.status_bar)
        self.apply_styles()

    def apply_styles(self):
        qss_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'styles',
                                'sonoma.qss')

        # 基础样式
        base_style = ""
        if os.path.exists(qss_path):
            with open(qss_path, 'r', encoding='utf-8') as f:
                base_style = f.read()

        # 🔥🔥🔥 修复点 1：追加 ToolTip 强制样式 🔥🔥🔥
        # 防止系统主题导致看不清
        tooltip_style = """
            QToolTip {
                color: #000000;
                background-color: #ffffe0;
                border: 1px solid #888;
                padding: 4px;
                border-radius: 4px;
            }
        """
        self.setStyleSheet(base_style + tooltip_style)

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            self.settings = ConfigManager.load_settings()
            self.cp_map = ConfigManager.load_cp_map()
            self.issue_map = ConfigManager.load_issue_map()
            self.parser_engine.settings = self.settings
            self.parser_engine.cp_map = self.cp_map
            self.parser_engine.issue_map = self.issue_map
            self.file_processor.settings = self.settings
            self.status_bar.update_status(self.model.rowCount(), 0, "Settings Reloaded")

    def browse_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Unit Excel", "", "Excel Files (*.xlsx *.xls)")
        if path:
            self.load_excel(path)
            self.settings['last_session']['excel_path'] = path
            ConfigManager.save_settings(self.settings)

    def load_excel(self, path):
        ok, msg = self.excel_engine.load_excel(path, self.settings['excel_header_map'])
        if ok:
            self.btn_excel.setText(f"📄 Excel: {os.path.basename(path)}")

            # 🔥🔥🔥 修复点 2：补上 Excel 按钮的悬停提示 🔥🔥🔥
            self.btn_excel.setToolTip(path)

            self.status_bar.update_status(0, 0, "Excel Loaded")
        else:
            QMessageBox.critical(self, "Error", msg)

    def browse_output(self, type_):
        path = QFileDialog.getExistingDirectory(self, f"Select {type_} Output Directory")
        if path:
            key = f"{type_}_output_dir"
            self.settings['last_session'][key] = path
            ConfigManager.save_settings(self.settings)
            # 实时更新按钮文字
            if type_ == 'regular':
                self.btn_reg_dir.setText(f"📂 Reg Out: {os.path.basename(path)}")
                self.btn_reg_dir.setToolTip(path)
            else:
                self.btn_issue_dir.setText(f"📂 Issue Out: {os.path.basename(path)}")
                self.btn_issue_dir.setToolTip(path)

    def clear_table(self):
        self.model.clear_all()
        self.status_bar.update_status(0, 0, "List Cleared")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        files = []
        for url in urls:
            path = url.toLocalFile()
            if os.path.isdir(path):
                for root, dirs, fnames in os.walk(path):
                    for f in fnames:
                        if f.lower().endswith(('.jpg', '.png', '.jpeg')):
                            files.append(os.path.join(root, f))
            elif path.lower().endswith(('.jpg', '.png', '.jpeg')):
                files.append(path)
        self.process_files(files)

    def process_files(self, file_paths):
        if not self.excel_engine.df is not None:
            QMessageBox.warning(self, "Warning", "Please load Excel first!")
            return

        results = []
        skipped_count = 0

        for f in file_paths:
            # 检查是否已存在
            if self.model.has_file(f):
                skipped_count += 1
                continue

            res = self.parser_engine.parse_filename(f)
            target_path, target_name = self.file_processor.generate_target_path(res)
            res['target_filename'] = target_name
            res['target_full_path'] = target_path
            results.append(res)

        self.model.add_rows(results)

        msg = f"Loaded {len(results)} files"
        if skipped_count > 0:
            msg += f" (Skipped {skipped_count} duplicates)"
        self.status_bar.update_status(self.model.rowCount(), 0, msg)

    @Slot(object, object)
    def on_data_changed(self, top_left, bottom_right):
        row = top_left.row()
        col = top_left.column()

        if col == self.model.COL_INDEX: return

        # 只有值真正改变了，才会进到这里 (因为 Model 的 setData 拦截了无修改的情况)
        if col == self.model.COL_STD_CP or col == self.model.COL_DETAIL:
            item = self.model.data_list[row]

            raw_cp = item['parse_result']['raw_cp']
            std_cp = item['parse_result']['std_cp']

            raw_detail = item['parse_result'].get('raw_detail', '')
            detail = item['parse_result']['detail']

            test = item['parse_result']['unit_data'].get('Test', 'Unknown')
            type_ = item['parse_result']['type']

            # 1. 空值处理
            if not std_cp or not std_cp.strip():
                std_cp = "[Unknown CP]"
                if type_ == 'Regular':
                    item['parse_result']['status_color'] = COLOR_ORANGE
                    item['parse_result']['status_msg'] = "Fix CP"
            else:
                item['parse_result']['status_color'] = COLOR_GREEN
                item['parse_result']['status_msg'] = "Ready"

                # 2. 触发 CP 自学习
                if col == self.model.COL_STD_CP and type_ == 'Regular' and raw_cp:
                    Learner.learn_new_cp_alias(test, std_cp, raw_cp)
                    self.cp_map = ConfigManager.load_cp_map()
                    self.parser_engine.cp_map = self.cp_map

            # 3. 🔥🔥🔥 触发 Issue 自学习 🔥🔥🔥
            # 如果修改的是 Detail 列，且类型是 Issue，且有原始词
            if col == self.model.COL_DETAIL and type_ == 'Issue' and raw_detail:
                # 只有当用户输入了有效的新 Issue 名时才学习
                if detail and detail.strip():
                    Learner.learn_new_issue_alias(detail, raw_detail)
                    self.issue_map = ConfigManager.load_issue_map()
                    self.parser_engine.issue_map = self.issue_map

            # 4. 更新内存并重新生成路径
            item['parse_result']['std_cp'] = std_cp
            item['parse_result']['detail'] = detail
            item['parse_result']['confidence'] = 1.0

            target_path, target_name = self.file_processor.generate_target_path(item['parse_result'])
            item['parse_result']['target_filename'] = target_name
            item['parse_result']['target_full_path'] = target_path

            self.model.update_row(row, item['parse_result'])

        # 🔥🔥🔥 修复点 2: 冲突处理逻辑 🔥🔥🔥

    def execute_rename(self):
        # 1. 预扫描：获取所有绿色行的索引
        green_indices = []
        other_count = 0

        for i, item in enumerate(self.model.data_list):
            if item['parse_result'].get('status_color') == COLOR_GREEN:
                green_indices.append(i)
            else:
                other_count += 1

        # 2. 检查逻辑
        if not green_indices and other_count == 0:
            QMessageBox.information(self, "Info", "List is empty.")
            return

        if other_count > 0:
            reply = QMessageBox.warning(self, "Warning",
                                        f"⚠️ {other_count} items are NOT Ready.\nOnly {len(green_indices)} Green items will be processed.\n\nContinue?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No: return

        if not green_indices:
            QMessageBox.information(self, "Info", "No Green (Ready) items to process.")
            return

        reg_out = self.settings['last_session'].get('regular_output_dir')
        issue_out = self.settings['last_session'].get('issue_output_dir')
        if not reg_out and not issue_out:
            QMessageBox.warning(self, "Warning", "Please select output directories first!")
            return

        # 3. 开始处理
        success_count = 0
        errors = []
        collision_policy = 0

        # 🔥🔥🔥 记录需要删除的行号 🔥🔥🔥
        indices_to_remove = []

        for i in green_indices:
            task = self.model.data_list[i]
            src = task['original_path']
            dst = task.get('target_full_path')

            if not dst: continue

            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)

                # 冲突检测逻辑
                target_exists = os.path.exists(dst)
                should_copy = True
                final_dst = dst

                if target_exists:
                    action = collision_policy
                    if collision_policy == 0:
                        dialog = ConflictDialog(os.path.basename(src), dst, self)
                        if dialog.exec():
                            action = dialog.result_action
                            if dialog.apply_to_all:
                                collision_policy = action
                        else:
                            should_copy = False  # Cancelled

                    if action == 2:  # Skip
                        should_copy = False
                    elif action == 3:  # Keep Both
                        base, ext = os.path.splitext(dst)
                        counter = 1
                        while os.path.exists(final_dst):
                            final_dst = f"{base}_{counter}{ext}"
                            counter += 1

                # 执行复制
                if should_copy:
                    shutil.copy2(src, final_dst)
                    success_count += 1
                    # 🔥🔥🔥 复制成功，标记该行待删除 🔥🔥🔥
                    indices_to_remove.append(i)

            except Exception as e:
                errors.append(f"{os.path.basename(src)}: {str(e)}")

        # 4. 🔥🔥🔥 从表格中移除已处理的行 🔥🔥🔥
        if indices_to_remove:
            self.model.remove_rows_by_indices(indices_to_remove)

        # 5. 结果提示
        msg = f"Successfully processed {success_count} files."

        # 如果全部处理完了，提示更简洁
        if self.model.rowCount() == 0:
            msg += "\nAll tasks completed! List cleared."
        elif other_count > 0:
            msg += f"\n({other_count} items were skipped/failed)"

        if errors:
            msg += f"\n\n{len(errors)} Errors occurred."
            print("Errors:", errors)

        QMessageBox.information(self, "Done", msg)


# ... (上面是 MainWindow 类的所有代码) ...

# 🔥🔥🔥 请把这段代码放到文件的最末尾 (不要有缩进) 🔥🔥🔥

class ConflictDialog(QDialog):
    def __init__(self, filename, target_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("File Exists - Conflict Resolution")
        self.resize(500, 220)
        self.result_action = 2  # 默认 Skip
        self.apply_to_all = False

        layout = QVBoxLayout(self)

        # 提示信息
        info_label = QLabel(
            f"<h3>Target file already exists</h3>"
            f"<p><b>File:</b> {filename}</p>"
            f"<p style='color:#666'><b>Target:</b> {target_path}</p>"
            f"<p>What do you want to do?</p>"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # "应用到所有" 复选框
        self.chk_all = QCheckBox("Do this for all remaining conflicts")
        layout.addWidget(self.chk_all)

        layout.addSpacing(10)

        # 按钮组
        btn_layout = QHBoxLayout()

        btn_overwrite = QPushButton("Overwrite (覆盖)")
        btn_skip = QPushButton("Skip (跳过)")
        btn_keep = QPushButton("Keep Both (自动重命名)")

        # 设置默认建议
        btn_keep.setDefault(True)

        # 绑定点击事件：1=Overwrite, 2=Skip, 3=KeepBoth
        btn_overwrite.clicked.connect(lambda: self.done_action(1))
        btn_skip.clicked.connect(lambda: self.done_action(2))
        btn_keep.clicked.connect(lambda: self.done_action(3))

        btn_layout.addWidget(btn_overwrite)
        btn_layout.addWidget(btn_skip)
        btn_layout.addWidget(btn_keep)

        layout.addLayout(btn_layout)

    def done_action(self, action_code):
        self.result_action = action_code
        self.apply_to_all = self.chk_all.isChecked()
        self.accept()