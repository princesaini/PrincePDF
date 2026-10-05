"""
PrincePDF - Document Model
High performance PyMuPDF wrapper providing document management, text extraction,
search indexing, outline/bookmarks, and metadata.
"""

import os
import fitz
from typing import List, Dict, Any, Optional, Tuple


class DocumentModel:
    def __init__(self, filepath: Optional[str] = None):
        self.filepath: Optional[str] = None
        self.doc: Optional[fitz.Document] = None
        self._page_count: int = 0
        self._words_cache: Dict[int, List[Tuple]] = {}
        if filepath:
            self.load(filepath)

    def load(self, filepath: str) -> bool:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        self.close()
        self.filepath = os.path.abspath(filepath)
        self.doc = fitz.open(self.filepath)
        self._page_count = len(self.doc)
        self._words_cache.clear()
        return True

    def close(self):
        if self.doc:
            try:
                self.doc.close()
            except Exception:
                pass
            self.doc = None
        self.filepath = None
        self._page_count = 0
        self._words_cache.clear()

    @property
    def is_open(self) -> bool:
        return self.doc is not None and not self.doc.is_closed

    @property
    def page_count(self) -> int:
        return self._page_count

    @property
    def file_name(self) -> str:
        if not self.filepath:
            return "Untitled"
        return os.path.basename(self.filepath)

    @property
    def file_size_str(self) -> str:
        if not self.filepath or not os.path.exists(self.filepath):
            return "Unknown"
        size_bytes = os.path.getsize(self.filepath)
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def get_page(self, page_num: int) -> Optional[fitz.Page]:
        if not self.is_open or page_num < 0 or page_num >= self._page_count:
            return None
        return self.doc[page_num]

    def get_page_size(self, page_num: int, rotation: int = 0) -> Tuple[float, float]:
        page = self.get_page(page_num)
        if not page:
            return (612.0, 792.0)
        rect = page.rect
        eff_rotation = (page.rotation + rotation) % 360
        if eff_rotation in (90, 270):
            return (rect.height, rect.width)
        return (rect.width, rect.height)

    def get_metadata(self) -> Dict[str, Any]:
        if not self.is_open:
            return {}
        meta = self.doc.metadata or {}
        page_size_str = "N/A"
        if self._page_count > 0:
            w, h = self.get_page_size(0)
            label = ""
            if abs(w - 612) < 2 and abs(h - 792) < 2:
                label = " (Letter)"
            elif abs(w - 595) < 2 and abs(h - 842) < 2:
                label = " (A4)"
            page_size_str = f"{int(w)} × {int(h)} pt{label}"

        return {
            "Title": meta.get("title") or self.file_name,
            "Author": meta.get("author") or "N/A",
            "Subject": meta.get("subject") or "N/A",
            "Keywords": meta.get("keywords") or "N/A",
            "Creator": meta.get("creator") or "N/A",
            "Producer": meta.get("producer") or "N/A",
            "CreationDate": meta.get("creationDate") or "N/A",
            "ModDate": meta.get("modDate") or "N/A",
            "Format": meta.get("format") or "PDF",
            "Pages": self._page_count,
            "Page Size": page_size_str,
            "File Size": self.file_size_str,
            "File Path": self.filepath or "N/A",
        }

    def get_toc(self) -> List[List]:
        """Returns [[level, title, page_number, ...], ...] where page is 1-indexed."""
        if not self.is_open:
            return []
        try:
            return self.doc.get_toc()
        except Exception:
            return []

    def get_page_words(self, page_num: int) -> List[Tuple]:
        """
        Returns cached list of words:
        [(x0, y0, x1, y1, "word", block_no, line_no, word_no), ...]
        """
        if page_num in self._words_cache:
            return self._words_cache[page_num]
        
        page = self.get_page(page_num)
        if not page:
            return []
        
        try:
            words = page.get_text("words")
            self._words_cache[page_num] = words
            return words
        except Exception:
            return []

    def get_text_in_rect(self, page_num: int, rect: fitz.Rect) -> str:
        page = self.get_page(page_num)
        if not page:
            return ""
        try:
            return page.get_text("text", clip=rect)
        except Exception:
            return ""

    def get_full_page_text(self, page_num: int) -> str:
        page = self.get_page(page_num)
        if not page:
            return ""
        try:
            return page.get_text("text")
        except Exception:
            return ""

    def search_page(self, page_num: int, query: str, match_case: bool = False) -> List[fitz.Rect]:
        if not self.is_open or not query:
            return []
        page = self.get_page(page_num)
        if not page:
            return []
        try:
            flags = 0
            if not match_case:
                flags |= fitz.TEXT_DEHYPHENATE
            # search_for returns list of fitz.Rect
            return page.search_for(query, flags=flags)
        except Exception:
            return []

    def search_document(self, query: str, match_case: bool = False) -> List[Dict[str, Any]]:
        """
        Searches entire document and returns:
        [{
           "page": page_index (0-based),
           "page_display": page_index + 1,
           "rects": [fitz.Rect, ...],
           "snippet": "...",
        }, ...]
        """
        results = []
        if not self.is_open or not query.strip():
            return results

        q = query if match_case else query.lower()

        for p_idx in range(self._page_count):
            rects = self.search_page(p_idx, query, match_case)
            if rects:
                # Find a text snippet around the first match
                page_text = self.get_full_page_text(p_idx)
                snippet = ""
                idx = page_text.find(query) if match_case else page_text.lower().find(q)
                if idx != -1:
                    start = max(0, idx - 40)
                    end = min(len(page_text), idx + len(query) + 40)
                    prefix = "..." if start > 0 else ""
                    suffix = "..." if end < len(page_text) else ""
                    snippet = prefix + page_text[start:end].replace("\n", " ") + suffix

                results.append({
                    "page": p_idx,
                    "page_display": p_idx + 1,
                    "rects": rects,
                    "count": len(rects),
                    "snippet": snippet or f"Match found on page {p_idx + 1}",
                })

        return results

    def get_page_links(self, page_num: int) -> List[Dict[str, Any]]:
        page = self.get_page(page_num)
        if not page:
            return []
        try:
            return page.get_links()
        except Exception:
            return []
