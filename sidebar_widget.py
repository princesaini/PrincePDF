"""
PrincePDF - Collapsible Sidebar Widget
Contains:
1. Page Thumbnails: Visual preview gallery for fast jumping
2. Document Outline: Table of contents tree
3. Search Results: Global search hits with snippets
"""

from typing import List, Dict, Any, Optional
import fitz
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QListWidget,
    QListWidgetItem, QTreeWidget, QTreeWidgetItem, QLabel,
    QPushButton, QFrame, QScrollArea
)


class ThumbnailItemWidget(QWidget):
    """Individual thumbnail card in the sidebar."""
    def __init__(self, page_num: int, parent=None):
        super().__init__(parent)
        self.page_num = page_num

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid #3a3f4d; border-radius: 4px; background: #2c303c;")
        layout.addWidget(self.image_label)

        self.num_label = QLabel(f"Page {page_num + 1}", self)
        self.num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.num_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(self.num_label)

    def set_pixmap(self, pixmap: QPixmap):
        self.image_label.setPixmap(pixmap)

    def set_active(self, active: bool):
        if active:
            self.image_label.setStyleSheet("border: 2px solid #3b82f6; border-radius: 4px; background: #2c303c;")
            self.num_label.setStyleSheet("color: #3b82f6; font-size: 11px; font-weight: bold;")
        else:
            self.image_label.setStyleSheet("border: 1px solid #3a3f4d; border-radius: 4px; background: #2c303c;")
            self.num_label.setStyleSheet("color: #94a3b8; font-size: 11px;")


class SidebarWidget(QWidget):
    pageSelected = pyqtSignal(int)
    searchResultSelected = pyqtSignal(int, fitz.Rect)

    def __init__(self, doc_model, render_cache, parent=None):
        super().__init__(parent)
        self.doc_model = doc_model
        self.render_cache = render_cache

        self.setMinimumWidth(220)
        self.setMaximumWidth(320)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Tab Widget
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setDocumentMode(True)
        main_layout.addWidget(self.tab_widget)

        # 1. Thumbnails Tab
        self.thumb_list = QListWidget(self)
        self.thumb_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.thumb_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.thumb_list.itemClicked.connect(self._on_thumb_clicked)
        self.tab_widget.addTab(self.thumb_list, "Pages")

        # 2. Outline / Bookmarks Tab
        self.outline_tree = QTreeWidget(self)
        self.outline_tree.setHeaderHidden(True)
        self.outline_tree.itemClicked.connect(self._on_outline_item_clicked)
        self.tab_widget.addTab(self.outline_tree, "Outline")

        # 3. Search Results Tab
        self.search_list = QListWidget(self)
        self.search_list.itemClicked.connect(self._on_search_item_clicked)
        self.tab_widget.addTab(self.search_list, "Search")

        self.current_page: int = 0
        self._thumbnail_widgets: List[ThumbnailItemWidget] = []

        self._apply_styling(is_dark=True)

    def _apply_styling(self, is_dark: bool):
        bg = "#1b1d23" if is_dark else "#f6f8fa"
        surface = "#242730" if is_dark else "#ffffff"
        border = "#3a3f4d" if is_dark else "#d0d7de"
        text = "#f1f5f9" if is_dark else "#1f2328"
        accent = "#3b82f6"
        tab_bg = "#20232c" if is_dark else "#eef1f4"

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg};
                color: {text};
            }}
            QTabWidget::pane {{
                border: none;
                background-color: {surface};
            }}
            QTabBar::tab {{
                background-color: {tab_bg};
                color: {text};
                padding: 8px 16px;
                border: none;
                border-bottom: 2px solid transparent;
                font-weight: 500;
                font-size: 12px;
            }}
            QTabBar::tab:selected {{
                background-color: {surface};
                border-bottom: 2px solid {accent};
                font-weight: bold;
            }}
            QTabBar::tab:hover {{
                background-color: {surface};
            }}
            QListWidget, QTreeWidget {{
                background-color: {surface};
                border: none;
                outline: none;
            }}
            QListWidget::item:hover, QTreeWidget::item:hover {{
                background-color: {tab_bg};
            }}
            QListWidget::item:selected, QTreeWidget::item:selected {{
                background-color: {accent};
                color: #ffffff;
            }}
        """)

    def set_theme(self, is_dark: bool):
        self._apply_styling(is_dark)

    # -------------------------------------------------------------------------
    # Document Loading
    # -------------------------------------------------------------------------
    def load_document(self):
        self.clear()
        if not self.doc_model.is_open:
            return

        self._build_thumbnails()
        self._build_outline()

    def clear(self):
        self.thumb_list.clear()
        self.outline_tree.clear()
        self.search_list.clear()
        self._thumbnail_widgets.clear()
        self.current_page = 0

    # -------------------------------------------------------------------------
    # Thumbnails
    # -------------------------------------------------------------------------
    def _build_thumbnails(self):
        self.thumb_list.clear()
        self._thumbnail_widgets.clear()
        dpr = self.devicePixelRatioF()

        for p_idx in range(self.doc_model.page_count):
            item = QListWidgetItem(self.thumb_list)
            card = ThumbnailItemWidget(p_idx, self)
            
            # Render thumbnail pixmap
            pixmap = self.render_cache.get_thumbnail(self.doc_model, p_idx, max_width=130, dpr=dpr)
            if pixmap:
                card.set_pixmap(pixmap)

            # Compute size hint based on aspect ratio
            w, h = self.doc_model.get_page_size(p_idx)
            ratio = h / max(1.0, w)
            card_h = int(130 * ratio) + 34
            item.setSizeHint(QSize(160, card_h))

            self.thumb_list.addItem(item)
            self.thumb_list.setItemWidget(item, card)
            self._thumbnail_widgets.append(card)

        self.highlight_page(0)

    def highlight_page(self, page_num: int):
        self.current_page = page_num
        for idx, card in enumerate(self._thumbnail_widgets):
            card.set_active(idx == page_num)

        if 0 <= page_num < self.thumb_list.count():
            item = self.thumb_list.item(page_num)
            self.thumb_list.scrollToItem(item)

    def _on_thumb_clicked(self, item: QListWidgetItem):
        row = self.thumb_list.row(item)
        if row >= 0:
            self.pageSelected.emit(row)

    # -------------------------------------------------------------------------
    # Outline / Bookmarks
    # -------------------------------------------------------------------------
    def _build_outline(self):
        self.outline_tree.clear()
        toc = self.doc_model.get_toc()

        if not toc:
            root = QTreeWidgetItem(["No table of contents available"])
            root.setForeground(0, QColor("#94a3b8"))
            self.outline_tree.addTopLevelItem(root)
            return

        # Stack to track hierarchy by level: [(level, item)]
        stack: List[tuple] = []

        for entry in toc:
            # entry is [level, title, page_number, ...]
            level = entry[0]
            title = entry[1]
            page_num = entry[2] - 1  # 1-indexed to 0-indexed

            item = QTreeWidgetItem([f"{title} (p. {page_num + 1})"])
            item.setData(0, Qt.ItemDataRole.UserRole, page_num)

            while stack and stack[-1][0] >= level:
                stack.pop()

            if not stack:
                self.outline_tree.addTopLevelItem(item)
            else:
                stack[-1][1].addChild(item)

            stack.append((level, item))

        self.outline_tree.expandAll()

    def _on_outline_item_clicked(self, item: QTreeWidgetItem, column: int):
        page_num = item.data(0, Qt.ItemDataRole.UserRole)
        if page_num is not None and isinstance(page_num, int):
            self.pageSelected.emit(page_num)

    # -------------------------------------------------------------------------
    # Search Results Tab
    # -------------------------------------------------------------------------
    def set_search_results(self, results: List[Dict[str, Any]]):
        self.search_list.clear()

        if not results:
            item = QListWidgetItem("No matches found")
            item.setForeground(QColor("#ef4444"))
            self.search_list.addItem(item)
            self.tab_widget.setCurrentWidget(self.search_list)
            return

        total_matches = sum(len(r["rects"]) for r in results)
        header_item = QListWidgetItem(f"Found {total_matches} occurrences in {len(results)} pages")
        header_item.setForeground(QColor("#10b981"))
        self.search_list.addItem(header_item)

        for res in results:
            p_display = res["page_display"]
            p_idx = res["page"]
            snippet = res.get("snippet", "")
            count = len(res["rects"])

            item_text = f"Page {p_display} ({count} match{'es' if count > 1 else ''})\n  {snippet}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, (p_idx, res["rects"][0]))
            self.search_list.addItem(item)

        self.tab_widget.setCurrentWidget(self.search_list)

    def _on_search_item_clicked(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            page_num, rect = data
            self.searchResultSelected.emit(page_num, rect)
