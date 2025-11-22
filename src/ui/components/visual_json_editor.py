from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLabel, QMenu, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QAction


class VisualJsonEditor(QWidget):
    def __init__(self, data, mode='flat', parent=None):
        super().__init__(parent)
        self.data = data  # 引用传递
        self.mode = mode
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)

        top_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索标准词或别名...")
        self.search_input.textChanged.connect(self.filter_tree)

        self.btn_add_root = QPushButton("➕ 新增分类/标准词")
        self.btn_add_root.clicked.connect(self.add_root_item)

        top_bar.addWidget(self.search_input)
        top_bar.addWidget(self.btn_add_root)
        layout.addLayout(top_bar)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)
        self.tree.itemDoubleClicked.connect(self.on_double_click)

        layout.addWidget(self.tree)

        hint = QLabel("提示：右键点击条目进行添加别名、重命名或删除操作。双击可快速编辑。")
        hint.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(hint)

        self.refresh_tree()

    def refresh_tree(self):
        self.tree.clear()
        for key, value in self.data.items():
            root_item = QTreeWidgetItem(self.tree)
            root_item.setText(0, key)
            f = root_item.font(0)
            f.setBold(True)
            root_item.setFont(0, f)
            root_item.setData(0, Qt.UserRole, "root")

            if self.mode == 'flat':
                for alias in value:
                    child = QTreeWidgetItem(root_item)
                    child.setText(0, alias)
                    child.setData(0, Qt.UserRole, "alias")
            elif self.mode == 'nested':
                root_item.setIcon(0, QIcon())
                for sub_key, sub_value in value.items():
                    sub_item = QTreeWidgetItem(root_item)
                    sub_item.setText(0, sub_key)
                    sub_item.setFont(0, f)
                    sub_item.setData(0, Qt.UserRole, "sub_root")
                    for alias in sub_value:
                        leaf = QTreeWidgetItem(sub_item)
                        leaf.setText(0, alias)
                        leaf.setData(0, Qt.UserRole, "alias")
        self.tree.expandAll()

    def filter_tree(self, text):
        text = text.lower()
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            self._filter_recursive(item, text)

    def _filter_recursive(self, item, text):
        match = text in item.text(0).lower()
        child_match = False
        for i in range(item.childCount()):
            if self._filter_recursive(item.child(i), text):
                child_match = True
        should_show = match or child_match
        item.setHidden(not should_show)
        if should_show: item.setExpanded(True)
        return should_show

    def open_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item: return
        role = item.data(0, Qt.UserRole)
        menu = QMenu()

        if role == "root":
            if self.mode == 'nested':
                menu.addAction("➕ 添加标准节点 (CP)", lambda: self.add_sub_root(item))
            else:
                menu.addAction("➕ 添加别名 (Alias)", lambda: self.add_alias(item))
            menu.addSeparator()
            menu.addAction("✏️ 重命名", lambda: self.edit_item(item))
            menu.addAction("🗑️ 删除此分类", lambda: self.delete_item(item))
        elif role == "sub_root":
            menu.addAction("➕ 添加别名 (Alias)", lambda: self.add_alias(item))
            menu.addSeparator()
            menu.addAction("✏️ 重命名", lambda: self.edit_item(item))
            menu.addAction("🗑️ 删除此节点", lambda: self.delete_item(item))
        elif role == "alias":
            menu.addAction("✏️ 修改别名", lambda: self.edit_item(item))
            menu.addAction("🗑️ 删除别名", lambda: self.delete_item(item))
        menu.exec(self.tree.viewport().mapToGlobal(position))

    def on_double_click(self, item, column):
        self.edit_item(item)

    def add_root_item(self):
        title = "新增测试项目 (Test)" if self.mode == 'nested' else "新增标准名称 (Key)"
        text, ok = QInputDialog.getText(self, "新增", f"请输入{title}:")
        if ok and text.strip():
            key = text.strip()
            if key in self.data:
                QMessageBox.warning(self, "Error", "该名称已存在！")
                return
            if self.mode == 'nested':
                self.data[key] = {}
            else:
                self.data[key] = []
            self.refresh_tree()
            items = self.tree.findItems(key, Qt.MatchExactly)
            if items: self.tree.scrollToItem(items[0])

    def add_sub_root(self, parent_item):
        test_name = parent_item.text(0)
        text, ok = QInputDialog.getText(self, "新增节点", f"在 [{test_name}] 下新增标准节点 (Standard CP):")
        if ok and text.strip():
            cp_key = text.strip()
            if cp_key in self.data[test_name]:
                QMessageBox.warning(self, "Error", "该节点已存在！")
                return
            self.data[test_name][cp_key] = []
            self.refresh_tree()

    def add_alias(self, parent_item):
        std_name = parent_item.text(0)
        text, ok = QInputDialog.getText(self, "新增别名", f"为 [{std_name}] 添加别名 (Alias):")
        if ok and text.strip():
            alias = text.strip()
            target_list = None
            if self.mode == 'flat':
                target_list = self.data[std_name]
            else:
                test_name = parent_item.parent().text(0)
                target_list = self.data[test_name][std_name]
            if alias in target_list:
                QMessageBox.warning(self, "Info", "该别名已存在。")
                return
            target_list.append(alias)
            self.refresh_tree()

    def edit_item(self, item):
        old_text = item.text(0)
        role = item.data(0, Qt.UserRole)
        text, ok = QInputDialog.getText(self, "编辑", "修改名称:", text=old_text)
        if ok and text.strip() and text.strip() != old_text:
            new_text = text.strip()
            if role == "alias":
                parent = item.parent()
                std_key = parent.text(0)
                target_list = None
                if self.mode == 'flat':
                    target_list = self.data[std_key]
                else:
                    test_key = parent.parent().text(0)
                    target_list = self.data[test_key][std_key]
                if old_text in target_list:
                    idx = target_list.index(old_text)
                    target_list[idx] = new_text
            elif role == "sub_root":
                test_key = item.parent().text(0)
                val = self.data[test_key].pop(old_text)
                self.data[test_key][new_text] = val
            elif role == "root":
                val = self.data.pop(old_text)
                self.data[new_text] = val
            self.refresh_tree()

    def delete_item(self, item):
        name = item.text(0)
        role = item.data(0, Qt.UserRole)
        reply = QMessageBox.question(self, "确认删除", f"确定要删除 '{name}' 吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No: return

        if role == "alias":
            parent = item.parent()
            std_key = parent.text(0)
            target_list = None
            if self.mode == 'flat':
                target_list = self.data[std_key]
            else:
                test_key = parent.parent().text(0)
                target_list = self.data[test_key][std_key]
            if name in target_list: target_list.remove(name)
        elif role == "sub_root":
            test_key = item.parent().text(0)
            del self.data[test_key][name]
        elif role == "root":
            del self.data[name]
        self.refresh_tree()