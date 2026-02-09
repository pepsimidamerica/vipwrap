"""
The orders module contains classes to aid in constructing order data.
"""

import io
import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

import pandas as pd

from .models import OrderModel

logger = logging.getLogger(__name__)

# Define the field names in the order they should appear in the output
FIELD_NAMES = OrderModel.FIELD_NAMES()


@dataclass
class OrderRow:
    """
    OrderRow represents a single row of order data in an given order.
    Each row corresponds to a product, with its associated details.

    :param productcode: 6-character product code
    :param orderquantity: 5-digit order quantity
    :param unitofmeasure: The unit of measure for the order quantity
    :param orderprice: Price in format of digits with up to 3 decimal places (optional)
    :param discountamount: Discount amount in format of digits with up to 2 decimal places
    :param postoffamount: Post-off amount in format of digits with up to 2 decimal places (optional)
    :param depositamount: Deposit amount in format of digits with up to 2 decimal places
    :param specialprice: "0" or "1". 0 = No special price, 1 = Special price applies (optional)
    :param voidflag: "Y" or "N" (optional)
    :param reasoncode: 2-character reason code (optional)
    :param discountcode: Up to 10 character discount code (optional)
    :param discountgroup: Up to 10 character discount group (optional)
    :param discountlevel: 1-character discount level (optional)
    :param ignoredeliverycharge: "Y" or "N" (optional)
    :param invoicecomments: Comments for the invoice (optional)
    """

    productcode: str
    orderquantity: int
    unitofmeasure: str
    orderprice: float | None = None
    discountamount: float | None = None
    postoffamount: float | None = None
    depositamount: float | None = None
    specialprice: str | None = None
    voidflag: str | None = None
    reasoncode: str | None = None
    discountcode: str | None = None
    discountgroup: str | None = None
    discountlevel: str | None = None
    ignoredeliverycharge: str | None = None
    invoicecomments: str | None = None

    def __post_init__(self):
        """
        Validate the length of fields to ensure they meet the requirements
        """
        if len(self.productcode) != 6:
            raise ValueError("productcode must be exactly 6 characters long")
        if len(self.unitofmeasure) != 2:
            raise ValueError("unitofmeasure must be exactly 2 characters long")
        if self.orderquantity < 0 or self.orderquantity > 99999:
            raise ValueError("orderquantity must be between 0 and 99999")
        if self.specialprice and self.specialprice not in ["0", "1"]:
            raise ValueError("specialprice must be '0' or '1'")
        if self.voidflag and self.voidflag not in ["Y", "N"]:
            raise ValueError("voidflag must be 'Y' or 'N'")
        if self.reasoncode and len(self.reasoncode) != 2:
            raise ValueError("reasoncode must be exactly 2 characters long")
        if self.discountcode and len(self.discountcode) > 10:
            raise ValueError("discountcode must be at most 10 characters long")
        if self.discountgroup and len(self.discountgroup) > 10:
            raise ValueError("discountgroup must be at most 10 characters long")
        if self.discountlevel and len(self.discountlevel) != 1:
            raise ValueError("discountlevel must be exactly 1 character long")
        if self.ignoredeliverycharge and self.ignoredeliverycharge not in ["Y", "N"]:
            raise ValueError("ignoredeliverycharge must be 'Y' or 'N'")


class Order:
    """
    Order represents a single order for a given retailer. Each order can have
    multiple rows.

    While working with order data, the productcode is considered the primary key
    that identifies each row. Only one row per productcode is allowed.
    Once a batch of orders are being exported, the linenumber will be added for each
    order line.
    """

    def __init__(
        self,
        retailerid: str,
        company: str,
        warehouse: str,
        ordernumber: str,
        deliverydate: date,
        loadnumber: str | None = None,
        driver: str | None = None,
        codedate: date | None = None,
        ponumber: str | None = None,
        performancediscountanswer: str | None = None,
        orderdate: date | None = None,
        orderaction: str | None = None,
        ordertype: Literal["S", "T"] | None = None,
    ):
        """
        Initialize an Order with header-level fields that will be the same
        for all order lines.

        :param retailerid: The ID of the retailer
        :param company: The company name
        :param warehouse: The warehouse location
        :param ordernumber: The order number
        :param deliverydate: The delivery date
        :param loadnumber: The load number (optional)
        :param driver: The driver ID (optional)
        :param codedate: The code date (optional)
        :param ponumber: The DSD or PO number (optional)
        :param performancediscountanswer: The performance discount answer (optional)
        :param orderdate: The order date (optional)
        :param orderaction: The order action. Combine, Lock, DTT (optional)
        :param ordertype: The order type. Sales = "S", Transfer = "T" (optional)
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
        self.orderdate = orderdate
        self.orderaction = orderaction
        self.ordertype = ordertype

        # Validate that header fields don't exceed their max lengths
        if len(self.retailerid) != 5:
            raise ValueError("retailerid must be exactly 5 characters long")
        if len(self.company) > 100:
            raise ValueError("company must be at most 100 characters long")
        if len(self.warehouse) > 100:
            raise ValueError("warehouse must be at most 100 characters long")
        if len(self.ordernumber) > 9:
            raise ValueError("ordernumber must be at most 9 characters long")
        if self.loadnumber and len(self.loadnumber) != 8:
            raise ValueError("loadnumber must be exactly 8 characters long")
        if self.driver and len(self.driver) != 5:
            raise ValueError("driver must be exactly 5 characters long")
        if self.ponumber and len(self.ponumber) > 15:
            raise ValueError("ponumber must be at most 15 characters long")
        if self.performancediscountanswer and len(self.performancediscountanswer) != 1:
            raise ValueError(
                "performancediscountanswer must be exactly 1 character long"
            )
        if self.orderaction and len(self.orderaction) != 2:
            raise ValueError("orderaction must be exactly 2 characters long")
        if self.ordertype and self.ordertype not in ["S", "T"]:
            raise ValueError("ordertype must be either 'S' or 'T'")

        # Create list to hold each order line as an OrderRow
        self.order_lines: list[OrderRow] = []
        self.order_comments: list[OrderRow] = []

    def add_order_line(
        self,
        productcode: str,
        orderquantity: int,
        unitofmeasure: Literal[
            "CW", "CB", "BW", "HK", "QK", "MI", "CS", "FS", "PO", "PR"
        ],
        orderprice: float | None = None,
        discountamount: float | None = None,
        postoffamount: float | None = None,
        depositamount: float | None = None,
        specialprice: Literal["0", "1"] | None = None,
        voidflag: Literal["Y", "N"] | None = None,
        reasoncode: str | None = None,
        discountcode: str | None = None,
        discountgroup: str | None = None,
        discountlevel: str | None = None,
        ignoredeliverycharge: Literal["Y", "N"] | None = None,
    ):
        """
        Add an order line to this order. The header fields will be automatically
        added to the order line.

        :param productcode: 6-character product code
        :param orderquantity: 5-digit order quantity
        :param unitofmeasure: 2-character unit of measure, CW = Case Wine, CB = case beer, BW = bottle wine, HK = Half Keg, QK=Quarter Keg, MI=Miscellaneous, CS= Case Soda, FS = Fountain Syrup, PO = Postmix, PR = Premix
        :param orderprice: Price in format of digits with up to 3 decimal places (optional)
        :param discountamount: Discount amount in format of digits with up to 2 decimal places (optional)
        :param postoffamount: Post-off amount in format of digits with up to 2 decimal places (optional)
        :param depositamount: Deposit amount in format of digits with up to 2 decimal places (optional)
        :param specialprice: "0" or "1". 0 = No special price, 1 = Special price applies (optional)
        :param voidflag: "Y" or "N" (optional)
        :param reasoncode: 2-character reason code (optional)
        :param discountcode: Up to 10 character discount code (optional)
        :param discountgroup: Up to 10 character discount group (optional)
        :param discountlevel: 1-character discount level (optional)
        :param ignoredeliverycharge: "Y" or "N" (optional)
        """

        # Check that productcode not already present
        if any(
            getattr(line, "productcode", None) == productcode
            for line in self.order_lines
        ):
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
        }

        # Remove None values to avoid overriding header values
        complete_order_line = {
            k: v for k, v in complete_order_line.items() if v is not None
        }
        self.order_lines.append(OrderRow(**complete_order_line))
        logger.info(
            f"Order line added for product {productcode} with quantity {orderquantity} {unitofmeasure}."
        )

    def add_order_comments(self, comments: str) -> None:
        """
        VIP allows comments to be added to an order. These take the form of a row
        in the order data with some specific formatting.
        Note: Comments will line break over 70 characters when viewed in the
        VIP interface.
        """
        logger.info(f"Adding order comments: {comments}")
        comment_row = OrderRow(
            productcode="000997",  # A specific product code used for comments
            orderquantity=0,
            unitofmeasure="MI",
            invoicecomments=comments,
        )
        self.order_comments.append(comment_row)

    def remove_order_line(self, productcode: str):
        """
        Remove an order line by its productcode.
        """

        logger.info(f"Attempting to remove order line with product code {productcode}")

        # Check that productcode is present
        if any(
            getattr(line, "productcode", None) == productcode
            for line in self.order_lines
        ):
            # If so, remove the corresponding order line
            self.order_lines = [
                line for line in self.order_lines if line.productcode != productcode
            ]
            logger.info(
                f"Successfully removed order line with product code {productcode}"
            )
        else:
            error_msg = f"Product code {productcode} not found in order lines."
            logger.error(error_msg)
            raise ValueError(error_msg)

    def remove_order_comments(self):
        """
        Clears out all order comments from the order.
        """
        logger.info("Removing all order comments")
        self.order_comments.clear()

    def update_order_line(self, productcode: str, **kwargs):
        """
        Update an existing order line with new values.

        :param productcode: The product code of the order line to update.
        :param kwargs: The fields to update and their new values.
        """

        # Find the order line to update
        order_line = next(
            (line for line in self.order_lines if line.productcode == productcode), None
        )

        if order_line:
            # Update the order line with new values
            for key, value in kwargs.items():
                setattr(order_line, key, value)
            logger.info(
                f"Successfully updated order line with product code {productcode}"
            )
        else:
            error_msg = f"Product code {productcode} not found in order lines."
            logger.error(error_msg)
            raise ValueError(error_msg)

    def __str__(self):
        """
        Prints a string representation of the order, including header fields
        and number of order lines.
        """
        return f"Order({self.retailerid}, {self.company}, {len(self.order_lines)})"


class OrderBatch:
    """
    OrderBatch represents a batch of one or more orders to be processed by VIP.
    Each order is represented by one or more OrderRows. It is the highest level
    data structure for managing orders.

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
        Ensures all date columns are strings in YYYYMMDD format and all columns are strings before validation/export.
        """
        logger.info("Converting order batch to DataFrame")
        df_orders = pd.DataFrame()

        for order in self.orders:
            all_rows = order.order_lines + order.order_comments
            rows_dicts = []

            # Row-level conversions
            for row in all_rows:
                row_dict = row.__dict__.copy()

                # Convert numeric fields to formatted strings
                if (
                    "orderquantity" in row_dict
                    and row_dict["orderquantity"] is not None
                ):
                    if isinstance(row_dict["orderquantity"], int):
                        row_dict["orderquantity"] = f"{row_dict['orderquantity']:05}"
                if "orderprice" in row_dict and row_dict["orderprice"] is not None:
                    if isinstance(row_dict["orderprice"], float):
                        row_dict["orderprice"] = f"{row_dict['orderprice']:.3f}"
                if (
                    "discountamount" in row_dict
                    and row_dict["discountamount"] is not None
                ):
                    if isinstance(row_dict["discountamount"], float):
                        row_dict["discountamount"] = f"{row_dict['discountamount']:.2f}"
                if (
                    "postoffamount" in row_dict
                    and row_dict["postoffamount"] is not None
                ):
                    if isinstance(row_dict["postoffamount"], float):
                        row_dict["postoffamount"] = f"{row_dict['postoffamount']:.2f}"
                if (
                    "depositamount" in row_dict
                    and row_dict["depositamount"] is not None
                ):
                    if isinstance(row_dict["depositamount"], float):
                        row_dict["depositamount"] = f"{row_dict['depositamount']:.2f}"

                rows_dicts.append(row_dict)

            order_df = pd.DataFrame(rows_dicts)

            # Add header-level fields to each row
            order_df["retailerid"] = order.retailerid
            order_df["company"] = order.company
            order_df["warehouse"] = order.warehouse
            order_df["ordernumber"] = order.ordernumber
            order_df["deliverydate"] = order.deliverydate
            order_df["loadnumber"] = order.loadnumber
            order_df["driver"] = order.driver
            order_df["codedate"] = order.codedate
            order_df["ponumber"] = order.ponumber
            order_df["performancediscountanswer"] = order.performancediscountanswer
            order_df["orderdate"] = order.orderdate
            order_df["orderaction"] = order.orderaction
            order_df["ordertype"] = order.ordertype

            # Header-level conversions: convert date fields to YYYYMMDD strings if not None
            for date_col in ["deliverydate", "codedate", "orderdate"]:
                if date_col in order_df:
                    # Convert each value in the column to string if it's a date, else leave as is
                    order_df[date_col] = order_df[date_col].apply(
                        lambda x: x.strftime("%Y%m%d")
                        if isinstance(x, (datetime, date))
                        else (str(x) if x is not None else None)
                    )

            # Create list of linenumbers for each order. Each linenumber is a 3-digit string starting from 001
            line_count = len(all_rows)
            line_numbers = [f"{i + 1:03}" for i in range(line_count)]
            order_df["linenumber"] = line_numbers

            df_orders = pd.concat([df_orders, order_df], ignore_index=True)

        # Ensure all required columns are present in the correct order
        for col in FIELD_NAMES:
            if col not in df_orders.columns:
                df_orders[col] = None

        # Reorder columns to match the expected field order
        df_orders = df_orders[FIELD_NAMES]

        # # Replace None/NaN with empty string, then cast to string
        # df_orders = df_orders.where(pd.notnull(df_orders), "")
        # df_orders = df_orders.astype(str)

        # Validate the DataFrame against the OrderModel
        OrderModel.validate(df_orders)

        # Add dataframe attributes for completeness
        df_orders.attrs["SEQUENCE"] = "85"
        df_orders.attrs["DATATYPE"] = "ORDERS"
        df_orders.attrs["ID"] = "0000000000"  # Placeholder for ID
        df_orders.attrs["DATE"] = datetime.now().strftime("%Y%m%d")
        df_orders.attrs["TIME"] = datetime.now().strftime("%H%M%S")

        return df_orders

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
