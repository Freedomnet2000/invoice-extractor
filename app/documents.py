"""Turn an uploaded file into something an LLM can read: plain text or a PNG image."""
from __future__ import annotations

import base64
import io
from dataclasses import dataclass

import pypdfium2 as pdfium
from PIL import Image
from pypdf import PdfReader

MIN_TEXT_CHARS = 40  # below this, treat the PDF as scanned and send an image instead
MAX_PAGES = 5


class UnsupportedDocument(ValueError):
    pass


@dataclass
class PreparedDocument:
    kind: str  # "text" or "image"
    text: str | None = None
    image_b64: str | None = None  # base64 PNG
    media_type: str = "image/png"


def _pdf_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    pages = reader.pages[:MAX_PAGES]
    return "\n\n".join((p.extract_text() or "") for p in pages).strip()


def _pdf_first_page_png(data: bytes) -> str:
    pdf = pdfium.PdfDocument(data)
    page = pdf[0]
    image = page.render(scale=2).to_pil()
    return _png_b64(image)


def _png_b64(image: Image.Image) -> str:
    image = image.convert("RGB")
    image.thumbnail((2000, 2000))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def prepare(data: bytes, filename: str, content_type: str | None) -> PreparedDocument:
    name = (filename or "").lower()
    ctype = (content_type or "").lower()

    if name.endswith(".pdf") or ctype == "application/pdf":
        try:
            text = _pdf_text(data)
        except Exception as exc:  # corrupt or encrypted PDF
            raise UnsupportedDocument(f"Could not read PDF: {exc}") from exc
        if len(text) >= MIN_TEXT_CHARS:
            return PreparedDocument(kind="text", text=text)
        return PreparedDocument(kind="image", image_b64=_pdf_first_page_png(data))

    if ctype.startswith("image/") or name.endswith((".png", ".jpg", ".jpeg", ".webp")):
        try:
            image = Image.open(io.BytesIO(data))
        except Exception as exc:
            raise UnsupportedDocument(f"Could not read image: {exc}") from exc
        return PreparedDocument(kind="image", image_b64=_png_b64(image))

    raise UnsupportedDocument("Supported formats: PDF, PNG, JPG, WEBP")
