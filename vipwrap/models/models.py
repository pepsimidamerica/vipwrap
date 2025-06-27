"""
models contains models used to validate Orders and Invoices/Sales History data.
"""

from pandera import DataFrameModel, Field


class OrderModel(DataFrameModel):
    """
    This model represents a dataframe containing one or more orders.
    Upon import into VIP, they will be unprocessed and need to be ran through
    the various steps to send to the warehouse to get picked.

    DataFrame Attributes:
    SEQUENCE: 85
    DATATYPE: ORDERS
    ID: Unique identifier for each file, max of 10 digits (alphanumeric)
    DATE: Date file was created, format YYYYMMDD
    TIME: Time file was created, format HHMMSS

    Output Filename: SEQUENCE_DATATYPE_ID_DATE_TIME.DAT
    """

    loadnumber: str | None = Field(str_length={"min_value": 8, "max_value": 8})
    driver: str | None = Field(str_length={"min_value": 5, "max_value": 5})
    retailerid: str = Field(str_length={"min_value": 5, "max_value": 5})
    linenumber: str = Field(
        str_length={"min_value": 3, "max_value": 3}, str_matches=r"^\d+$"
    )
    unitofmeasure: str = Field(
        str_length={"min_value": 2, "max_value": 2}, isin=["CW", "CB"]
    )
    productcode: str = Field(str_length={"min_value": 6, "max_value": 6})
    orderquantity: str = Field(
        str_length={"min_value": 5, "max_value": 5}, str_matches=r"^\d+$"
    )
    orderprice: str | None = Field(str_matches=r"^\d{1,9}(\.\d{1,3})?$")
    discountamount: str | None = Field(str_matches=r"^\d{1,7}(\.\d{1,2})?$")
    postoffamount: str | None = Field(str_matches=r"^\d{1,7}(\.\d{1,2})?$")
    depositamount: str | None = Field(str_matches=r"^\d{1,7}(\.\d{1,2})?$")
    specialprice: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["0", "1"]
    )
    voidflag: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["Y", "N"]
    )
    reasoncode: str | None = Field(str_length={"min_value": 2, "max_value": 2})
    codedate: str | None = Field(
        str_matches=r"^\d{8}$", in_range={"min_value": 19700101, "max_value": 20991231}
    )
    deliverydate: str = Field(
        str_matches=r"^\d{8}$", in_range={"min_value": 19700101, "max_value": 20991231}
    )
    ponumber: str | None = Field(str_length={"min_value": 1, "max_value": 15})
    company: str = Field(str_length={"min_value": 1, "max_value": 5})
    warehouse: str = Field(str_length={"min_value": 1, "max_value": 5})
    ordernumber: str = Field(str_length={"min_value": 1, "max_value": 9})
    performancediscountanswer: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["Y", "N"]
    )
    discountcode: str | None = Field(str_length={"min_value": 1, "max_value": 10})
    discountgroup: str | None = Field(str_length={"min_value": 1, "max_value": 10})
    discountlevel: str | None = Field(str_length={"min_value": 1, "max_value": 1})
    ignoredeliverycharge: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["Y", "N"]
    )
    orderdate: str | None = Field(
        str_matches=r"^\d{8}$", in_range={"min_value": 19700101, "max_value": 20991231}
    )
    invoicecomments: str | None = Field(str_length={"min_value": 1, "max_value": 560})
    orderaction: str | None = Field(str_length={"min_value": 1, "max_value": 2})
    ordertype: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["S", "T"]
    )


class InvoiceModel(DataFrameModel):
    """
    This model represents invoices/sales history. No processing is done on this
    data, it is posted directly to the retailer's account. If anything posted
    is incorrect, it would need to be fixed by posting a credit.

    DataFrame Attributes:
    SEQUENCE: 90
    DATATYPE: SALESHISTORY
    ID: Unique identifier for each file, max of 10 digits (alphanumeric)
    DATE: Date file was created, format YYYYMMDD
    TIME: Time file was created, format HHMMSS

    Output Filename: SEQUENCE_DATATYPE_ID_DATE_TIME.DAT
    """

    retailerid: str = Field(str_length={"min_value": 5, "max_value": 5})
    invoicenumber: str = Field(
        str_length={"min_value": 1, "max_value": 15}, str_matches=r"^\d+$"
    )
    invoicedate: str = Field(
        str_matches=r"^\d{8}$", in_range={"min_value": 19700101, "max_value": 20991231}
    )
    arstatus: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["1", "3"]
    )
    ordertype: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["S", "T"]
    )
    loadnumber: str = Field(str_length={"min_value": 8, "max_value": 8})
    driver: str = Field(str_length={"min_value": 5, "max_value": 5})
    helper1: str | None = Field(str_length={"min_value": 5, "max_value": 5})
    helper2: str | None = Field(str_length={"min_value": 5, "max_value": 5})
    helper3: str | None = Field(str_length={"min_value": 5, "max_value": 5})
    helper4: str | None = Field(str_length={"min_value": 5, "max_value": 5})
    helper5: str | None = Field(str_length={"min_value": 5, "max_value": 5})
    company: str | None = Field(str_length={"min_value": 1, "max_value": 5})
    warehouse: str | None = Field(str_length={"min_value": 1, "max_value": 5})
    flpgroup: str | None = Field(str_length={"min_value": 1, "max_value": 5})
    pricegroup: str | None = Field(str_length={"min_value": 1, "max_value": 5})
    subpricegroup: str | None = Field(str_length={"min_value": 1, "max_value": 5})
    salesrep: str | None = Field(str_length={"min_value": 1, "max_value": 5})
    voidflag: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["Y", "N"]
    )
    voidreason: str | None = Field(str_length={"min_value": 1, "max_value": 2})
    invoicetype: str | None = Field(str_length={"min_value": 1, "max_value": 1})
    artype: str | None = Field(str_length={"min_value": 1, "max_value": 1})
    trucktype: str | None = Field(str_length={"min_value": 1, "max_value": 1})
    ponumber: str | None = Field(str_length={"min_value": 1, "max_value": 15})
    linenumber: str = Field(
        str_length={"min_value": 3, "max_value": 3}, str_matches=r"^\d+$"
    )
    productcode: str = Field(str_length={"min_value": 6, "max_value": 6})
    unitofmeasure: str | None = Field(
        str_length={"min_value": 2, "max_value": 2}, isin=["CW", "CB"]
    )
    ordermode: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["0", "1", "2", "3"]
    )
    orderquantity: str | None = Field(
        str_length={"min_value": 5, "max_value": 5}, str_matches=r"^\d+$"
    )
    outquantity: str | None = Field(
        str_length={"min_value": 1, "max_value": 5}, str_matches=r"^\d+$"
    )
    onhandquantity: str | None = Field(
        str_length={"min_value": 1, "max_value": 7}, str_matches=r"^\d+$"
    )
    partialcasequantity: str | None = Field(
        str_length={"min_value": 1, "max_value": 2}, str_matches=r"^\d+$"
    )
    returnreasoncode: str | None = Field(str_length={"min_value": 2, "max_value": 2})
    codedate: str | None = Field(
        str_matches=r"^\d{8}$", in_range={"min_value": 19700101, "max_value": 20991231}
    )
    orderprice: str | None = Field(str_matches=r"^\d{1,6}(\.\d{1,3})?$")
    ordercost: str | None = Field(str_matches=r"^\d{1,7}(\.\d{1,2})?$")
    depositamount: str | None = Field(str_matches=r"^\d{1,5}(\.\d{1,2})?$")
    deposittype: str | None = Field(str_length={"min_value": 1, "max_value": 1})
    depletionallowance: str | None = Field(str_matches=r"^\d{1,6}(\.\d{1,5})?$")
    postoffamount: str | None = Field(str_matches=r"^\d{1,5}(\.\d{1,2})?$")
    discountamount: str | None = Field(str_matches=r"^\d{1,5}(\.\d{1,2})?$")
    discountlevel1: str | None = Field(str_length={"min_value": 1, "max_value": 10})
    discountlevel2: str | None = Field(str_length={"min_value": 1, "max_value": 10})
    discountlevel3: str | None = Field(str_length={"min_value": 1, "max_value": 10})
    discountlevel4: str | None = Field(str_length={"min_value": 1, "max_value": 10})
    discountlevel: str | None = Field(str_length={"min_value": 1, "max_value": 1})
    specialprice: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["0", "1"]
    )
