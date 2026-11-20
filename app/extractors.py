"""LLM providers. Pick one with the LLM_PROVIDER env var: openai, anthropic or mock."""
from __future__ import annotations

import json
import os
import re
from typing import Protocol

from .documents import PreparedDocument
from .schemas import Invoice

SYSTEM_PROMPT = """You extract structured data from invoices and receipts.
The document may be in Hebrew, English or another language.
Return ONLY a JSON object with these keys:
vendor_name, vendor_tax_id, invoice_number, invoice_date (YYYY-MM-DD),
currency (ISO 4217; ₪/ש"ח = ILS), subtotal, vat_amount, total_amount,
line_items (list of {description, quantity, unit_price, total}),
language (ISO 639-1),
confidence (object mapping each top-level field name to a number 0-1).
Use null for anything not present. Numbers must be plain numbers without
currency symbols or thousands separators. Never invent values."""


class Extractor(Protocol):
    provider: str
    model: str

    def extract(self, doc: PreparedDocument) -> Invoice: ...


def _parse_json(raw: str) -> Invoice:
    # Models sometimes wrap JSON in ```json fences; strip them.
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    return Invoice.model_validate(json.loads(cleaned))


class OpenAIExtractor:
    provider = "openai"

    def __init__(self) -> None:
        from openai import OpenAI

        self.client = OpenAI()  # reads OPENAI_API_KEY
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def extract(self, doc: PreparedDocument) -> Invoice:
        if doc.kind == "text":
            content = [{"type": "text", "text": doc.text}]
        else:
            content = [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{doc.media_type};base64,{doc.image_b64}"},
                }
            ]
        resp = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
        )
        return _parse_json(resp.choices[0].message.content or "{}")


class AnthropicExtractor:
    provider = "anthropic"

    def __init__(self) -> None:
        from anthropic import Anthropic

        self.client = Anthropic()  # reads ANTHROPIC_API_KEY
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")

    def extract(self, doc: PreparedDocument) -> Invoice:
        if doc.kind == "text":
            content = [{"type": "text", "text": doc.text}]
        else:
            content = [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": doc.media_type, "data": doc.image_b64},
                }
            ]
        content.append({"type": "text", "text": "Return the JSON object now."})
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
        )
        raw = "".join(block.text for block in resp.content if block.type == "text")
        return _parse_json(raw)


class MockExtractor:
    """Works without an API key. Returns a fixed invoice so the API can be demoed and tested."""

    provider = "mock"
    model = "mock"

    def extract(self, doc: PreparedDocument) -> Invoice:
        return Invoice(
            vendor_name="Example Ltd.",
            invoice_number="INV-1001",
            invoice_date="2026-11-01",
            currency="ILS",
            subtotal=1000.0,
            vat_amount=180.0,
            total_amount=1180.0,
            line_items=[{"description": "Consulting", "quantity": 1, "unit_price": 1000.0, "total": 1000.0}],
            language="en",
            confidence={"vendor_name": 1.0, "total_amount": 1.0},
        )


def get_extractor() -> Extractor:
    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    if provider == "openai":
        return OpenAIExtractor()
    if provider == "anthropic":
        return AnthropicExtractor()
    if provider == "mock":
        return MockExtractor()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
