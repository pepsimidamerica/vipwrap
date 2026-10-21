import io
from datetime import date, datetime

import pytest

from vipwrap.models import Invoice, InvoiceBatch, InvoiceModel


def test_invoice_batch():
    invoice = Invoice(
        "45316", "1762", date(2024, 11, 15), arstatus=1, company="11", ponumber="1762"
    )
    invoice.add_invoice_line("922774", "CW", 2, 15.3, ordermode="1", ordercost=7)
    invoice.add_invoice_line("999522", "BW", -1, 999.9999999999999, codedate=20241231)
    detailless = Invoice("C0001", "I204", 20240305)

    batch = InvoiceBatch()
    batch.add_invoice(invoice)
    batch.add_invoice(detailless)
    rows = batch.to_flat_file().read().decode().split("\r\n")

    assert rows[0] == "|".join(InvoiceModel.FIELD_NAMES())
    assert len(rows) == 5  # header, 2 lines, 1 detail-less, trailing empty string
    parsed = [dict(zip(rows[0].split("|"), r.split("|"))) for r in rows[1:-1]]
    assert all(len(r) == len(InvoiceModel.FIELD_NAMES()) for r in parsed)
    first, second, third = parsed
    assert first["invoicedate"] == "20241115"
    assert first["linenumber"] == "1"
    assert first["orderprice"] == "15.300"
    assert first["ordercost"] == "7.00000"
    assert second["orderquantity"] == "-1"
    assert second["orderprice"] == "1000.000"
    assert second["codedate"] == "20241231"
    assert third["invoicenumber"] == "I204"
    assert third["linenumber"] == "" and third["productcode"] == ""

    invoice.update_invoice_line("922774", orderquantity=3)
    assert invoice.invoice_lines[0].orderquantity == 3
    invoice.remove_invoice_line("999522")
    assert len(invoice.invoice_lines) == 1


def test_invoice_validation():
    with pytest.raises(ValueError):
        Invoice("1234", "1", 20240101)
    with pytest.raises(ValueError):
        Invoice("12345", "1", 20241301)
    with pytest.raises(ValueError):
        Invoice("12345", "1", 20240101, loadnumber="81234567")
    with pytest.raises(ValueError):
        Invoice("12345", "1", 20240101, arstatus=2)
    with pytest.raises(ValueError):
        Invoice("12345", "1", 20240101, ponumber="a,b")

    invoice = Invoice("12345", "1", 20240101, loadnumber="11234567")
    with pytest.raises(ValueError):
        invoice.add_invoice_line("13002", "CW", 1, 1.0)
    with pytest.raises(ValueError):
        invoice.add_invoice_line("013002", "CW", 1, None)
    with pytest.raises(ValueError):
        invoice.add_invoice_line("013002", "CW", 100000, 1.0)
    with pytest.raises(ValueError):
        invoice.add_invoice_line("013002", "CW", 1, 1.0, discountamount=-1)
    with pytest.raises(ValueError):
        invoice.add_invoice_line("013002", "CW", 1, 1.0, deposittype="X")
    invoice.add_invoice_line("013002", "EA", 1, 1.0)
    with pytest.raises(ValueError):
        invoice.add_invoice_line("013002", "CW", 1, 1.0)
    with pytest.raises(ValueError):
        invoice.update_invoice_line("013002", ordermode="9")

    assert (
        InvoiceBatch.generate_filename("1", datetime(2024, 1, 2, 3, 4, 5))
        == "90_SALESHISTORY_1_20240102_030405.DAT"
    )


def test_invoice_round_trip(tmp_path):
    invoice = Invoice("45316", "1762", 20241115, arstatus=1, company="11")
    invoice.add_invoice_line("922774", "CW", 1, 15.3, ordermode="1", ordercost=0)
    invoice.add_invoice_line("999522", "BW", -1, 3.32)
    batch = InvoiceBatch()
    batch.add_invoice(invoice)
    batch.add_invoice(Invoice("C0001", "I204", 20240305))
    original = batch.to_flat_file().read()

    path = tmp_path / "90_SALESHISTORY_1_20240102_030405.DAT"
    path.write_bytes(original)
    rebuilt = InvoiceBatch.from_flat_file(path)
    assert rebuilt.to_flat_file().read() == original
    assert [len(i.invoice_lines) for i in rebuilt.invoices] == [2, 0]
