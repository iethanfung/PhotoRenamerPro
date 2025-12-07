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
from src.utils.constants import COLOR_GREEN, COLOR_YELLOW, COLOR_ORANGE, COLOR_RED, SUPPORTED_IMAGE_FORMATS


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photo Renamer Pro")
        self.resize(1300, 800)
        self.setAcceptDrops(True)

        self.settings = ConfigManager.load_settings()
        self.cp_map = ConfigManager.load_cp_map()
        self.issue_map = ConfigManager.load_issue_map()
        self.orient_map = ConfigManager.load_orient_map()

        self.excel_engine = ExcelEngine()
        self.parser_engine = ParserEngine(self.excel_engine, self.settings, self.cp_map, self.issue_map,self.orient_map)
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
            self.btn_reg_dir.setText(f"📂 标准照输出路径: {os.path.basename(last_reg_out)}")
            self.btn_reg_dir.setToolTip(last_reg_out)  # 鼠标悬停显示全路径

        # 3. 恢复 Issue 输出路径
        last_issue_out = last_session.get('issue_output_dir')
        if last_issue_out and os.path.exists(last_issue_out):
            self.btn_issue_dir.setText(f"📂 失效照输出路径: {os.path.basename(last_issue_out)}")
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
        self.btn_excel = QPushButton("📄 导入机台信息CSV格式的文件")
        self.btn_excel.clicked.connect(self.browse_excel)
        self.btn_reg_dir = QPushButton("📂 选择标准照输出文件夹")
        self.btn_reg_dir.clicked.connect(lambda: self.browse_output('regular'))
        self.btn_issue_dir = QPushButton("📂 选择问题照输出文件夹")
        self.btn_issue_dir.clicked.connect(lambda: self.browse_output('issue'))

        for btn in [self.btn_excel, self.btn_reg_dir, self.btn_issue_dir]:
            btn.setObjectName("ConfigButton")
            left_layout.addWidget(btn)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        top_btns = QHBoxLayout()
        self.btn_settings = QPushButton("⚙️ 设置")
        self.btn_settings.clicked.connect(self.open_settings)
        self.btn_clear = QPushButton("🗑️ 清空列表")
        self.btn_clear.clicked.connect(self.clear_table)
        top_btns.addWidget(self.btn_settings)
        top_btns.addWidget(self.btn_clear)

        self.btn_start = QPushButton("▶ 开始重命名")
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
            # 🔥 重新加载 Orient Map
            self.orient_map = ConfigManager.load_orient_map()

            # 🔥 更新引擎引用
            self.parser_engine.settings = self.settings
            self.parser_engine.cp_map = self.cp_map
            self.parser_engine.issue_map = self.issue_map
            self.parser_engine.orient_map = self.orient_map

            self.file_processor.settings = self.settings
            
            # --- 🔥🔥🔥 修复点：检测路径变更并刷新 UI 🔥🔥🔥 ---
            last_session = self.settings.get('last_session', {})
            
            # 1. 检查 Excel 变更
            new_excel = last_session.get('excel_path')
            if new_excel and os.path.exists(new_excel):
                # 如果路径变了，或者当前没加载 Excel，则重新加载
                current_excel_text = self.btn_excel.toolTip()
                if new_excel != current_excel_text:
                    self.load_excel(new_excel)

            # 2. 检查 Regular Output 变更
            new_reg = last_session.get('regular_output_dir')
            if new_reg:
                self.btn_reg_dir.setText(f"📂 标准照输出路径: {os.path.basename(new_reg)}")
                self.btn_reg_dir.setToolTip(new_reg)

            # 3. 检查 Issue Output 变更
            new_issue = last_session.get('issue_output_dir')
            if new_issue:
                self.btn_issue_dir.setText(f"📂 失效照输出路径: {os.path.basename(new_issue)}")
                self.btn_issue_dir.setToolTip(new_issue)

            # 4. 刷新列表数据 (重新解析)
            self.refresh_list()
            
            self.status_bar.update_status(self.model.rowCount(), 0, "设置已重载，列表已刷新")

    def refresh_list(self):
        """
        当设置发生变化时（如非法字符、映射表等），
        重新遍历当前列表中的所有文件，使用新配置重新解析。
        """
        if self.model.rowCount() == 0:
            return
        
        updated_count = 0
        for i, item in enumerate(self.model.data_list):
            src_path = item['original_path']
            
            # 1. 重新解析
            new_res = self.parser_engine.parse_filename(src_path)
            
            # 2. 重新生成目标路径
            target_path, target_name = self.file_processor.generate_target_path(new_res)
            new_res['target_filename'] = target_name
            new_res['target_full_path'] = target_path
            
            # 3. 更新 Model
            self.model.update_row(i, new_res)
            updated_count += 1

        print(f"Refreshed {updated_count} items with new settings.")

    def browse_excel(self):
        # 🔥 修改点：过滤器改为 *.csv
        path, _ = QFileDialog.getOpenFileName(self, "选择机台信息CSV文件", "", "CSV Files (*.csv);;All Files (*)")
        if path:
            self.load_excel(path)
            self.settings['last_session']['excel_path'] = path
            ConfigManager.save_settings(self.settings)

    def load_excel(self, path):
        ok, msg = self.excel_engine.load_excel(path, self.settings['excel_header_map'])
        if ok:
            # 🔥 修改点：显示文本改为 CSV
            self.btn_excel.setText(f"📄 CSV: {os.path.basename(path)}")
            self.btn_excel.setToolTip(path)
            self.status_bar.update_status(0, 0, "CSV 已加载")
        else:
            QMessageBox.critical(self, "Error", msg)

    def browse_output(self, type_):
        title = "选择标准照输出文件夹" if type_ == 'regular' else "选择问题照输出文件夹"
        path = QFileDialog.getExistingDirectory(self, title)
        if path:
            key = f"{type_}_output_dir"
            self.settings['last_session'][key] = path
            ConfigManager.save_settings(self.settings)
            # 实时更新按钮文字
            if type_ == 'regular':
                self.btn_reg_dir.setText(f"📂 标准照输出路径: {os.path.basename(path)}")
                self.btn_reg_dir.setToolTip(path)
            else:
                self.btn_issue_dir.setText(f"📂 失效照输出路径: {os.path.basename(path)}")
                self.btn_issue_dir.setToolTip(path)

    def clear_table(self):
        self.model.clear_all()
        self.status_bar.update_status(0, 0, "列表已清空")

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
                        if f.lower().endswith(SUPPORTED_IMAGE_FORMATS):
                            files.append(os.path.join(root, f))
            elif path.lower().endswith(SUPPORTED_IMAGE_FORMATS):
                files.append(path)
        self.process_files(files)

    def process_files(self, file_paths):
        if not self.excel_engine.df is not None:
            QMessageBox.warning(self, "Warning", "请先加载CSV文件！")
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

        msg = f"已加载 {len(results)} 个文件"
        if skipped_count > 0:
            msg += f" (跳过 {skipped_count} 个重复项)"
        self.status_bar.update_status(self.model.rowCount(), 0, msg)

    @Slot(object, object)
    def on_data_changed(self, top_left, bottom_right):
        row = top_left.row()
        col = top_left.column()
        if col == self.model.COL_INDEX: return

        # 1. 物理重命名逻辑
        if col == self.model.COL_NAME:
            item = self.model.data_list[row]
            old_full_path = item['original_path']
            new_name = item['original_name']
            dir_name = os.path.dirname(old_full_path)
            new_full_path = os.path.join(dir_name, new_name)
            try:
                if not os.path.splitext(new_name)[1]:
                    _, old_ext = os.path.splitext(old_full_path)
                    new_full_path += old_ext
                    new_name += old_ext
                if os.path.exists(new_full_path): raise FileExistsError("File exists")
                os.rename(old_full_path, new_full_path)
                self.model.update_source_path(row, new_full_path)
                new_res = self.parser_engine.parse_filename(new_full_path)
                target_path, target_name = self.file_processor.generate_target_path(new_res)
                new_res['target_filename'] = target_name
                new_res['target_full_path'] = target_path
                self.model.update_row(row, new_res)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"重命名失败: {str(e)}")
                # 使用 blockSignals 防止无限循环
                self.model.blockSignals(True)
                self.model.data_list[row]['original_name'] = os.path.basename(old_full_path)
                self.model.dataChanged.emit(top_left, bottom_right)
                self.model.blockSignals(False)
            return

        # 2. 自学习与重算逻辑
        if col == self.model.COL_STD_CP or col == self.model.COL_DETAIL:
            item = self.model.data_list[row]
            raw_cp = item['parse_result']['raw_cp']
            raw_detail = item['parse_result'].get('raw_detail', '')
            test = item['parse_result']['unit_data'].get('Test', 'Unknown')

            # 获取用户修改后的值
            user_std_cp = item['parse_result']['std_cp']
            user_detail = item['parse_result']['detail']

            map_updated = False
            learning_failed = False  # 🔥🔥🔥 新增：追踪学习是否失败 🔥🔥🔥

            # A. CP 学习
            if col == self.model.COL_STD_CP:
                if user_std_cp and user_std_cp != "[Unknown CP]" and raw_cp:
                    success, msg = Learner.learn_new_cp_alias(test, user_std_cp, raw_cp)
                    if success:
                        map_updated = True
                    else:
                        learning_failed = True  # 🔥 标记学习失败
                        QMessageBox.critical(self, "Error", msg)

            # B. Detail 学习
            if col == self.model.COL_DETAIL:
                import re
                is_orient = re.match(r'(?i)^O\d+$', user_detail) or (user_detail in self.orient_map)
                if is_orient and raw_detail:
                    success, msg = Learner.learn_new_orient_alias(user_detail, raw_detail)
                    if success:
                        map_updated = True
                    else:
                        learning_failed = True  # 🔥 标记学习失败
                        QMessageBox.critical(self, "Error", msg)
                elif user_detail != "[Unknown]" and user_detail != "[Unknown Issue]" and raw_detail:
                    if user_detail and user_detail.strip():
                        success, msg = Learner.learn_new_issue_alias(user_detail, raw_detail)
                        if success:
                            map_updated = True
                        else:
                            learning_failed = True  # 🔥 标记学习失败
                            QMessageBox.critical(self, "Error", msg)

            # 🔥🔥🔥 新增：如果学习失败，需要回滚用户的修改 🔥🔥🔥
            if learning_failed:
                # 重新解析文件以恢复原值（因为setData已经修改了值）
                new_res = self.parser_engine.parse_filename(item['original_path'])
                
                # 重新生成路径
                target_path, target_name = self.file_processor.generate_target_path(new_res)
                new_res['target_filename'] = target_name
                new_res['target_full_path'] = target_path
                
                # 更新数据并刷新界面
                item['parse_result'] = new_res
                self.model.update_row(row, new_res)
                return  # 🔥 提前返回，不执行后续逻辑

            # 🔥🔥🔥 核心修改：重算与回填 🔥🔥🔥
            if map_updated:
                # 1. 重新加载 Map
                self.cp_map = ConfigManager.load_cp_map()
                self.issue_map = ConfigManager.load_issue_map()
                self.orient_map = ConfigManager.load_orient_map()
                self.parser_engine.cp_map = self.cp_map
                self.parser_engine.issue_map = self.issue_map
                self.parser_engine.orient_map = self.orient_map

                # 2. 重新解析
                new_res = self.parser_engine.parse_filename(item['original_path'])

                # 3. 校验：算法是否真的学会了？(检查重算结果是否匹配用户输入)
                # 如果匹配，说明置信度是真实的；如果不匹配，说明学漏了或者其他原因，强制覆盖
                if col == self.model.COL_STD_CP and new_res['std_cp'] != user_std_cp:
                    new_res['std_cp'] = user_std_cp
                    new_res['confidence'] = 1.0  # 算法没跟上，人工强制满分

                if col == self.model.COL_DETAIL and new_res['detail'] != user_detail:
                    new_res['detail'] = user_detail
                    new_res['confidence'] = 1.0

                item['parse_result'] = new_res

            else:
                # 如果没有触发学习（比如只是改了值但没法学），手动置 1.0
                item['parse_result']['confidence'] = 1.0
                item['parse_result']['status_color'] = COLOR_GREEN
                item['parse_result']['status_msg'] = "Ready"

            # 重新生成路径
            target_path, target_name = self.file_processor.generate_target_path(item['parse_result'])
            item['parse_result']['target_filename'] = target_name
            item['parse_result']['target_full_path'] = target_path

            self.model.update_row(row, item['parse_result'])
            
            # 🔥🔥🔥 新增：修改数据后重新排序 🔥🔥🔥
            self.model.resort_all()

    def execute_rename(self):
        green_indices = []
        other_count = 0
        for i, item in enumerate(self.model.data_list):
            if item['parse_result'].get('status_color') == COLOR_GREEN:
                green_indices.append(i)
            else:
                other_count += 1

        if not green_indices and other_count == 0:
            QMessageBox.information(self, "Info", "列表为空。")
            return

        if other_count > 0:
            reply = QMessageBox.warning(self, "Warning",
                                        f"⚠️ {other_count} 项未就绪。\n仅 {len(green_indices)} 个绿色项将被处理。\n\n是否继续？",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No: return

        if not green_indices:
            QMessageBox.information(self, "Info", "没有绿色（就绪）项可处理。")
            return

        reg_out = self.settings['last_session'].get('regular_output_dir')
        issue_out = self.settings['last_session'].get('issue_output_dir')
        if not reg_out and not issue_out:
            QMessageBox.warning(self, "Warning", "请先选择输出目录！")
            return

        success_count = 0
        errors = []
        collision_policy = 0
        indices_to_remove = []

        for i in green_indices:
            task = self.model.data_list[i]
            src = task['original_path']
            dst = task.get('target_full_path')
            if not dst: continue

            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if os.path.exists(dst):
                    final_dst = dst
                    action = collision_policy
                    if collision_policy == 0:
                        dialog = ConflictDialog(os.path.basename(src), dst, self)
                        if dialog.exec():
                            action = dialog.result_action
                            if dialog.apply_to_all: collision_policy = action
                        else:
                            continue

                    if action == 1:
                        shutil.copy2(src, final_dst)
                    elif action == 2:
                        pass
                    elif action == 3:
                        base, ext = os.path.splitext(dst)
                        counter = 1
                        while os.path.exists(final_dst):
                            final_dst = f"{base}_{counter}{ext}"
                            counter += 1
                        shutil.copy2(src, final_dst)
                    if action != 2:
                        success_count += 1
                        indices_to_remove.append(i)
                else:
                    shutil.copy2(src, dst)
                    success_count += 1
                    indices_to_remove.append(i)
            except Exception as e:
                errors.append(f"{os.path.basename(src)}: {str(e)}")

        if indices_to_remove:
            self.model.remove_rows_by_indices(indices_to_remove)

        msg = f"成功处理 {success_count} 个文件。"
        if self.model.rowCount() == 0:
            msg += "\n所有任务已完成！列表已清空。"
        elif other_count > 0:
            msg += f"\n({other_count} 项被跳过)"
        if errors:
            msg += f"\n\n{len(errors)} 个错误发生。"
            print("Errors:", errors)
        QMessageBox.information(self, "Done", msg)


class ConflictDialog(QDialog):
    def __init__(self, filename, target_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("文件已存在 - 冲突解决")
        self.resize(500, 220)
        self.result_action = 2  # 默认 Skip
        self.apply_to_all = False

        layout = QVBoxLayout(self)

        # 提示信息
        info_label = QLabel(
            f"<h3>目标文件已存在</h3>"
            f"<p><b>文件:</b> {filename}</p>"
            f"<p style='color:#666'><b>目标:</b> {target_path}</p>"
            f"<p>您希望怎么做？</p>"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # "应用到所有" 复选框
        self.chk_all = QCheckBox("对剩余冲突应用此操作")
        layout.addWidget(self.chk_all)

        layout.addSpacing(10)

        # 按钮组
        btn_layout = QHBoxLayout()

        btn_overwrite = QPushButton("覆盖")
        btn_skip = QPushButton("跳过")
        btn_keep = QPushButton("保留两者 (自动重命名)")

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