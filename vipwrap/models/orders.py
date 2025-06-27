"""
The orders module contains classes to aid in constructing order data.
"""

import io
import logging
from typing import Literal

import pandas as pd
from pandera import Field, SeriesSchema

from .models import OrderModel

logger = logging.getLogger(__name__)


class OrderRow(SeriesSchema):
    """
    This model represents a single row of an order. Each order can have multiple
    rows. This model is used in the OrderBatchModel.
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


class Order:
    """
    This model represents a single order. Each order can have multiple rows.
    This model is used in the OrderBatchModel. An order is a dataframe
    where each row is a dataframe series (OrderRow).

    The OrderModel now maintains header-level fields that are the same for every
    order line, while still preserving the complete flat file structure.
    """

    # Define the field names in the order they should appear in the output
    FIELD_NAMES = list(OrderRow.__annotations__.keys())

    # Define which fields are header-level (order-level) fields
    HEADER_FIELDS = [
        "loadnumber",
        "driver",
        "retailerid",
        "codedate",
        "deliverydate",
        "ponumber",
        "company",
        "warehouse",
        "ordernumber",
        "performancediscountanswer",
    ]

    def __init__(
        self,
        retailerid: str,
        company: str,
        warehouse: str,
        ordernumber: str,
        deliverydate: str,
        loadnumber: str | None = None,
        driver: str | None = None,
        codedate: str | None = None,
        ponumber: str | None = None,
        performancediscountanswer: str | None = None,
    ):
        """
        Initialize an OrderModel with header-level fields that will be the same
        for all order lines.
        """
        logger.info(
            f"Creating new order for retailer {retailerid}, order number {ordernumber}"
        )
        # # Store header fields
        # self.header_fields = {
        #     "retailerid": retailerid,
        #     "company": company,
        #     "warehouse": warehouse,
        #     "ordernumber": ordernumber,
        #     "deliverydate": deliverydate,
        #     "loadnumber": loadnumber,
        #     "driver": driver,
        #     "codedate": codedate,
        #     "ponumber": ponumber,
        #     "performancediscountanswer": performancediscountanswer,
        # }

        # Store each field
        self.retailerid = retailerid
        self.company = company
        self.warehouse = warehouse
        self.ordernumber = ordernumber
        self.deliverydate = deliverydate
        self.loadnumber = loadnumber
        self.driver = driver
        self.codedate = codedate
        self.ponumber = ponumber
        self.performancediscountanswer = performancediscountanswer

        # Initialize empty dataframe for the line-level details
        self.order_lines = pd.DataFrame(columns=self.FIELD_NAMES)

    def add_order_line(
        self,
        productcode: str,
        orderquantity: str,
        unitofmeasure: str,
        orderprice: str | None = None,
        discountamount: str | None = None,
        postoffamount: str | None = None,
        depositamount: str | None = None,
        specialprice: Literal["0", "1"] | None = None,
        voidflag: Literal["Y", "N"] | None = None,
        reasoncode: str | None = None,
        discountcode: str | None = None,
        discountgroup: str | None = None,
        discountlevel: str | None = None,
        ignoredeliverycharge: Literal["Y", "N"] | None = None,
        orderdate: str | None = None,
        invoicecomments: str | None = None,
        orderaction: str | None = None,
        ordertype: Literal["S", "T"] | None = None,
    ):
        """
        Add an order line to this order. The header fields will be automatically
        added to the order line.

        Required Parameters:
        - productcode: 6-character product code
        - orderquantity: 5-digit order quantity
        - unitofmeasure: 2-character unit of measure (CW or CB)

        Optional Parameters:
        - orderprice: Price in format of digits with up to 3 decimal places
        - discountamount: Discount amount in format of digits with up to 2 decimal places
        - postoffamount: Post-off amount in format of digits with up to 2 decimal places
        - depositamount: Deposit amount in format of digits with up to 2 decimal places
        - specialprice: "0" or "1"
        - voidflag: "Y" or "N"
        - reasoncode: 2-character reason code
        - discountcode: Up to 10 character discount code
        - discountgroup: Up to 10 character discount group
        - discountlevel: 1-character discount level
        - ignoredeliverycharge: "Y" or "N"
        - orderdate: Date in format YYYYMMDD
        - invoicecomments: Up to 560 character comments
        - orderaction: Up to 2 character action code
        - ordertype: "S" or "T"
        """
        logger.info(
            f"Adding order line for product {productcode}, quantity {orderquantity} {unitofmeasure}"
        )
        # Automatically generate the linenumber
        linenumber = str(len(self.order_lines) + 1).zfill(3)

        # Create the order line dictionary with provided parameters
        complete_order_line = {
            "linenumber": linenumber,
            "productcode": productcode,
            "orderquantity": orderquantity,
            "unitofmeasure": unitofmeasure,
            "orderprice": orderprice,
            "discountamount": discountamount,
            "postoffamount": postoffamount,
            "depositamount": depositamount,
            "specialprice": specialprice,
            "voidflag": voidflag,
            "reasoncode": reasoncode,
            "discountcode": discountcode,
            "discountgroup": discountgroup,
            "discountlevel": discountlevel,
            "ignoredeliverycharge": ignoredeliverycharge,
            "orderdate": orderdate,
            "invoicecomments": invoicecomments,
            "orderaction": orderaction,
            "ordertype": ordertype,
        }

        # Remove None values to avoid overriding header values
        complete_order_line = {
            k: v for k, v in complete_order_line.items() if v is not None
        }

        # Add header fields to the order line
        for field, value in self.header_fields.items():
            if value is not None:  # Only set non-None values
                complete_order_line[field] = value

        # Add the order line to the dataframe
        self.order_lines = pd.concat(
            [self.order_lines, pd.DataFrame([complete_order_line])], ignore_index=True
        )
        logger.info(
            f"Order line added for product {productcode} with quantity {orderquantity} {unitofmeasure}."
        )

    def remove_order_line(self, productcode: str):
        """
        Remove an order line by its productcode.
        """
        logger.info(f"Attempting to remove order line with product code {productcode}")
        if productcode in self.order_lines["productcode"].values:
            self.order_lines = self.order_lines[
                self.order_lines["productcode"] != productcode
            ].reset_index(drop=True)
            # Re-generate linenumbers
            self.order_lines["linenumber"] = [
                str(i + 1).zfill(3) for i in range(len(self.order_lines))
            ]
            logger.info(
                f"Successfully removed order line with product code {productcode}"
            )
        else:
            error_msg = f"Product code {productcode} not found in order lines."
            logger.error(error_msg)
            raise ValueError(error_msg)

    def __str__(self):
        """
        Allows for printing order dataframe in a readable format.
        """
        return self.order_lines.to_string(index=False)


class OrderBatch:
    """
    This model represents a batch of one or more orders to be processed by VIP.
    Each order is represented by one or more OrderRow.

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

    def __init__(self):
        logger.info("Creating new OrderBatchModel")
        self.orders: list[Order] = []

    def add_order(self, order: Order):
        """
        Add an order to the batch.
        """
        logger.info(f"Adding order for retailer {order.retailerid} to batch")
        self.orders.append(order)

    def remove_order(self, order: Order):
        """
        Remove an order from the batch.
        """
        logger.info(f"Removing order for retailer {order.retailerid} from batch")
        self.orders.remove(order)

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the batch of orders to a single DataFrame.
        Each order's lines are concatenated into a single DataFrame.
        """
        logger.info("Converting order batch to DataFrame")
        all_data = pd.concat(
            [order.order_lines for order in self.orders], ignore_index=True
        )

        # Ensure all required columns are present in the correct order
        for col in Order.FIELD_NAMES:
            if col not in all_data.columns:
                all_data[col] = None

        # Reorder columns to match the expected field order
        all_data = all_data[Order.FIELD_NAMES]

        # Validate the DataFrame against the OrderModel
        OrderModel.validate(all_data)

        return all_data

    def to_flat_file(self) -> io.BytesIO:
        """
        Export the order batch as a BytesIO object containing the flat file data.
        """
        logger.info("Exporting order batch to flat file")

        all_data = self.to_dataframe()
        data_str = all_data.to_csv(
            sep="|", index=False, header=False, lineterminator="\n"
        )
        header_str = "|".join(Order.FIELD_NAMES)

        output = io.BytesIO()
        output.write((header_str + "\n").encode("utf-8"))
        output.write(data_str.encode("utf-8"))
        output.seek(0)

        return output

    @staticmethod
    def generate_filename(id: str, datetime: datetime):
        """
        Generate the filename for the order file to be uploaded to VIP.
        """
        filename = f"85_ORDERS_{id}_{datetime.strftime('%Y%m%d_%H%M%S')}.DAT"
        logger.info(f"Generated filename: {filename}")
        return filename

    def __str__(self):
        return "\n".join([str(order) for order in self.orders])
