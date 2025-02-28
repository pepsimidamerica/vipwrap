import sys
from datetime import datetime

sys.path.insert(0, "")
from vipwrap.models import OrderBatchModel, OrderModel, OrderRowModel


def test_order_batch_model():
    # Create an order batch
    order_batch = OrderBatchModel()

    # Create first order and add order lines
    order1 = OrderModel()
    order1.add_order_line(
        {
            "loadnumber": "12345678",
            "driver": "ABCDE",
            "retailerid": "12345",
            "unitofmeasure": "CW",
            "productcode": "123456",
            "orderquantity": "00010",
            "orderprice": "100.00",
            "discountamount": "10.00",
            "postoffamount": "5.00",
            "depositamount": "2.00",
            "specialprice": "0",
            "voidflag": "N",
            "reasoncode": "01",
            "codedate": "20230101",
            "deliverydate": "20230102",
            "ponumber": "PO12345",
            "company": "COMP",
            "warehouse": "WHSE",
            "ordernumber": "ORD123456",
            "performancediscountanswer": "Y",
            "discountcode": "DISC10",
            "discountgroup": "GRP1",
            "discountlevel": "1",
            "ignoredeliverycharge": "N",
            "orderdate": "20230101",
            "invoicecomments": "Test comment",
            "orderaction": "01",
            "ordertype": "S",
        }
    )
    order1.add_order_line(
        {
            "loadnumber": "12345678",
            "driver": "ABCDE",
            "retailerid": "12345",
            "unitofmeasure": "CB",
            "productcode": "654321",
            "orderquantity": "00020",
            "orderprice": "200.00",
            "discountamount": "20.00",
            "postoffamount": "10.00",
            "depositamount": "4.00",
            "specialprice": "1",
            "voidflag": "Y",
            "reasoncode": "02",
            "codedate": "20230103",
            "deliverydate": "20230104",
            "ponumber": "PO54321",
            "company": "COMP",
            "warehouse": "WHSE",
            "ordernumber": "ORD654321",
            "performancediscountanswer": "N",
            "discountcode": "DISC20",
            "discountgroup": "GRP2",
            "discountlevel": "2",
            "ignoredeliverycharge": "Y",
            "orderdate": "20230102",
            "invoicecomments": "Test comment 2",
            "orderaction": "02",
            "ordertype": "T",
        }
    )

    # Create second order and add order lines
    order2 = OrderModel()
    order2.add_order_line(
        {
            "loadnumber": "87654321",
            "driver": "EDCBA",
            "retailerid": "54321",
            "unitofmeasure": "CW",
            "productcode": "654321",
            "orderquantity": "00030",
            "orderprice": "300.00",
            "discountamount": "30.00",
            "postoffamount": "15.00",
            "depositamount": "6.00",
            "specialprice": "0",
            "voidflag": "N",
            "reasoncode": "03",
            "codedate": "20230105",
            "deliverydate": "20230106",
            "ponumber": "PO67890",
            "company": "COMP",
            "warehouse": "WHSE",
            "ordernumber": "ORD789012",
            "performancediscountanswer": "Y",
            "discountcode": "DISC30",
            "discountgroup": "GRP3",
            "discountlevel": "3",
            "ignoredeliverycharge": "N",
            "orderdate": "20230103",
            "invoicecomments": "Test comment 3",
            "orderaction": "03",
            "ordertype": "S",
        }
    )
    order2.add_order_line(
        {
            "loadnumber": "87654321",
            "driver": "EDCBA",
            "retailerid": "54321",
            "unitofmeasure": "CB",
            "productcode": "123456",
            "orderquantity": "00040",
            "orderprice": "400.00",
            "discountamount": "40.00",
            "postoffamount": "20.00",
            "depositamount": "8.00",
            "specialprice": "1",
            "voidflag": "Y",
            "reasoncode": "04",
            "codedate": "20230107",
            "deliverydate": "20230108",
            "ponumber": "PO09876",
            "company": "COMP",
            "warehouse": "WHSE",
            "ordernumber": "ORD210987",
            "performancediscountanswer": "N",
            "discountcode": "DISC40",
            "discountgroup": "GRP4",
            "discountlevel": "4",
            "ignoredeliverycharge": "Y",
            "orderdate": "20230104",
            "invoicecomments": "Test comment 4",
            "orderaction": "04",
            "ordertype": "T",
        }
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
    assert lines[0] == "|".join(OrderRowModel.__annotations__.keys())
    assert len(lines) == 6  # 1 header + 4 data rows + 1 empty row

    # Validate the data rows
    for line in lines[1:-1]:
        assert len(line.split("|")) == len(OrderRowModel.__annotations__.keys())

    # Test removing an order line by productcode
    order1.remove_order_line("123456")
    assert "123456" not in order1.df["productcode"].values
    assert order1.df["linenumber"].tolist() == ["001"]

    order2.remove_order_line("654321")
    assert "654321" not in order2.df["productcode"].values
    assert order2.df["linenumber"].tolist() == ["001"]


if __name__ == "__main__":
    # pytest.main()
    test_order_batch_model()
