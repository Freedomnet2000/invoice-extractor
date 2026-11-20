"""Sanity checks on extracted numbers. These catch model mistakes and surface them as warnings."""
from __future__ import annotations

from .schemas import Invoice

ABS_TOLERANCE = 0.05   # rounding on VAT and line totals
REL_TOLERANCE = 0.001  # 0.1% for large amounts with many rounded lines


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= max(ABS_TOLERANCE, REL_TOLERANCE * max(abs(a), abs(b)))


def check(invoice: Invoice) -> list[str]:
    warnings: list[str] = []

    if invoice.subtotal is not None and invoice.vat_amount is not None and invoice.total_amount is not None:
        expected = invoice.subtotal + invoice.vat_amount
        if not _close(expected, invoice.total_amount):
            warnings.append(
                f"subtotal + vat ({expected:.2f}) does not match total ({invoice.total_amount:.2f})"
            )

    line_totals = [li.total for li in invoice.line_items if li.total is not None]
    if line_totals and invoice.subtotal is not None:
        lines = sum(line_totals)
        discount = invoice.discount or 0.0
        after_discount = lines - discount
        if not _close(after_discount, invoice.subtotal):
            label = f"line items ({lines:.2f}) minus discount ({discount:.2f})" if discount else f"line items sum ({lines:.2f})"
            warnings.append(f"{label} does not match subtotal ({invoice.subtotal:.2f})")

    if invoice.total_amount is None:
        warnings.append("total_amount not found")

    for field, score in invoice.confidence.items():
        # A field that is simply absent (e.g. no VAT on the invoice) is not "uncertain".
        if getattr(invoice, field, None) is None:
            continue
        if score < 0.6:
            warnings.append(f"low confidence for {field} ({score:.2f})")

    return warnings
