"""
PrincePDF - Dialog Windows
1. Document Properties Dialog (Metadata, Page Size, File Info)
2. Go to Page Dialog
3. Windows 11 Default PDF Viewer Setup Dialog
4. About & Shortcuts Guide Dialog
"""

import os
from typing import Dict, Any
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QMessageBox, QTextBrowser
)
import windows_integration as wi
from app_config import APP_VERSION


class DocumentPropertiesDialog(QDialog):
    def __init__(self, metadata: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Document Properties")
        self.setFixedSize(520, 460)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        title_lbl = QLabel("Document Details")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #3b82f6;")
        layout.addWidget(title_lbl)

        # Metadata Table
        table = QTableWidget(len(metadata), 2, self)
        table.setHorizontalHeaderLabels(["Property", "Value"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        row = 0
        for k, v in metadata.items():
            k_item = QTableWidgetItem(str(k))
            k_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            v_item = QTableWidgetItem(str(v))
            v_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 0, k_item)
            table.setItem(row, 1, v_item)
            row += 1

        layout.addWidget(table)

        # Close button
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        close_btn = QPushButton("Close", self)
        close_btn.setFixedWidth(90)
        close_btn.clicked.connect(self.accept)
        btn_box.addWidget(close_btn)
        layout.addLayout(btn_box)


class GoToPageDialog(QDialog):
    def __init__(self, current_page: int, total_pages: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Go to Page")
        self.setFixedSize(300, 150)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        prompt_lbl = QLabel(f"Enter page number (1 – {total_pages}):")
        prompt_lbl.setStyleSheet("font-weight: 500;")
        layout.addWidget(prompt_lbl)

        self.spin = QSpinBox(self)
        self.spin.setRange(1, max(1, total_pages))
        self.spin.setValue(current_page + 1)
        self.spin.selectAll()
        self.spin.setStyleSheet("font-size: 14px; padding: 4px;")
        layout.addWidget(self.spin)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(cancel_btn)

        go_btn = QPushButton("Go", self)
        go_btn.setDefault(True)
        go_btn.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold;")
        go_btn.clicked.connect(self.accept)
        btn_box.addWidget(go_btn)
        layout.addLayout(btn_box)

    def get_selected_page(self) -> int:
        return self.spin.value() - 1  # 0-indexed


class WindowsDefaultAppDialog(QDialog):
    def __init__(self, current_file: str = "", parent=None):
        super().__init__(parent)
        self.current_file = current_file
        self.setWindowTitle("Set PrincePDF as Windows 11 Default PDF Viewer")
        self.setFixedSize(540, 420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title_lbl = QLabel("Windows 11 Default PDF Viewer Integration")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #3b82f6;")
        layout.addWidget(title_lbl)

        # Status badge
        is_reg = wi.is_registered()
        status_text = "✓ PrincePDF is registered with Windows 11" if is_reg else "● Registering PrincePDF..."
        status_color = "#10b981" if is_reg else "#f59e0b"
        self.status_lbl = QLabel(status_text)
        self.status_lbl.setStyleSheet(f"color: {status_color}; font-weight: bold; font-size: 13px;")
        layout.addWidget(self.status_lbl)

        info_box = QTextBrowser(self)
        info_box.setHtml("""
            <div style="font-family: 'Segoe UI', sans-serif; font-size: 12px; line-height: 1.5;">
                <p>In Windows 11, setting a default PDF viewer is safe and user-controlled:</p>
                <ol style="margin-left: -15px;">
                    <li><b>Step 1:</b> Click <b>Register & Open Windows Settings</b> below.</li>
                    <li><b>Step 2:</b> In the Windows Settings window, search for <b>.pdf</b> or <b>PrincePDF</b>.</li>
                    <li><b>Step 3:</b> Click on <b>PrincePDF</b> and choose <b>Set default</b>!</li>
                </ol>
                <p>Alternatively, you can click <b>Choose with Windows Prompt</b> to set it directly for PDF files.</p>
            </div>
        """)
        layout.addWidget(info_box)

        # Buttons
        btn_grid = QVBoxLayout()
        btn_grid.setSpacing(10)

        self.open_settings_btn = QPushButton("① Register & Open Windows 11 Default Apps Settings", self)
        self.open_settings_btn.setFixedHeight(36)
        self.open_settings_btn.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; font-size: 12px; border-radius: 6px;")
        self.open_settings_btn.clicked.connect(self._on_register_and_open_settings)
        btn_grid.addWidget(self.open_settings_btn)

        if self.current_file:
            self.open_with_btn = QPushButton("② Set Default via Windows 'Open With' Prompt", self)
            self.open_with_btn.setFixedHeight(34)
            self.open_with_btn.clicked.connect(self._on_open_with_prompt)
            btn_grid.addWidget(self.open_with_btn)

        self.shortcut_btn = QPushButton("Create Desktop Shortcut", self)
        self.shortcut_btn.setFixedHeight(32)
        self.shortcut_btn.clicked.connect(self._on_create_shortcut)
        btn_grid.addWidget(self.shortcut_btn)

        layout.addLayout(btn_grid)

        # Close
        close_box = QHBoxLayout()
        close_box.addStretch()
        done_btn = QPushButton("Done", self)
        done_btn.setFixedWidth(80)
        done_btn.clicked.connect(self.accept)
        close_box.addWidget(done_btn)
        layout.addLayout(close_box)

    def _on_register_and_open_settings(self):
        ok, msg = wi.register_windows_file_association()
        if ok:
            self.status_lbl.setText("✓ PrincePDF is registered with Windows 11")
            self.status_lbl.setStyleSheet("color: #10b981; font-weight: bold; font-size: 13px;")
            wi.open_windows_default_apps()
            QMessageBox.information(
                self,
                "Windows 11 Settings Opened",
                "Windows Default Apps settings has been opened!\n\n"
                "Search for '.pdf' in the search box, click on it, and select 'PrincePDF'."
            )
        else:
            QMessageBox.warning(self, "Registration Error", msg)

    def _on_open_with_prompt(self):
        wi.register_windows_file_association()
        if self.current_file and os.path.exists(self.current_file):
            wi.open_windows_open_with(self.current_file)

    def _on_create_shortcut(self):
        ok, msg = wi.create_desktop_shortcut()
        if ok:
            QMessageBox.information(self, "Shortcut Created", "Desktop shortcut 'PrincePDF' created successfully!")
        else:
            QMessageBox.warning(self, "Error", f"Could not create shortcut: {msg}")


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About PrincePDF")
        self.setFixedSize(500, 440)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Header with app icon and title
        header = QHBoxLayout()
        icon_path = wi.get_png_icon_path()
        if icon_path and os.path.exists(icon_path):
            icon_lbl = QLabel(self)
            dpr = self.devicePixelRatioF() if hasattr(self, "devicePixelRatioF") else 1.0
            size_px = int(56 * dpr)
            pix = QPixmap(icon_path).scaled(size_px, size_px, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            pix.setDevicePixelRatio(dpr)
            icon_lbl.setPixmap(pix)
            header.addWidget(icon_lbl)

        title_box = QVBoxLayout()
        title_lbl = QLabel("PrincePDF")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #3b82f6;")
        sub_lbl = QLabel(f"Version {APP_VERSION} — Modern High-Performance PDF Viewer")
        sub_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header.addLayout(title_box)
        header.addStretch()
        layout.addLayout(header)

        # Content info
        browser = QTextBrowser(self)
        browser.setHtml("""
            <div style="font-family: 'Segoe UI', sans-serif; font-size: 12px; line-height: 1.5;">
                <p><b>PrincePDF</b> is engineered for speed, clean aesthetics, and seamless Windows 11 integration.</p>
                <p><b>Key Features:</b></p>
                <ul>
                    <li><b>High Performance:</b> Instant rendering via PyMuPDF native C++ engine with smart LRU caching.</li>
                    <li><b>Versatile Views:</b> Single page, Continuous scroll, and Side-by-side (2-page spread).</li>
                    <li><b>Text Copying:</b> Native word-level selection with Ctrl+C and context menu copying.</li>
                    <li><b>Search:</b> In-document text search with match highlights and snippet previews.</li>
                    <li><b>Night Mode:</b> Instant PDF color inversion for comfortable low-light reading.</li>
                    <li><b>Windows 11 Ready:</b> Direct default app registration and High-DPI support.</li>
                </ul>
                <p><b>Shortcuts:</b><br>
                <code>Ctrl+O</code> Open &nbsp;|&nbsp; <code>Ctrl+F</code> Find &nbsp;|&nbsp; <code>Ctrl+C</code> Copy &nbsp;|&nbsp; <code>Ctrl+G</code> Go to<br>
                <code>Ctrl++ / Ctrl+-</code> Zoom &nbsp;|&nbsp; <code>Ctrl+0</code> 100% &nbsp;|&nbsp; <code>Ctrl+1/2</code> Fit Page/Width<br>
                <code>Ctrl+R</code> Rotate &nbsp;|&nbsp; <code>F4</code> Sidebar &nbsp;|&nbsp; <code>F11</code> Fullscreen
                </p>
            </div>
        """)
        layout.addWidget(browser)

        # Close button
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        close_btn = QPushButton("OK", self)
        close_btn.setFixedWidth(80)
        close_btn.clicked.connect(self.accept)
        btn_box.addWidget(close_btn)
        layout.addLayout(btn_box)
