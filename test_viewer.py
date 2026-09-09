"""
Automated Test Suite for PrincePDF
Tests:
1. DocumentModel loading, metadata, TOC, search, and word extraction
2. RenderCache pixmap rendering, thumbnail generation, and night mode inversion
3. PdfPageWidget rendering, word selection, and text copying
4. PdfViewWidget view modes (Single, Continuous, Side-by-Side) and zooming
5. Windows 11 integration and registry registration
"""

import sys
import os
import fitz
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from document_model import DocumentModel
from render_cache import RenderCache
from page_widget import PdfPageWidget
from pdf_view_widget import PdfViewWidget, ViewMode
from viewer_window import ViewerWindow
import windows_integration as wi


def run_tests():
    print("=== Starting PrincePDF Automated Test Suite ===")

    # Initialize QApplication for GUI testing
    app = QApplication.instance() or QApplication(sys.argv)

    # Test 1: DocumentModel
    pdf_path = os.path.abspath("sample_document.pdf")
    assert os.path.exists(pdf_path), "sample_document.pdf does not exist!"
    
    doc_model = DocumentModel(pdf_path)
    assert doc_model.is_open, "DocumentModel failed to open document!"
    assert doc_model.page_count == 3, f"Expected 3 pages, got {doc_model.page_count}"
    print("[PASS] Test 1: DocumentModel loaded sample_document.pdf (3 pages)")

    # Test 2: Metadata & Outline
    meta = doc_model.get_metadata()
    assert meta["Pages"] == 3
    print("[PASS] Test 2: Metadata verified:", meta["Title"], f"({meta['File Size']})")

    toc = doc_model.get_toc()
    assert len(toc) == 3, f"Expected 3 TOC entries, got {len(toc)}"
    print("[PASS] Test 3: Outline / Table of Contents verified (3 bookmarks)")

    # Test 3: Words & Text Extraction
    words_p0 = doc_model.get_page_words(0)
    assert len(words_p0) > 0, "Failed to extract words from page 0"
    print(f"[PASS] Test 4: Extracted {len(words_p0)} words from page 0")

    # Test 4: Search Engine
    search_results = doc_model.search_document("PrincePDF")
    assert len(search_results) >= 2, f"Expected at least 2 pages with 'PrincePDF', got {len(search_results)}"
    total_matches = sum(len(r["rects"]) for r in search_results)
    print(f"[PASS] Test 5: Search engine found 'PrincePDF' in {len(search_results)} pages ({total_matches} occurrences)")

    # Test 5: RenderCache
    cache = RenderCache()
    pm = cache.get_pixmap(doc_model, 0, zoom=1.0, rotation=0, night_mode=False)
    assert pm is not None and not pm.isNull(), "Failed to render page pixmap!"
    assert pm.width() == 612 and pm.height() == 792, f"Unexpected dimensions: {pm.width()}x{pm.height()}"
    print(f"[PASS] Test 6: RenderCache rendered page 0 pixmap ({pm.width()}x{pm.height()})")

    pm_night = cache.get_pixmap(doc_model, 0, zoom=1.0, rotation=0, night_mode=True)
    assert pm_night is not None and not pm_night.isNull(), "Failed to render night mode pixmap!"
    print("[PASS] Test 7: Night Mode color inversion rendered successfully")

    thumb = cache.get_thumbnail(doc_model, 0, max_width=130)
    assert thumb is not None and not thumb.isNull(), "Failed to render thumbnail!"
    print(f"[PASS] Test 8: RenderCache generated thumbnail ({thumb.width()}x{thumb.height()})")

    # Test 6: PdfPageWidget & Text Selection
    page_widget = PdfPageWidget(0, doc_model, cache)
    assert page_widget.width() == 612 and page_widget.height() == 792
    page_widget.select_all()
    copied = page_widget.copy_selection()
    assert "PrincePDF" in copied, f"Expected 'PrincePDF' in selected text, got: {copied[:50]}"
    print(f"[PASS] Test 9: PdfPageWidget text selection & copy verified ({len(copied)} chars selected)")

    # Test 7: PdfViewWidget Modes and Zooming
    view_widget = PdfViewWidget(doc_model, cache)
    view_widget.load_document()
    assert len(view_widget.page_widgets) == 3

    # Test View Modes
    view_widget.set_view_mode(ViewMode.SINGLE)
    assert view_widget.view_mode == ViewMode.SINGLE
    view_widget.set_view_mode(ViewMode.CONTINUOUS)
    assert view_widget.view_mode == ViewMode.CONTINUOUS
    view_widget.set_view_mode(ViewMode.SIDE_BY_SIDE)
    assert view_widget.view_mode == ViewMode.SIDE_BY_SIDE
    print("[PASS] Test 10: All 3 view modes verified (Single, Continuous, Side-by-Side)")

    # Test Zooming
    view_widget.set_zoom(1.5)
    assert abs(view_widget.zoom - 1.5) < 0.01
    view_widget.zoom_in()
    assert view_widget.zoom > 1.5
    view_widget.zoom_out()
    view_widget.reset_zoom()
    assert abs(view_widget.zoom - 1.0) < 0.01
    print("[PASS] Test 11: Zoom controls verified (in, out, reset, custom)")

    # Test Rotation
    view_widget.rotate_clockwise()
    assert view_widget.rotation == 90
    view_widget.rotate_counter_clockwise()
    assert view_widget.rotation == 0
    print("[PASS] Test 12: Clockwise and counter-clockwise rotation verified")

    # Test 8: Windows 11 Registration
    assert wi.is_registered(), "PrincePDF is not registered in HKCU!"
    print("[PASS] Test 13: Windows 11 file association registration verified")

    # Test 9: ViewerWindow Integration
    win = ViewerWindow(pdf_path)
    assert win.doc_model.is_open
    assert win.total_pages_lbl.text() == "/ 3"
    print("[PASS] Test 14: ViewerWindow full UI integration verified")

    # Test 10: Custom Unified Title & Menu Bar
    assert win.windowFlags() & Qt.WindowType.FramelessWindowHint, "FramelessWindowHint not set!"
    assert hasattr(win, "custom_title_bar"), "custom_title_bar not found on ViewerWindow!"
    assert win.menuWidget() == win.custom_title_bar, "custom_title_bar is not set as menuWidget!"
    assert "sample_document.pdf" in win.custom_title_bar.title_lbl.text(), f"Expected document name in title, got: {win.custom_title_bar.title_lbl.text()}"
    assert win.custom_title_bar.min_btn is not None
    assert win.custom_title_bar.max_btn is not None
    assert win.custom_title_bar.close_btn is not None
    print(f"[PASS] Test 15: Custom Title & Menu Bar verified (Title: '{win.custom_title_bar.title_lbl.text()}')")

    # Test 11: Document Close & Title Reset
    win.close_document()
    assert win.custom_title_bar.title_lbl.text() == "PrincePDF", f"Expected 'PrincePDF', got '{win.custom_title_bar.title_lbl.text()}'"
    print("[PASS] Test 16: Document close resets title label to 'PrincePDF'")

    win.close()
    print("\n=== ALL 16 TESTS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    run_tests()
