"""
PrincePDF - Modern Floating / Inline Search Bar
Provides quick in-document search with match counts, next/prev navigation, and match case.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLineEdit, QPushButton, QLabel, QCheckBox
)


class SearchBar(QFrame):
    searchRequested = pyqtSignal(str, bool)
    findNextRequested = pyqtSignal()
    findPrevRequested = pyqtSignal()
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SearchBarFrame")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        # Search Input
        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("Find in document... (Ctrl+F)")
        self.input_field.setClearButtonEnabled(True)
        self.input_field.setMinimumWidth(200)
        self.input_field.textChanged.connect(self._on_text_changed)
        self.input_field.returnPressed.connect(self._on_enter_pressed)
        layout.addWidget(self.input_field)

        # Match Count Label
        self.count_label = QLabel("0 matches", self)
        self.count_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(self.count_label)

        # Prev Button
        self.prev_btn = QPushButton("▲", self)
        self.prev_btn.setToolTip("Previous Match (Shift+Enter)")
        self.prev_btn.setFixedSize(26, 26)
        self.prev_btn.clicked.connect(self.findPrevRequested.emit)
        layout.addWidget(self.prev_btn)

        # Next Button
        self.next_btn = QPushButton("▼", self)
        self.next_btn.setToolTip("Next Match (Enter)")
        self.next_btn.setFixedSize(26, 26)
        self.next_btn.clicked.connect(self.findNextRequested.emit)
        layout.addWidget(self.next_btn)

        # Match Case Checkbox
        self.case_checkbox = QCheckBox("Aa", self)
        self.case_checkbox.setToolTip("Match Case")
        self.case_checkbox.stateChanged.connect(self._on_text_changed)
        layout.addWidget(self.case_checkbox)

        # Close Button
        self.close_btn = QPushButton("✕", self)
        self.close_btn.setToolTip("Close Search (Esc)")
        self.close_btn.setFixedSize(26, 26)
        self.close_btn.clicked.connect(self.hide_and_clear)
        layout.addWidget(self.close_btn)

        self._apply_styling()

    def _apply_styling(self):
        self.setStyleSheet("""
            #SearchBarFrame {
                background-color: #242730;
                border: 1px solid #3a3f4d;
                border-radius: 8px;
            }
            QLineEdit {
                background-color: #1b1d23;
                color: #f1f5f9;
                border: 1px solid #3a3f4d;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
            QPushButton {
                background-color: #2c303c;
                color: #f1f5f9;
                border: 1px solid #3a3f4d;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3b82f6;
                color: #ffffff;
                border: 1px solid #3b82f6;
            }
            QCheckBox {
                color: #f1f5f9;
                font-weight: bold;
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border-radius: 3px;
                border: 1px solid #3a3f4d;
                background-color: #1b1d23;
            }
            QCheckBox::indicator:checked {
                background-color: #3b82f6;
                border-color: #3b82f6;
            }
        """)

    def set_theme(self, is_dark: bool):
        bg = "#242730" if is_dark else "#ffffff"
        border = "#3a3f4d" if is_dark else "#d0d7de"
        input_bg = "#1b1d23" if is_dark else "#f6f8fa"
        text = "#f1f5f9" if is_dark else "#1f2328"
        btn_bg = "#2c303c" if is_dark else "#f3f4f6"
        lbl_color = "#94a3b8" if is_dark else "#656d76"

        self.count_label.setStyleSheet(f"color: {lbl_color}; font-size: 11px;")
        self.setStyleSheet(f"""
            #SearchBarFrame {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            QLineEdit {{
                background-color: {input_bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid #3b82f6;
            }}
            QPushButton {{
                background-color: {btn_bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #3b82f6;
                color: #ffffff;
                border: 1px solid #3b82f6;
            }}
            QCheckBox {{
                color: {text};
                font-weight: bold;
                font-size: 12px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border-radius: 3px;
                border: 1px solid {border};
                background-color: {input_bg};
            }}
            QCheckBox::indicator:checked {{
                background-color: #3b82f6;
                border-color: #3b82f6;
            }}
        """)

    def show_and_focus(self):
        self.show()
        self.input_field.setFocus()
        self.input_field.selectAll()

    def hide_and_clear(self):
        self.hide()
        self.closed.emit()

    def update_match_count(self, current_index: int, total_count: int):
        if total_count == 0:
            self.count_label.setText("No matches")
            self.count_label.setStyleSheet("color: #ef4444; font-size: 11px;")
        else:
            self.count_label.setText(f"{current_index + 1} of {total_count}")
            self.count_label.setStyleSheet("color: #10b981; font-size: 11px; font-weight: bold;")

    def _on_text_changed(self):
        query = self.input_field.text().strip()
        match_case = self.case_checkbox.isChecked()
        self.searchRequested.emit(query, match_case)

    def _on_enter_pressed(self):
        self.findNextRequested.emit()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.hide_and_clear()
            event.accept()
            return
        super().keyPressEvent(event)
