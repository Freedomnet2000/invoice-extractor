from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from .documents import UnsupportedDocument, prepare
from .extractors import Extractor, get_extractor
from .schemas import ExtractionResult
from .validation import check

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="Invoice Extractor",
    description="Extract structured data from invoices and receipts (Hebrew and English) using an LLM.",
    version="0.1.0",
)


@lru_cache
def extractor_dependency() -> Extractor:
    return get_extractor()


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health(extractor: Extractor = Depends(extractor_dependency)) -> dict:
    return {"status": "ok", "provider": extractor.provider, "model": extractor.model}


@app.post("/extract", response_model=ExtractionResult)
async def extract(
    file: UploadFile = File(..., description="Invoice as PDF, PNG, JPG or WEBP"),
    extractor: Extractor = Depends(extractor_dependency),
) -> ExtractionResult:
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File too large (max 10 MB)")

    try:
        doc = prepare(data, file.filename or "", file.content_type)
    except UnsupportedDocument as exc:
        raise HTTPException(415, str(exc)) from exc

    try:
        invoice = extractor.extract(doc)
    except Exception as exc:  # provider errors, bad JSON from the model
        raise HTTPException(502, f"Extraction failed: {exc}") from exc

    return ExtractionResult(
        invoice=invoice,
        provider=extractor.provider,
        model=extractor.model,
        source=doc.kind,
        warnings=check(invoice),
    )
