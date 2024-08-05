"""
models represents all data models used in VIP imports. Used to validate order
and invoice/sales history data before creating file to be uploaded to their GDI system.
"""

import re
from typing import Optional

import pandas
import pandera
from pandera import DataFrameModel, Field
from pandera.typing import DataFrame, Index, Series


class OrderModel(pandera.DataFrameModel):
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

    loadnumber: Optional[str] = Field(str_length={"min_value": 8, "max_value": 8})
    driver: Optional[str] = Field(str_length={"min_value": 5, "max_value": 5})
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
    orderprice: Optional[str] = Field(str_matches=r"^\d{1,9}(\.\d{1,3})?$")
    discountamount: Optional[str] = Field(str_matches=r"^\d{1,7}(\.\d{1,2})?$")
    postoffamount: Optional[str] = Field(str_matches=r"^\d{1,7}(\.\d{1,2})?$")
    depositamount: Optional[str] = Field(str_matches=r"^\d{1,7}(\.\d{1,2})?$")
    specialprice: Optional[str] = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["0", "1"]
    )
    voidflag: Optional[str] = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["Y", "N"]
    )
    reasoncode: Optional[str] = Field(str_length={"min_value": 2, "max_value": 2})
    codedate: Optional[str] = Field(
        str_matches=r"^\d{8}$", in_range={"min_value": 19700101, "max_value": 20991231}
    )
    deliverydate: str = Field(
        str_matches=r"^\d{8}$", in_range={"min_value": 19700101, "max_value": 20991231}
    )
    ponumber: Optional[str] = Field(str_length={"min_value": 1, "max_value": 15})
    company: str = Field(str_length={"min_value": 1, "max_value": 5})
    warehouse: str = Field(str_length={"min_value": 1, "max_value": 5})
    ordernumber: str = Field(str_length={"min_value": 1, "max_value": 9})
    performancediscountanswer: Optional[str] = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["Y", "N"]
    )
    discountcode: Optional[str] = Field(str_length={"min_value": 1, "max_value": 10})
    discountgroup: Optional[str] = Field(str_length={"min_value": 1, "max_value": 10})
    discountlevel: Optional[str] = Field(str_length={"min_value": 1, "max_value": 1})
    ignoredeliverycharge: Optional[str] = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["Y", "N"]
    )
    orderdate: Optional[str] = Field(
        str_matches=r"^\d{8}$", in_range={"min_value": 19700101, "max_value": 20991231}
    )
    invoicecomments: Optional[str] = Field(
        str_length={"min_value": 1, "max_value": 560}
    )
    orderaction: Optional[str] = Field(str_length={"min_value": 1, "max_value": 2})
    ordertype: Optional[str] = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["S", "T"]
    )


class InvoiceModel(pandera.DataFrameModel):
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
    arstatus: Optional[str] = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["1", "3"]
    )
    ordertype: Optional[str] = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["S", "T"]
    )
    loadnumber: str = Field(str_length={"min_value": 8, "max_value": 8})
    driver: str = Field(str_length={"min_value": 5, "max_value": 5})
    helper1: Optional[str] = Field(str_length={"min_value": 5, "max_value": 5})
    helper2: Optional[str] = Field(str_length={"min_value": 5, "max_value": 5})
    helper3: Optional[str] = Field(str_length={"min_value": 5, "max_value": 5})
    helper4: Optional[str] = Field(str_length={"min_value": 5, "max_value": 5})
    helper5: Optional[str] = Field(str_length={"min_value": 5, "max_value": 5})
    company: Optional[str] = Field(str_length={"min_value": 1, "max_value": 5})
    warehouse: Optional[str] = Field(str_length={"min_value": 1, "max_value": 5})
    flpgroup: Optional[str] = Field(str_length={"min_value": 1, "max_value": 5})
    pricegroup: Optional[str] = Field(str_length={"min_value": 1, "max_value": 5})
    subpricegroup: Optional[str] = Field(str_length={"min_value": 1, "max_value": 5})
    salesrep: Optional[str] = Field(str_length={"min_value": 1, "max_value": 5})
    voidflag: Optional[str] = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["Y", "N"]
    )
    voidreason: Optional[str] = Field(str_length={"min_value": 1, "max_value": 2})
    invoicetype: Optional[str] = Field(str_length={"min_value": 1, "max_value": 1})
    artype: Optional[str] = Field(str_length={"min_value": 1, "max_value": 1})
    trucktype: Optional[str] = Field(str_length={"min_value": 1, "max_value": 1})
    ponumber: Optional[str] = Field(str_length={"min_value": 1, "max_value": 15})
    linenumber: str = Field(
        str_length={"min_value": 3, "max_value": 3}, str_matches=r"^\d+$"
    )
    productcode: str = Field(str_length={"min_value": 6, "max_value": 6})
    unitofmeasure: Optional[str] = Field(
        str_length={"min_value": 2, "max_value": 2}, isin=["CW", "CB"]
    )
    ordermode: Optional[str] = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["0", "1", "2", "3"]
    )
    orderquantity: Optional[str] = Field(
        str_length={"min_value": 5, "max_value": 5}, str_matches=r"^\d+$"
    )
    outquantity: Optional[str] = Field(
        str_length={"min_value": 1, "max_value": 5}, str_matches=r"^\d+$"
    )
    onhandquantity: Optional[str] = Field(
        str_length={"min_value": 1, "max_value": 7}, str_matches=r"^\d+$"
    )
    partialcasequantity: Optional[str] = Field(
        str_length={"min_value": 1, "max_value": 2}, str_matches=r"^\d+$"
    )
    returnreasoncode: Optional[str] = Field(str_length={"min_value": 2, "max_value": 2})
    codedate: Optional[str] = Field(
        str_matches=r"^\d{8}$", in_range={"min_value": 19700101, "max_value": 20991231}
    )
    orderprice: Optional[str] = Field(str_matches=r"^\d{1,6}(\.\d{1,3})?$")
    ordercost: Optional[str] = Field(str_matches=r"^\d{1,7}(\.\d{1,2})?$")
    depositamount: Optional[str] = Field(str_matches=r"^\d{1,5}(\.\d{1,2})?$")
    deposittype: Optional[str] = Field(str_length={"min_value": 1, "max_value": 1})
    depletionallowance: Optional[str] = Field(str_matches=r"^\d{1,6}(\.\d{1,5})?$")
    postoffamount: Optional[str] = Field(str_matches=r"^\d{1,5}(\.\d{1,2})?$")
    discountamount: Optional[str] = Field(str_matches=r"^\d{1,5}(\.\d{1,2})?$")
    discountlevel1: Optional[str] = Field(str_length={"min_value": 1, "max_value": 10})
    discountlevel2: Optional[str] = Field(str_length={"min_value": 1, "max_value": 10})
    discountlevel3: Optional[str] = Field(str_length={"min_value": 1, "max_value": 10})
    discountlevel4: Optional[str] = Field(str_length={"min_value": 1, "max_value": 10})
    discountlevel: Optional[str] = Field(str_length={"min_value": 1, "max_value": 1})
    specialprice: Optional[str] = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["0", "1"]
    )
