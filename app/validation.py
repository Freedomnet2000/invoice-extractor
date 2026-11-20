"""Sanity checks on extracted numbers. These catch model mistakes and surface them as warnings."""
from __future__ import annotations

from .schemas import Invoice

TOLERANCE = 0.02  # allow small rounding differences


def check(invoice: Invoice) -> list[str]:
    warnings: list[str] = []

    if invoice.subtotal is not None and invoice.vat_amount is not None and invoice.total_amount is not None:
        expected = invoice.subtotal + invoice.vat_amount
        if abs(expected - invoice.total_amount) > max(TOLERANCE, 0.005 * invoice.total_amount):
            warnings.append(
                f"subtotal + vat ({expected:.2f}) does not match total ({invoice.total_amount:.2f})"
            )

    line_totals = [li.total for li in invoice.line_items if li.total is not None]
    if line_totals and invoice.subtotal is not None:
        s = sum(line_totals)
        if abs(s - invoice.subtotal) > max(TOLERANCE, 0.005 * invoice.subtotal):
            warnings.append(f"line items sum ({s:.2f}) does not match subtotal ({invoice.subtotal:.2f})")

    if invoice.total_amount is None:
        warnings.append("total_amount not found")

    for field, score in invoice.confidence.items():
        if score < 0.6:
            warnings.append(f"low confidence for {field} ({score:.2f})")

    return warnings
