"""
PrincePDF - Main Application Window
Integrates document model, high-performance view widget, collapsible sidebar,
modern toolbar, menu actions, print support, and Windows 11 integration.
"""

import os
import sys
import ctypes
from ctypes import wintypes
from typing import Optional

from PyQt6.QtCore import Qt, QSize, QEvent
from PyQt6.QtGui import (
    QAction, QIcon, QKeySequence, QDragEnterEvent, QDropEvent,
    QPixmap, QPainter, QCursor, QIntValidator
)
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QToolBar, QToolButton, QComboBox, QLineEdit, QLabel,
    QFileDialog, QMessageBox, QStatusBar, QStackedWidget,
    QPushButton, QFrame, QApplication
)
from custom_title_bar import CustomTitleBar

from app_config import AppConfig
from document_model import DocumentModel
from render_cache import RenderCache
from pdf_view_widget import PdfViewWidget, ViewMode
from sidebar_widget import SidebarWidget
from search_bar import SearchBar
import windows_integration as wi
import style


class WelcomeWidget(QWidget):
    """Modern drag & drop landing card displayed when no document is open."""
    def __init__(self, open_callback, recent_callback, parent=None):
        super().__init__(parent)
        self.open_callback = open_callback
        self.recent_callback = recent_callback
        self.is_dark = True

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)

        self.card = QFrame(self)
        self.card.setObjectName("WelcomeCard")
        self.card.setFixedWidth(520)
        card_layout = QVBoxLayout(self.card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(16)

        # Icon / Logo
        png_path = wi.get_png_icon_path()
        if png_path and os.path.exists(png_path):
            logo = QLabel(self.card)
            dpr = self.card.devicePixelRatioF() if hasattr(self.card, "devicePixelRatioF") else 1.0
            size_px = int(80 * dpr)
            pix = QPixmap(png_path).scaled(size_px, size_px, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            pix.setDevicePixelRatio(dpr)
            logo.setPixmap(pix)
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(logo)

        # Welcome Text
        title = QLabel("PrincePDF", self.card)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #3b82f6;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        self.subtitle = QLabel("Fast, Minimalist & Modern PDF Viewer for Windows 11\nDrag & drop a PDF file here or open from disk", self.card)
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.subtitle)

        # Open File Button
        open_btn = QPushButton("📂 Open PDF File", self.card)
        open_btn.setFixedHeight(40)
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                padding: 8px 24px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        open_btn.clicked.connect(self.open_callback)
        card_layout.addWidget(open_btn)

        # Recent Files Box
        self.recent_frame = QFrame(self.card)
        self.recent_layout = QVBoxLayout(self.recent_frame)
        self.recent_layout.setContentsMargins(0, 10, 0, 0)
        self.recent_layout.setSpacing(6)
        card_layout.addWidget(self.recent_frame)

        layout.addWidget(self.card)
        self.set_theme(is_dark=True)

    def set_theme(self, is_dark: bool):
        self.is_dark = is_dark
        card_bg = "#20232c" if is_dark else "#ffffff"
        card_border = "#3a3f4d" if is_dark else "#cbd5e1"
        sub_color = "#94a3b8" if is_dark else "#64748b"
        self.card.setStyleSheet(f"""
            QFrame#WelcomeCard {{
                background-color: {card_bg};
                border: 2px dashed {card_border};
                border-radius: 12px;
                padding: 30px;
            }}
        """)
        self.subtitle.setStyleSheet(f"font-size: 13px; color: {sub_color}; text-align: center;")
        self.refresh_recents()

    def refresh_recents(self):
        # Clear previous items
        while self.recent_layout.count():
            child = self.recent_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        config = AppConfig()
        recents = config.get_recent_files()
        if recents:
            header_color = "#94a3b8" if self.is_dark else "#64748b"
            header = QLabel("Recent Documents:")
            header.setStyleSheet(f"color: {header_color}; font-size: 11px; font-weight: bold; text-transform: uppercase;")
            self.recent_layout.addWidget(header)

            btn_bg = "#181a20" if self.is_dark else "#f8fafc"
            btn_color = "#f1f5f9" if self.is_dark else "#0f172a"
            btn_border = "#333846" if self.is_dark else "#e2e8f0"
            btn_hover = "#2c303c" if self.is_dark else "#f1f5f9"

            for path in recents[:5]:
                btn = QPushButton(f"📄 {os.path.basename(path)}")
                btn.setToolTip(path)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        text-align: left;
                        background-color: {btn_bg};
                        color: {btn_color};
                        border: 1px solid {btn_border};
                        border-radius: 5px;
                        padding: 6px 12px;
                        font-size: 12px;
                    }}
                    QPushButton:hover {{
                        background-color: {btn_hover};
                        border-color: #3b82f6;
                    }}
                """)
                btn.clicked.connect(lambda checked, p=path: self.recent_callback(p))
                self.recent_layout.addWidget(btn)


class ViewerWindow(QMainWindow):
    def __init__(self, initial_filepath: Optional[str] = None):
        super().__init__()
        self.config = AppConfig()
        self.doc_model = DocumentModel()
        self.render_cache = RenderCache()

        self.current_theme = self.config.get("theme", "dark")
        self.is_night_mode = self.config.get("night_mode", False)

        # Frameless Window for modern Windows 11 look
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(800, 600)

        # Restore window geometry and state
        saved_geom = self.config.get("window_geometry")
        if saved_geom and len(saved_geom) == 4:
            self.setGeometry(*saved_geom)
        if self.config.get("window_maximized", True):
            self.setWindowState(Qt.WindowState.WindowMaximized)

        # Enable Windows 11 DWM shadow and rounded corners
        if sys.platform == "win32":
            try:
                class MARGINS(ctypes.Structure):
                    _fields_ = [
                        ("cxLeftWidth", ctypes.c_int),
                        ("cxRightWidth", ctypes.c_int),
                        ("cyTopHeight", ctypes.c_int),
                        ("cyBottomHeight", ctypes.c_int),
                    ]
                margins = MARGINS(1, 1, 1, 1)
                ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(int(self.winId()), ctypes.byref(margins))
            except Exception:
                pass

        # Set App Icon
        icon_path = wi.get_icon_path()
        if icon_path and os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Enable Drag & Drop
        self.setAcceptDrops(True)

        # Unified Custom Title & Menu Bar
        self.custom_title_bar = CustomTitleBar(self)
        self.setMenuWidget(self.custom_title_bar)

        self.setWindowTitle("PrincePDF")

        # Build UI Components
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_statusbar()
        self._apply_theme()

        # Restore user preferences
        saved_mode = self.config.get("view_mode", ViewMode.CONTINUOUS)
        self.set_view_mode(saved_mode)
        sidebar_vis = self.config.get("sidebar_visible", True)
        self.sidebar.setVisible(sidebar_vis)
        saved_tab = self.config.get("sidebar_tab", 0)
        if 0 <= saved_tab < self.sidebar.tab_widget.count():
            self.sidebar.tab_widget.setCurrentIndex(saved_tab)
        saved_zoom_mode = self.config.get("zoom_mode", "fit_width")
        self.pdf_view.zoom_mode = saved_zoom_mode
        if saved_zoom_mode == "custom":
            saved_zoom = self.config.get("custom_zoom", 1.0)
            self.pdf_view.set_zoom(saved_zoom)

        # Connect Search
        self._search_matches = []
        self._current_search_idx = -1

        # Load initial file if specified
        if initial_filepath and os.path.exists(initial_filepath):
            self.open_file(initial_filepath)
        else:
            self._show_welcome()

    # -------------------------------------------------------------------------
    # UI Setup
    # -------------------------------------------------------------------------
    def _setup_ui(self):
        # Central Splitter: Sidebar + Main Content
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.splitter.setChildrenCollapsible(False)
        self.setCentralWidget(self.splitter)

        # Left: Sidebar
        self.sidebar = SidebarWidget(self.doc_model, self.render_cache, self)
        self.sidebar.pageSelected.connect(self._on_sidebar_page_selected)
        self.sidebar.searchResultSelected.connect(self._on_search_result_selected)
        self.splitter.addWidget(self.sidebar)

        # Right: Main Content Area
        right_container = QWidget(self)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Inline Search Bar (Hidden by default)
        self.search_bar = SearchBar(right_container)
        self.search_bar.hide()
        self.search_bar.searchRequested.connect(self._on_search_requested)
        self.search_bar.findNextRequested.connect(self._on_find_next)
        self.search_bar.findPrevRequested.connect(self._on_find_prev)
        self.search_bar.closed.connect(self._on_search_closed)
        right_layout.addWidget(self.search_bar)

        # Stacked Widget: Welcome Card vs PDF Viewer
        self.stack = QStackedWidget(right_container)
        self.welcome_view = WelcomeWidget(self.choose_and_open_file, self.open_file, self)
        self.pdf_view = PdfViewWidget(self.doc_model, self.render_cache, self)

        self.pdf_view.currentPageChanged.connect(self._on_page_changed)
        self.pdf_view.zoomChanged.connect(self._on_zoom_changed)
        self.pdf_view.statusMessageRequested.connect(self._show_status_message)
        self.pdf_view.linkClicked.connect(self._on_link_clicked)

        self.stack.addWidget(self.welcome_view)
        self.stack.addWidget(self.pdf_view)
        right_layout.addWidget(self.stack)

        self.splitter.addWidget(right_container)
        self.splitter.setSizes([260, 940])

    # -------------------------------------------------------------------------
    # Menus
    # -------------------------------------------------------------------------
    def _setup_menus(self):
        menubar = self.custom_title_bar.menu_bar

        def add_act(menu, action):
            menu.addAction(action)
            self.addAction(action)
            return action

        # File Menu
        file_menu = menubar.addMenu("&File")

        open_action = QAction("📂 &Open...", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.choose_and_open_file)
        add_act(file_menu, open_action)

        self.recent_menu = file_menu.addMenu("🕒 Open &Recent")
        self._update_recent_menu()

        file_menu.addSeparator()

        save_action = QAction("💾 Save &As...", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_as)
        add_act(file_menu, save_action)

        print_action = QAction("🖨️ &Print...", self)
        print_action.setShortcut(QKeySequence("Ctrl+P"))
        print_action.triggered.connect(self.print_document)
        add_act(file_menu, print_action)

        file_menu.addSeparator()

        close_action = QAction("✕ &Close Document", self)
        close_action.setShortcut(QKeySequence("Ctrl+W"))
        close_action.triggered.connect(self.close_document)
        add_act(file_menu, close_action)

        exit_action = QAction("🚪 E&xit", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)
        add_act(file_menu, exit_action)

        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")

        copy_action = QAction("📋 &Copy Text", self)
        copy_action.setShortcut(QKeySequence("Ctrl+C"))
        copy_action.triggered.connect(self.pdf_view.copy_current_selection)
        add_act(edit_menu, copy_action)

        select_all_action = QAction("☑️ &Select All (Page)", self)
        select_all_action.setShortcut(QKeySequence("Ctrl+A"))
        select_all_action.triggered.connect(self.pdf_view.select_all_current_page)
        add_act(edit_menu, select_all_action)

        edit_menu.addSeparator()

        find_action = QAction("🔍 &Find in Document...", self)
        find_action.setShortcut(QKeySequence("Ctrl+F"))
        find_action.triggered.connect(self.toggle_search_bar)
        add_act(edit_menu, find_action)

        find_next_action = QAction("Find Next", self)
        find_next_action.setShortcut(QKeySequence("F3"))
        find_next_action.triggered.connect(self._on_find_next)
        add_act(edit_menu, find_next_action)

        find_prev_action = QAction("Find Previous", self)
        find_prev_action.setShortcut(QKeySequence("Shift+F3"))
        find_prev_action.triggered.connect(self._on_find_prev)
        add_act(edit_menu, find_prev_action)

        # View Menu
        view_menu = menubar.addMenu("&View")

        # View Modes
        single_action = QAction("📄 Single Page View", self)
        single_action.setShortcut(QKeySequence("Ctrl+Alt+1"))
        single_action.triggered.connect(lambda: self.set_view_mode(ViewMode.SINGLE))
        add_act(view_menu, single_action)

        continuous_action = QAction("📜 Continuous Scroll View", self)
        continuous_action.setShortcut(QKeySequence("Ctrl+Alt+2"))
        continuous_action.triggered.connect(lambda: self.set_view_mode(ViewMode.CONTINUOUS))
        add_act(view_menu, continuous_action)

        side_action = QAction("📖 Side-by-Side (Spread) View", self)
        side_action.setShortcut(QKeySequence("Ctrl+Alt+3"))
        side_action.triggered.connect(lambda: self.set_view_mode(ViewMode.SIDE_BY_SIDE))
        add_act(view_menu, side_action)

        view_menu.addSeparator()

        zoom_in_act = QAction("➕ Zoom &In", self)
        zoom_in_act.setShortcut(QKeySequence("Ctrl+="))
        zoom_in_act.triggered.connect(self.pdf_view.zoom_in)
        add_act(view_menu, zoom_in_act)

        zoom_out_act = QAction("➖ Zoom &Out", self)
        zoom_out_act.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out_act.triggered.connect(self.pdf_view.zoom_out)
        add_act(view_menu, zoom_out_act)

        zoom_100_act = QAction("100% Actual Size", self)
        zoom_100_act.setShortcut(QKeySequence("Ctrl+0"))
        zoom_100_act.triggered.connect(self.pdf_view.reset_zoom)
        add_act(view_menu, zoom_100_act)

        fit_w_act = QAction("⬌ Fit to &Width", self)
        fit_w_act.setShortcut(QKeySequence("Ctrl+2"))
        fit_w_act.triggered.connect(self.pdf_view.set_fit_width)
        add_act(view_menu, fit_w_act)

        fit_p_act = QAction("⬍ Fit to &Page", self)
        fit_p_act.setShortcut(QKeySequence("Ctrl+1"))
        fit_p_act.triggered.connect(self.pdf_view.set_fit_page)
        add_act(view_menu, fit_p_act)

        view_menu.addSeparator()

        rot_cw_act = QAction("↻ Rotate Clockwise", self)
        rot_cw_act.setShortcut(QKeySequence("Ctrl+R"))
        rot_cw_act.triggered.connect(self.rotate_clockwise)
        add_act(view_menu, rot_cw_act)

        rot_ccw_act = QAction("↺ Rotate Counter-Clockwise", self)
        rot_ccw_act.setShortcut(QKeySequence("Ctrl+Shift+R"))
        rot_ccw_act.triggered.connect(self.rotate_counter_clockwise)
        add_act(view_menu, rot_ccw_act)

        night_act = QAction("🌙 Night Reading Mode", self)
        night_act.setCheckable(True)
        night_act.setChecked(self.is_night_mode)
        night_act.setShortcut(QKeySequence("Ctrl+N"))
        night_act.triggered.connect(self.toggle_night_mode)
        add_act(view_menu, night_act)

        view_menu.addSeparator()

        sidebar_act = QAction("📑 Toggle Sidebar", self)
        sidebar_act.setShortcut(QKeySequence("F4"))
        sidebar_act.triggered.connect(self.toggle_sidebar)
        add_act(view_menu, sidebar_act)

        fs_act = QAction("⛶ Fullscreen", self)
        fs_act.setShortcut(QKeySequence("F11"))
        fs_act.triggered.connect(self.toggle_fullscreen)
        add_act(view_menu, fs_act)

        theme_act = QAction("🌓 Toggle Dark / Light Theme", self)
        theme_act.triggered.connect(self.toggle_theme)
        add_act(view_menu, theme_act)

        # Go Menu
        go_menu = menubar.addMenu("&Go")

        next_act = QAction("Next Page", self)
        next_act.setShortcut(QKeySequence("PgDown"))
        next_act.triggered.connect(self.pdf_view.next_page)
        add_act(go_menu, next_act)

        prev_act = QAction("Previous Page", self)
        prev_act.setShortcut(QKeySequence("PgUp"))
        prev_act.triggered.connect(self.pdf_view.prev_page)
        add_act(go_menu, prev_act)

        first_act = QAction("First Page", self)
        first_act.setShortcut(QKeySequence("Home"))
        first_act.triggered.connect(self.pdf_view.first_page)
        add_act(go_menu, first_act)

        last_act = QAction("Last Page", self)
        last_act.setShortcut(QKeySequence("End"))
        last_act.triggered.connect(self.pdf_view.last_page)
        add_act(go_menu, last_act)

        go_menu.addSeparator()

        goto_act = QAction("Go to Page...", self)
        goto_act.setShortcut(QKeySequence("Ctrl+G"))
        goto_act.triggered.connect(self.show_goto_dialog)
        add_act(go_menu, goto_act)

        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")

        default_app_act = QAction("⚙️ Set as Windows 11 Default PDF Viewer...", self)
        default_app_act.triggered.connect(self.show_default_app_dialog)
        add_act(tools_menu, default_app_act)

        shortcut_act = QAction("📌 Create Desktop Shortcut", self)
        shortcut_act.triggered.connect(self.create_desktop_shortcut)
        add_act(tools_menu, shortcut_act)

        tools_menu.addSeparator()

        props_act = QAction("ℹ️ Document Properties...", self)
        props_act.setShortcut(QKeySequence("Ctrl+D"))
        props_act.triggered.connect(self.show_properties_dialog)
        add_act(tools_menu, props_act)

        # Help Menu
        help_menu = menubar.addMenu("&Help")

        about_act = QAction("About PrincePDF", self)
        about_act.triggered.connect(self.show_about_dialog)
        add_act(help_menu, about_act)

    # -------------------------------------------------------------------------
    # Toolbar
    # -------------------------------------------------------------------------
    def _setup_toolbar(self):
        self.toolbar = QToolBar("Main Controls", self)
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(self.toolbar)

        # Sidebar Toggle
        self.sidebar_btn = QToolButton(self)
        self.sidebar_btn.setText("📑")
        self.sidebar_btn.setToolTip("Toggle Sidebar (F4)")
        self.sidebar_btn.clicked.connect(self.toggle_sidebar)
        self.toolbar.addWidget(self.sidebar_btn)

        # Open
        open_btn = QToolButton(self)
        open_btn.setText("📂 Open")
        open_btn.setToolTip("Open PDF File (Ctrl+O)")
        open_btn.clicked.connect(self.choose_and_open_file)
        self.toolbar.addWidget(open_btn)

        self.toolbar.addSeparator()

        # Page Navigation
        self.prev_btn = QToolButton(self)
        self.prev_btn.setText("◀")
        self.prev_btn.setToolTip("Previous Page (PgUp)")
        self.prev_btn.clicked.connect(self.pdf_view.prev_page)
        self.toolbar.addWidget(self.prev_btn)

        self.page_input = QLineEdit(self)
        self.page_input.setFixedWidth(42)
        self.page_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_input.setText("1")
        self.page_input.setValidator(QIntValidator(1, 99999, self))
        self.page_input.returnPressed.connect(self._on_page_input_entered)
        self.toolbar.addWidget(self.page_input)

        self.total_pages_lbl = QLabel("/ 0", self)
        self.total_pages_lbl.setStyleSheet("color: #94a3b8; font-weight: 500; padding: 0 4px;")
        self.toolbar.addWidget(self.total_pages_lbl)

        self.next_btn = QToolButton(self)
        self.next_btn.setText("▶")
        self.next_btn.setToolTip("Next Page (PgDown)")
        self.next_btn.clicked.connect(self.pdf_view.next_page)
        self.toolbar.addWidget(self.next_btn)

        self.toolbar.addSeparator()

        # Zoom Controls
        zoom_out_btn = QToolButton(self)
        zoom_out_btn.setText("➖")
        zoom_out_btn.setToolTip("Zoom Out (Ctrl+-)")
        zoom_out_btn.clicked.connect(self.pdf_view.zoom_out)
        self.toolbar.addWidget(zoom_out_btn)

        self.zoom_combo = QComboBox(self)
        self.zoom_combo.setFixedWidth(82)
        self.zoom_combo.setEditable(True)
        if self.zoom_combo.lineEdit():
            self.zoom_combo.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.zoom_combo.lineEdit().returnPressed.connect(self._on_zoom_combo_entered)
        self.zoom_combo.addItems(["50%", "75%", "100%", "125%", "150%", "200%", "300%", "400%"])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.activated.connect(self._on_zoom_combo_activated)
        self.toolbar.addWidget(self.zoom_combo)

        zoom_in_btn = QToolButton(self)
        zoom_in_btn.setText("➕")
        zoom_in_btn.setToolTip("Zoom In (Ctrl++)")
        zoom_in_btn.clicked.connect(self.pdf_view.zoom_in)
        self.toolbar.addWidget(zoom_in_btn)

        fit_w_btn = QToolButton(self)
        fit_w_btn.setText("⬌ Width")
        fit_w_btn.setToolTip("Fit to Width (Ctrl+2)")
        fit_w_btn.clicked.connect(self.pdf_view.set_fit_width)
        self.toolbar.addWidget(fit_w_btn)

        fit_p_btn = QToolButton(self)
        fit_p_btn.setText("⬍ Page")
        fit_p_btn.setToolTip("Fit to Page (Ctrl+1)")
        fit_p_btn.clicked.connect(self.pdf_view.set_fit_page)
        self.toolbar.addWidget(fit_p_btn)

        self.toolbar.addSeparator()

        # View Mode Group
        self.single_mode_btn = QToolButton(self)
        self.single_mode_btn.setText("📄")
        self.single_mode_btn.setToolTip("Single Page View (Ctrl+Alt+1)")
        self.single_mode_btn.setCheckable(True)
        self.single_mode_btn.clicked.connect(lambda: self.set_view_mode(ViewMode.SINGLE))
        self.toolbar.addWidget(self.single_mode_btn)

        self.cont_mode_btn = QToolButton(self)
        self.cont_mode_btn.setText("📜")
        self.cont_mode_btn.setToolTip("Continuous Scroll View (Ctrl+Alt+2)")
        self.cont_mode_btn.setCheckable(True)
        self.cont_mode_btn.setChecked(True)
        self.cont_mode_btn.clicked.connect(lambda: self.set_view_mode(ViewMode.CONTINUOUS))
        self.toolbar.addWidget(self.cont_mode_btn)

        self.spread_mode_btn = QToolButton(self)
        self.spread_mode_btn.setText("📖")
        self.spread_mode_btn.setToolTip("Side-by-Side (2 Pages) View (Ctrl+Alt+3)")
        self.spread_mode_btn.setCheckable(True)
        self.spread_mode_btn.clicked.connect(lambda: self.set_view_mode(ViewMode.SIDE_BY_SIDE))
        self.toolbar.addWidget(self.spread_mode_btn)

        self.toolbar.addSeparator()

        # Rotate
        rot_btn = QToolButton(self)
        rot_btn.setText("↻")
        rot_btn.setToolTip("Rotate Clockwise (Ctrl+R)")
        rot_btn.clicked.connect(self.rotate_clockwise)
        self.toolbar.addWidget(rot_btn)

        # Night Mode
        self.night_btn = QToolButton(self)
        self.night_btn.setText("🌙")
        self.night_btn.setToolTip("Invert PDF Colors for Night Reading (Ctrl+N)")
        self.night_btn.setCheckable(True)
        self.night_btn.setChecked(self.is_night_mode)
        self.night_btn.clicked.connect(self.toggle_night_mode)
        self.toolbar.addWidget(self.night_btn)

        # Search
        find_btn = QToolButton(self)
        find_btn.setText("🔍")
        find_btn.setToolTip("Search in Document (Ctrl+F)")
        find_btn.clicked.connect(self.toggle_search_bar)
        self.toolbar.addWidget(find_btn)

        # Spacer to push theme and fullscreen to right
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().horizontalPolicy().Expanding, spacer.sizePolicy().verticalPolicy().Preferred)
        self.toolbar.addWidget(spacer)

        # Theme
        self.theme_btn = QToolButton(self)
        self.theme_btn.setText("☀️ Light" if self.current_theme == "dark" else "🌙 Dark")
        self.theme_btn.setToolTip("Switch Dark / Light Theme")
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.toolbar.addWidget(self.theme_btn)

        # Fullscreen
        fs_btn = QToolButton(self)
        fs_btn.setText("⛶")
        fs_btn.setToolTip("Toggle Fullscreen (F11)")
        fs_btn.clicked.connect(self.toggle_fullscreen)
        self.toolbar.addWidget(fs_btn)

    # -------------------------------------------------------------------------
    # Status Bar
    # -------------------------------------------------------------------------
    def _setup_statusbar(self):
        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)

        self.status_msg_lbl = QLabel("Ready")
        self.statusbar.addWidget(self.status_msg_lbl, 1)

        self.status_dim_lbl = QLabel("")
        self.statusbar.addPermanentWidget(self.status_dim_lbl)

        self.status_zoom_lbl = QLabel("100%")
        self.statusbar.addPermanentWidget(self.status_zoom_lbl)

    # -------------------------------------------------------------------------
    # Theming
    # -------------------------------------------------------------------------
    def _apply_theme(self):
        sheet = style.get_stylesheet(self.current_theme)
        self.setStyleSheet(sheet)
        is_dark = (self.current_theme == "dark")
        self.pdf_view.set_canvas_theme(is_dark)
        self.sidebar.set_theme(is_dark)
        self.search_bar.set_theme(is_dark)
        self.welcome_view.set_theme(is_dark)
        self.theme_btn.setText("☀️ Light" if is_dark else "🌙 Dark")
        self.config.set("theme", self.current_theme)

    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self._apply_theme()

    def toggle_night_mode(self):
        self.is_night_mode = not self.is_night_mode
        self.night_btn.setChecked(self.is_night_mode)
        self.pdf_view.toggle_night_mode(self.is_night_mode)
        self.config.set("night_mode", self.is_night_mode)
        mode_str = "Enabled" if self.is_night_mode else "Disabled"
        self._show_status_message(f"Night reading mode: {mode_str}")

    # -------------------------------------------------------------------------
    # Document Open / Close / Save
    # -------------------------------------------------------------------------
    def choose_and_open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open PDF Document",
            "",
            "PDF Files (*.pdf);;All Files (*.*)"
        )
        if path:
            self.open_file(path)

    def open_file(self, filepath: str):
        if not os.path.exists(filepath):
            QMessageBox.warning(self, "Error", f"File does not exist:\n{filepath}")
            return

        try:
            self.render_cache.clear()
            self.doc_model.load(filepath)

            if self.doc_model.doc and self.doc_model.doc.needs_pass:
                from PyQt6.QtWidgets import QInputDialog
                pwd, ok = QInputDialog.getText(
                    self, "Password Protected PDF",
                    f"'{os.path.basename(filepath)}' is password protected.\nEnter Password:",
                    QLineEdit.EchoMode.Password
                )
                if ok and pwd:
                    if not self.doc_model.doc.authenticate(pwd):
                        QMessageBox.warning(self, "Invalid Password", "Incorrect password for document.")
                        self.close_document()
                        return
                else:
                    self.close_document()
                    return

            self.pdf_view.load_document()
            self.sidebar.load_document()

            self.stack.setCurrentWidget(self.pdf_view)
            self.setWindowTitle(f"{self.doc_model.file_name} - PrincePDF")
            self.total_pages_lbl.setText(f"/ {self.doc_model.page_count}")
            self.page_input.setText("1")

            self.config.add_recent_file(filepath)
            self._update_recent_menu()
            self.welcome_view.refresh_recents()

            self._update_dim_label(0)
            self._show_status_message(f"Loaded {self.doc_model.file_name} ({self.doc_model.file_size_str})")
        except Exception as e:
            QMessageBox.critical(self, "Failed to Open PDF", f"Could not load document:\n{e}")

    def close_document(self):
        self.doc_model.close()
        self.render_cache.clear()
        self.pdf_view.clear_pages()
        self.sidebar.clear()
        self.search_bar.hide_and_clear()
        self._search_matches = []
        self._current_search_idx = -1
        self._show_welcome()

    def _show_welcome(self):
        self.stack.setCurrentWidget(self.welcome_view)
        self.setWindowTitle("PrincePDF")
        self.total_pages_lbl.setText("/ 0")
        self.page_input.setText("0")
        self.status_dim_lbl.setText("")
        self._show_status_message("Welcome to PrincePDF")

    def save_as(self):
        if not self.doc_model.is_open:
            return
        out_path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF As", self.doc_model.file_name, "PDF Files (*.pdf)"
        )
        if out_path:
            try:
                self.doc_model.doc.save(out_path)
                self._show_status_message(f"Saved copy to {os.path.basename(out_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Could not save document:\n{e}")

    def print_document(self):
        if not self.doc_model.is_open:
            return

        from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
        from PyQt6.QtGui import QImage
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            self._show_status_message("Printing document...")
            painter = QPainter(printer)
            total = self.doc_model.page_count

            first_page = printer.fromPage() if printer.fromPage() > 0 else 1
            last_page = printer.toPage() if printer.toPage() > 0 else total
            first_idx = max(0, first_page - 1)
            last_idx = min(total - 1, last_page - 1)

            for idx in range(first_idx, last_idx + 1):
                if idx > first_idx:
                    printer.newPage()
                page = self.doc_model.get_page(idx)
                if page:
                    pix = page.get_pixmap(dpi=300)
                    qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888).copy()
                    target_rect = printer.pageRect(QPrinter.Unit.DevicePixel).toRect()
                    scaled_img = qimg.scaled(
                        target_rect.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    x = target_rect.x() + (target_rect.width() - scaled_img.width()) // 2
                    y = target_rect.y() + (target_rect.height() - scaled_img.height()) // 2
                    painter.drawImage(x, y, scaled_img)

            painter.end()
            self._show_status_message("Printing complete!")

    def _update_recent_menu(self):
        self.recent_menu.clear()
        recents = self.config.get_recent_files()
        if not recents:
            empty_action = QAction("(No recent files)", self)
            empty_action.setEnabled(False)
            self.recent_menu.addAction(empty_action)
            return

        for p in recents:
            act = QAction(f"📄 {os.path.basename(p)}", self)
            act.setToolTip(p)
            act.triggered.connect(lambda checked, path=p: self.open_file(path))
            self.recent_menu.addAction(act)

        self.recent_menu.addSeparator()
        clear_act = QAction("Clear Recent Files", self)
        clear_act.triggered.connect(self._on_clear_recents)
        self.recent_menu.addAction(clear_act)

    def _on_clear_recents(self):
        self.config.clear_recent_files()
        self._update_recent_menu()
        self.welcome_view.refresh_recents()

    # -------------------------------------------------------------------------
    # View Modes & Zoom
    # -------------------------------------------------------------------------
    def set_view_mode(self, mode: str):
        self.single_mode_btn.setChecked(mode == ViewMode.SINGLE)
        self.cont_mode_btn.setChecked(mode == ViewMode.CONTINUOUS)
        self.spread_mode_btn.setChecked(mode == ViewMode.SIDE_BY_SIDE)
        self.pdf_view.set_view_mode(mode)
        self.config.set("view_mode", mode)

    def _on_zoom_changed(self, zoom: float):
        pct = int(round(zoom * 100))
        self.zoom_combo.blockSignals(True)
        self.zoom_combo.setCurrentText(f"{pct}%")
        self.zoom_combo.blockSignals(False)
        self.status_zoom_lbl.setText(f"{pct}%")

    def _on_zoom_combo_activated(self, index: int):
        text = self.zoom_combo.itemText(index).replace("%", "").strip()
        try:
            val = float(text) / 100.0
            self.pdf_view.set_zoom(val)
        except Exception:
            pass

    def _on_zoom_combo_changed(self, text: str):
        text = text.replace("%", "").strip()
        try:
            val = float(text) / 100.0
            self.pdf_view.set_zoom(val)
        except Exception:
            pass

    def _on_zoom_combo_entered(self):
        text = self.zoom_combo.currentText().replace("%", "").strip()
        try:
            val = float(text) / 100.0
            self.pdf_view.set_zoom(val)
        except Exception:
            pass

    def rotate_clockwise(self):
        self.pdf_view.rotate_clockwise()
        self.sidebar.set_rotation(self.pdf_view.rotation)
        self._update_dim_label(self.pdf_view.current_page)

    def rotate_counter_clockwise(self):
        self.pdf_view.rotate_counter_clockwise()
        self.sidebar.set_rotation(self.pdf_view.rotation)
        self._update_dim_label(self.pdf_view.current_page)


    # -------------------------------------------------------------------------
    # Navigation & Page Tracking
    # -------------------------------------------------------------------------
    def _on_page_changed(self, page_num: int):
        self.page_input.setText(str(page_num + 1))
        self.sidebar.highlight_page(page_num)
        self._update_dim_label(page_num)

    def _on_page_input_entered(self):
        try:
            val = int(self.page_input.text().strip())
            self.pdf_view.go_to_page(val - 1)
        except Exception:
            self.page_input.setText(str(self.pdf_view.current_page + 1))

    def _on_sidebar_page_selected(self, page_num: int):
        self.pdf_view.go_to_page(page_num)

    def _update_dim_label(self, page_num: int):
        if not self.doc_model.is_open:
            self.status_dim_lbl.setText("")
            return
        w, h = self.doc_model.get_page_size(page_num, self.pdf_view.rotation)
        # Check standard sizes (Letter: 612x792, A4: 595x842)
        label = ""
        if abs(w - 612) < 2 and abs(h - 792) < 2:
            label = " (Letter)"
        elif abs(w - 595) < 2 and abs(h - 842) < 2:
            label = " (A4)"
        self.status_dim_lbl.setText(f"{int(w)} × {int(h)} pt{label}")

    def _on_link_clicked(self, link: dict):
        uri = link.get("uri")
        if uri:
            import webbrowser
            webbrowser.open(uri)
            self._show_status_message(f"Opened link: {uri}")

    # -------------------------------------------------------------------------
    # Search Handling
    # -------------------------------------------------------------------------
    def toggle_search_bar(self):
        if self.search_bar.isVisible():
            self.search_bar.hide_and_clear()
        else:
            self.search_bar.show_and_focus()

    def _on_search_requested(self, query: str, match_case: bool):
        if not self.doc_model.is_open or not query:
            self.pdf_view.clear_search_highlights()
            self.search_bar.update_match_count(0, 0)
            self._search_matches = []
            self._current_search_idx = -1
            return

        # Global search
        results = self.doc_model.search_document(query, match_case)
        self.sidebar.set_search_results(results)

        # Flatten matches: list of (page_num, rect)
        self._search_matches = []
        for r in results:
            p = r["page"]
            for rect in r["rects"]:
                self._search_matches.append((p, rect))

        total = len(self._search_matches)
        if total > 0:
            self._current_search_idx = 0
            self._navigate_to_search_match(0)
            self.search_bar.update_match_count(0, total)
        else:
            self._current_search_idx = -1
            self.pdf_view.clear_search_highlights()
            self.search_bar.update_match_count(0, 0)

    def _on_find_next(self):
        if not self._search_matches:
            return
        self._current_search_idx = (self._current_search_idx + 1) % len(self._search_matches)
        self._navigate_to_search_match(self._current_search_idx)
        self.search_bar.update_match_count(self._current_search_idx, len(self._search_matches))

    def _on_find_prev(self):
        if not self._search_matches:
            return
        self._current_search_idx = (self._current_search_idx - 1) % len(self._search_matches)
        self._navigate_to_search_match(self._current_search_idx)
        self.search_bar.update_match_count(self._current_search_idx, len(self._search_matches))

    def _navigate_to_search_match(self, match_idx: int):
        if 0 <= match_idx < len(self._search_matches):
            page_num, rect = self._search_matches[match_idx]
            self.pdf_view.scroll_to_rect(page_num, rect)
            # Find all rects on this page for highlighting
            page_rects = [r for p, r in self._search_matches if p == page_num]
            self.pdf_view.show_search_matches(page_num, page_rects, active_rect=rect)

    def _on_search_result_selected(self, page_num: int, rect):
        self.pdf_view.scroll_to_rect(page_num, rect)
        page_rects = [r for p, r in self._search_matches if p == page_num]
        self.pdf_view.show_search_matches(page_num, page_rects, active_rect=rect)

        # Synchronize search match index and counter
        for idx, (p, r) in enumerate(self._search_matches):
            if p == page_num and (r == rect or (abs(r.x0 - rect.x0) < 1.0 and abs(r.y0 - rect.y0) < 1.0)):
                self._current_search_idx = idx
                self.search_bar.update_match_count(idx, len(self._search_matches))
                break

    def _on_search_closed(self):
        self.pdf_view.clear_search_highlights()

    # -------------------------------------------------------------------------
    # Dialogs & Windows Integration
    # -------------------------------------------------------------------------
    def show_properties_dialog(self):
        if not self.doc_model.is_open:
            QMessageBox.information(self, "No Document", "Please open a PDF document first.")
            return
        from dialogs import DocumentPropertiesDialog
        meta = self.doc_model.get_metadata()
        dlg = DocumentPropertiesDialog(meta, self)
        dlg.exec()

    def show_goto_dialog(self):
        if not self.doc_model.is_open:
            return
        from dialogs import GoToPageDialog
        dlg = GoToPageDialog(self.pdf_view.current_page, self.doc_model.page_count, self)
        if dlg.exec() == GoToPageDialog.DialogCode.Accepted:
            self.pdf_view.go_to_page(dlg.get_selected_page())

    def show_default_app_dialog(self):
        from dialogs import WindowsDefaultAppDialog
        current_file = self.doc_model.filepath or ""
        dlg = WindowsDefaultAppDialog(current_file, self)
        dlg.exec()

    def create_desktop_shortcut(self):
        ok, msg = wi.create_desktop_shortcut()
        if ok:
            QMessageBox.information(self, "Shortcut Created", "PrincePDF desktop shortcut created successfully!")
        else:
            QMessageBox.warning(self, "Error", f"Failed to create shortcut: {msg}")

    def show_about_dialog(self):
        from dialogs import AboutDialog
        dlg = AboutDialog(self)
        dlg.exec()

    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showMaximized()
        else:
            self.showFullScreen()

    def _show_status_message(self, text: str):
        self.status_msg_lbl.setText(text)

    # -------------------------------------------------------------------------
    # Drag and Drop
    # -------------------------------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".pdf"):
                    event.acceptProposedAction()
                    return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if filepath.lower().endswith(".pdf"):
                self.open_file(filepath)
                event.acceptProposedAction()
                return
        super().dropEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self.showMaximized()
            event.accept()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        try:
            self.config.set("sidebar_visible", self.sidebar.isVisible())
            self.config.set("sidebar_tab", self.sidebar.tab_widget.currentIndex())
            self.config.set("view_mode", self.pdf_view.view_mode)
            self.config.set("zoom_mode", self.pdf_view.zoom_mode)
            self.config.set("custom_zoom", self.pdf_view.zoom)
            self.config.set("night_mode", self.is_night_mode)
            self.config.set("window_maximized", self.isMaximized())
            if not self.isMaximized() and not self.isFullScreen():
                geom = self.geometry()
                self.config.set("window_geometry", [geom.x(), geom.y(), geom.width(), geom.height()])
        except Exception:
            pass
        self.doc_model.close()
        super().closeEvent(event)

    # -------------------------------------------------------------------------
    # Window State, Frameless Title & Edge Resizing
    # -------------------------------------------------------------------------
    def setWindowTitle(self, title: str):
        super().setWindowTitle(title)
        if hasattr(self, "custom_title_bar") and self.custom_title_bar:
            self.custom_title_bar.set_title(title)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if hasattr(self, "custom_title_bar") and self.custom_title_bar:
                self.custom_title_bar.update_max_button(self.isMaximized())
        super().changeEvent(event)

    def nativeEvent(self, eventType, message):
        if sys.platform == "win32":
            try:
                msg = wintypes.MSG.from_address(int(message))
                if msg.message == 0x0084:  # WM_NCHITTEST
                    if self.isMaximized() or self.isFullScreen():
                        return False, 0
                    pos = self.mapFromGlobal(QCursor.pos())
                    gx, gy = pos.x(), pos.y()
                    w, h = self.width(), self.height()
                    BORDER, CORNER = 6, 14
                    # Check corners first
                    if gx < CORNER and gy < CORNER:
                        return True, 13  # HTTOPLEFT
                    if gx >= w - CORNER and gy < CORNER:
                        return True, 14  # HTTOPRIGHT
                    if gx < CORNER and gy >= h - CORNER:
                        return True, 16  # HTBOTTOMLEFT
                    if gx >= w - CORNER and gy >= h - CORNER:
                        return True, 17  # HTBOTTOMRIGHT
                    # Check edges
                    if gx < BORDER:
                        return True, 10  # HTLEFT
                    if gx >= w - BORDER:
                        return True, 11  # HTRIGHT
                    if gy < BORDER:
                        return True, 12  # HTTOP
                    if gy >= h - BORDER:
                        return True, 15  # HTBOTTOM
            except Exception:
                pass
        return False, 0

