from collections import Counter
from pathlib import Path
from typing import List
import logging
import os
import re

from pypdf import PdfReader

from .models import PageText


LOGGER = logging.getLogger(__name__)
_SPACE_RE = re.compile(r"[ \t]+")
_MULTI_BLANK_RE = re.compile(r"\n{3,}")
_HYPHEN_BREAK_RE = re.compile(r"(?<=\w)-\n(?=\w)")


def _clean_text(raw_text: str) -> str:
    if not raw_text:
        return ""

    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    text = _HYPHEN_BREAK_RE.sub("", text)

    normalized_lines = []
    for line in text.split("\n"):
        line = _SPACE_RE.sub(" ", line).strip()
        normalized_lines.append(line)

    text = "\n".join(normalized_lines)
    text = _MULTI_BLANK_RE.sub("\n\n", text)
    return text.strip()


def _remove_repeated_headers_footers(pages: List[PageText]) -> List[PageText]:
    if len(pages) < 3:
        return pages

    first_lines_counter = Counter()
    last_lines_counter = Counter()

    for page in pages:
        lines = [line.strip() for line in page.text.splitlines() if line.strip()]

        for line in lines[:2]:
            if len(line) <= 120:
                first_lines_counter[line] += 1

        for line in lines[-2:]:
            if len(line) <= 120:
                last_lines_counter[line] += 1

    threshold = max(2, int(len(pages) * 0.7))
    repeated_first = {line for line, count in first_lines_counter.items() if count >= threshold}
    repeated_last = {line for line, count in last_lines_counter.items() if count >= threshold}

    cleaned_pages: List[PageText] = []

    for page in pages:
        lines = [line.strip() for line in page.text.splitlines() if line.strip()]

        while lines and lines[0] in repeated_first:
            lines.pop(0)

        while lines and lines[-1] in repeated_last:
            lines.pop()

        cleaned_text = "\n".join(lines).strip()
        if cleaned_text:
            cleaned_pages.append(PageText(page_number=page.page_number, text=cleaned_text))

    return cleaned_pages


def _extract_with_pypdf(pdf_path: Path) -> tuple[int, List[PageText]]:
    reader = PdfReader(str(pdf_path))
    pages = []

    for index, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        cleaned = _clean_text(raw_text)
        if cleaned:
            pages.append(PageText(page_number=index, text=cleaned))

    return len(reader.pages), pages


def _extract_with_pymupdf(pdf_path: Path) -> tuple[int, List[PageText]]:
    try:
        import fitz  # PyMuPDF
    except Exception as exc:
        raise RuntimeError(
            "PyMuPDF is not installed. Install dependencies again to enable fallback extractor."
        ) from exc

    doc = fitz.open(str(pdf_path))
    total_pages = doc.page_count
    pages = []

    try:
        for index in range(total_pages):
            page = doc.load_page(index)
            raw_text = page.get_text("text") or ""
            cleaned = _clean_text(raw_text)
            if cleaned:
                pages.append(PageText(page_number=index + 1, text=cleaned))
    finally:
        doc.close()

    return total_pages, pages


def _extract_with_ocr(pdf_path: Path) -> tuple[int, List[PageText]]:
    try:
        import fitz  # PyMuPDF
        import pytesseract
        from PIL import Image
    except Exception as exc:
        raise RuntimeError(
            "OCR dependencies are not installed. Install pytesseract and pillow."
        ) from exc

    tesseract_cmd = os.getenv("TESSERACT_CMD", "").strip()
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    ocr_lang = os.getenv("UPLOAD_OCR_LANG", "eng").strip() or "eng"
    ocr_zoom = float(os.getenv("UPLOAD_OCR_ZOOM", "2.0"))

    doc = fitz.open(str(pdf_path))
    total_pages = doc.page_count
    pages = []

    try:
        matrix = fitz.Matrix(ocr_zoom, ocr_zoom)

        for index in range(total_pages):
            page = doc.load_page(index)
            pix = page.get_pixmap(matrix=matrix, alpha=False)

            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            raw_text = pytesseract.image_to_string(image, lang=ocr_lang) or ""

            cleaned = _clean_text(raw_text)
            if cleaned:
                pages.append(PageText(page_number=index + 1, text=cleaned))
    finally:
        doc.close()

    return total_pages, pages


def extract_pdf_pages(pdf_path: Path) -> List[PageText]:
    total_pages = 0
    pages: List[PageText] = []

    try:
        total_pages, pages = _extract_with_pypdf(pdf_path)
    except Exception:
        LOGGER.exception("pypdf extraction failed | file=%s", pdf_path.name)

    if not pages:
        try:
            fallback_total_pages, fallback_pages = _extract_with_pymupdf(pdf_path)
            if total_pages == 0:
                total_pages = fallback_total_pages
            pages = fallback_pages
            LOGGER.info("Fallback extractor used (PyMuPDF) | file=%s", pdf_path.name)
        except Exception:
            LOGGER.exception("PyMuPDF fallback extraction failed | file=%s", pdf_path.name)

    if not pages:
        try:
            ocr_total_pages, ocr_pages = _extract_with_ocr(pdf_path)
            if total_pages == 0:
                total_pages = ocr_total_pages
            pages = ocr_pages
            LOGGER.info("Fallback extractor used (OCR) | file=%s", pdf_path.name)
        except Exception:
            LOGGER.exception("OCR fallback extraction failed | file=%s", pdf_path.name)

    pages = _remove_repeated_headers_footers(pages)

    LOGGER.info(
        "PDF extracted | file=%s | total_pages=%s | text_pages=%s",
        pdf_path.name,
        total_pages,
        len(pages),
    )

    return pages
