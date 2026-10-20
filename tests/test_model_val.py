from datetime import date, datetime

import pytest

from vipwrap.models import Order, OrderBatch, OrderModel


def test_order_batch_model():
    # Create an order batch
    order_batch = OrderBatch()

    # Create first order with header-level fields
    order1 = Order(
        retailerid="12345",
        company="COMP",
        warehouse="WHSE",
        ordernumber="ORD123456",
        deliverydate=date(2025, 7, 2),
        loadnumber="12345678",
        driver="ABCDE",
        ponumber="PO12345",
        performancediscountanswer="Y",
    )

    # Add order lines with explicit parameters
    order1.add_order_line(
        productcode="123456",
        orderquantity=10,
        unitofmeasure="CW",
        orderprice=100.00,
        discountamount=10.00,
        postoffamount=5.00,
        depositamount=2.00,
        specialprice="0",
        voidflag="N",
        reasoncode="01",
        codedate=date(2025, 7, 2),
        discountcode="DISC10",
        discountgroup="GRP1",
        discountlevel="1",
        ignoredeliverycharge="N",
    )

    order1.add_order_line(
        productcode="654321",
        orderquantity=20,
        unitofmeasure="CB",
        orderprice=200.00,
        discountamount=20.00,
        postoffamount=10.00,
        depositamount=4.00,
        specialprice="1",
        voidflag="Y",
        reasoncode="02",
        discountcode="DISC20",
        discountgroup="GRP2",
        discountlevel="2",
        ignoredeliverycharge="Y",
    )

    # Create second order with header-level fields
    order2 = Order(
        retailerid="54321",
        company="COMP",
        warehouse="WHSE",
        ordernumber="ORD789012",
        deliverydate=date(2025, 7, 2),
        loadnumber="87654321",
        driver="EDCBA",
        ponumber="PO67890",
        performancediscountanswer="Y",
    )

    # Add order lines with explicit parameters
    order2.add_order_line(
        productcode="654321",
        orderquantity=30,
        unitofmeasure="CW",
        orderprice=300.00,
        discountamount=30.00,
        postoffamount=15.00,
        depositamount=6.00,
        specialprice="0",
        voidflag="N",
        reasoncode="03",
        codedate=20250701,
        discountcode="DISC30",
        discountgroup="GRP3",
        discountlevel="3",
        ignoredeliverycharge="N",
    )

    # Add a different order line with minimal required parameters
    order2.add_order_line(
        productcode="123456",
        orderquantity=40,
        unitofmeasure="CB",
        # Only providing required parameters to test defaults
    )

    order2.add_order_comments("Test comment")

    # Add orders to the batch
    order_batch.add_order(order1)
    order_batch.add_order(order2)

    print(order_batch)

    df_batch = order_batch.to_dataframe()

    # Export the order batch to a flat file
    flat_file = order_batch.to_flat_file()

    # Read the file and validate its content
    content = flat_file.read()

    # Validate the header and data rows
    lines = content.decode().split("\r\n")
    assert lines[0] == "|".join(OrderModel.FIELD_NAMES())
    assert len(lines) == 7  # header, 5 rows, trailing empty string after final CRLF

    # Validate the data rows
    for line in lines[1:-1]:
        assert len(line.split("|")) == len(OrderModel.FIELD_NAMES())

    # Test removing an order line by productcode
    order1.remove_order_line("123456")
    assert all(line.productcode != "123456" for line in order1.order_lines)
    assert len(order1.order_lines) == 1

    order2.remove_order_line("654321")
    assert all(line.productcode != "654321" for line in order2.order_lines)
    assert len(order2.order_lines) == 1

    # Test that header fields are applied correctly (now on the Order object)
    assert order1.retailerid == "12345"
    assert order1.loadnumber == "12345678"
    assert order2.retailerid == "54321"
    assert order2.loadnumber == "87654321"


def test_order_validation():
    order = Order("12345", "COMP", "WHSE", "ORD1", deliverydate=0, salesrep="S1000")
    with pytest.raises(ValueError):
        Order("12345", "TOOLONG", "WHSE", "ORD1", deliverydate=0)
    with pytest.raises(ValueError):
        Order("12345", "COMP", "WHSE", "ORD1", deliverydate=20251301)
    with pytest.raises(ValueError):
        order.add_order_line("12345A", 1, "CW")
    with pytest.raises(ValueError):
        order.add_order_line("123456", 1, "XX")
    with pytest.raises(ValueError):
        order.add_order_line("123456", 1, "CW", orderprice=1_000_000)
    with pytest.raises(ValueError):
        order.add_order_comments("no, commas")
    with pytest.raises(ValueError):
        order.add_order_comments("x" * 561)

    order.add_order_line("123456", 1, "CW", orderprice=10, discountamount=1.5)
    order.add_order_line("654321", 1, "CW")
    with pytest.raises(ValueError):
        order.update_order_line("123456", reasoncode="TOOLONG")
    order.add_order_comments("first")
    order.add_order_comments("second")

    batch = OrderBatch()
    batch.add_order(order)
    rows = batch.to_flat_file().read().decode().split("\r\n")
    first = dict(zip(rows[0].split("|"), rows[1].split("|")))
    assert first["orderprice"] == "10.000"
    assert first["discountamount"] == "1.50"
    assert first["deliverydate"] == "0"
    assert first["salesrep"] == "S1000"
    assert [r.split("|")[5] for r in rows[1:-1]] == ["123456", "654321", "000997", "000997"]

    with pytest.raises(ValueError):
        OrderBatch.generate_filename("TOO_LONG_ID!", datetime.now())


if __name__ == "__main__":
    test_order_batch_model()
