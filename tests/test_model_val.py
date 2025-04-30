import sys
from datetime import datetime

sys.path.insert(0, "")
from vipwrap.models import OrderBatchModel, OrderModel


def test_order_batch_model():
    # Create an order batch
    order_batch = OrderBatchModel()

    # Create first order with header-level fields
    order1 = OrderModel(
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
        orderdate="20230101",
        invoicecomments="Test comment",
        orderaction="01",
        ordertype="S",
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
        orderdate="20230102",
        invoicecomments="Test comment 2",
        orderaction="02",
        ordertype="T",
    )

    # Create second order with header-level fields
    order2 = OrderModel(
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
        orderdate="20230103",
        invoicecomments="Test comment 3",
        orderaction="03",
        ordertype="S",
    )

    # Add a different order line with minimal required parameters
    order2.add_order_line(
        productcode="123456",
        orderquantity="00040",
        unitofmeasure="CB",
        # Only providing required parameters to test defaults
    )

    # Add orders to the batch
    order_batch.add_order(order1)
    order_batch.add_order(order2)

    print(order_batch)

    # Export the order batch to a flat file
    filename = OrderBatchModel.generate_filename("TESTID", datetime.now())
    order_batch.to_flat_file(filename)

    # Read the exported file and validate its content
    with open(filename, "r") as file:
        content = file.read()

    # Validate the header and data rows
    lines = content.split("\n")
    assert lines[0] == "|".join(OrderModel.FIELD_NAMES)
    assert len(lines) == 7  # 1 header + 5 data rows + 1 empty row

    # Validate the data rows
    for line in lines[1:-1]:
        assert len(line.split("|")) == len(OrderModel.FIELD_NAMES)

    # Test removing an order line by productcode
    order1.remove_order_line("123456")
    assert "123456" not in order1.df["productcode"].values
    assert order1.df["linenumber"].tolist() == ["001"]

    order2.remove_order_line("654321")
    assert "654321" not in order2.df["productcode"].values
    assert order2.df["linenumber"].tolist() == ["001", "002"]

    # Test that header fields are applied correctly
    assert order1.df.loc[0, "retailerid"] == "12345"
    assert order1.df.loc[0, "loadnumber"] == "12345678"
    assert order2.df.loc[0, "retailerid"] == "54321"
    assert order2.df.loc[0, "loadnumber"] == "87654321"


if __name__ == "__main__":
    # pytest.main()
    test_order_batch_model()
