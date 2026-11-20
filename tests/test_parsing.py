from app.extractors import _parse_json


def test_parses_plain_json():
    inv = _parse_json('{"vendor_name": "ACME", "total_amount": 99.5}')
    assert inv.vendor_name == "ACME"
    assert inv.total_amount == 99.5


def test_parses_fenced_json():
    inv = _parse_json('```json\n{"vendor_name": "חברת דוגמה בע\\"מ", "currency": "ILS"}\n```')
    assert inv.vendor_name == 'חברת דוגמה בע"מ'
    assert inv.currency == "ILS"


def test_missing_fields_default_to_none():
    inv = _parse_json("{}")
    assert inv.total_amount is None
    assert inv.line_items == []
