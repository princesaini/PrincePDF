"""
PrincePDF - Central PDF Viewer Widget
Manages layout, viewport scrolling, view modes (Single, Continuous, Side-by-Side),
smooth zooming, rotation, keyboard shortcuts, and page virtualization.
"""

from typing import List, Optional, Dict
import fitz
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect, QTimer
from PyQt6.QtGui import QWheelEvent, QKeyEvent, QResizeEvent, QPalette, QColor, QCursor
from PyQt6.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QApplication, QFrame
)
from PyQt6 import sip

from page_widget import PdfPageWidget


class ViewMode:
    SINGLE = "single"
    CONTINUOUS = "continuous"
    SIDE_BY_SIDE = "side_by_side"


ZOOM_STEPS = [0.15, 0.25, 0.33, 0.5, 0.67, 0.75, 0.9, 1.0, 1.1, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0, 5.0, 8.0]


class PdfViewWidget(QScrollArea):
    """
    Main interactive PDF scroll area supporting Single, Continuous, and Side-by-Side views,
    dynamic high-DPI zoom, text selection, and fast navigation.
    """
    currentPageChanged = pyqtSignal(int)
    pageCountChanged = pyqtSignal(int)
    zoomChanged = pyqtSignal(float)
    selectionTextCopied = pyqtSignal(str)
    statusMessageRequested = pyqtSignal(str)
    linkClicked = pyqtSignal(dict)

    def __init__(self, doc_model, render_cache, parent=None):
        super().__init__(parent)
        self.doc_model = doc_model
        self.render_cache = render_cache

        self.current_page: int = 0
        self.view_mode: str = ViewMode.CONTINUOUS
        self.zoom: float = 1.0
        self.zoom_mode: str = "fit_width"  # "fit_width", "fit_page", "custom"
        self.rotation: int = 0
        self.night_mode: bool = False

        self.page_widgets: List[PdfPageWidget] = []
        self._is_updating_scroll: bool = False

        # Container widget inside scroll area
        self.container = QWidget(self)
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFrameShape(QFrame.Shape.NoFrame)

        # Style canvas background
        self.setStyleSheet("""
            QScrollArea {
                background-color: #1a1c23;
                border: none;
            }
            QScrollBar:vertical {
                background: #1e212b;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #3e4452;
                min-height: 25px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #5c6370;
            }
            QScrollBar:horizontal {
                background: #1e212b;
                height: 12px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #3e4452;
                min-width: 25px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #5c6370;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                width: 0px;
                height: 0px;
            }
        """)

        # Listen to scroll events to update current page indicator
        self.verticalScrollBar().valueChanged.connect(self._on_scroll_changed)

    def set_canvas_theme(self, is_dark: bool):
        self._theme_is_dark = is_dark
        effective_dark = is_dark or self.night_mode
        bg = "#1a1c23" if effective_dark else "#e9ecef"
        bar_bg = "#1e212b" if effective_dark else "#dee2e6"
        bar_handle = "#3e4452" if effective_dark else "#adb5bd"
        bar_hover = "#5c6370" if effective_dark else "#6c757d"
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: {bg};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {bar_bg};
                width: 12px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {bar_handle};
                min-height: 25px;
                border-radius: 6px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {bar_hover};
            }}
            QScrollBar:horizontal {{
                background: {bar_bg};
                height: 12px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: {bar_handle};
                min-width: 25px;
                border-radius: 6px;
                margin: 2px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {bar_hover};
            }}
            QScrollBar::add-line, QScrollBar::sub-line {{
                width: 0px;
                height: 0px;
            }}
        """)

    # -------------------------------------------------------------------------
    # Document Loading & Setup
    # -------------------------------------------------------------------------
    def load_document(self):
        """Initializes page widgets when document model is loaded."""
        self.clear_pages()
        if not self.doc_model.is_open:
            return

        total_pages = self.doc_model.page_count
        self.pageCountChanged.emit(total_pages)

        # Create PdfPageWidget for each page
        for p_idx in range(total_pages):
            pw = PdfPageWidget(p_idx, self.doc_model, self.render_cache, self.container)
            pw.pageClicked.connect(self._on_page_clicked)
            pw.linkActivated.connect(self._on_link_activated)
            pw.selectionChanged.connect(self._on_selection_changed)
            self.page_widgets.append(pw)

        self.apply_zoom_mode()
        self._rebuild_layout()
        self.go_to_page(0)

    def clear_pages(self):
        for pw in self.page_widgets:
            pw.deleteLater()
        self.page_widgets.clear()
        self.current_page = 0

    # -------------------------------------------------------------------------
    # Layout Modes: Single, Continuous, Side-by-Side
    # -------------------------------------------------------------------------
    def set_view_mode(self, mode: str):
        if mode not in (ViewMode.SINGLE, ViewMode.CONTINUOUS, ViewMode.SIDE_BY_SIDE):
            return
        if self.view_mode != mode:
            saved_page = self.current_page
            self.view_mode = mode
            self.apply_zoom_mode()
            self._rebuild_layout()
            self.go_to_page(saved_page)

    def _rebuild_layout(self):
        if not self.page_widgets:
            return

        # Clear existing layout on container
        old_layout = self.container.layout()
        if old_layout is not None:
            while old_layout.count():
                old_layout.takeAt(0)
            sip.delete(old_layout)

        dpr = self.devicePixelRatioF()

        if self.view_mode == ViewMode.SINGLE:
            layout = QVBoxLayout(self.container)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            for idx, pw in enumerate(self.page_widgets):
                pw.set_display_params(self.zoom, self.rotation, self.night_mode, dpr)
                layout.addWidget(pw)
                pw.setVisible(idx == self.current_page)

        elif self.view_mode == ViewMode.CONTINUOUS:
            layout = QVBoxLayout(self.container)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(16)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            for pw in self.page_widgets:
                pw.set_display_params(self.zoom, self.rotation, self.night_mode, dpr)
                pw.setVisible(True)
                layout.addWidget(pw)

        elif self.view_mode == ViewMode.SIDE_BY_SIDE:
            layout = QGridLayout(self.container)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setHorizontalSpacing(16)
            layout.setVerticalSpacing(16)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            row = 0
            col = 0
            for pw in self.page_widgets:
                pw.set_display_params(self.zoom, self.rotation, self.night_mode, dpr)
                pw.setVisible(True)
                layout.addWidget(pw, row, col)
                col += 1
                if col > 1:
                    col = 0
                    row += 1

        self.container.setLayout(layout)
        self.container.adjustSize()

    # -------------------------------------------------------------------------
    # Zoom Management
    # -------------------------------------------------------------------------
    def apply_zoom_mode(self):
        if not self.doc_model.is_open or not self.page_widgets:
            return

        viewport_w = self.viewport().width() - 60
        viewport_h = self.viewport().height() - 60
        if viewport_w <= 100 or viewport_h <= 100:
            return

        p_idx = max(0, min(self.current_page, self.doc_model.page_count - 1))
        page_w, page_h = self.doc_model.get_page_size(p_idx, self.rotation)

        if self.view_mode == ViewMode.SIDE_BY_SIDE:
            page_w = page_w * 2 + 20

        if self.zoom_mode == "fit_width":
            calc_zoom = max(0.2, viewport_w / max(1.0, page_w))
            self.set_zoom(calc_zoom, record_mode="fit_width")
        elif self.zoom_mode == "fit_page":
            calc_zoom = max(0.2, min(viewport_w / max(1.0, page_w), viewport_h / max(1.0, page_h)))
            self.set_zoom(calc_zoom, record_mode="fit_page")

    def set_zoom(self, zoom: float, record_mode: Optional[str] = None):
        zoom = max(0.1, min(zoom, 8.0))
        if abs(self.zoom - zoom) > 0.001:
            self.zoom = zoom
            if record_mode:
                self.zoom_mode = record_mode
            else:
                self.zoom_mode = "custom"

            dpr = self.devicePixelRatioF()
            for pw in self.page_widgets:
                pw.set_display_params(self.zoom, self.rotation, self.night_mode, dpr)

            self.container.adjustSize()
            self.zoomChanged.emit(self.zoom)

    def zoom_in(self):
        for step in ZOOM_STEPS:
            if step > self.zoom + 0.05:
                self.set_zoom(step)
                return
        self.set_zoom(min(8.0, self.zoom * 1.25))

    def zoom_out(self):
        for step in reversed(ZOOM_STEPS):
            if step < self.zoom - 0.05:
                self.set_zoom(step)
                return
        self.set_zoom(max(0.1, self.zoom / 1.25))

    def reset_zoom(self):
        self.set_zoom(1.0)

    def set_fit_width(self):
        self.zoom_mode = "fit_width"
        self.apply_zoom_mode()

    def set_fit_page(self):
        self.zoom_mode = "fit_page"
        self.apply_zoom_mode()

    # -------------------------------------------------------------------------
    # Rotation & Night Mode
    # -------------------------------------------------------------------------
    def rotate_clockwise(self):
        self.rotation = (self.rotation + 90) % 360
        self.apply_zoom_mode()
        self._rebuild_layout()

    def rotate_counter_clockwise(self):
        self.rotation = (self.rotation - 90) % 360
        self.apply_zoom_mode()
        self._rebuild_layout()

    def toggle_night_mode(self, enabled: bool):
        self.night_mode = enabled
        self.set_canvas_theme(getattr(self, "_theme_is_dark", True))
        dpr = self.devicePixelRatioF()
        for pw in self.page_widgets:
            pw.set_display_params(self.zoom, self.rotation, self.night_mode, dpr)

    # -------------------------------------------------------------------------
    # Navigation
    # -------------------------------------------------------------------------
    def go_to_page(self, page_num: int):
        if not self.page_widgets:
            return
        total = len(self.page_widgets)
        page_num = max(0, min(page_num, total - 1))
        self.current_page = page_num
        self.currentPageChanged.emit(self.current_page)

        if self.view_mode == ViewMode.SINGLE:
            dpr = self.devicePixelRatioF()
            for idx, pw in enumerate(self.page_widgets):
                if idx == page_num:
                    pw.set_display_params(self.zoom, self.rotation, self.night_mode, dpr)
                    pw.setVisible(True)
                else:
                    pw.setVisible(False)
            self.container.adjustSize()
            self.verticalScrollBar().setValue(0)
            self.horizontalScrollBar().setValue(0)
        else:
            # Scroll to target page widget
            pw = self.page_widgets[page_num]
            target_y = pw.pos().y()
            self._is_updating_scroll = True
            self.verticalScrollBar().setValue(target_y)
            self._is_updating_scroll = False

    def scroll_to_rect(self, page_num: int, rect: fitz.Rect):
        """Scrolls viewport so that specified page and fitz.Rect are centered in view."""
        if not self.page_widgets or page_num < 0 or page_num >= len(self.page_widgets):
            return

        self.go_to_page(page_num)
        pw = self.page_widgets[page_num]
        w_rect = pw._pdf_rect_to_widget_rect(rect)

        vp_w = self.viewport().width()
        vp_h = self.viewport().height()

        target_y = int(pw.pos().y() + w_rect.center().y() - vp_h / 2)
        target_x = int(pw.pos().x() + w_rect.center().x() - vp_w / 2)

        self._is_updating_scroll = True
        self.verticalScrollBar().setValue(max(0, target_y))
        self.horizontalScrollBar().setValue(max(0, target_x))
        self._is_updating_scroll = False

    def next_page(self):
        if self.current_page < len(self.page_widgets) - 1:
            step = 2 if self.view_mode == ViewMode.SIDE_BY_SIDE else 1
            self.go_to_page(min(len(self.page_widgets) - 1, self.current_page + step))

    def prev_page(self):
        if self.current_page > 0:
            step = 2 if self.view_mode == ViewMode.SIDE_BY_SIDE else 1
            self.go_to_page(max(0, self.current_page - step))

    def first_page(self):
        self.go_to_page(0)

    def last_page(self):
        if self.page_widgets:
            self.go_to_page(len(self.page_widgets) - 1)

    def _on_scroll_changed(self, value: int):
        if self._is_updating_scroll or not self.page_widgets or self.view_mode == ViewMode.SINGLE:
            return

        probe_y = value + self.viewport().height() // 3
        best_page = self.current_page
        min_dist = float("inf")

        for idx, pw in enumerate(self.page_widgets):
            top = pw.pos().y()
            bottom = top + pw.height()
            if top <= probe_y <= bottom:
                best_page = idx
                break
            dist = min(abs(top - probe_y), abs(bottom - probe_y))
            if dist < min_dist:
                min_dist = dist
                best_page = idx

        if best_page != self.current_page:
            self.current_page = best_page
            self.currentPageChanged.emit(self.current_page)

    def _on_page_clicked(self, page_num: int):
        if self.current_page != page_num:
            self.current_page = page_num
            self.currentPageChanged.emit(self.current_page)

    def _on_link_activated(self, link: dict):
        kind = link.get("kind", 0)
        if kind == fitz.LINK_GOTO:
            target_page = link.get("page", 0)
            to_pt = link.get("to")
            if to_pt is not None:
                # Scroll to target point with small rect around it
                target_rect = fitz.Rect(to_pt.x, to_pt.y, to_pt.x + 10, to_pt.y + 10)
                self.scroll_to_rect(target_page, target_rect)
            else:
                self.go_to_page(target_page)
        elif kind == fitz.LINK_URI:
            self.linkClicked.emit(link)

    def _on_selection_changed(self, selected_text: str):
        if selected_text:
            # Clear selection in all other pages
            sender_pw = self.sender()
            for pw in self.page_widgets:
                if pw is not sender_pw:
                    pw.clear_selection()
            self.selectionTextCopied.emit(selected_text)

    def copy_current_selection(self):
        for pw in self.page_widgets:
            if pw._selected_text:
                text = pw.copy_selection()
                if text:
                    self.statusMessageRequested.emit(f"Copied {len(text)} characters to clipboard")
                    return text
        return ""

    def select_all_current_page(self):
        if 0 <= self.current_page < len(self.page_widgets):
            self.page_widgets[self.current_page].select_all()

    # -------------------------------------------------------------------------
    # Search Results Overlay
    # -------------------------------------------------------------------------
    def show_search_matches(self, page_num: int, rects: List[fitz.Rect], active_rect: Optional[fitz.Rect] = None):
        for idx, pw in enumerate(self.page_widgets):
            if idx == page_num:
                pw.set_search_results(rects, active_rect)
            else:
                pw.set_search_results([])

    def clear_search_highlights(self):
        for pw in self.page_widgets:
            pw.set_search_results([])

    # -------------------------------------------------------------------------
    # Event Handlers: Resize, Wheel Zoom, Key Navigation
    # -------------------------------------------------------------------------
    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        if self.zoom_mode in ("fit_width", "fit_page"):
            self.apply_zoom_mode()

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl + Mouse Wheel for smooth anchor-based zooming
            delta = event.angleDelta().y()
            if delta == 0:
                return

            mouse_pos = event.position()
            vbar = self.verticalScrollBar()
            hbar = self.horizontalScrollBar()

            old_cw = max(1, self.container.width())
            old_ch = max(1, self.container.height())
            rel_x = (mouse_pos.x() + hbar.value()) / old_cw
            rel_y = (mouse_pos.y() + vbar.value()) / old_ch

            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()

            # Restore anchor point under mouse
            new_cw = self.container.width()
            new_ch = self.container.height()
            self._is_updating_scroll = True
            hbar.setValue(int(rel_x * new_cw - mouse_pos.x()))
            vbar.setValue(int(rel_y * new_ch - mouse_pos.y()))
            self._is_updating_scroll = False

            event.accept()
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self._pan_start_pos = event.globalPosition().toPoint()
            self._pan_start_v = self.verticalScrollBar().value()
            self._pan_start_h = self.horizontalScrollBar().value()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, "_is_panning", False) and (event.buttons() & Qt.MouseButton.MiddleButton):
            delta = event.globalPosition().toPoint() - self._pan_start_pos
            self.verticalScrollBar().setValue(self._pan_start_v - delta.y())
            self.horizontalScrollBar().setValue(self._pan_start_h - delta.x())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton and getattr(self, "_is_panning", False):
            self._is_panning = False
            self.unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_C:
                self.copy_current_selection()
                event.accept()
                return
            elif key == Qt.Key.Key_A:
                self.select_all_current_page()
                event.accept()
                return
            elif key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
                self.zoom_in()
                event.accept()
                return
            elif key == Qt.Key.Key_Minus:
                self.zoom_out()
                event.accept()
                return
            elif key == Qt.Key.Key_0:
                self.reset_zoom()
                event.accept()
                return
            elif key == Qt.Key.Key_1:
                self.set_fit_page()
                event.accept()
                return
            elif key == Qt.Key.Key_2:
                self.set_fit_width()
                event.accept()
                return
            elif key == Qt.Key.Key_R:
                if modifiers & Qt.KeyboardModifier.ShiftModifier:
                    self.rotate_counter_clockwise()
                else:
                    self.rotate_clockwise()
                event.accept()
                return

        # Direct navigation keys
        if key in (Qt.Key.Key_PageDown, Qt.Key.Key_Right) or (key == Qt.Key.Key_Down and self.view_mode == ViewMode.SINGLE):
            self.next_page()
            event.accept()
            return
        elif key in (Qt.Key.Key_PageUp, Qt.Key.Key_Left) or (key == Qt.Key.Key_Up and self.view_mode == ViewMode.SINGLE):
            self.prev_page()
            event.accept()
            return
        elif key == Qt.Key.Key_Down:
            vbar = self.verticalScrollBar()
            if vbar.maximum() == 0 or vbar.value() >= vbar.maximum() - 2:
                self.next_page()
                event.accept()
                return
        elif key == Qt.Key.Key_Up:
            vbar = self.verticalScrollBar()
            if vbar.maximum() == 0 or vbar.value() <= 2:
                self.prev_page()
                event.accept()
                return
        elif key == Qt.Key.Key_Home:
            self.first_page()
            event.accept()
            return
        elif key == Qt.Key.Key_End:
            self.last_page()
            event.accept()
            return
        elif key == Qt.Key.Key_Space:
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                self.prev_page()
            else:
                self.next_page()
            event.accept()
            return

        super().keyPressEvent(event)
