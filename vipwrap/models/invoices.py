"""
The invoices module contains classes to aid in constructing invoice/sales history data.
"""

import dataclasses
import io
import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import BinaryIO, Literal

import pandas as pd

from .models import InvoiceModel
from .utils import (
    check_forbidden_chars,
    check_int,
    format_decimal,
    parse_numbers,
    read_flat_file,
    to_yyyymmdd,
)
from .utils import generate_filename as build_filename

logger = logging.getLogger(__name__)

# Define the field names in the order they should appear in the output
FIELD_NAMES = InvoiceModel.FIELD_NAMES()

# Integer fields mapped to (max digits, whether negatives are allowed)
INT_FIELDS = {
    "orderquantity": (5, True),
    "outquantity": (5, False),
    "onhandquantity": (7, False),
    "partialcasequantity": (2, False),
}

# Decimal fields mapped to (max digits before the decimal point, decimal places, whether negatives are allowed)
DECIMAL_FIELDS = {
    "orderprice": (6, 3, True),
    "ordercost": (6, 5, True),
    "depositamount": (5, 2, True),
    "depletionallowance": (6, 5, True),
    "postoffamount": (5, 2, True),
    "discountamount": (5, 2, False),
}

# Columns written as nullable integers
INT_COLUMNS = ["invoicedate", "arstatus", "linenumber", "codedate", *INT_FIELDS]


def check_fields(
    values: dict[str, object],
    exact: dict[str, int] | None = None,
    maximum: dict[str, int] | None = None,
    choices: dict[str, list] | None = None,
) -> None:
    """
    Validate string lengths and allowed values. None values are skipped.

    :param values: Mapping of field name to value
    :type values: dict[str, object]
    :param exact: Fields that must be exactly this many characters
    :type exact: dict[str, int] | None
    :param maximum: Fields that must be 1 to this many characters
    :type maximum: dict[str, int] | None
    :param choices: Fields that must be one of the listed values
    :type choices: dict[str, list] | None
    :raises ValueError: If a field fails its check
    """
    for name, length in (exact or {}).items():
        if values[name] is not None and len(values[name]) != length:
            raise ValueError(f"{name} must be exactly {length} characters long")
    for name, length in (maximum or {}).items():
        if values[name] is not None and not 1 <= len(values[name]) <= length:
            raise ValueError(f"{name} must be 1 to {length} characters long")
    for name, allowed in (choices or {}).items():
        if values[name] is not None and values[name] not in allowed:
            raise ValueError(f"{name} must be one of {allowed}")


@dataclass
class InvoiceRow:
    """
    InvoiceRow represents a single product line on a given invoice.

    :param productcode: 6-digit product code
    :param unitofmeasure: 2-character unit of measure, e.g. CW, BW, EA
    :param orderquantity: Quantity, -99999 to 99999. Negative for credits
    :param orderprice: Net price per selling unit, up to 6 digits before the decimal point
    :param ordermode: "0" = presale, "1" = driver sale, "2" = good return, "3" = bad return (optional)
    :param outquantity: Out quantity, 0 to 99999 (optional)
    :param onhandquantity: On hand quantity, 0 to 9999999 (optional)
    :param partialcasequantity: Partial case quantity, 0 to 99 (optional)
    :param returnreasoncode: 2-character return reason code (optional)
    :param codedate: Code date as a date or YYYYMMDD integer, stored as an integer (optional)
    :param ordercost: Cost per selling unit, up to 6 digits before the decimal point (optional)
    :param depositamount: Deposit amount, up to 5 digits before the decimal point (optional)
    :param deposittype: "K" = Keg Deposit, "C" = CRV, "O" = Other/Bottle Deposit (optional)
    :param depletionallowance: Depletion allowance per selling unit, up to 6 digits before the decimal point (optional)
    :param postoffamount: Post-off amount, up to 5 digits before the decimal point (optional)
    :param discountamount: Discount amount, non-negative, up to 5 digits before the decimal point (optional)
    :param discountlevel1: Up to 10 character discount level 1 (optional)
    :param discountlevel2: Up to 10 character discount level 2 (optional)
    :param discountlevel3: Up to 10 character discount level 3 (optional)
    :param discountlevel4: Up to 10 character discount level 4 (optional)
    :param discountlevel: 1-character discount level (optional)
    :param specialprice: "0" or "1". 0 = No special price, 1 = Special price applies (optional)
    """

    productcode: str
    unitofmeasure: str
    orderquantity: int
    orderprice: int | float
    ordermode: str | None = None
    outquantity: int | None = None
    onhandquantity: int | None = None
    partialcasequantity: int | None = None
    returnreasoncode: str | None = None
    codedate: date | int | None = None
    ordercost: int | float | None = None
    depositamount: int | float | None = None
    deposittype: str | None = None
    depletionallowance: int | float | None = None
    postoffamount: int | float | None = None
    discountamount: int | float | None = None
    discountlevel1: str | None = None
    discountlevel2: str | None = None
    discountlevel3: str | None = None
    discountlevel4: str | None = None
    discountlevel: str | None = None
    specialprice: str | None = None

    def __post_init__(self) -> None:
        """
        Validate the fields to ensure they meet the requirements, and normalize
        codedate to a YYYYMMDD integer.
        """
        values = dataclasses.asdict(self)
        check_forbidden_chars(values)
        if not re.fullmatch(r"\d{6}", self.productcode):
            raise ValueError("productcode must be exactly 6 digits")
        if not re.fullmatch(r"[A-Z]{2}", self.unitofmeasure):
            raise ValueError("unitofmeasure must be 2 uppercase letters")
        for name in ["orderquantity", "orderprice"]:
            if values[name] is None:
                raise ValueError(f"{name} is required on an invoice line")
        for name, (digits, signed) in INT_FIELDS.items():
            if values[name] is not None:
                check_int(values[name], name, digits, signed)
        for name, spec in DECIMAL_FIELDS.items():
            if values[name] is not None:
                format_decimal(values[name], name, *spec)
        check_fields(
            values,
            exact={"returnreasoncode": 2},
            maximum={
                "discountlevel1": 10,
                "discountlevel2": 10,
                "discountlevel3": 10,
                "discountlevel4": 10,
                "discountlevel": 1,
            },
            choices={
                "ordermode": ["0", "1", "2", "3"],
                "deposittype": ["K", "C", "O"],
                "specialprice": ["0", "1"],
            },
        )
        if self.codedate is not None:
            self.codedate = to_yyyymmdd(self.codedate, "codedate")


@dataclass(eq=False)
class Invoice:
    """
    Invoice represents a single invoice for a given retailer, holding the
    header-level fields that will be the same for all invoice lines.
    An invoice with no lines is exported as a detail-less invoice.

    While working with invoice data, the productcode is considered the primary key
    that identifies each line. Only one line per productcode is allowed.
    Once a batch of invoices is being exported, the linenumber will be added for
    each invoice line.

    :param retailerid: The 5-character VIP account number of the retailer
    :param invoicenumber: The invoice number, up to 15 alphanumeric characters
    :param invoicedate: The invoice date, as a date or YYYYMMDD integer
    :param arstatus: 1 = In A/R (balance exists until paid), 3 = Not found in A/R (payment not expected) (optional)
    :param ordertype: Up to 2 character order type (optional)
    :param loadnumber: 8-character load number, starting with the day number, Monday = 1 (optional)
    :param driver: 5-character driver ID (optional)
    :param helper1: 5-character helper ID (optional)
    :param helper2: 5-character helper ID (optional)
    :param helper3: 5-character helper ID (optional)
    :param helper4: 5-character helper ID (optional)
    :param helper5: 5-character helper ID (optional)
    :param company: Company ID, up to 5 characters (optional)
    :param warehouse: Warehouse ID, up to 5 characters (optional)
    :param flpgroup: FLP group, up to 5 characters (optional)
    :param pricegroup: Price group, up to 5 characters (optional)
    :param subpricegroup: Sub price group, up to 5 characters (optional)
    :param salesrep: Sales rep, up to 5 characters (optional)
    :param voidflag: "Y" or "N" (optional)
    :param voidreason: 2-character void reason code (optional)
    :param invoicetype: 1-character invoice type (optional)
    :param artype: 1-character A/R type (optional)
    :param trucktype: 1-character truck type (optional)
    :param ponumber: PO number, up to 15 characters (optional)
    """

    retailerid: str
    invoicenumber: str
    invoicedate: date | int
    arstatus: Literal[1, 3] | None = None
    ordertype: str | None = None
    loadnumber: str | None = None
    driver: str | None = None
    helper1: str | None = None
    helper2: str | None = None
    helper3: str | None = None
    helper4: str | None = None
    helper5: str | None = None
    company: str | None = None
    warehouse: str | None = None
    flpgroup: str | None = None
    pricegroup: str | None = None
    subpricegroup: str | None = None
    salesrep: str | None = None
    voidflag: Literal["Y", "N"] | None = None
    voidreason: str | None = None
    invoicetype: str | None = None
    artype: str | None = None
    trucktype: str | None = None
    ponumber: str | None = None
    invoice_lines: list[InvoiceRow] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        """
        Validate the header fields, and normalize invoicedate to a YYYYMMDD integer.
        """
        logger.info(
            f"Creating new invoice for retailer {self.retailerid}, invoice number {self.invoicenumber}"
        )
        values = self.header()
        check_forbidden_chars(values)
        if not re.fullmatch(r"[A-Za-z0-9]{1,15}", self.invoicenumber):
            raise ValueError("invoicenumber must be 1 to 15 alphanumeric characters")
        if self.loadnumber is not None and not re.fullmatch(
            r"[1-7].{7}", self.loadnumber
        ):
            raise ValueError(
                "loadnumber must be exactly 8 characters long and start with the day number (1-7)"
            )
        check_fields(
            values,
            exact={
                "retailerid": 5,
                "driver": 5,
                "helper1": 5,
                "helper2": 5,
                "helper3": 5,
                "helper4": 5,
                "helper5": 5,
                "voidreason": 2,
            },
            maximum={
                "ordertype": 2,
                "company": 5,
                "warehouse": 5,
                "flpgroup": 5,
                "pricegroup": 5,
                "subpricegroup": 5,
                "salesrep": 5,
                "invoicetype": 1,
                "artype": 1,
                "trucktype": 1,
                "ponumber": 15,
            },
            choices={"arstatus": [1, 3], "voidflag": ["Y", "N"]},
        )
        self.invoicedate = to_yyyymmdd(self.invoicedate, "invoicedate")

    def header(self) -> dict[str, object]:
        """
        Return the header-level fields of the invoice.

        :return: Mapping of header field name to value
        :rtype: dict[str, object]
        """
        return {
            f.name: getattr(self, f.name) for f in dataclasses.fields(self) if f.init
        }

    def add_invoice_line(
        self,
        productcode: str,
        unitofmeasure: str,
        orderquantity: int,
        orderprice: int | float,
        **kwargs,
    ) -> None:
        """
        Add a line to this invoice. The header fields will be automatically
        added to the line on export.

        :param productcode: 6-digit product code
        :param unitofmeasure: 2-character unit of measure
        :param orderquantity: Quantity, -99999 to 99999. Negative for credits
        :param orderprice: Net price per selling unit
        :param kwargs: Any optional InvoiceRow field, e.g. ordermode, ordercost, codedate
        """
        # Check that productcode not already present
        if any(line.productcode == productcode for line in self.invoice_lines):
            error_msg = (
                f"Product code {productcode} is already present in invoice lines."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        self.invoice_lines.append(
            InvoiceRow(productcode, unitofmeasure, orderquantity, orderprice, **kwargs)
        )
        logger.info(
            f"Invoice line added for product {productcode} with quantity {orderquantity} {unitofmeasure}."
        )

    def remove_invoice_line(self, productcode: str) -> None:
        """
        Remove an invoice line by its productcode.

        :param productcode: The product code of the line to remove
        """
        logger.info(
            f"Attempting to remove invoice line with product code {productcode}"
        )
        remaining = [
            line for line in self.invoice_lines if line.productcode != productcode
        ]
        if len(remaining) == len(self.invoice_lines):
            error_msg = f"Product code {productcode} not found in invoice lines."
            logger.error(error_msg)
            raise ValueError(error_msg)
        self.invoice_lines = remaining
        logger.info(
            f"Successfully removed invoice line with product code {productcode}"
        )

    def update_invoice_line(self, productcode: str, **kwargs) -> None:
        """
        Update an existing invoice line with new values. The updated line is
        validated the same way as a new one.

        :param productcode: The product code of the line to update.
        :param kwargs: The fields to update and their new values.
        """
        index = next(
            (
                i
                for i, line in enumerate(self.invoice_lines)
                if line.productcode == productcode
            ),
            None,
        )
        if index is None:
            error_msg = f"Product code {productcode} not found in invoice lines."
            logger.error(error_msg)
            raise ValueError(error_msg)

        # replace() builds a new InvoiceRow, so __post_init__ validation runs again
        self.invoice_lines[index] = dataclasses.replace(
            self.invoice_lines[index], **kwargs
        )
        logger.info(
            f"Successfully updated invoice line with product code {productcode}"
        )

    def __str__(self) -> str:
        """
        Prints a string representation of the invoice, including header fields
        and number of invoice lines.
        """
        return f"Invoice({self.retailerid}, {self.invoicenumber}, {len(self.invoice_lines)})"


# Field names used when building invoices from an existing file
HEADER_FIELDS = [f.name for f in dataclasses.fields(Invoice) if f.init]
LINE_FIELDS = [f.name for f in dataclasses.fields(InvoiceRow)]


class InvoiceBatch:
    """
    InvoiceBatch represents a batch of one or more invoices to be posted as
    sales history in VIP. It is the highest level data structure for managing
    invoices.

    DataFrame Attributes:
    SEQUENCE: 90
    DATATYPE: SALESHISTORY
    ID: Unique identifier for each file, max of 10 digits (alphanumeric)
    DATE: Date file was created, format YYYYMMDD
    TIME: Time file was created, format HHMMSS

    Output Filename: SEQUENCE_DATATYPE_ID_DATE_TIME.DAT
    """

    def __init__(self) -> None:
        """
        Construct a new batch of invoices for import into VIP.
        """
        logger.info("Creating new InvoiceBatch")
        self.invoices: list[Invoice] = []

    def add_invoice(self, invoice: Invoice) -> None:
        """
        Add an invoice to the batch.

        :param invoice: The invoice to add
        """
        logger.info(f"Adding invoice {invoice.invoicenumber} to batch")
        self.invoices.append(invoice)

    def remove_invoice(self, invoice: Invoice) -> None:
        """
        Remove an invoice from the batch.

        :param invoice: The invoice to remove
        """
        logger.info(f"Removing invoice {invoice.invoicenumber} from batch")
        self.invoices.remove(invoice)

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the batch of invoices to a single DataFrame, one row per invoice
        line, or a single header-only row for a detail-less invoice.
        Decimal fields are formatted as strings, integer and date fields are
        nullable integers.

        :return: The validated invoice data
        :rtype: pd.DataFrame
        """
        logger.info("Converting invoice batch to DataFrame")
        rows = []
        for invoice in self.invoices:
            header = invoice.header()
            if not invoice.invoice_lines:
                rows.append(header)
            for i, line in enumerate(invoice.invoice_lines, start=1):
                row = {**header, **dataclasses.asdict(line), "linenumber": i}
                for name, spec in DECIMAL_FIELDS.items():
                    if row[name] is not None:
                        row[name] = format_decimal(row[name], name, *spec)
                rows.append(row)

        df_invoices = pd.DataFrame(rows, columns=FIELD_NAMES)
        df_invoices = df_invoices.astype(object).where(df_invoices.notna(), None)
        for col in INT_COLUMNS:
            df_invoices[col] = df_invoices[col].astype("Int64")

        # Validate the DataFrame against the InvoiceModel
        InvoiceModel.validate(df_invoices)

        # Add dataframe attributes for completeness
        df_invoices.attrs["SEQUENCE"] = "90"
        df_invoices.attrs["DATATYPE"] = "SALESHISTORY"
        df_invoices.attrs["ID"] = "0000000000"  # Placeholder for ID
        df_invoices.attrs["DATE"] = datetime.now().strftime("%Y%m%d")
        df_invoices.attrs["TIME"] = datetime.now().strftime("%H%M%S")

        return df_invoices

    def to_flat_file(self) -> io.BytesIO:
        """
        Export the invoice batch as a BytesIO object containing the flat file data.

        :return: The file contents, header row first
        :rtype: io.BytesIO
        """
        logger.info("Exporting invoice batch to flat file")
        data_str = self.to_dataframe().to_csv(
            sep="|", index=False, header=False, lineterminator="\r\n"
        )
        header_str = "|".join(FIELD_NAMES)

        output = io.BytesIO()
        output.write((header_str + "\r\n").encode("utf-8"))
        output.write(data_str.encode("utf-8"))
        output.seek(0)

        return output

    @classmethod
    def from_flat_file(cls, source: str | Path | BinaryIO) -> "InvoiceBatch":
        """
        Build an InvoiceBatch from an existing sales history file, e.g. one
        generated by another process, so it can be reviewed or updated and
        exported again.

        Rows are grouped into invoices by retailerid, invoicenumber, and
        invoicedate. A row without a productcode is a detail-less invoice.
        Line numbers are regenerated on export.

        :param source: Path to the .DAT file, or a binary file-like object
        :type source: str | Path | BinaryIO
        :return: The batch of invoices in the file
        :rtype: InvoiceBatch
        :raises ValueError: If a row fails validation, or rows of the same invoice have different header values
        """
        logger.info("Building invoice batch from flat file")
        batch = cls()
        invoices: dict[tuple, Invoice] = {}
        for line_no, row in enumerate(read_flat_file(source), start=2):
            try:
                parse_numbers(
                    row,
                    ints=[col for col in INT_COLUMNS if col != "linenumber"],
                    floats=list(DECIMAL_FIELDS),
                )
                header = {name: row.get(name) for name in HEADER_FIELDS}
                key = (
                    header["retailerid"],
                    header["invoicenumber"],
                    header["invoicedate"],
                )
                if key not in invoices:
                    invoices[key] = Invoice(**header)
                    batch.add_invoice(invoices[key])
                elif header != invoices[key].header():
                    raise ValueError(
                        f"Header values differ from earlier rows of invoice {key}"
                    )

                if row.get("productcode") is not None:
                    invoices[key].add_invoice_line(
                        **{name: row.get(name) for name in LINE_FIELDS}
                    )
            except (ValueError, TypeError) as e:
                raise ValueError(f"Row {line_no}: {e}") from e
        return batch

    @staticmethod
    def generate_filename(id: str, datetime: datetime) -> str:
        """
        Generate the filename for the sales history file to be uploaded to VIP.

        :param id: Unique identifier for the file, 1 to 10 alphanumeric characters
        :type id: str
        :param datetime: Timestamp the file was created
        :type datetime: datetime
        :return: The filename
        :rtype: str
        :raises ValueError: If id is not 1 to 10 alphanumeric characters
        """
        return build_filename("90", "SALESHISTORY", id, datetime)

    def __str__(self) -> str:
        """
        Prints a string representation of an InvoiceBatch.
        """
        return "\n".join([str(invoice) for invoice in self.invoices])
