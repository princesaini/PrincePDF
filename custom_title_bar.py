"""
PrincePDF - Custom Title & Menu Bar
Integrates app icon, menu bar, centered document title, and native-styled
window control buttons (Minimize, Maximize/Restore, Close) into a single sleek top bar.
Supports native Windows 11 Aero Snap dragging and double-click maximize toggle.
"""

import sys
import os
import ctypes
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QCursor
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton,
    QMenuBar, QSizePolicy, QMainWindow
)

import windows_integration as wi


class CustomTitleBar(QWidget):
    """
    Unified title and menu bar widget for frameless PrincePDF window.
    Layout: [App Icon] [QMenuBar: File, Edit, ...] [Center: Document Name] [— 🗖 ✕]
    """

    def __init__(self, parent_window: QMainWindow):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setFixedHeight(36)
        self.setObjectName("CustomTitleBar")

        # Top-level layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(6)

        # 1. High-DPI App Icon
        self.icon_lbl = QLabel(self)
        self.icon_lbl.setFixedSize(20, 20)
        self.icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._load_icon()
        layout.addWidget(self.icon_lbl)

        # 2. QMenuBar for Application Menus
        self.menu_bar = QMenuBar(self)
        self.menu_bar.setObjectName("CustomMenuBar")
        self.menu_bar.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.menu_bar)

        # 3. Centered Document Title
        layout.addStretch(1)
        self.title_lbl = QLabel("PrincePDF", self)
        self.title_lbl.setObjectName("TitleLabel")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.title_lbl)
        layout.addStretch(1)

        # 4. Window Controls: Minimize, Maximize/Restore, Close
        btn_box = QHBoxLayout()
        btn_box.setSpacing(0)
        btn_box.setContentsMargins(0, 0, 0, 0)

        # Minimize Button
        self.min_btn = QPushButton("—", self)
        self.min_btn.setFixedSize(46, 36)
        self.min_btn.setObjectName("TitleBtn")
        self.min_btn.setToolTip("Minimize")
        self.min_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.min_btn.clicked.connect(self.parent_window.showMinimized)
        btn_box.addWidget(self.min_btn)

        # Maximize / Restore Button
        self.max_btn = QPushButton("🗗" if self.parent_window.isMaximized() else "🗖", self)
        self.max_btn.setFixedSize(46, 36)
        self.max_btn.setObjectName("TitleBtn")
        self.max_btn.setToolTip("Restore Down" if self.parent_window.isMaximized() else "Maximize")
        self.max_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.max_btn.clicked.connect(self._toggle_maximize)
        btn_box.addWidget(self.max_btn)

        # Close Button
        self.close_btn = QPushButton("✕", self)
        self.close_btn.setFixedSize(46, 36)
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.setToolTip("Close (Alt+F4)")
        self.close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.close_btn.clicked.connect(self.parent_window.close)
        btn_box.addWidget(self.close_btn)

        layout.addLayout(btn_box)

    def _load_icon(self):
        """Loads and scales high-resolution PNG icon respecting DPI scale."""
        png_path = wi.get_png_icon_path()
        if png_path and os.path.exists(png_path):
            dpr = self.devicePixelRatioF() if hasattr(self, "devicePixelRatioF") else 1.0
            size_px = int(20 * dpr)
            pix = QPixmap(png_path).scaled(
                size_px, size_px,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            pix.setDevicePixelRatio(dpr)
            self.icon_lbl.setPixmap(pix)

    def set_title(self, title: str):
        """Updates the centered title text and tooltip."""
        self.title_lbl.setText(title)
        self.title_lbl.setToolTip(title)

    def update_max_button(self, is_maximized: bool):
        """Updates the maximize/restore button icon and tooltip based on state."""
        if is_maximized:
            self.max_btn.setText("🗗")
            self.max_btn.setToolTip("Restore Down")
        else:
            self.max_btn.setText("🗖")
            self.max_btn.setToolTip("Maximize")

    def _toggle_maximize(self):
        """Toggles between maximized and restored normal states."""
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
        else:
            self.parent_window.showMaximized()

    def mousePressEvent(self, event):
        """Initiates native Windows caption dragging for Aero Snap and multi-monitor support."""
        if event.button() == Qt.MouseButton.LeftButton:
            if sys.platform == "win32":
                try:
                    hwnd = int(self.parent_window.winId())
                    ctypes.windll.user32.ReleaseCapture()
                    # 0xA1 = WM_NCLBUTTONDOWN, 2 = HTCAPTION
                    ctypes.windll.user32.SendMessageW(hwnd, 0xA1, 2, 0)
                    event.accept()
                    return
                except Exception:
                    pass
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Double clicking empty space or document title toggles maximize/restore."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)
