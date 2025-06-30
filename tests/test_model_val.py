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
        deliverydate="20230102",
        loadnumber="12345678",
        driver="ABCDE",
        codedate="20230101",
        ponumber="PO12345",
        performancediscountanswer="Y",
    )

    # Add order lines with explicit parameters
    order1.add_order_line(
        productcode="123456",
        orderquantity="00010",
        unitofmeasure="CW",
        orderprice="100.00",
        discountamount="10.00",
        postoffamount="5.00",
        depositamount="2.00",
        specialprice="0",
        voidflag="N",
        reasoncode="01",
        discountcode="DISC10",
        discountgroup="GRP1",
        discountlevel="1",
        ignoredeliverycharge="N",
    )

    order1.add_order_line(
        productcode="654321",
        orderquantity="00020",
        unitofmeasure="CB",
        orderprice="200.00",
        discountamount="20.00",
        postoffamount="10.00",
        depositamount="4.00",
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
        deliverydate="20230106",
        loadnumber="87654321",
        driver="EDCBA",
        codedate="20230105",
        ponumber="PO67890",
        performancediscountanswer="Y",
    )

    # Add order lines with explicit parameters
    order2.add_order_line(
        productcode="654321",
        orderquantity="00030",
        unitofmeasure="CW",
        orderprice="300.00",
        discountamount="30.00",
        postoffamount="15.00",
        depositamount="6.00",
        specialprice="0",
        voidflag="N",
        reasoncode="03",
        discountcode="DISC30",
        discountgroup="GRP3",
        discountlevel="3",
        ignoredeliverycharge="N",
    )

    # Add a different order line with minimal required parameters
    order2.add_order_line(
        productcode="123456",
        orderquantity="00040",
        unitofmeasure="CB",
        # Only providing required parameters to test defaults
    )

    order2.add_order_comments("Test comment")

    # Add orders to the batch
    order_batch.add_order(order1)
    order_batch.add_order(order2)

    print(order_batch)

    # Export the order batch to a flat file
    flat_file = order_batch.to_flat_file()

    # Read the file and validate its content
    content = flat_file.read()

    # Validate the header and data rows
    lines = str(content).split("\n")
    assert lines[0] == "|".join(OrderModel.FIELD_NAMES())
    assert len(lines) == 8

    # Validate the data rows
    for line in lines[1:-1]:
        assert len(line.split("|")) == len(OrderModel.FIELD_NAMES())

    # Test removing an order line by productcode
    order1.remove_order_line("123456")
    assert all(line.productcode != "123456" for line in order1.order_lines)
    assert len(order1.order_lines) == 1

    order2.remove_order_line("654321")
    assert all(line.productcode != "654321" for line in order2.order_lines)
    assert len(order2.order_lines) == 2

    # Test that header fields are applied correctly (now on the Order object)
    assert order1.retailerid == "12345"
    assert order1.loadnumber == "12345678"
    assert order2.retailerid == "54321"
    assert order2.loadnumber == "87654321"


if __name__ == "__main__":
    test_order_batch_model()
