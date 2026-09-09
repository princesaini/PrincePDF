"""
PrincePDF - Main Application Entry Point
High-performance, modern, and minimalist PDF viewer for Windows 11.
"""

import sys
import os
import ctypes

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication, QIcon
from PyQt6.QtWidgets import QApplication

from viewer_window import ViewerWindow
import windows_integration as wi


def main():
    # 1. Set Windows 11 AppUserModelID so taskbar displays app icon properly
    if sys.platform == "win32":
        try:
            myappid = "princepdf.viewer.modern.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    # 2. Configure High-DPI Scaling for razor-sharp rendering on 4K/retina displays
    try:
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("PrincePDF")
    app.setApplicationDisplayName("PrincePDF")
    app.setOrganizationName("Prince")

    # Set Application Icon
    icon_path = wi.get_icon_path()
    if icon_path and os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Parse CLI argument for PDF file
    initial_file = None
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--register":
            ok, msg = wi.register_windows_file_association()
            print(msg)
            sys.exit(0 if ok else 1)
        elif os.path.exists(arg) and arg.lower().endswith(".pdf"):
            initial_file = os.path.abspath(arg)

    # Automatically register file association if not already registered
    if not wi.is_registered():
        try:
            wi.register_windows_file_association()
        except Exception:
            pass

    window = ViewerWindow(initial_filepath=initial_file)
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
