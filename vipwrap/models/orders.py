"""
The orders module contains classes to aid in constructing order data.
"""

import io
import logging
from datetime import datetime
from typing import Literal

import pandas as pd
from pandera import Field, SeriesSchema

from .models import OrderModel

logger = logging.getLogger(__name__)

# Define the field names in the order they should appear in the output
FIELD_NAMES = OrderModel.FIELD_NAMES()


class OrderRow(SeriesSchema):
    """
    This model represents a single row of an order. Each order can have multiple
    rows. This model is used in the OrderBatchModel.
    """

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

        # Validate that header fields don't exceed their max lengths
        if len(self.retailerid) != 5:
            raise ValueError("retailerid must be exactly 5 characters long")
        if len(self.company) > 100:
            raise ValueError("company must be at most 100 characters long")
        if len(self.warehouse) > 100:
            raise ValueError("warehouse must be at most 100 characters long")
        if len(self.ordernumber) != 10:
            raise ValueError("ordernumber must be exactly 10 characters long")
        if self.loadnumber and len(self.loadnumber) != 10:
            raise ValueError("loadnumber must be exactly 10 characters long")
        if self.driver and len(self.driver) != 5:
            raise ValueError("driver must be exactly 5 characters long")
        if self.codedate and len(self.codedate) != 8:
            raise ValueError("codedate must be exactly 8 characters long")
        if self.ponumber and len(self.ponumber) != 10:
            raise ValueError("ponumber must be exactly 10 characters long")
        if self.performancediscountanswer and len(self.performancediscountanswer) != 1:
            raise ValueError(
                "performancediscountanswer must be exactly 1 character long"
            )

        # Initialize empty dataframe for the line-level details
        self.order_lines = pd.DataFrame(columns=FIELD_NAMES)

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

        # Check that productcode not already present
        if productcode in self.order_lines["productcode"].values:
            error_msg = f"Product code {productcode} is already present in order lines."
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(
            f"Adding order line for product {productcode}, quantity {orderquantity} {unitofmeasure}"
        )

        # Create the order line dictionary with provided parameters
        complete_order_line = {
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
            logger.info(
                f"Successfully removed order line with product code {productcode}"
            )
        else:
            error_msg = f"Product code {productcode} not found in order lines."
            logger.error(error_msg)
            raise ValueError(error_msg)

    def update_order_line(self, productcode: str, **kwargs):
        """
        Update an existing order line with new values.
        """
        logger.info(f"Attempting to update order line with product code {productcode}")
        if productcode in self.order_lines["productcode"].values:
            self.order_lines.loc[
                self.order_lines["productcode"] == productcode, list(kwargs.keys())
            ] = list(kwargs.values())
            logger.info(
                f"Successfully updated order line with product code {productcode}"
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

        # TODO Potentially want to break this up more. One thing is moving
        # the line number functionality out of the Order class entirely. Only
        # really needs to be calculated once we're here creating the final
        # dataframe technically. So might move that logic here where we go through
        # each order and do last minute adjustments like that.
        all_data = pd.concat(
            [order.order_lines for order in self.orders], ignore_index=True
        )

        # Ensure all required columns are present in the correct order
        for col in FIELD_NAMES:
            if col not in all_data.columns:
                all_data[col] = None

        # Reorder columns to match the expected field order
        all_data = all_data[FIELD_NAMES]

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
        header_str = "|".join(FIELD_NAMES)

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
