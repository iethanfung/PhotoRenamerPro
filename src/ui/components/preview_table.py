from PySide6.QtWidgets import QTableView, QHeaderView, QAbstractItemView
from PySide6.QtCore import Qt, Signal, QPoint
from src.ui.components.image_pop import ImagePop
from src.utils.image_loader import ImageLoader


class PreviewTable(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.pop = ImagePop(self)
        self.last_row = -1

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.verticalHeader().setVisible(False)

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Delete, Qt.Key_Backspace]:
            self.delete_selected_rows()
        else:
            super().keyPressEvent(event)

    def delete_selected_rows(self):
        selection = self.selectionModel().selectedRows()
        if not selection: return
        rows_to_delete = [index.row() for index in selection]
        if self.model():
            self.model().remove_rows_by_indices(rows_to_delete)

    def mouseMoveEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            row = index.row()

            # 🔥🔥🔥 修复点：只在“原文件名”列显示自定义弹窗 🔥🔥🔥
            # 注意：这里的列索引 1 对应 COL_NAME
            if index.column() == 1:
                if row != self.last_row:
                    model = self.model()
                    if hasattr(model, 'get_file_path'):
                        file_path = model.get_file_path(row)
                        if file_path:
                            pix = ImageLoader.load_thumbnail(file_path)
                            # 🔥 调用新方法，传入图片和路径 🔥
                            self.pop.set_content(pix, file_path)

                            global_pos = self.mapToGlobal(event.pos())
                            self.pop.move(global_pos + QPoint(20, 20))
                            self.pop.show()
                        else:
                            self.pop.hide()
                    self.last_row = row
            else:
                # 其他列隐藏图片弹窗（系统 Tooltip 会自动接管）
                self.pop.hide()
                self.last_row = -1
        else:
            self.pop.hide()
            self.last_row = -1

        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.pop.hide()
        super().leaveEvent(event)