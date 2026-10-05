"""
PrincePDF - Render Cache & Pipeline
High-performance rendering pipeline with LRU cache, High-DPI support,
color inversion (Night Mode), and thumbnail generation.
"""

from collections import OrderedDict
from typing import Optional, Tuple
import fitz
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool
from PyQt6.QtGui import QImage, QPixmap


class RenderTask(QRunnable):
    """Background task to pre-render a page pixmap."""
    def __init__(self, doc_model, page_num: int, zoom: float, rotation: int,
                 night_mode: bool, dpr: float, callback):
        super().__init__()
        self.doc_model = doc_model
        self.page_num = page_num
        self.zoom = zoom
        self.rotation = rotation
        self.night_mode = night_mode
        self.dpr = dpr
        self.callback = callback

    def run(self):
        try:
            page = self.doc_model.get_page(self.page_num)
            if not page:
                return
            mat = fitz.Matrix(self.zoom * self.dpr, self.zoom * self.dpr).prerotate(self.rotation)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            if self.night_mode:
                pix.invert_irect(pix.irect)
            qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888).copy()
            qimg.setDevicePixelRatio(self.dpr)
            if self.callback:
                self.callback(self.page_num, qimg)
        except Exception:
            pass


class RenderCache(QObject):
    pageRendered = pyqtSignal(int, QPixmap)

    def __init__(self, max_cached_pages: int = 40):
        super().__init__()
        self.max_cached_pages = max_cached_pages
        # Cache key: (page_num, round(zoom, 3), rotation, night_mode, dpr) -> QPixmap
        self._cache: OrderedDict = OrderedDict()
        self._thumb_cache: OrderedDict = OrderedDict()
        self.thread_pool = QThreadPool.globalInstance()

    def clear(self):
        self._cache.clear()
        self._thumb_cache.clear()

    def _make_key(self, page_num: int, zoom: float, rotation: int, night_mode: bool, dpr: float):
        return (page_num, round(zoom, 3), rotation % 360, bool(night_mode), round(dpr, 2))

    def get_pixmap(self, doc_model, page_num: int, zoom: float, rotation: int = 0,
                   night_mode: bool = False, dpr: float = 1.0) -> Optional[QPixmap]:
        key = self._make_key(page_num, zoom, rotation, night_mode, dpr)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]

        page = doc_model.get_page(page_num)
        if not page:
            return None

        # Render synchronously
        try:
            mat = fitz.Matrix(zoom * dpr, zoom * dpr).prerotate(rotation)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            if night_mode:
                pix.invert_irect(pix.irect)
            qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888).copy()
            qimg.setDevicePixelRatio(dpr)
            pixmap = QPixmap.fromImage(qimg)

            # Store in cache
            if len(self._cache) >= self.max_cached_pages:
                self._cache.popitem(last=False)
            self._cache[key] = pixmap
            return pixmap
        except Exception:
            return None

    def get_thumbnail(self, doc_model, page_num: int, max_width: int = 140,
                      rotation: int = 0, night_mode: bool = False, dpr: float = 1.0) -> Optional[QPixmap]:
        key = (page_num, max_width, rotation % 360, bool(night_mode), round(dpr, 2))
        if key in self._thumb_cache:
            self._thumb_cache.move_to_end(key)
            return self._thumb_cache[key]

        page = doc_model.get_page(page_num)
        if not page:
            return None

        try:
            page_w, page_h = doc_model.get_page_size(page_num, rotation)
            scale = (max_width * dpr) / max(1.0, page_w)
            mat = fitz.Matrix(scale, scale).prerotate(rotation)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            if night_mode:
                pix.invert_irect(pix.irect)
            qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888).copy()
            qimg.setDevicePixelRatio(dpr)
            pixmap = QPixmap.fromImage(qimg)

            if len(self._thumb_cache) >= 150:
                self._thumb_cache.popitem(last=False)
            self._thumb_cache[key] = pixmap
            return pixmap
        except Exception:
            return None

