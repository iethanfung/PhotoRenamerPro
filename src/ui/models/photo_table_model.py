from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMessageBox
import os
from src.utils.constants import COLOR_GREEN, COLOR_YELLOW, COLOR_ORANGE, COLOR_RED


class PhotoTableModel(QAbstractTableModel):
    # 列定义
    COL_INDEX = 0
    COL_NAME = 1
    COL_REL = 2
    COL_RAW_CP = 3
    COL_STD_CP = 4
    COL_DETAIL = 5
    COL_CONF = 6
    COL_STATUS = 7
    COL_NEW_NAME = 8
    COL_FOLDER = 9

    def __init__(self, parent=None):
        super().__init__(parent)
        self.headers = [
            "序号", "原文件名", "Rel No", "原始词", "标准节点 (CP)", "方向/问题描述",
            "置信度", "状态", "新文件名", "目标文件夹"
        ]
        self.data_list = []
        self.existing_paths = set()

    def rowCount(self, parent=QModelIndex()):
        return len(self.data_list)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def data(self, index, role):
        if not index.isValid(): return None
        row = index.row()
        col = index.column()
        item = self.data_list[row]

        if role == Qt.DisplayRole:
            if col == self.COL_INDEX: return str(row + 1)
            if col == self.COL_NAME: return item['original_name']
            if col == self.COL_REL: return item['parse_result']['rel_no']

            if col == self.COL_RAW_CP:
                res = item['parse_result']
                r_cp = res.get('raw_cp', '').strip()
                r_det = res.get('raw_detail', '').strip()
                display_str = ""
                if r_cp and r_det:
                    display_str = f"[{r_cp}@{r_det}]"
                elif r_cp:
                    display_str = f"[{r_cp}]"
                elif r_det:
                    display_str = f"[@{r_det}]"
                return display_str

            if col == self.COL_STD_CP: return item['parse_result']['std_cp']
            if col == self.COL_DETAIL: return item['parse_result']['detail']

            if col == self.COL_CONF:
                conf_val = f"{item['parse_result']['confidence']:.2f}"
                color = item['parse_result'].get('status_color')
                prefix = "🔴"
                if color == COLOR_GREEN:
                    prefix = "🟢"
                elif color == COLOR_YELLOW:
                    prefix = "🟡"
                elif color == COLOR_ORANGE:
                    prefix = "🟠"
                return f"{prefix} {conf_val}"

            if col == self.COL_STATUS: return item['parse_result']['status_msg']
            if col == self.COL_NEW_NAME: return item.get('target_filename', '')
            if col == self.COL_FOLDER:
                full_path = item.get('target_full_path', '')
                if full_path: return os.path.dirname(full_path)
                return ""

        # 编辑模式
        if role == Qt.EditRole:
            if col == self.COL_NAME: return item['original_name']  # 🔥 允许编辑文件名
            if col == self.COL_STD_CP: return item['parse_result']['std_cp']
            if col == self.COL_DETAIL: return item['parse_result']['detail']

        if role == Qt.BackgroundRole:
            color_hex = item['parse_result'].get('status_color', '#FFFFFF')
            return QColor(color_hex)

        if role == Qt.ToolTipRole:
            if col == self.COL_NAME: return None
            if col == self.COL_NEW_NAME or col == self.COL_FOLDER:
                return item.get('target_full_path', '')
            return self.data(index, Qt.DisplayRole)

        if role == Qt.TextAlignmentRole:
            if col in [self.COL_INDEX, self.COL_CONF, self.COL_STATUS]:
                return Qt.AlignCenter
            return Qt.AlignVCenter | Qt.AlignLeft
        return None

    def setData(self, index, value, role):
        if not index.isValid(): return False
        row = index.row()
        col = index.column()

        if role == Qt.EditRole:
            old_val = ""
            field_name = ""

            if col == self.COL_STD_CP:
                old_val = self.data_list[row]['parse_result']['std_cp']
                field_name = "标准节点"
            elif col == self.COL_DETAIL:
                old_val = self.data_list[row]['parse_result']['detail']
                field_name = "方向/问题"
            elif col == self.COL_NAME:  # 🔥 原文件名处理
                old_val = self.data_list[row]['original_name']
                field_name = "原文件名 (重命名源文件)"

            if old_val == value: return False
            if not value or not value.strip(): return False  # 不允许改为空

            # 确认弹窗
            msg = f"原值: 【{old_val}】\n新值: 【{value}】\n\n是否确认修改？"
            if col == self.COL_NAME:
                msg += "\n\n⚠️ 注意：这将直接修改硬盘上的源文件名！"

            reply = QMessageBox.question(None, f"修改 {field_name}", msg, QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)
            if reply == QMessageBox.No: return False

            # 更新内存数据
            if col == self.COL_STD_CP:
                self.data_list[row]['parse_result']['std_cp'] = value
            elif col == self.COL_DETAIL:
                self.data_list[row]['parse_result']['detail'] = value
            elif col == self.COL_NAME:
                self.data_list[row]['original_name'] = value

            self.dataChanged.emit(index, index, [Qt.DisplayRole])
            return True
        return False

    def flags(self, index):
        flags = super().flags(index)
        flags |= Qt.ItemIsEnabled | Qt.ItemIsSelectable
        col = index.column()
        # 🔥 开放 COL_NAME 的编辑权限
        if col in [self.COL_STD_CP, self.COL_DETAIL, self.COL_NAME]:
            flags |= Qt.ItemIsEditable
        return flags

    # 🔥🔥🔥 新增：更新源文件路径 (物理重命名成功后调用) 🔥🔥🔥
    def update_source_path(self, row, new_full_path):
        old_path = self.data_list[row]['original_path']

        # 1. 更新查重集合
        if os.path.normpath(old_path) in self.existing_paths:
            self.existing_paths.remove(os.path.normpath(old_path))
        self.existing_paths.add(os.path.normpath(new_full_path))

        # 2. 更新数据
        self.data_list[row]['original_path'] = new_full_path
        self.data_list[row]['original_name'] = os.path.basename(new_full_path)

        # 3. 刷新界面
        # 这里不需要 emit dataChanged，因为在 MainWindow 里会调用 update_row 刷新整行

    def has_file(self, file_path):
        return os.path.normpath(file_path) in self.existing_paths

    def add_rows(self, parser_results):
        if not parser_results: return
        self.beginInsertRows(QModelIndex(), len(self.data_list), len(self.data_list) + len(parser_results) - 1)
        for res in parser_results:
            original_path = res['original']
            self.existing_paths.add(os.path.normpath(original_path))
            self.data_list.append({
                'original_path': original_path,
                'original_name': os.path.basename(original_path),
                'parse_result': res,
                'target_filename': res.get('target_filename', ''),
                'target_full_path': res.get('target_full_path', '')
            })
        self.endInsertRows()

    def clear_all(self):
        if not self.data_list: return
        self.beginResetModel()
        self.data_list.clear()
        self.existing_paths.clear()
        self.endResetModel()

    def remove_rows_by_indices(self, rows):
        if not rows: return
        rows = sorted(list(set(rows)), reverse=True)
        for row in rows:
            path = self.data_list[row]['original_path']
            if os.path.normpath(path) in self.existing_paths:
                self.existing_paths.remove(os.path.normpath(path))
            self.beginRemoveRows(QModelIndex(), row, row)
            del self.data_list[row]
            self.endRemoveRows()

    def get_file_path(self, row):
        if 0 <= row < len(self.data_list):
            return self.data_list[row]['original_path']
        return None

    def update_row(self, row, new_parse_result):
        self.data_list[row]['parse_result'] = new_parse_result
        self.data_list[row]['target_filename'] = new_parse_result.get('target_filename', '')
        self.data_list[row]['target_full_path'] = new_parse_result.get('target_full_path', '')
        self.dataChanged.emit(self.index(row, 0), self.index(row, self.columnCount() - 1))