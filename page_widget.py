"""
PrincePDF - Page Widget
High fidelity individual PDF page display widget with smooth rendering,
accurate text selection, copy-to-clipboard, search highlights, and link navigation.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
import fitz
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPixmap, QCursor,
    QMouseEvent, QContextMenuEvent, QAction, QPainterPath
)
from PyQt6.QtWidgets import QWidget, QMenu, QApplication


class PdfPageWidget(QWidget):
    """
    Renders an individual PDF page with:
    - Native High-DPI QPixmap caching
    - Word-level text selection and clipboard copying
    - Search hit highlighting
    - Hyperlink detection and clicking
    """
    pageClicked = pyqtSignal(int)
    linkActivated = pyqtSignal(dict)
    selectionChanged = pyqtSignal(str)
    searchResultClicked = pyqtSignal(int, fitz.Rect)

    def __init__(self, page_num: int, doc_model, render_cache, parent=None):
        super().__init__(parent)
        self.page_num = page_num
        self.doc_model = doc_model
        self.render_cache = render_cache

        self.zoom: float = 1.0
        self.rotation: int = 0
        self.night_mode: bool = False
        self.dpr: float = 1.0

        # Cached pixmap
        self._pixmap: Optional[QPixmap] = None

        # Text selection state
        self._is_selecting: bool = False
        self._selection_start_pt: Optional[QPointF] = None
        self._selection_current_pt: Optional[QPointF] = None
        self._selected_word_indices: Set[int] = set()
        self._selected_text: str = ""

        # Search highlights: list of fitz.Rect
        self._search_rects: List[fitz.Rect] = []
        self._active_search_rect: Optional[fitz.Rect] = None

        # Links on this page: list of dicts from page.get_links()
        self._links: List[Dict[str, Any]] = []

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._update_geometry()

    def _update_geometry(self):
        w_pts, h_pts = self.doc_model.get_page_size(self.page_num, self.rotation)
        display_w = int(w_pts * self.zoom)
        display_h = int(h_pts * self.zoom)
        self.setFixedSize(display_w, display_h)

    def set_display_params(self, zoom: float, rotation: int, night_mode: bool, dpr: float):
        changed = (
            abs(self.zoom - zoom) > 0.001 or
            self.rotation != rotation or
            self.night_mode != night_mode or
            abs(self.dpr - dpr) > 0.05
        )
        if changed:
            self.zoom = zoom
            self.rotation = rotation
            self.night_mode = night_mode
            self.dpr = dpr
            self._pixmap = None  # invalidate cached pixmap
            self._update_geometry()
            self.update()

    def set_search_results(self, rects: List[fitz.Rect], active_rect: Optional[fitz.Rect] = None):
        self._search_rects = rects or []
        self._active_search_rect = active_rect
        self.update()

    def clear_selection(self):
        if self._selected_word_indices or self._selected_text:
            self._selected_word_indices.clear()
            self._selected_text = ""
            self.selectionChanged.emit("")
            self.update()

    def select_all(self):
        words = self.doc_model.get_page_words(self.page_num)
        self._selected_word_indices = set(range(len(words)))
        self._rebuild_selected_text()
        self.selectionChanged.emit(self._selected_text)
        self.update()

    def copy_selection(self):
        if self._selected_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(self._selected_text)
            return self._selected_text
        return ""

    def copy_all_page_text(self):
        text = self.doc_model.get_full_page_text(self.page_num)
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
        return text

    def _ensure_pixmap(self) -> Optional[QPixmap]:
        if self._pixmap is None or self._pixmap.isNull():
            self._pixmap = self.render_cache.get_pixmap(
                self.doc_model,
                self.page_num,
                self.zoom,
                self.rotation,
                self.night_mode,
                self.dpr
            )
        return self._pixmap

    def _ensure_links(self):
        if not self._links:
            self._links = self.doc_model.get_page_links(self.page_num)

    # -------------------------------------------------------------------------
    # Coordinate transforms
    # -------------------------------------------------------------------------
    def _widget_to_pdf_point(self, pt: QPointF) -> QPointF:
        """Converts widget pixel coords to PDF point coords (unrotated)."""
        scale = max(0.001, self.zoom)
        return QPointF(pt.x() / scale, pt.y() / scale)

    def _pdf_rect_to_widget_rect(self, rect: fitz.Rect) -> QRectF:
        """Converts fitz.Rect in PDF points to QRectF in widget pixel coords."""
        scale = self.zoom
        return QRectF(
            rect.x0 * scale,
            rect.y0 * scale,
            rect.width * scale,
            rect.height * scale
        )

    # -------------------------------------------------------------------------
    # Painting
    # -------------------------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        # 1. Draw Page Pixmap
        pixmap = self._ensure_pixmap()
        if pixmap and not pixmap.isNull():
            # Source rect scaled for High DPR
            target_rect = self.rect()
            painter.drawPixmap(target_rect, pixmap)
        else:
            # Placeholder while loading
            painter.fillRect(self.rect(), QColor(40, 40, 45) if self.night_mode else QColor(255, 255, 255))
            painter.setPen(QColor(128, 128, 128))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"Page {self.page_num + 1}")

        # 2. Draw Search Highlights
        if self._search_rects:
            for s_rect in self._search_rects:
                w_rect = self._pdf_rect_to_widget_rect(s_rect)
                is_active = (self._active_search_rect is not None and
                             abs(self._active_search_rect.x0 - s_rect.x0) < 1.0 and
                             abs(self._active_search_rect.y0 - s_rect.y0) < 1.0)
                if is_active:
                    painter.fillRect(w_rect, QColor(255, 152, 0, 160)) # Vivid Orange
                    painter.setPen(QPen(QColor(230, 81, 0, 220), 1.5))
                    painter.drawRect(w_rect)
                else:
                    painter.fillRect(w_rect, QColor(255, 235, 59, 130)) # Bright Yellow
                    painter.setPen(QPen(QColor(245, 127, 23, 160), 1.0))
                    painter.drawRect(w_rect)

        # 3. Draw Selected Text Highlights
        if self._selected_word_indices:
            words = self.doc_model.get_page_words(self.page_num)
            selection_color = QColor(0, 120, 215, 90)     # Modern Fluent selection blue
            border_color = QColor(0, 120, 215, 180)
            painter.setPen(QPen(border_color, 1.0))
            painter.setBrush(QBrush(selection_color))

            for idx in self._selected_word_indices:
                if 0 <= idx < len(words):
                    w = words[idx]
                    rect = fitz.Rect(w[0], w[1], w[2], w[3])
                    w_rect = self._pdf_rect_to_widget_rect(rect)
                    painter.drawRoundedRect(w_rect, 2.0, 2.0)

        painter.end()

    # -------------------------------------------------------------------------
    # Mouse & Text Selection Handling
    # -------------------------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.pageClicked.emit(self.page_num)
            pos = event.position()
            pdf_pos = self._widget_to_pdf_point(pos)

            # Check if clicked on a link
            self._ensure_links()
            for link in self._links:
                from_rect = link.get("from")
                if from_rect and fitz.Rect(from_rect).contains(fitz.Point(pdf_pos.x(), pdf_pos.y())):
                    self.linkActivated.emit(link)
                    return

            # Start text selection
            self._is_selecting = True
            self._selection_start_pt = pos
            self._selection_current_pt = pos
            self._selected_word_indices.clear()
            self._selected_text = ""
            self.selectionChanged.emit("")
            self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position()

        # Update cursor when hovering over links
        self._ensure_links()
        pdf_pos = self._widget_to_pdf_point(pos)
        over_link = False
        for link in self._links:
            from_rect = link.get("from")
            if from_rect and fitz.Rect(from_rect).contains(fitz.Point(pdf_pos.x(), pdf_pos.y())):
                over_link = True
                break

        if over_link:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.IBeamCursor))

        if self._is_selecting and (event.buttons() & Qt.MouseButton.LeftButton):
            self._selection_current_pt = pos
            self._compute_selection()
            self.update()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._is_selecting:
            self._is_selecting = False
            self._compute_selection()
            self._rebuild_selected_text()
            self.selectionChanged.emit(self._selected_text)
            self.update()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Double click selects word under cursor."""
        if event.button() == Qt.MouseButton.LeftButton:
            pdf_pt = self._widget_to_pdf_point(event.position())
            words = self.doc_model.get_page_words(self.page_num)
            for idx, w in enumerate(words):
                w_rect = fitz.Rect(w[0], w[1], w[2], w[3])
                if w_rect.contains(fitz.Point(pdf_pt.x(), pdf_pt.y())):
                    self._selected_word_indices = {idx}
                    self._selected_text = w[4]
                    self.selectionChanged.emit(self._selected_text)
                    self.update()
                    return
        super().mouseDoubleClickEvent(event)

    def _compute_selection(self):
        """Computes selected words based on start and current drag points."""
        if not self._selection_start_pt or not self._selection_current_pt:
            return

        p1 = self._widget_to_pdf_point(self._selection_start_pt)
        p2 = self._widget_to_pdf_point(self._selection_current_pt)
        words = self.doc_model.get_page_words(self.page_num)
        if not words:
            return

        drag_rect = fitz.Rect(
            min(p1.x(), p2.x()),
            min(p1.y(), p2.y()),
            max(p1.x(), p2.x()),
            max(p1.y(), p2.y())
        )

        # 1. Check if dragging vertically across text lines in reading order
        start_word_idx = -1
        end_word_idx = -1

        for idx, w in enumerate(words):
            w_rect = fitz.Rect(w[0], w[1], w[2], w[3])
            if start_word_idx == -1 and w_rect.contains(fitz.Point(p1.x(), p1.y())):
                start_word_idx = idx
            if w_rect.contains(fitz.Point(p2.x(), p2.y())):
                end_word_idx = idx

        new_selected: Set[int] = set()

        if start_word_idx != -1 and end_word_idx != -1:
            # Linear reading order selection between start and end words
            low = min(start_word_idx, end_word_idx)
            high = max(start_word_idx, end_word_idx)
            new_selected = set(range(low, high + 1))
        else:
            # Bounding box intersection selection
            for idx, w in enumerate(words):
                w_rect = fitz.Rect(w[0], w[1], w[2], w[3])
                if drag_rect.intersects(w_rect):
                    new_selected.add(idx)

        self._selected_word_indices = new_selected

    def _rebuild_selected_text(self):
        """Builds cleanly formatted text string from selected word indices."""
        if not self._selected_word_indices:
            self._selected_text = ""
            return

        words = self.doc_model.get_page_words(self.page_num)
        sorted_indices = sorted(self._selected_word_indices)
        
        lines = []
        curr_line_no = -1
        curr_words = []

        for idx in sorted_indices:
            if 0 <= idx < len(words):
                w = words[idx]
                line_no = w[6]
                word_str = w[4]

                if curr_line_no != -1 and line_no != curr_line_no:
                    lines.append(" ".join(curr_words))
                    curr_words = [word_str]
                else:
                    curr_words.append(word_str)
                curr_line_no = line_no

        if curr_words:
            lines.append(" ".join(curr_words))

        self._selected_text = "\n".join(lines)

    # -------------------------------------------------------------------------
    # Context Menu
    # -------------------------------------------------------------------------
    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #242730;
                color: #f1f5f9;
                border: 1px solid #3a3f4d;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3b82f6;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: #3a3f4d;
                margin: 4px 8px;
            }
        """)

        copy_action = menu.addAction("Copy (Ctrl+C)")
        copy_action.setEnabled(bool(self._selected_text))
        copy_action.triggered.connect(self.copy_selection)

        select_all_action = menu.addAction("Select All (Ctrl+A)")
        select_all_action.triggered.connect(self.select_all)

        menu.addSeparator()

        copy_all_action = menu.addAction("Copy Page Text")
        copy_all_action.triggered.connect(self.copy_all_page_text)

        menu.exec(event.globalPos())
