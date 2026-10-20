"""
The orders module contains classes to aid in constructing order data.
"""

import dataclasses
import io
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

import pandas as pd

from .models import OrderModel

logger = logging.getLogger(__name__)

# Define the field names in the order they should appear in the output
FIELD_NAMES = OrderModel.FIELD_NAMES()

UNITS_OF_MEASURE = ["CW", "CB", "BW", "HK", "QK", "MI", "CS", "FS", "PO", "PR"]

# Characters that would break the pipe-delimited file format
FORBIDDEN_CHARS = set(",'\"|\r\n")

# Decimal fields mapped to (max digits before the decimal point, decimal places)
DECIMAL_FIELDS = {
    "orderprice": (6, 3),
    "discountamount": (5, 2),
    "postoffamount": (5, 2),
    "depositamount": (5, 2),
}

COMMENT_PRODUCTCODE = "000997"


def check_forbidden_chars(fields: dict[str, object]) -> None:
    """
    Raise if any string value contains a character that would break the file format.

    :param fields: Mapping of field name to value
    :type fields: dict[str, object]
    :raises ValueError: If a value contains a comma, quote, pipe, or line break
    """
    for name, value in fields.items():
        if isinstance(value, str) and FORBIDDEN_CHARS & set(value):
            raise ValueError(
                f"{name} must not contain commas, quotes, pipes, or line breaks"
            )


def to_yyyymmdd(value: date | int, name: str, allow_zero: bool = False) -> int:
    """
    Convert a date, or validate an integer, as a YYYYMMDD integer.

    :param value: A date, or an integer already in YYYYMMDD format
    :type value: date | int
    :param name: Field name, used in error messages
    :type name: str
    :param allow_zero: Whether 0 is accepted (unassigned delivery day)
    :type allow_zero: bool
    :return: The date as a YYYYMMDD integer
    :rtype: int
    :raises ValueError: If the value is not a valid date
    """
    if isinstance(value, date):
        return int(value.strftime("%Y%m%d"))
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be a date or a YYYYMMDD integer")
    if allow_zero and value == 0:
        return 0
    try:
        datetime.strptime(str(value), "%Y%m%d")
    except ValueError:
        raise ValueError(f"{name} must be a valid YYYYMMDD date, got {value}") from None
    if len(str(value)) != 8:
        raise ValueError(f"{name} must be a valid YYYYMMDD date, got {value}")
    return value


def format_decimal(value: int | float, name: str) -> str:
    """
    Format a decimal field to its fixed number of decimal places, validating its size.

    :param value: The numeric value
    :type value: int | float
    :param name: Field name, must be a key of DECIMAL_FIELDS
    :type name: str
    :return: The formatted value, e.g. "10.500"
    :rtype: str
    :raises ValueError: If the value is not a non-negative number that fits the field
    """
    int_digits, places = DECIMAL_FIELDS[name]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    text = f"{value:.{places}f}"
    if not re.fullmatch(rf"\d{{1,{int_digits}}}\.\d{{{places}}}", text):
        raise ValueError(
            f"{name} must be non-negative with at most {int_digits} digits before the decimal point"
        )
    return text


@dataclass
class OrderRow:
    """
    OrderRow represents a single row of order data in an given order.
    Each row corresponds to a product, with its associated details.

    :param productcode: 6-digit product code
    :param orderquantity: Order quantity, 0 to 99999
    :param unitofmeasure: The unit of measure for the order quantity
    :param orderprice: Price, up to 6 digits before the decimal point (optional)
    :param discountamount: Discount amount, up to 5 digits before the decimal point (optional)
    :param postoffamount: Post-off amount, up to 5 digits before the decimal point (optional)
    :param depositamount: Deposit amount, up to 5 digits before the decimal point (optional)
    :param specialprice: "0" or "1". 0 = No special price, 1 = Special price applies (optional)
    :param voidflag: "Y" or "N" (optional)
    :param reasoncode: 2-character reason code (optional)
    :param codedate: Code date as a date or YYYYMMDD integer, stored as an integer (optional)
    :param discountcode: Up to 10 character discount code (optional)
    :param discountgroup: Up to 10 character discount group (optional)
    :param discountlevel: 1-character discount level (optional)
    :param ignoredeliverycharge: "Y" or "N" (optional)
    :param invoicecomments: Comments for the invoice, only allowed on comment rows (optional)
    """

    productcode: str
    orderquantity: int
    unitofmeasure: str
    orderprice: int | float | None = None
    discountamount: int | float | None = None
    postoffamount: int | float | None = None
    depositamount: int | float | None = None
    specialprice: str | None = None
    voidflag: str | None = None
    reasoncode: str | None = None
    codedate: date | int | None = None
    discountcode: str | None = None
    discountgroup: str | None = None
    discountlevel: str | None = None
    ignoredeliverycharge: str | None = None
    invoicecomments: str | None = None

    def __post_init__(self) -> None:
        """
        Validate the fields to ensure they meet the requirements, and normalize
        codedate to a YYYYMMDD integer.
        """
        check_forbidden_chars(dataclasses.asdict(self))
        if not re.fullmatch(r"\d{6}", self.productcode):
            raise ValueError("productcode must be exactly 6 digits")
        if self.unitofmeasure not in UNITS_OF_MEASURE:
            raise ValueError(f"unitofmeasure must be one of {UNITS_OF_MEASURE}")
        if (
            isinstance(self.orderquantity, bool)
            or not isinstance(self.orderquantity, int)
            or not 0 <= self.orderquantity <= 99999
        ):
            raise ValueError("orderquantity must be an integer between 0 and 99999")
        for name in DECIMAL_FIELDS:
            if getattr(self, name) is not None:
                format_decimal(getattr(self, name), name)
        if self.specialprice and self.specialprice not in ["0", "1"]:
            raise ValueError("specialprice must be '0' or '1'")
        if self.voidflag and self.voidflag not in ["Y", "N"]:
            raise ValueError("voidflag must be 'Y' or 'N'")
        if self.reasoncode and len(self.reasoncode) != 2:
            raise ValueError("reasoncode must be exactly 2 characters long")
        if self.codedate is not None:
            self.codedate = to_yyyymmdd(self.codedate, "codedate")
        if self.discountcode and len(self.discountcode) > 10:
            raise ValueError("discountcode must be at most 10 characters long")
        if self.discountgroup and len(self.discountgroup) > 10:
            raise ValueError("discountgroup must be at most 10 characters long")
        if self.discountlevel and len(self.discountlevel) != 1:
            raise ValueError("discountlevel must be exactly 1 character long")
        if self.ignoredeliverycharge and self.ignoredeliverycharge not in ["Y", "N"]:
            raise ValueError("ignoredeliverycharge must be 'Y' or 'N'")
        if self.invoicecomments:
            if self.productcode != COMMENT_PRODUCTCODE:
                raise ValueError(
                    f"invoicecomments only allowed on comment rows (productcode {COMMENT_PRODUCTCODE})"
                )
            if len(self.invoicecomments) > 560:
                raise ValueError("invoicecomments must be at most 560 characters long")


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
        deliverydate: date | int,
        loadnumber: str | None = None,
        driver: str | None = None,
        ponumber: str | None = None,
        performancediscountanswer: Literal["Y", "N"] | None = None,
        salesrep: str | None = None,
        orderdate: date | int | None = None,
        orderaction: str | None = None,
        ordertype: Literal["S", "T"] | None = None,
    ) -> None:
        """
        Initialize an Order with header-level fields that will be the same
        for all order lines.

        :param retailerid: The 5-character VIP account number of the retailer
        :param company: The company ID, up to 5 characters
        :param warehouse: The warehouse ID, up to 5 characters
        :param ordernumber: The order number, up to 9 characters
        :param deliverydate: The delivery date, as a date or YYYYMMDD integer. 0 = unassigned delivery day
        :param loadnumber: The 8-character load number (optional)
        :param driver: The 5-character driver ID (optional)
        :param ponumber: The DSD or PO number (optional)
        :param performancediscountanswer: "Y" or "N" (optional)
        :param salesrep: Sales rep override, up to 5 characters (optional)
        :param orderdate: The order date, as a date or YYYYMMDD integer (optional)
        :param orderaction: The 2-character order action. Combine, Lock, DTT (optional)
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
        self.deliverydate = to_yyyymmdd(deliverydate, "deliverydate", allow_zero=True)
        self.loadnumber = loadnumber
        self.driver = driver
        self.ponumber = ponumber
        self.performancediscountanswer = performancediscountanswer
        self.salesrep = salesrep
        self.orderdate = (
            to_yyyymmdd(orderdate, "orderdate") if orderdate is not None else None
        )
        self.orderaction = orderaction
        self.ordertype = ordertype

        # Validate that header fields meet their requirements
        check_forbidden_chars(vars(self))
        if len(self.retailerid) != 5:
            raise ValueError("retailerid must be exactly 5 characters long")
        if not 1 <= len(self.company) <= 5:
            raise ValueError("company must be 1 to 5 characters long")
        if not 1 <= len(self.warehouse) <= 5:
            raise ValueError("warehouse must be 1 to 5 characters long")
        if not 1 <= len(self.ordernumber) <= 9:
            raise ValueError("ordernumber must be 1 to 9 characters long")
        if self.loadnumber and len(self.loadnumber) != 8:
            raise ValueError("loadnumber must be exactly 8 characters long")
        if self.driver and len(self.driver) != 5:
            raise ValueError("driver must be exactly 5 characters long")
        if self.ponumber and len(self.ponumber) > 15:
            raise ValueError("ponumber must be at most 15 characters long")
        if self.performancediscountanswer and self.performancediscountanswer not in [
            "Y",
            "N",
        ]:
            raise ValueError("performancediscountanswer must be 'Y' or 'N'")
        if self.salesrep and len(self.salesrep) > 5:
            raise ValueError("salesrep must be at most 5 characters long")
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
        orderprice: int | float | None = None,
        discountamount: int | float | None = None,
        postoffamount: int | float | None = None,
        depositamount: int | float | None = None,
        specialprice: Literal["0", "1"] | None = None,
        voidflag: Literal["Y", "N"] | None = None,
        reasoncode: str | None = None,
        codedate: date | int | None = None,
        discountcode: str | None = None,
        discountgroup: str | None = None,
        discountlevel: str | None = None,
        ignoredeliverycharge: Literal["Y", "N"] | None = None,
    ) -> None:
        """
        Add an order line to this order. The header fields will be automatically
        added to the order line.

        :param productcode: 6-digit product code
        :param orderquantity: Order quantity, 0 to 99999
        :param unitofmeasure: 2-character unit of measure, CW = Case Wine, CB = case beer, BW = bottle wine, HK = Half Keg, QK=Quarter Keg, MI=Miscellaneous, CS= Case Soda, FS = Fountain Syrup, PO = Postmix, PR = Premix
        :param orderprice: Price, up to 6 digits before the decimal point (optional)
        :param discountamount: Discount amount, up to 5 digits before the decimal point (optional)
        :param postoffamount: Post-off amount, up to 5 digits before the decimal point (optional)
        :param depositamount: Deposit amount, up to 5 digits before the decimal point (optional)
        :param specialprice: "0" or "1". 0 = No special price, 1 = Special price applies (optional)
        :param voidflag: "Y" or "N" (optional)
        :param reasoncode: 2-character reason code (optional)
        :param codedate: Code date, as a date or YYYYMMDD integer (optional)
        :param discountcode: Up to 10 character discount code (optional)
        :param discountgroup: Up to 10 character discount group (optional)
        :param discountlevel: 1-character discount level (optional)
        :param ignoredeliverycharge: "Y" or "N" (optional)
        """
        # Check that productcode not already present
        if any(line.productcode == productcode for line in self.order_lines):
            error_msg = f"Product code {productcode} is already present in order lines."
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(
            f"Adding order line for product {productcode}, quantity {orderquantity} {unitofmeasure}"
        )

        self.order_lines.append(
            OrderRow(
                productcode=productcode,
                orderquantity=orderquantity,
                unitofmeasure=unitofmeasure,
                orderprice=orderprice,
                discountamount=discountamount,
                postoffamount=postoffamount,
                depositamount=depositamount,
                specialprice=specialprice,
                voidflag=voidflag,
                reasoncode=reasoncode,
                codedate=codedate,
                discountcode=discountcode,
                discountgroup=discountgroup,
                discountlevel=discountlevel,
                ignoredeliverycharge=ignoredeliverycharge,
            )
        )
        logger.info(
            f"Order line added for product {productcode} with quantity {orderquantity} {unitofmeasure}."
        )

    def add_order_comments(self, comments: str) -> None:
        """
        VIP allows comments to be added to an order. These take the form of a row
        in the order data with some specific formatting. Multiple comment rows
        per order are allowed.
        Note: Comments will line break over 70 characters when viewed in the
        VIP interface.

        :param comments: The comment text, up to 560 characters
        :type comments: str
        """
        logger.info(f"Adding order comments: {comments}")
        comment_row = OrderRow(
            productcode=COMMENT_PRODUCTCODE,
            orderquantity=0,
            unitofmeasure="MI",
            invoicecomments=comments,
        )
        self.order_comments.append(comment_row)

    def remove_order_line(self, productcode: str) -> None:
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

    def remove_order_comments(self) -> None:
        """
        Clears out all order comments from the order.
        """
        logger.info("Removing all order comments")
        self.order_comments.clear()

    def update_order_line(self, productcode: str, **kwargs) -> None:
        """
        Update an existing order line with new values. The updated line is
        validated the same way as a new one.

        :param productcode: The product code of the order line to update.
        :param kwargs: The fields to update and their new values.
        """
        # Find the order line to update
        index = next(
            (
                i
                for i, line in enumerate(self.order_lines)
                if line.productcode == productcode
            ),
            None,
        )
        if index is None:
            error_msg = f"Product code {productcode} not found in order lines."
            logger.error(error_msg)
            raise ValueError(error_msg)

        # replace() builds a new OrderRow, so __post_init__ validation runs again
        self.order_lines[index] = dataclasses.replace(self.order_lines[index], **kwargs)
        logger.info(f"Successfully updated order line with product code {productcode}")

    def __str__(self) -> str:
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

    def __init__(self) -> None:
        """
        Construct a new batch of orders for import into VIP.
        """
        logger.info("Creating new OrderBatchModel")
        self.orders: list[Order] = []

    def add_order(self, order: Order) -> None:
        """
        Add an order to the batch.
        """
        logger.info(f"Adding order for retailer {order.retailerid} to batch")
        self.orders.append(order)

    def remove_order(self, order: Order) -> None:
        """
        Remove an order from the batch.
        """
        logger.info(f"Removing order for retailer {order.retailerid} from batch")
        self.orders.remove(order)

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the batch of orders to a single DataFrame.
        Each order's lines are concatenated into a single DataFrame.
        Decimal fields are formatted as strings, date fields are nullable integers.
        """
        logger.info("Converting order batch to DataFrame")
        df_orders = pd.DataFrame()

        for order in self.orders:
            all_rows = order.order_lines + order.order_comments
            rows_dicts = []

            # Row-level conversions
            for row in all_rows:
                row_dict = dataclasses.asdict(row)
                row_dict["orderquantity"] = f"{row.orderquantity:05}"
                for name in DECIMAL_FIELDS:
                    if row_dict[name] is not None:
                        row_dict[name] = format_decimal(row_dict[name], name)
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
            order_df["ponumber"] = order.ponumber
            order_df["performancediscountanswer"] = order.performancediscountanswer
            order_df["salesrep"] = order.salesrep
            order_df["orderdate"] = order.orderdate
            order_df["orderaction"] = order.orderaction
            order_df["ordertype"] = order.ordertype

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

        # Nullable integer dtype keeps dates as integers instead of floats when blanks are present
        for col in ["codedate", "deliverydate", "orderdate"]:
            df_orders[col] = df_orders[col].astype("Int64")

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
            sep="|", index=False, header=False, lineterminator="\r\n"
        )
        header_str = "|".join(FIELD_NAMES)

        output = io.BytesIO()
        output.write((header_str + "\r\n").encode("utf-8"))
        output.write(data_str.encode("utf-8"))
        output.seek(0)

        return output

    @staticmethod
    def generate_filename(id: str, datetime: datetime) -> str:
        """
        Generate the filename for the order file to be uploaded to VIP.

        :param id: Unique identifier for the file, 1 to 10 alphanumeric characters
        :type id: str
        :param datetime: Timestamp the file was created
        :type datetime: datetime
        :return: The filename
        :rtype: str
        :raises ValueError: If id is not 1 to 10 alphanumeric characters
        """
        if not re.fullmatch(r"[A-Za-z0-9]{1,10}", id):
            raise ValueError("id must be 1 to 10 alphanumeric characters")
        filename = f"85_ORDERS_{id}_{datetime.strftime('%Y%m%d_%H%M%S')}.DAT"
        logger.info(f"Generated filename: {filename}")
        return filename

    def __str__(self) -> str:
        """
        Prints a string representation of an OrderBatch.
        """
        return "\n".join([str(order) for order in self.orders])
