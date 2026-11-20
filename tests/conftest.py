import io
import os

import pytest
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

os.environ.setdefault("LLM_PROVIDER", "mock")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def text_pdf() -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    lines = [
        "Example Ltd. - Tax ID 515123456",
        "Invoice INV-1001   Date: 2026-11-01",
        "Consulting services   1 x 1,000.00 = 1,000.00",
        "Subtotal 1,000.00   VAT 18% 180.00   Total 1,180.00 ILS",
    ]
    for i, line in enumerate(lines):
        c.drawString(72, 760 - i * 20, line)
    c.save()
    return buf.getvalue()


@pytest.fixture
def blank_pdf() -> bytes:
    """A PDF with no extractable text, like a scanned invoice."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.rect(72, 600, 200, 100)
    c.save()
    return buf.getvalue()


@pytest.fixture
def png_image() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (400, 300), "white").save(buf, format="PNG")
    return buf.getvalue()
