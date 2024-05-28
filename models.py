"""
models represents all data models used in VIP. Used to validate order
and sales history data.
"""

import pandas
import pandera
from pandera.typing import DataFrame, Index, Series

# Field checks
driver_check = pandera.Check.str_length(5, 5)
linenumber_check = [pandera.Check.str_length(3, 3), pandera.Check.str_matches(r"^\d+$")]
loadnumber_check = pandera.Check.str_length(8, 8)
ordertype_check = [pandera.Check.str_length(1, 1), pandera.Check.isin(["S", "T"])]
orderquantity_check = pandera.Check.str_length(5, 5)
productcode_check = pandera.Check.str_length(6, 6)
retailerid_check = pandera.Check.str_length(5, 5)
unitofmeasure_check = [pandera.Check.str_length(2, 2), pandera.Check.isin(["CW", "CB"])]

# orderprice_check = pandera.Check
# discountamount_check = pandera.Check
# postoffamount_check = pandera.Check
# depositamount_check = pandera.Check
# specialprice_check = pandera.Check
# voidflag_check = pandera.Check
# reasoncode_check = pandera.Check
# codedate_check = pandera.Check
# deliverydate_check = pandera.Check
# ponumber_check = pandera.Check
# company_check = pandera.Check
# warehouse_check = pandera.Check
# ordernumber_check = pandera.Check
# performancediscountanswer_check = pandera.Check
# discountcode_check = pandera.Check
# discountgroup_check = pandera.Check
# discountlevel_check = pandera.Check
# ignoredeliverycharge_check = pandera.Check
# salesrep_check = pandera.Check
# orderdate_check = pandera.Check
# invoicecomments_check = pandera.Check
# orderaction_check = pandera.Check


# Models
class OrderModel(pandera.DataFrameModel):
    """
    This model represents orders.
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
    # orderprice
    # discountamount
    # postoffamount
    # depositamount
    # specialprice
    # voidflag
    # reasoncode
    # codedate
    # deliverydate  # required
    # ponumber
    # company  # required
    # warehouse  # required
    # ordernumber  # required
    # performancediscountanswer
    # discountcode
    # discountgroup
    # discountlevel
    # ignoredeliverycharge
    # salesrep
    # orderdate
    # invoicecomments
    # orderaction
    # ordertype


class SalesModel(pandera.DataFrameModel):
    retailerid: Series[pandera.String] = pandera.Field(checks=retailerid_check)
