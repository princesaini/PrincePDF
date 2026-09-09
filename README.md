# PrincePDF 🚀
**A Fast, Modern, and Minimalist PDF Viewer for Windows 11**

PrincePDF is an ultra-responsive, lightweight PDF viewer written in Python with PyQt6 and PyMuPDF (MuPDF C++ engine). It is designed to deliver fluid 60+ FPS navigation, crisp High-DPI typography, modern Windows 11 Fluent dark and light styling, and seamless integration as your default system PDF reader.

---

## ✨ Key Features

- ⚡ **Instant Rendering & High Performance**: Powered by native PyMuPDF C++ rasterization with smart LRU page and thumbnail memory caching. Only visible pages plus neighboring buffer pages are rendered in high resolution.
- 📐 **Multiple View Modes**:
  - **Single Page View**: Focus on one page at a time with instant keyboard/wheel page-flipping.
  - **Continuous Scroll View**: Smooth vertical reading flow with automatic page tracking.
  - **Side-by-Side (Spread) View**: Two-page book/manual spread view.
- 🔍 **Smooth Zooming**:
  - Dynamic Zoom (`10%` to `800%`) with `Ctrl + Mouse Wheel`, `Ctrl + +`, `Ctrl + -`.
  - **Fit to Width** (`Ctrl + 2`) and **Fit to Page** (`Ctrl + 1`).
  - Pre-calibrated zoom dropdown (`50%`, `75%`, `100%`, `125%`, `150%`, `200%`, `300%`, `400%`).
- 📋 **Native Text Selection & Copy**:
  - Click and drag over text with standard semi-transparent blue highlights.
  - Double-click to select a word, triple-click to select a line, or `Ctrl + A` to select all text on the current page.
  - Right-click context menu or `Ctrl + C` to copy formatted text to the Windows clipboard.
- 🔎 **In-Document Search (Ctrl + F)**:
  - Floating search bar with real-time match counter (`3 of 24`).
  - Next (`Enter` / `F3`) and Previous (`Shift + Enter` / `Shift + F3`) match navigation.
  - On-page highlighting (bright yellow with vivid orange active match).
  - Search results panel in the sidebar with page badges and contextual text snippets.
- 🌙 **Night Reading Mode (Ctrl + N)**:
  - High-speed color inversion inverting white backgrounds to dark for eye-friendly nighttime reading.
- 🌓 **Modern Fluent UI Themes**:
  - Windows 11 Dark Mode and Light Mode with a 1-click switcher.
  - Minimalist toolbar with crisp iconography, clean tooltips, and page jump box.
- 📑 **Collapsible Sidebar (F4)**:
  - **Page Thumbnails**: Visual gallery of all pages with active page highlight.
  - **Document Outline / Bookmarks**: Interactive table of contents tree view.
  - **Search Results**: List of matching pages and excerpts.
- 🖨️ **Print & Export**:
  - Native Windows printing dialog with page ranges (`Ctrl + P`).
  - "Save As..." to export copies (`Ctrl + S`).
- 🪟 **Windows 11 Default PDF Viewer Integration**:
  - Registers `PrincePDF.Document` ProgID and `.pdf` file association in `HKCU` without requiring administrator privileges.
  - Seamlessly appears in Windows 11 Default Apps (`ms-settings:defaultapps`) and "Open With" menus.
  - Generates desktop shortcuts and silent windowless launchers (`pythonw.exe`).
  - Drag and drop any `.pdf` directly onto the viewer.

---

## ⌨️ Keyboard Shortcuts Reference

| Action | Shortcut |
| :--- | :--- |
| **Open File** | `Ctrl + O` |
| **Save As** | `Ctrl + S` |
| **Print Document** | `Ctrl + P` |
| **Close Document** | `Ctrl + W` |
| **Copy Selected Text** | `Ctrl + C` |
| **Select All on Page** | `Ctrl + A` |
| **Find in Page** | `Ctrl + F` |
| **Find Next / Previous** | `Enter` / `Shift + Enter` |
| **Next Page** | `Page Down` / `Down Arrow` / `Right Arrow` / `Space` |
| **Previous Page** | `Page Up` / `Up Arrow` / `Left Arrow` / `Shift + Space` |
| **First / Last Page** | `Home` / `End` |
| **Go to Page Dialog** | `Ctrl + G` |
| **Single Page View** | `Ctrl + Alt + 1` |
| **Continuous Scroll** | `Ctrl + Alt + 2` |
| **Side-by-Side (Spread)**| `Ctrl + Alt + 3` |
| **Zoom In / Zoom Out** | `Ctrl + +` / `Ctrl + -` (or `Ctrl + Wheel`) |
| **Actual Size (100%)** | `Ctrl + 0` |
| **Fit to Page** | `Ctrl + 1` |
| **Fit to Width** | `Ctrl + 2` |
| **Rotate Clockwise** | `Ctrl + R` |
| **Night Reading Mode** | `Ctrl + N` |
| **Toggle Sidebar** | `F4` |
| **Fullscreen Mode** | `F11` (or `Esc` to exit) |
| **Document Properties** | `Ctrl + D` |

---

## 🛠️ How to Set as Default PDF Viewer in Windows 11

1. Open PrincePDF (or run `PrincePDF.exe`) and go to **Tools** → **Set as Windows 11 Default PDF Viewer...**
2. Click **① Register & Open Windows 11 Default Apps Settings** (this automatically registers `PrincePDF.exe` with Windows 11).
3. In the Windows Settings search box, type `.pdf` (or `PrincePDF`).
4. Click on `.pdf` and select **PrincePDF** as your default app.
5. **Direct Explorer Method**: Right-click any `.pdf` file in Windows Explorer, select **Open with** → **Choose another app** → choose **PrincePDF** (or click *Choose an app on your PC* and select `PrincePDF.exe`) → select **"Always"**.

---

## 📁 Project Architecture

```
PrincePDF/
├── PrincePDF.exe            # Standalone single-file Windows 11 executable (85 MB)
├── main.py                  # Entry point, High-DPI setup, AppUserModelID, CLI args
├── viewer_window.py         # Main window, menus, modern toolbar, status bar
├── pdf_view_widget.py       # Core viewer: Single, Continuous, Side-by-Side views
├── page_widget.py           # Individual page: vector text selection, copy, search hits
├── sidebar_widget.py        # Collapsible sidebar: Thumbnails, Outline, Search hits
├── search_bar.py            # Floating / inline search control with match count
├── document_model.py        # PyMuPDF document interface, text, search, metadata
├── render_cache.py          # LRU memory cache, pixmap rendering, night mode inversion
├── windows_integration.py   # Registry file associations, Default Apps, desktop shortcut
├── app_config.py            # Settings persistence (~/.princepdf_config.json)
├── style.py                 # Modern Fluent-inspired Dark and Light stylesheets
├── dialogs.py               # Document properties, Go to page, Default app, About
├── resources/
│   ├── app_icon.ico         # Multi-resolution (16 to 256px) Windows icon
│   ├── app_icon.png         # 1024x1024 master supersampled PNG
│   ├── app_icon_512.png     # 512x512 High-DPI icon
│   └── app_icon_256.png     # 256x256 High-DPI icon
├── PrincePDF.bat            # Quick command-line launcher
├── PrincePDF.vbs            # Silent background launcher (no command window)
├── sample_document.pdf      # Test document with multi-page text & outline
└── test_viewer.py           # Automated test suite (14 test cases)
```

---

## 🚀 Running PrincePDF

### Direct Executable (Recommended for Windows 11):
Double-click:
```
PrincePDF.exe
```
Or open a PDF with the executable from command line:
```bash
.\PrincePDF.exe "sample_document.pdf"
```

### From Python Source:
```bash
python main.py "sample_document.pdf"
```
Or silently without console window:
```bash
pythonw main.py
```

To run the automated test suite:
```bash
python test_viewer.py
```
