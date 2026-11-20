from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total: Optional[float] = None


class Invoice(BaseModel):
    vendor_name: Optional[str] = Field(None, description="Name of the issuing business")
    vendor_tax_id: Optional[str] = Field(None, description="VAT / tax registration number")
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = Field(None, description="ISO date, YYYY-MM-DD")
    currency: Optional[str] = Field(None, description="ISO 4217 code, e.g. USD, ILS, EUR")
    subtotal: Optional[float] = None
    vat_amount: Optional[float] = None
    total_amount: Optional[float] = None
    line_items: list[LineItem] = Field(default_factory=list)
    language: Optional[str] = Field(None, description="Detected document language, e.g. he, en")
    confidence: dict[str, float] = Field(
        default_factory=dict,
        description="Per-field confidence between 0 and 1",
    )


class ExtractionResult(BaseModel):
    invoice: Invoice
    provider: str
    model: str
    source: str = Field(description="How the document was read: 'text' or 'image'")
    warnings: list[str] = Field(default_factory=list)
