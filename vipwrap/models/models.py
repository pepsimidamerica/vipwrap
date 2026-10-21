"""
models contains models used to validate Orders and Invoices/Sales History data.
"""

import pandas as pd
from pandera.pandas import DataFrameModel, Field, SeriesSchema, check, dataframe_check


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

    loadnumber: str | None = Field(
        str_length={"min_value": 8, "max_value": 8}, nullable=True
    )
    driver: str | None = Field(
        str_length={"min_value": 5, "max_value": 5}, nullable=True
    )
    retailerid: str = Field(str_length={"min_value": 5, "max_value": 5})
    linenumber: str = Field(
        str_length={"min_value": 3, "max_value": 3}, str_matches=r"^\d+$"
    )
    unitofmeasure: str = Field(
        str_length={"min_value": 2, "max_value": 2},
        isin=["CW", "CB", "BW", "HK", "QK", "MI", "CS", "FS", "PO", "PR"],
    )
    productcode: str = Field(str_matches=r"^\d{6}$")
    orderquantity: str = Field(str_matches=r"^\d{5}$")
    orderprice: str | None = Field(str_matches=r"^\d{1,6}\.\d{3}$", nullable=True)
    discountamount: str | None = Field(str_matches=r"^\d{1,5}\.\d{2}$", nullable=True)
    postoffamount: str | None = Field(str_matches=r"^\d{1,5}\.\d{2}$", nullable=True)
    depositamount: str | None = Field(str_matches=r"^\d{1,5}\.\d{2}$", nullable=True)
    specialprice: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["0", "1"], nullable=True
    )
    voidflag: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["Y", "N"], nullable=True
    )
    reasoncode: str | None = Field(
        str_length={"min_value": 2, "max_value": 2}, nullable=True
    )
    codedate: pd.Int64Dtype = Field(
        in_range={"min_value": 19700101, "max_value": 20991231}, nullable=True
    )
    deliverydate: pd.Int64Dtype = Field()
    ponumber: str | None = Field(
        str_length={"min_value": 1, "max_value": 15}, nullable=True
    )
    company: str = Field(str_length={"min_value": 1, "max_value": 5})
    warehouse: str = Field(str_length={"min_value": 1, "max_value": 5})
    ordernumber: str = Field(str_length={"min_value": 1, "max_value": 9})
    performancediscountanswer: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["Y", "N"], nullable=True
    )
    discountcode: str | None = Field(
        str_length={"min_value": 1, "max_value": 10}, nullable=True
    )
    discountgroup: str | None = Field(
        str_length={"min_value": 1, "max_value": 10}, nullable=True
    )
    discountlevel: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, nullable=True
    )
    ignoredeliverycharge: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["Y", "N"], nullable=True
    )
    salesrep: str | None = Field(
        str_length={"min_value": 1, "max_value": 5}, nullable=True
    )
    orderdate: pd.Int64Dtype = Field(
        in_range={"min_value": 19700101, "max_value": 20991231}, nullable=True
    )
    invoicecomments: str | None = Field(
        str_length={"min_value": 1, "max_value": 560}, nullable=True
    )
    orderaction: str | None = Field(
        str_length={"min_value": 2, "max_value": 2}, nullable=True
    )
    ordertype: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["S", "T"], nullable=True
    )

    @check("deliverydate")
    def deliverydate_valid(cls, series: pd.Series) -> pd.Series:
        """
        deliverydate is either a YYYYMMDD integer or 0 for an unassigned delivery day.

        :param series: The deliverydate column
        :type series: pd.Series
        :return: Boolean mask of valid values
        :rtype: pd.Series
        """
        return (series == 0) | series.between(19700101, 20991231)

    @classmethod
    def FIELD_NAMES(cls) -> list[str]:
        """
        Returns the field names of the model as a list.
        """
        return [
            "loadnumber",
            "driver",
            "retailerid",
            "linenumber",
            "unitofmeasure",
            "productcode",
            "orderquantity",
            "orderprice",
            "discountamount",
            "postoffamount",
            "depositamount",
            "specialprice",
            "voidflag",
            "reasoncode",
            "codedate",
            "deliverydate",
            "ponumber",
            "company",
            "warehouse",
            "ordernumber",
            "performancediscountanswer",
            "discountcode",
            "discountgroup",
            "discountlevel",
            "ignoredeliverycharge",
            "salesrep",
            "orderdate",
            "invoicecomments",
            "orderaction",
            "ordertype",
        ]


class OrderRowModel(SeriesSchema):
    """
    OrderRow represents a single row of an order. Each order can have multiple
    rows.
    """

    unitofmeasure: str = Field(
        str_length={"min_value": 2, "max_value": 2}, isin=["CW", "CB"]
    )
    productcode: str = Field(str_length={"min_value": 6, "max_value": 6})
    orderquantity: str = Field(
        str_length={"min_value": 5, "max_value": 5}, str_matches=r"^\d+$"
    )
    orderprice: str | None = Field(str_matches=r"^\d{1,9}(\.\d{1,3})?$", nullable=True)
    discountamount: str | None = Field(
        str_matches=r"^\d{1,7}(\.\d{1,2})?$", nullable=True
    )
    postoffamount: str | None = Field(
        str_matches=r"^\d{1,7}(\.\d{1,2})?$", nullable=True
    )
    depositamount: str | None = Field(
        str_matches=r"^\d{1,7}(\.\d{1,2})?$", nullable=True
    )
    specialprice: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["0", "1"], nullable=True
    )
    voidflag: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["Y", "N"], nullable=True
    )
    reasoncode: str | None = Field(
        str_length={"min_value": 2, "max_value": 2}, nullable=True
    )
    performancediscountanswer: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["Y", "N"], nullable=True
    )
    discountcode: str | None = Field(
        str_length={"min_value": 1, "max_value": 10}, nullable=True
    )
    discountgroup: str | None = Field(
        str_length={"min_value": 1, "max_value": 10}, nullable=True
    )
    discountlevel: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, nullable=True
    )
    ignoredeliverycharge: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["Y", "N"], nullable=True
    )
    invoicecomments: str | None = Field(
        str_length={"min_value": 1, "max_value": 560}, nullable=True
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

    # Header-level fields
    retailerid: str = Field(str_length={"min_value": 5, "max_value": 5})
    invoicenumber: str = Field(str_matches=r"^[A-Za-z0-9]{1,15}$")
    invoicedate: pd.Int64Dtype = Field(
        in_range={"min_value": 19700101, "max_value": 20991231}
    )
    arstatus: pd.Int64Dtype = Field(isin=[1, 3], nullable=True)
    ordertype: str | None = Field(
        str_length={"min_value": 1, "max_value": 2}, nullable=True
    )
    loadnumber: str | None = Field(str_matches=r"^[1-7].{7}$", nullable=True)
    driver: str | None = Field(
        str_length={"min_value": 5, "max_value": 5}, nullable=True
    )
    helper1: str | None = Field(
        str_length={"min_value": 5, "max_value": 5}, nullable=True
    )
    helper2: str | None = Field(
        str_length={"min_value": 5, "max_value": 5}, nullable=True
    )
    helper3: str | None = Field(
        str_length={"min_value": 5, "max_value": 5}, nullable=True
    )
    helper4: str | None = Field(
        str_length={"min_value": 5, "max_value": 5}, nullable=True
    )
    helper5: str | None = Field(
        str_length={"min_value": 5, "max_value": 5}, nullable=True
    )
    company: str | None = Field(
        str_length={"min_value": 1, "max_value": 5}, nullable=True
    )
    warehouse: str | None = Field(
        str_length={"min_value": 1, "max_value": 5}, nullable=True
    )
    flpgroup: str | None = Field(
        str_length={"min_value": 1, "max_value": 5}, nullable=True
    )
    pricegroup: str | None = Field(
        str_length={"min_value": 1, "max_value": 5}, nullable=True
    )
    subpricegroup: str | None = Field(
        str_length={"min_value": 1, "max_value": 5}, nullable=True
    )
    salesrep: str | None = Field(
        str_length={"min_value": 1, "max_value": 5}, nullable=True
    )
    voidflag: str | None = Field(isin=["Y", "N"], nullable=True)
    voidreason: str | None = Field(
        str_length={"min_value": 2, "max_value": 2}, nullable=True
    )
    invoicetype: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, nullable=True
    )
    artype: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, nullable=True
    )
    trucktype: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, nullable=True
    )
    ponumber: str | None = Field(
        str_length={"min_value": 1, "max_value": 15}, nullable=True
    )

    # Detail-level fields, all blank on a detail-less invoice
    linenumber: pd.Int64Dtype = Field(
        in_range={"min_value": 1, "max_value": 999}, nullable=True
    )
    productcode: str | None = Field(str_matches=r"^\d{6}$", nullable=True)
    unitofmeasure: str | None = Field(str_matches=r"^[A-Z]{2}$", nullable=True)
    ordermode: str | None = Field(isin=["0", "1", "2", "3"], nullable=True)
    orderquantity: pd.Int64Dtype = Field(
        in_range={"min_value": -99999, "max_value": 99999}, nullable=True
    )
    outquantity: pd.Int64Dtype = Field(
        in_range={"min_value": 0, "max_value": 99999}, nullable=True
    )
    onhandquantity: pd.Int64Dtype = Field(
        in_range={"min_value": 0, "max_value": 9999999}, nullable=True
    )
    partialcasequantity: pd.Int64Dtype = Field(
        in_range={"min_value": 0, "max_value": 99}, nullable=True
    )
    returnreasoncode: str | None = Field(
        str_length={"min_value": 2, "max_value": 2}, nullable=True
    )
    codedate: pd.Int64Dtype = Field(
        in_range={"min_value": 19700101, "max_value": 20991231}, nullable=True
    )
    orderprice: str | None = Field(str_matches=r"^-?\d{1,6}\.\d{3}$", nullable=True)
    ordercost: str | None = Field(str_matches=r"^-?\d{1,6}\.\d{5}$", nullable=True)
    depositamount: str | None = Field(str_matches=r"^-?\d{1,5}\.\d{2}$", nullable=True)
    deposittype: str | None = Field(isin=["K", "C", "O"], nullable=True)
    depletionallowance: str | None = Field(
        str_matches=r"^-?\d{1,6}\.\d{5}$", nullable=True
    )
    postoffamount: str | None = Field(str_matches=r"^-?\d{1,5}\.\d{2}$", nullable=True)
    discountamount: str | None = Field(str_matches=r"^\d{1,5}\.\d{2}$", nullable=True)
    discountlevel1: str | None = Field(
        str_length={"min_value": 1, "max_value": 10}, nullable=True
    )
    discountlevel2: str | None = Field(
        str_length={"min_value": 1, "max_value": 10}, nullable=True
    )
    discountlevel3: str | None = Field(
        str_length={"min_value": 1, "max_value": 10}, nullable=True
    )
    discountlevel4: str | None = Field(
        str_length={"min_value": 1, "max_value": 10}, nullable=True
    )
    discountlevel: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, nullable=True
    )
    specialprice: str | None = Field(isin=["0", "1"], nullable=True)

    @dataframe_check
    def product_fields_present(cls, df: pd.DataFrame) -> pd.Series:
        """
        unitofmeasure, orderquantity, and orderprice are required when a productcode is given.

        :param df: The invoice dataframe
        :type df: pd.DataFrame
        :return: Boolean mask of valid rows
        :rtype: pd.Series
        """
        required = (
            df[["unitofmeasure", "orderquantity", "orderprice"]].notna().all(axis=1)
        )
        return df["productcode"].isna() | required

    @classmethod
    def FIELD_NAMES(cls) -> list[str]:
        """
        Returns the field names of the model as a list.
        """
        return [
            "retailerid",
            "invoicenumber",
            "invoicedate",
            "arstatus",
            "ordertype",
            "loadnumber",
            "driver",
            "helper1",
            "helper2",
            "helper3",
            "helper4",
            "helper5",
            "company",
            "warehouse",
            "flpgroup",
            "pricegroup",
            "subpricegroup",
            "salesrep",
            "voidflag",
            "voidreason",
            "invoicetype",
            "artype",
            "trucktype",
            "ponumber",
            "linenumber",
            "productcode",
            "unitofmeasure",
            "ordermode",
            "orderquantity",
            "outquantity",
            "onhandquantity",
            "partialcasequantity",
            "returnreasoncode",
            "codedate",
            "orderprice",
            "ordercost",
            "depositamount",
            "deposittype",
            "depletionallowance",
            "postoffamount",
            "discountamount",
            "discountlevel1",
            "discountlevel2",
            "discountlevel3",
            "discountlevel4",
            "discountlevel",
            "specialprice",
        ]
