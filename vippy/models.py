"""
models represents all data models used in VIP imports. Used to validate order
and invoice/sales history data before creating file to be uploaded to their GDI system.
"""

import re
from typing import Required

import pandas
import pandera
from numpy import require
from pandera.typing import DataFrame, Index, Series

"""
Field Checks

These checks are used to validate each field in the various models below. Generally,
each unique field will have its own check. Checks are used to ensure that the
data conforms to what is expected by VIP if a dataframe is exported into CSV format
and uploaded into VIP's GDI system.

Could alternatively make a check only for each unique data type rather than one
for every individual field, but this way is more explicit and easier to change
if there's an update to the required format and one field needs to be changed.
"""
arstatus_check = [pandera.Check.str_length(1, 1), pandera.Check.isin(["1", "3"])]
artype_check = pandera.Check.str_length(1, 1)
codedate_check = pandera.Check.in_range(19700101, 20991231)  # YYYYMMDD
company_check = pandera.Check.str_length(1, 5)
deliverydate_check = pandera.Check.in_range(19700101, 20991231)  # YYYYMMDD
depletionallowance_check = [
    pandera.Check.in_range(0, 999999.99999),
    pandera.Check.str_matches(r"^\d{1,6}(\.\d{1,5})?$"),
]
depositamount_check = [
    pandera.Check.in_range(0, 9999999.99),
    pandera.Check.str_matches(r"^\d{1,7}(\.\d{1,2})?$"),
]
deposittype_check = pandera.Check.str_length(1, 1)
discountamount_check = [
    pandera.Check.in_range(0, 9999999.99),
    pandera.Check.str_matches(r"^\d{1,7}(\.\d{1,2})?$"),
]
discountcode_check = pandera.Check.str_length(1, 10)
discountgroup_check = pandera.Check.str_length(1, 10)
discountlevel_check = pandera.Check.str_length(1, 1)
discountlevel10_check = pandera.Check.str_length(10, 10)
driver_check = pandera.Check.str_length(1, 5)
flpgroup_check = pandera.Check.str_length(1, 5)
helper_check = pandera.Check.str_length(1, 5)
ignoredeliverycharge_check = [
    pandera.Check.str_length(1, 1),
    pandera.Check.isin(["Y", "N"]),
]
invoicecomments_check = pandera.Check.str_length(1, 560)
invoicedate_check = pandera.Check.in_range(19700101, 20991231)  # YYYYMMDD
invoicenumber_check = [
    pandera.Check.str_length(1, 15),
    pandera.Check.str_matches(r"^\d+$"),
]
invoicetype_check = pandera.Check.str_length(1, 1)
linenumber_check = [pandera.Check.str_length(3, 3), pandera.Check.str_matches(r"^\d+$")]
loadnumber_check = pandera.Check.str_length(8, 8)
onhandquantity_check = pandera.Check.str_length(7, 7)
orderaction_check = [
    pandera.Check.str_length(1, 2)
]  # Not actually sure what the valid values are
ordercost_check = [
    pandera.Check.in_range(0, 999999.99999),
    pandera.Check.str_matches(r"^\d{1,7}(\.\d{1,2})?$"),
]
orderdate_check = pandera.Check.in_range(19700101, 20991231)  # YYYYMMDD
ordermode_check = [
    pandera.Check.str_length(1, 1),
    pandera.Check.isin(["0", "1", "2", "3"]),
]
ordernumber_check = pandera.Check.str_length(1, 9)
orderprice_check = [
    pandera.Check.in_range(0, 999999999.999),
    pandera.Check.str_matches(r"^\d{1,9}(\.\d{1,3})?$"),
]
ordertype_check = [pandera.Check.str_length(1, 1), pandera.Check.isin(["S", "T"])]
orderquantity_check = pandera.Check.str_length(5, 5)
outquantity_check = pandera.Check.str_length(5, 5)
partialcasequantity_check = pandera.Check.str_length(2, 2)
performancediscountanswer_check = [
    pandera.Check.str_length(1, 1),
    pandera.Check.isin(["Y", "N"]),
]
ponumber_check = pandera.Check.str_length(1, 15)
postoffamount_check = [
    pandera.Check.in_range(0, 9999999.99),
    pandera.Check.str_matches(r"^\d{1,7}(\.\d{1,2})?$"),
]
pricegroup_check = pandera.Check.str_length(1, 5)
productcode_check = pandera.Check.str_length(6, 6)
reasoncode_check = pandera.Check.str_length(2, 2)
retailerid_check = pandera.Check.str_length(5, 5)
salesrep_check = pandera.Check.str_length(1, 5)
specialprice_check = [pandera.Check.str_length(1, 1), pandera.Check.isin(["0", "1"])]
subpricegroup_check = pandera.Check.str_length(1, 5)
trucktype_check = pandera.Check.str_length(1, 1)
unitofmeasure_check = [pandera.Check.str_length(2, 2), pandera.Check.isin(["CW", "CB"])]
voidflag_check = [pandera.Check.str_length(1, 1), pandera.Check.isin(["Y", "N"])]
voidreason_check = pandera.Check.str_length(1, 2)
warehouse_check = pandera.Check.str_length(1, 5)


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

    loadnumber: Series[pandera.String] = pandera.Field(checks=loadnumber_check)
    retailerid: Series[pandera.String] = pandera.Field(
        checks=retailerid_check, required=True
    )
    driver: Series[pandera.String] = pandera.Field(checks=driver_check)
    linenumber: Series[pandera.String] = pandera.Field(
        checks=linenumber_check, required=True
    )
    unitofmeasure: Series[pandera.String] = pandera.Field(
        checks=unitofmeasure_check, required=True
    )
    productcode: Series[pandera.String] = pandera.Field(
        checks=productcode_check, required=True
    )
    orderquantity: Series[pandera.String] = pandera.Field(
        checks=orderquantity_check, required=True
    )
    orderprice: Series[pandera.Float] = pandera.Field(checks=orderprice_check)
    discountamount: Series[pandera.Float] = pandera.Field(checks=discountamount_check)
    postoffamount: Series[pandera.Float] = pandera.Field(checks=postoffamount_check)
    depositamount: Series[pandera.Float] = pandera.Field(checks=depositamount_check)
    specialprice: Series[pandera.String] = pandera.Field(checks=specialprice_check)
    voidflag: Series[pandera.String] = pandera.Field(checks=voidflag_check)
    reasoncode: Series[pandera.String] = pandera.Field(checks=reasoncode_check)
    codedate: Series[pandera.Int] = pandera.Field(checks=codedate_check)
    deliverydate: Series[pandera.Int] = pandera.Field(
        checks=deliverydate_check, required=True
    )
    ponumber: Series[pandera.String] = pandera.Field(checks=ponumber_check)
    company: Series[pandera.String] = pandera.Field(checks=company_check, required=True)
    warehouse: Series[pandera.String] = pandera.Field(
        checks=warehouse_check, required=True
    )
    ordernumber: Series[pandera.String] = pandera.Field(checks=ordernumber_check)
    performancediscountanswer: Series[pandera.String] = pandera.Field(
        checks=performancediscountanswer_check
    )
    discountcode: Series[pandera.String] = pandera.Field(checks=discountcode_check)
    discountgroup: Series[pandera.String] = pandera.Field(checks=discountgroup_check)
    discountlevel: Series[pandera.String] = pandera.Field(checks=discountlevel_check)
    ignoredeliverycharge: Series[pandera.String] = pandera.Field(
        checks=ignoredeliverycharge_check
    )
    salesrep: Series[pandera.String] = pandera.Field(checks=salesrep_check)
    orderdate: Series[pandera.Int] = pandera.Field(checks=orderdate_check)
    invoicecomments: Series[pandera.String] = pandera.Field(
        checks=invoicecomments_check
    )
    orderaction: Series[pandera.String] = pandera.Field(checks=orderaction_check)
    ordertype: Series[pandera.String] = pandera.Field(checks=ordertype_check)


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

    retailerid: Series[pandera.String] = pandera.Field(
        checks=retailerid_check, required=True
    )
    invoicenumber: Series[pandera.String] = pandera.Field(
        checks=invoicenumber_check, required=True
    )
    invoicedate: Series[pandera.Int] = pandera.Field(
        checks=invoicedate_check, required=True
    )
    arstatus: Series[pandera.String] = pandera.Field(checks=arstatus_check)
    ordertype: Series[pandera.String] = pandera.Field(checks=ordertype_check)
    loadnumber: Series[pandera.String] = pandera.Field(checks=loadnumber_check)
    driver: Series[pandera.String] = pandera.Field(checks=driver_check)
    helper1: Series[pandera.String] = pandera.Field(checks=helper_check)
    helper2: Series[pandera.String] = pandera.Field(checks=helper_check)
    helper3: Series[pandera.String] = pandera.Field(checks=helper_check)
    helper4: Series[pandera.String] = pandera.Field(checks=helper_check)
    helper5: Series[pandera.String] = pandera.Field(checks=helper_check)
    company: Series[pandera.String] = pandera.Field(checks=company_check)
    warehouse: Series[pandera.String] = pandera.Field(checks=warehouse_check)
    flpgroup: Series[pandera.String] = pandera.Field(checks=flpgroup_check)
    pricegroup: Series[pandera.String] = pandera.Field(checks=pricegroup_check)
    subpricegroup: Series[pandera.String] = pandera.Field(checks=subpricegroup_check)
    salesrep: Series[pandera.String] = pandera.Field(checks=salesrep_check)
    voidflag: Series[pandera.String] = pandera.Field(checks=voidflag_check)
    voidreason: Series[pandera.String] = pandera.Field(checks=voidreason_check)
    invoicetype: Series[pandera.String] = pandera.Field(checks=invoicetype_check)
    artype: Series[pandera.String] = pandera.Field(checks=artype_check)
    trucktype: Series[pandera.String] = pandera.Field(checks=trucktype_check)
    ponumber: Series[pandera.String] = pandera.Field(checks=ponumber_check)
    linenumber: Series[pandera.String] = pandera.Field(checks=linenumber_check)
    productcode: Series[pandera.String] = pandera.Field(checks=productcode_check)
    # unitofmeasure # required if prodcutcode specified
    ordermode: Series[pandera.String] = pandera.Field(checks=ordermode_check)
    # orderquantity # required if productcode specified
    outquantity: Series[pandera.String] = pandera.Field(checks=outquantity_check)
    onhandquantity: Series[pandera.String] = pandera.Field(checks=onhandquantity_check)
    partialcasequantity: Series[pandera.String] = pandera.Field(
        checks=partialcasequantity_check
    )
    returnreasoncode: Series[pandera.String] = pandera.Field(checks=reasoncode_check)
    codedate: Series[pandera.Int] = pandera.Field(checks=codedate_check)
    # orderprice # required if productcode specified
    ordercost: Series[pandera.Float] = pandera.Field(checks=ordercost_check)
    depositamount: Series[pandera.Float] = pandera.Field(checks=depositamount_check)
    deposittype: Series[pandera.String] = pandera.Field(checks=deposittype_check)
    depletionallowance: Series[pandera.Float] = pandera.Field(
        checks=depletionallowance_check
    )
    postoffamount: Series[pandera.Float] = pandera.Field(checks=postoffamount_check)
    discountamount: Series[pandera.Float] = pandera.Field(checks=discountamount_check)
    discountlevel1: Series[pandera.String] = pandera.Field(checks=discountlevel10_check)
    discountlevel2: Series[pandera.String] = pandera.Field(checks=discountlevel10_check)
    discountlevel3: Series[pandera.String] = pandera.Field(checks=discountlevel10_check)
    discountlevel4: Series[pandera.String] = pandera.Field(checks=discountlevel10_check)
    discountlevel: Series[pandera.String] = pandera.Field(checks=discountlevel_check)
    specialprice: Series[pandera.String] = pandera.Field(checks=specialprice_check)
