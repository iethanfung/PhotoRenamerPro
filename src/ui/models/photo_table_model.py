from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMessageBox  # 🔥 新增引用
import os


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
            if col == self.COL_RAW_CP: return item['parse_result']['raw_cp']

            if col == self.COL_STD_CP: return item['parse_result']['std_cp']
            if col == self.COL_DETAIL: return item['parse_result']['detail']

            if col == self.COL_CONF: return f"{item['parse_result']['confidence']:.1f}"
            if col == self.COL_STATUS: return item['parse_result']['status_msg']
            if col == self.COL_NEW_NAME: return item.get('target_filename', '')
            if col == self.COL_FOLDER:
                full_path = item.get('target_full_path', '')
                if full_path: return os.path.dirname(full_path)
                return ""

        # 🔥🔥🔥 修复点 1: 编辑时始终显示原始值 (不再显示空白) 🔥🔥🔥
        if role == Qt.EditRole:
            if col == self.COL_STD_CP:
                return item['parse_result']['std_cp']
            if col == self.COL_DETAIL:
                return item['parse_result']['detail']

        if role == Qt.BackgroundRole:
            color_hex = item['parse_result'].get('status_color', '#FFFFFF')
            return QColor(color_hex)

        if role == Qt.TextAlignmentRole:
            if col in [self.COL_INDEX, self.COL_CONF, self.COL_STATUS]:
                return Qt.AlignCenter
            return Qt.AlignVCenter | Qt.AlignLeft

        return None

    def setData(self, index, value, role):
        if not index.isValid():
            return False

        row = index.row()
        col = index.column()

        if role == Qt.EditRole:
            # 获取旧值
            old_val = ""
            if col == self.COL_STD_CP:
                old_val = self.data_list[row]['parse_result']['std_cp']
            elif col == self.COL_DETAIL:
                old_val = self.data_list[row]['parse_result']['detail']

            # 如果值没变，直接忽略，不弹窗
            if old_val == value:
                return False

            # 🔥🔥🔥 修复点 2: 增加确认弹窗 🔥🔥🔥
            # 注意：parent=None 意味着这是一个顶层弹窗
            reply = QMessageBox.question(
                None,
                "确认修改",
                f"原值: 【{old_val}】\n\n新值: 【{value}】\n\n是否确认修改？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No  # 默认选中 No，防止手抖
            )

            if reply == QMessageBox.No:
                return False  # 返回 False，View 会保持原值不变

            # 用户点击 Yes，执行更新
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

    def add_rows(self, parser_results):
        if not parser_results: return
        self.beginInsertRows(QModelIndex(), len(self.data_list), len(self.data_list) + len(parser_results) - 1)
        for res in parser_results:
            self.data_list.append({
                'original_path': res['original'],
                'original_name': os.path.basename(res['original']),
                'parse_result': res,
                'target_filename': res.get('target_filename', ''),
                'target_full_path': res.get('target_full_path', '')
            })
        self.endInsertRows()

    def clear_all(self):
        if not self.data_list: return
        self.beginResetModel()
        self.data_list.clear()
        self.endResetModel()

    def remove_rows_by_indices(self, rows):
        if not rows: return
        rows = sorted(list(set(rows)), reverse=True)
        for row in rows:
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