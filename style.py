"""
PrincePDF - Modern Minimalist Windows 11 Theme Stylesheets
Provides cohesive, sleek Fluent-inspired Dark and Light themes.
"""


def get_stylesheet(theme: str = "dark") -> str:
    is_dark = (theme == "dark")

    bg = "#181a20" if is_dark else "#f3f4f6"
    surface = "#20232c" if is_dark else "#ffffff"
    surface_alt = "#1b1d24" if is_dark else "#f8fafc"
    surface_hover = "#2c303c" if is_dark else "#e9ecef"
    surface_active = "#373c4b" if is_dark else "#dee2e6"
    border = "#333846" if is_dark else "#d0d7de"
    text = "#f8fafc" if is_dark else "#0f172a"
    text_muted = "#94a3b8" if is_dark else "#64748b"
    accent = "#3b82f6" if is_dark else "#2563eb"
    accent_hover = "#60a5fa" if is_dark else "#1d4ed8"

    return f"""
        QMainWindow, QDialog {{
            background-color: {bg};
            color: {text};
            font-family: "Segoe UI Variable Text", "Segoe UI", -apple-system, sans-serif;
            font-size: 13px;
        }}

        QWidget {{
            background-color: transparent;
            color: {text};
            font-family: "Segoe UI Variable Text", "Segoe UI", -apple-system, sans-serif;
            font-size: 13px;
        }}

        /* Top Menu Bar */
        QMenuBar {{
            background-color: {surface_alt};
            color: {text};
            border-bottom: 1px solid {border};
            padding: 2px 6px;
        }}
        QMenuBar::item {{
            background: transparent;
            padding: 6px 10px;
            border-radius: 4px;
        }}
        QMenuBar::item:selected {{
            background-color: {surface_hover};
        }}
        QMenu {{
            background-color: {surface};
            color: {text};
            border: 1px solid {border};
            border-radius: 6px;
            padding: 4px;
        }}
        QMenu::item {{
            padding: 6px 24px 6px 12px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background-color: {accent};
            color: #ffffff;
        }}
        QMenu::separator {{
            height: 1px;
            background-color: {border};
            margin: 4px 8px;
        }}

        /* Modern Toolbar */
        QToolBar {{
            background-color: {surface_alt};
            border-bottom: 1px solid {border};
            padding: 4px 8px;
            spacing: 6px;
        }}
        QToolButton {{
            background-color: transparent;
            color: {text};
            border: 1px solid transparent;
            border-radius: 5px;
            padding: 5px 8px;
            font-size: 12px;
            font-weight: 500;
        }}
        QToolButton:hover {{
            background-color: {surface_hover};
            border: 1px solid {border};
        }}
        QToolButton:pressed, QToolButton:checked {{
            background-color: {surface_active};
            border: 1px solid {accent};
            color: {accent};
        }}
        QToolBar::separator {{
            width: 1px;
            background-color: {border};
            margin: 4px 6px;
        }}

        /* Buttons */
        QPushButton {{
            background-color: {surface};
            color: {text};
            border: 1px solid {border};
            border-radius: 5px;
            padding: 5px 12px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {surface_hover};
            border-color: {accent};
        }}
        QPushButton:pressed {{
            background-color: {surface_active};
        }}
        QPushButton:disabled {{
            color: {text_muted};
            border-color: {border};
            background-color: transparent;
        }}

        /* Input Controls */
        QLineEdit, QSpinBox, QComboBox {{
            background-color: {surface};
            color: {text};
            border: 1px solid {border};
            border-radius: 5px;
            padding: 4px 8px;
            selection-background-color: {accent};
        }}
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
            border-color: {accent};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: none;
        }}
        QComboBox QAbstractItemView {{
            background-color: {surface};
            color: {text};
            border: 1px solid {border};
            selection-background-color: {accent};
            selection-color: #ffffff;
            border-radius: 4px;
            padding: 2px;
        }}

        /* Status Bar */
        QStatusBar {{
            background-color: {surface_alt};
            color: {text_muted};
            border-top: 1px solid {border};
            padding: 3px 8px;
            font-size: 12px;
        }}
        QStatusBar QLabel {{
            color: {text_muted};
        }}

        /* Tooltip */
        QToolTip {{
            background-color: {surface};
            color: {text};
            border: 1px solid {border};
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 11px;
        }}

        /* Splitter */
        QSplitter::handle {{
            background-color: {border};
        }}
        QSplitter::handle:horizontal {{
            width: 1px;
        }}
        QSplitter::handle:vertical {{
            height: 1px;
        }}

        /* Tables & Lists */
        QTableWidget, QTreeWidget, QListWidget {{
            background-color: {surface};
            color: {text};
            border: 1px solid {border};
            border-radius: 6px;
            gridline-color: {border};
        }}
        QHeaderView::section {{
            background-color: {surface_alt};
            color: {text_muted};
            padding: 6px;
            border: none;
            border-bottom: 1px solid {border};
            font-weight: bold;
        }}
        QTextBrowser {{
            background-color: {surface};
            color: {text};
            border: 1px solid {border};
            border-radius: 6px;
        }}
    """
