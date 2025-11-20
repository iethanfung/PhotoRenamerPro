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
            "序号", "原文件名", "Rel No", "原始CP/issue", "标准CP", "方向/issue",
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
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        item = self.data_list[row]

        if role == Qt.DisplayRole:
            if col == self.COL_INDEX: return str(row + 1)
            if col == self.COL_NAME: return item['original_name']
            if col == self.COL_REL: return item['parse_result']['rel_no']

            # 🔥🔥🔥 修改点：Issue 类型显示 "原始CP / 原始Issue" 🔥🔥🔥
            if col == self.COL_RAW_CP:
                res = item['parse_result']
                raw_cp = res.get('raw_cp', '')

                if res.get('type') == 'Issue':
                    raw_detail = res.get('raw_detail', '')
                    # 只有当 raw_detail 有值时才拼接，避免显示多余的 "/"
                    if raw_detail:
                        return f"{raw_cp} / {raw_detail}" if raw_cp else raw_detail

                return raw_cp

            if col == self.COL_STD_CP: return item['parse_result']['std_cp']
            # 注意：COL_DETAIL 显示的是标准化的 Issue 或 Orient，不是原始词
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

        if role == Qt.EditRole:
            if col == self.COL_STD_CP:
                return item['parse_result']['std_cp']
            if col == self.COL_DETAIL:
                return item['parse_result']['detail']

        if role == Qt.BackgroundRole:
            color_hex = item['parse_result'].get('status_color', '#FFFFFF')
            return QColor(color_hex)

        # 🔥🔥🔥 修复点：解决悬停冲突 🔥🔥🔥
        if role == Qt.ToolTipRole:
            # 1. 如果是【原文件名】列，返回 None (禁用系统 Tooltip)
            # 因为这一列我们会有自定义的图片+路径弹窗
            if col == self.COL_NAME:
                return None

            # 2. 其他路径类列：显示完整的绝对路径
            if col == self.COL_NEW_NAME or col == self.COL_FOLDER:
                return item.get('target_full_path', '')

            # 3. 其他列：显示单元格内容
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
            if col == self.COL_STD_CP:
                old_val = self.data_list[row]['parse_result']['std_cp']
            elif col == self.COL_DETAIL:
                old_val = self.data_list[row]['parse_result']['detail']

            if old_val == value: return False

            reply = QMessageBox.question(
                None, "确认修改",
                f"原值: 【{old_val}】\n\n新值: 【{value}】\n\n是否确认修改？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No: return False

            if col == self.COL_STD_CP:
                self.data_list[row]['parse_result']['std_cp'] = value
            elif col == self.COL_DETAIL:
                self.data_list[row]['parse_result']['detail'] = value

            self.dataChanged.emit(index, index, [Qt.DisplayRole])
            return True
        return False

    def flags(self, index):
        flags = super().flags(index)
        flags |= Qt.ItemIsEnabled | Qt.ItemIsSelectable
        col = index.column()
        if col == self.COL_STD_CP or col == self.COL_DETAIL:
            flags |= Qt.ItemIsEditable
        return flags

    # 🔥🔥🔥 修复点：新增查重方法 🔥🔥🔥
    def has_file(self, file_path):
        # 使用标准化路径进行比较，防止 c:\A.jpg 和 c:/A.jpg 被当成两个
        return os.path.normpath(file_path) in self.existing_paths

    def add_rows(self, parser_results):
        if not parser_results: return
        self.beginInsertRows(QModelIndex(), len(self.data_list), len(self.data_list) + len(parser_results) - 1)
        for res in parser_results:
            original_path = res['original']
            self.existing_paths.add(os.path.normpath(original_path))  # 记录路径

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
        # 🔥🔥🔥 必须添加这一行 🔥🔥🔥
        self.existing_paths.clear()
        self.endResetModel()

    def remove_rows_by_indices(self, rows):
        if not rows: return
        rows = sorted(list(set(rows)), reverse=True)
        for row in rows:
            # 🔥🔥🔥 添加这两行逻辑 🔥🔥🔥
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