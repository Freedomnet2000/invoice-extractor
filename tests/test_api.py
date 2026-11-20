from app.documents import prepare
from app.schemas import Invoice
from app.validation import check


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["provider"] == "mock"


def test_index_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Invoice Extractor" in r.text


def test_extract_text_pdf(client, text_pdf):
    r = client.post("/extract", files={"file": ("invoice.pdf", text_pdf, "application/pdf")})
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "text"
    assert body["invoice"]["total_amount"] == 1180.0
    assert body["warnings"] == []


def test_scanned_pdf_falls_back_to_image(client, blank_pdf):
    r = client.post("/extract", files={"file": ("scan.pdf", blank_pdf, "application/pdf")})
    assert r.status_code == 200
    assert r.json()["source"] == "image"


def test_extract_image(client, png_image):
    r = client.post("/extract", files={"file": ("receipt.png", png_image, "image/png")})
    assert r.status_code == 200
    assert r.json()["source"] == "image"


def test_rejects_unsupported_type(client):
    r = client.post("/extract", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert r.status_code == 415


def test_rejects_empty_file(client):
    r = client.post("/extract", files={"file": ("empty.pdf", b"", "application/pdf")})
    assert r.status_code == 400


def test_prepare_reads_pdf_text(text_pdf):
    doc = prepare(text_pdf, "a.pdf", "application/pdf")
    assert doc.kind == "text"
    assert "INV-1001" in doc.text


def test_validation_flags_mismatched_totals():
    inv = Invoice(subtotal=100, vat_amount=18, total_amount=150)
    assert any("does not match total" in w for w in check(inv))


def test_validation_flags_low_confidence():
    inv = Invoice(total_amount=10, confidence={"vendor_name": 0.3})
    assert any("low confidence" in w for w in check(inv))


def test_validation_accepts_consistent_invoice():
    inv = Invoice(
        subtotal=1000,
        vat_amount=180,
        total_amount=1180,
        line_items=[{"description": "x", "total": 1000}],
    )
    assert check(inv) == []
