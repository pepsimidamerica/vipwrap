"""
Validation and formatting helpers shared by the orders and invoices modules.
"""

import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import BinaryIO

logger = logging.getLogger(__name__)

# Characters that would break the pipe-delimited file format
FORBIDDEN_CHARS = set(",'\"|\r\n")


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


def check_int(value: int, name: str, max_digits: int, signed: bool = False) -> None:
    """
    Raise if a value is not an integer that fits in the given number of digits.

    :param value: The value to check
    :type value: int
    :param name: Field name, used in error messages
    :type name: str
    :param max_digits: Maximum number of digits
    :type max_digits: int
    :param signed: Whether negative values are allowed
    :type signed: bool
    :raises ValueError: If the value is not an integer in range
    """
    limit = 10**max_digits - 1
    low = -limit if signed else 0
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not low <= value <= limit
    ):
        raise ValueError(f"{name} must be an integer between {low} and {limit}")


def format_decimal(
    value: int | float, name: str, int_digits: int, places: int, signed: bool = False
) -> str:
    """
    Format a decimal field to its fixed number of decimal places, validating its size.

    :param value: The numeric value
    :type value: int | float
    :param name: Field name, used in error messages
    :type name: str
    :param int_digits: Maximum digits before the decimal point
    :type int_digits: int
    :param places: Number of decimal places
    :type places: int
    :param signed: Whether negative values are allowed
    :type signed: bool
    :return: The formatted value, e.g. "10.500"
    :rtype: str
    :raises ValueError: If the value is not a number that fits the field
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    text = f"{value:.{places}f}"
    sign = "-?" if signed else ""
    if not re.fullmatch(rf"{sign}\d{{1,{int_digits}}}\.\d{{{places}}}", text):
        raise ValueError(
            f"{name} must be {'a' if signed else 'a non-negative'} number with at most {int_digits} digits before the decimal point"
        )
    return text


def read_flat_file(source: str | Path | BinaryIO) -> list[dict[str, str | None]]:
    """
    Read a pipe-delimited GDI file into one dict per data row, keyed by the
    file's header row. Blank lines are skipped, blank values become None.

    :param source: Path to the file, or a binary file-like object
    :type source: str | Path | BinaryIO
    :return: The data rows
    :rtype: list[dict[str, str | None]]
    :raises ValueError: If a row has a different number of fields than the header
    """
    data = (
        Path(source).read_bytes() if isinstance(source, (str, Path)) else source.read()
    )
    lines = [line for line in data.decode("utf-8").splitlines() if line.strip()]
    field_names = lines[0].split("|")
    rows = []
    for line_no, line in enumerate(lines[1:], start=2):
        values = line.split("|")
        if len(values) != len(field_names):
            raise ValueError(
                f"Row {line_no} has {len(values)} fields, header has {len(field_names)}"
            )
        rows.append({k: v.strip() or None for k, v in zip(field_names, values)})
    logger.info(f"Read {len(rows)} rows from flat file")
    return rows


def parse_numbers(
    row: dict[str, str | None], ints: list[str], floats: list[str]
) -> None:
    """
    Convert the given fields of a row read from a flat file to numbers, in place.
    Missing and blank fields are left as None.

    :param row: A row from read_flat_file
    :type row: dict[str, str | None]
    :param ints: Fields to convert to int
    :type ints: list[str]
    :param floats: Fields to convert to float
    :type floats: list[str]
    :raises ValueError: If a value is not a valid number
    """
    for names, kind in ((ints, int), (floats, float)):
        for name in names:
            if row.get(name) is not None:
                row[name] = kind(row[name])


def generate_filename(sequence: str, datatype: str, id: str, dt: datetime) -> str:
    """
    Generate the filename for a file to be uploaded to VIP.

    :param sequence: The file sequence, e.g. "85"
    :type sequence: str
    :param datatype: The file data type, e.g. "ORDERS"
    :type datatype: str
    :param id: Unique identifier for the file, 1 to 10 alphanumeric characters
    :type id: str
    :param dt: Timestamp the file was created
    :type dt: datetime
    :return: The filename
    :rtype: str
    :raises ValueError: If id is not 1 to 10 alphanumeric characters
    """
    if not re.fullmatch(r"[A-Za-z0-9]{1,10}", id):
        raise ValueError("id must be 1 to 10 alphanumeric characters")
    filename = f"{sequence}_{datatype}_{id}_{dt.strftime('%Y%m%d_%H%M%S')}.DAT"
    logger.info(f"Generated filename: {filename}")
    return filename
