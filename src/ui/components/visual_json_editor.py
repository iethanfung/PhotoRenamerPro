from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLabel, QMenu, QInputDialog, QMessageBox,
    QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QAction


class OrderedTreeWidget(QTreeWidget):
    """
    A QTreeWidget that supports Drag & Drop reordering and emits a signal when order changes.
    It also validates drops to prevent hierarchy violations (e.g. dropping a Root into a Root).
    """
    item_dropped = Signal()
    item_drop_failed = Signal()  # Emitted when a drop is invalid (to trigger a refresh/revert)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        # Enable ExtendedSelection for batch delete
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAnimated(True)  # Enable animations for smoother feel
        self.setIndentation(20) # Ensure indentation is visible

    def keyPressEvent(self, event):
        """
        Override keyPressEvent to support expand/collapse with arrow keys.
        Supports both single and multiple selection.
        Right arrow: expand selected items that have children
        Left arrow: collapse selected items (or move to parent if single item and no children/collapsed)
        """
        selected_items = self.selectedItems()
        
        if selected_items:
            if event.key() == Qt.Key_Right:
                # Right arrow: expand all selected items that have children
                expanded_any = False
                for item in selected_items:
                    if item.childCount() > 0 and not item.isExpanded():
                        item.setExpanded(True)
                        expanded_any = True
                
                if expanded_any:
                    event.accept()
                    return
                    
            elif event.key() == Qt.Key_Left:
                # Left arrow: collapse all selected items that are expanded
                # Special case: if only one item selected and it's collapsed/has no children, move to parent
                if len(selected_items) == 1:
                    item = selected_items[0]
                    if item.childCount() > 0 and item.isExpanded():
                        item.setExpanded(False)
                        event.accept()
                        return
                    else:
                        # If already collapsed or no children, move to parent
                        parent = item.parent()
                        if parent:
                            self.setCurrentItem(parent)
                            event.accept()
                            return
                else:
                    # Multiple items selected: collapse all that are expanded
                    collapsed_any = False
                    for item in selected_items:
                        if item.childCount() > 0 and item.isExpanded():
                            item.setExpanded(False)
                            collapsed_any = True
                    
                    if collapsed_any:
                        event.accept()
                        return
        
        # For all other cases, use default behavior
        super().keyPressEvent(event)

    def dragMoveEvent(self, event):
        """
        Override dragMoveEvent to control the drop indicator and validity.
        """
        item = self.itemAt(event.position().toPoint())
        if not item:
            event.ignore()
            return

        # Get the item being dragged
        selected_items = self.selectedItems()
        if not selected_items:
            event.ignore()
            return
        
        # For Drag & Drop, we currently only support dragging ONE item at a time for simplicity
        # If multiple are selected, we might want to disable drag or just drag the first one.
        # Let's just drag the first one for now to avoid complex logic of moving multiple items
        dragged_item = selected_items[0]
        dragged_role = dragged_item.data(0, Qt.UserRole)
        
        target_role = item.data(0, Qt.UserRole)
        
        # Call super to let Qt calculate the proposed action
        super().dragMoveEvent(event)
        
        indicator = self.dropIndicatorPosition()
        
        is_valid = False
        
        if dragged_role == "root":
            if target_role == "root":
                # Allow dropping anywhere on a root (On/Above/Below)
                # We will strictly interpret this as Reorder in dropEvent
                is_valid = True 
            else:
                is_valid = False # Cannot drop root onto/between children
                
        elif dragged_role == "sub_root":
            if target_role == "root":
                if indicator == QAbstractItemView.OnItem:
                    is_valid = True
                else:
                    is_valid = False
            elif target_role == "sub_root":
                if indicator == QAbstractItemView.OnItem:
                    is_valid = False 
                else:
                    is_valid = True
            else:
                is_valid = False

        elif dragged_role == "alias":
            if target_role == "alias":
                if indicator == QAbstractItemView.OnItem:
                    is_valid = False 
                else:
                    is_valid = True 
            elif target_role in ("root", "sub_root"):
                if indicator == QAbstractItemView.OnItem:
                    is_valid = True 
                else:
                    is_valid = False

        if not is_valid:
            event.ignore()
        else:
            event.accept()

    def dropEvent(self, event):
        if event.source() != self:
            event.ignore()
            return

        item = self.itemAt(event.position().toPoint())
        selected_items = self.selectedItems()
        
        if item and selected_items:
            # Only handle the first item for drag & drop logic
            dragged_item = selected_items[0]
            dragged_role = dragged_item.data(0, Qt.UserRole)
            target_role = item.data(0, Qt.UserRole)
            
            # CRITICAL FIX: Strictly handle Root-on-Root drops manually
            # This prevents ANY chance of nesting, regardless of what indicator Qt showed
            if dragged_role == "root" and target_role == "root":
                # Determine insertion based on mouse position relative to target center
                target_rect = self.visualItemRect(item)
                mouse_y = event.position().y()
                center_y = target_rect.y() + target_rect.height() / 2
                
                insert_above = mouse_y < center_y
                
                # Perform manual move
                dragged_index = self.indexOfTopLevelItem(dragged_item)
                target_index = self.indexOfTopLevelItem(item)
                
                # If dropping on itself, do nothing
                if dragged_item == item:
                    event.ignore()
                    return

                # Remove dragged item
                self.takeTopLevelItem(dragged_index)
                
                # Adjust target index if dragged item was above target
                # (Because removing it shifted indices)
                if dragged_index < target_index:
                    target_index -= 1
                
                # Insert at new position
                new_index = target_index if insert_above else target_index + 1
                self.insertTopLevelItem(new_index, dragged_item)
                
                # Select it again
                self.setCurrentItem(dragged_item)
                
                self.item_dropped.emit()
                return

        # For all other cases (Alias moves, Sub-root moves), let Qt handle it
        # But we must be careful: Qt might still try to nest if we are not careful.
        # Since dragMoveEvent filtered invalid moves, we trust super() for non-Root-on-Root cases.
        super().dropEvent(event)
        self.item_dropped.emit()


class VisualJsonEditor(QWidget):
    def __init__(self, data, mode='flat', parent=None):
        super().__init__(parent)
        self.data = data  # Reference to the dictionary
        self.mode = mode
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)

        top_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索标准词或别名...")
        self.search_input.textChanged.connect(self.on_search_changed)

        self.btn_add_root = QPushButton("➕ 批量新增分类/标准词")
        self.btn_add_root.clicked.connect(self.add_root_item)

        top_bar.addWidget(self.search_input)
        top_bar.addWidget(self.btn_add_root)
        layout.addLayout(top_bar)

        # Use our custom OrderedTreeWidget
        self.tree = OrderedTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)
        self.tree.itemDoubleClicked.connect(self.on_double_click)
        
        # Connect drop signals
        self.tree.item_dropped.connect(self.sync_data_from_tree)
        self.tree.item_drop_failed.connect(self.refresh_tree)

        layout.addWidget(self.tree)

        hint = QLabel("提示：支持拖拽排序。支持多选删除。新增时可输入多行进行批量添加。")
        hint.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(hint)

        self.refresh_tree()

    def refresh_tree(self):
        # Save current expansion state? (Optional, but expandAll is used currently)
        # Save current selection?
        
        self.tree.clear()
        # Block signals to prevent unnecessary syncs during population (though sync is triggered by drop)
        
        for key, value in self.data.items():
            root_item = QTreeWidgetItem(self.tree)
            root_item.setText(0, key)
            f = root_item.font(0)
            f.setBold(True)
            root_item.setFont(0, f)
            root_item.setData(0, Qt.UserRole, "root")
            # Prevent dropping *on* items to force dropping *between* items (for reordering)
            # However, we need to drop *on* a root to add an alias via drag? 
            # No, usually we drag aliases.
            # If we disable DropEnabled, we can only reorder siblings.
            # Let's try NOT disabling it first, relying on our validation logic.
            # root_item.setFlags(root_item.flags() & ~Qt.ItemIsDropEnabled) 

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
        
        # Don't expand all by default - let user expand what they need
        # self.tree.expandAll()
        self.tree.collapseAll()
        
        # Restore search filter
        current_search = self.search_input.text().strip()
        if current_search:
            self.filter_tree(current_search)

    def on_search_changed(self, text):
        self.filter_tree(text)

    def filter_tree(self, text):
        text = text.lower()
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            self._filter_recursive(item, text, parent_matches=False)

    def _filter_recursive(self, item, text, parent_matches):
        self_matches = text in item.text(0).lower()
        force_show_children = parent_matches or self_matches
        
        any_child_visible = False
        for i in range(item.childCount()):
            child = item.child(i)
            child_visible = self._filter_recursive(child, text, parent_matches=force_show_children)
            if child_visible:
                any_child_visible = True

        should_show = parent_matches or self_matches or any_child_visible
        item.setHidden(not should_show)
        if should_show:
            item.setExpanded(True)
        return should_show

    def sync_data_from_tree(self):
        """Rebuild self.data based on the visual order in the tree."""
        new_data = {}
        root = self.tree.invisibleRootItem()
        
        for i in range(root.childCount()):
            root_item = root.child(i)
            key = root_item.text(0)
            
            if self.mode == 'flat':
                aliases = []
                for j in range(root_item.childCount()):
                    aliases.append(root_item.child(j).text(0))
                new_data[key] = aliases
            
            elif self.mode == 'nested':
                sub_dict = {}
                for j in range(root_item.childCount()):
                    sub_item = root_item.child(j)
                    sub_key = sub_item.text(0)
                    sub_aliases = []
                    for k in range(sub_item.childCount()):
                        sub_aliases.append(sub_item.child(k).text(0))
                    sub_dict[sub_key] = sub_aliases
                new_data[key] = sub_dict
        
        # Update self.data in-place to preserve reference
        self.data.clear()
        self.data.update(new_data)
        
        # We don't call refresh_tree() here because the tree is already visually correct (that's why we synced)
        # But we might want to re-apply filter if search is active?
        # If we just moved items, the filter state might be weird if we moved hidden items?
        # But usually drag-drop is done when filter is clear or on visible items.
        # If filter is active, drag-drop might be confusing. 
        # For now, let's leave it.

    def _rename_key_in_dict(self, data, old_key, new_key):
        """Rename a key in a dictionary while preserving insertion order."""
        if old_key == new_key:
            return data
        if new_key in data:
            return data # Should have been checked before
            
        new_data = {}
        for k, v in data.items():
            if k == old_key:
                new_data[new_key] = v
            else:
                new_data[k] = v
        return new_data

    def open_context_menu(self, position):
        item = self.tree.itemAt(position)
        # If no item is clicked, maybe show a global menu?
        # But for now let's stick to item context menu
        if not item: return
        
        # Check if multiple items are selected
        selected_items = self.tree.selectedItems()
        if len(selected_items) > 1:
            # Multi-selection menu
            menu = QMenu()
            menu.addAction("🗑️ 批量删除选中项", lambda: self.delete_selected_items())
            menu.exec(self.tree.viewport().mapToGlobal(position))
            return

        role = item.data(0, Qt.UserRole)
        menu = QMenu()

        if role == "root":
            if self.mode == 'nested':
                menu.addAction("➕ 批量添加标准节点 (CP)", lambda: self.add_sub_root(item))
            else:
                menu.addAction("➕ 批量添加别名 (Alias)", lambda: self.add_alias(item))
            menu.addSeparator()
            menu.addAction("✏️ 重命名", lambda: self.edit_item(item))
            menu.addAction("🗑️ 删除此分类", lambda: self.delete_item(item))
        elif role == "sub_root":
            menu.addAction("➕ 批量添加别名 (Alias)", lambda: self.add_alias(item))
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
        text, ok = QInputDialog.getMultiLineText(self, "批量新增", f"请输入{title} (每行一个):")
        if ok and text.strip():
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            added_count = 0
            for key in lines:
                if key in self.data:
                    continue # Skip duplicates
                if self.mode == 'nested':
                    self.data[key] = {}
                else:
                    self.data[key] = []
                added_count += 1
            
            if added_count > 0:
                self.refresh_tree()
                # Scroll to the last added item?
                items = self.tree.findItems(lines[-1], Qt.MatchExactly)
                if items: self.tree.scrollToItem(items[0])
            else:
                if len(lines) > 0:
                    QMessageBox.warning(self, "Info", "所有输入的名称均已存在。")

    def add_sub_root(self, parent_item):
        test_name = parent_item.text(0)
        text, ok = QInputDialog.getMultiLineText(self, "批量新增节点", f"在 [{test_name}] 下新增标准节点 (Standard CP) (每行一个):")
        if ok and text.strip():
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            added_count = 0
            for cp_key in lines:
                if cp_key in self.data[test_name]:
                    continue
                self.data[test_name][cp_key] = []
                added_count += 1
            
            if added_count > 0:
                self.refresh_tree()
                parent_item.setExpanded(True)

    def add_alias(self, parent_item):
        std_name = parent_item.text(0)
        text, ok = QInputDialog.getMultiLineText(self, "批量新增别名", f"为 [{std_name}] 添加别名 (Alias) (每行一个):")
        if ok and text.strip():
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            target_list = None
            if self.mode == 'flat':
                target_list = self.data[std_name]
            else:
                test_name = parent_item.parent().text(0)
                target_list = self.data[test_name][std_name]
            
            added_count = 0
            for alias in lines:
                if alias in target_list:
                    continue
                target_list.append(alias)
                added_count += 1
            
            if added_count > 0:
                self.refresh_tree()
                parent_item.setExpanded(True)

    def edit_item(self, item):
        old_text = item.text(0)
        role = item.data(0, Qt.UserRole)
        text, ok = QInputDialog.getText(self, "编辑", "修改名称:", text=old_text)
        if ok and text.strip() and text.strip() != old_text:
            new_text = text.strip()
            
            if role == "alias":
                # Alias rename: just update list, order in list matters
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
                # Sub-root rename: Use _rename_key_in_dict
                test_key = item.parent().text(0)
                sub_dict = self.data[test_key]
                if new_text in sub_dict:
                     QMessageBox.warning(self, "Error", "该名称已存在！")
                     return
                
                new_sub_dict = self._rename_key_in_dict(sub_dict, old_text, new_text)
                self.data[test_key].clear()
                self.data[test_key].update(new_sub_dict)
                
            elif role == "root":
                # Root rename: Use _rename_key_in_dict
                if new_text in self.data:
                    QMessageBox.warning(self, "Error", "该名称已存在！")
                    return
                
                new_data = self._rename_key_in_dict(self.data, old_text, new_text)
                self.data.clear()
                self.data.update(new_data)

            self.refresh_tree()

    def delete_item(self, item):
        # Single item delete (kept for context menu on single item)
        name = item.text(0)
        role = item.data(0, Qt.UserRole)
        reply = QMessageBox.question(self, "确认删除", f"确定要删除 '{name}' 吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No: return

        self._perform_delete(item)
        self.refresh_tree()

    def delete_selected_items(self):
        selected_items = self.tree.selectedItems()
        if not selected_items: return

        count = len(selected_items)
        reply = QMessageBox.question(self, "确认批量删除", f"确定要删除选中的 {count} 个项目吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No: return

        # We need to be careful about deleting items. 
        # If we delete a parent, its children are gone too. 
        # If we selected both parent and child, we might try to delete child twice or crash.
        # Strategy: Sort items by depth (deepest first) or just handle errors.
        # Better: Filter out items whose ancestors are also selected.
        
        # 1. Identify items to delete
        items_to_delete = []
        for item in selected_items:
            # Check if any ancestor is also selected
            parent = item.parent()
            is_ancestor_selected = False
            while parent:
                if parent in selected_items:
                    is_ancestor_selected = True
                    break
                parent = parent.parent()
            
            if not is_ancestor_selected:
                items_to_delete.append(item)

        # 2. Delete them
        for item in items_to_delete:
            self._perform_delete(item)
        
        self.refresh_tree()

    def _perform_delete(self, item):
        """Helper to delete a single item from data structure."""
        name = item.text(0)
        role = item.data(0, Qt.UserRole)
        
        try:
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
                if name in self.data[test_key]:
                    del self.data[test_key][name]
            elif role == "root":
                if name in self.data:
                    del self.data[name]
        except KeyError:
            pass # Already deleted?