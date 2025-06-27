"""
models represents all data models used in VIP imports. Orders and Invoices/Sales History
Used to create and validate data as well as exporting to flat files for upload to VIP.
"""

import logging
from datetime import datetime

import pandas as pd
from pandera import DataFrameModel, Field, SeriesSchema, check_types

logger = logging.getLogger(__name__)


class OrderRowModel(SeriesSchema):
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


class OrderModel:
    """
    This model represents a single order. Each order can have multiple rows.
    This model is used in the OrderBatchModel. An order is a dataframe
    where each row is a dataframe series (OrderRowModel).

    The OrderModel now maintains header-level fields that are the same for every
    order line, while still preserving the complete flat file structure.
    """

    # Define the field names in the order they should appear in the output
    FIELD_NAMES = list(OrderRowModel.__annotations__.keys())

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
        # Store header fields
        self.header_fields = {
            "retailerid": retailerid,
            "company": company,
            "warehouse": warehouse,
            "ordernumber": ordernumber,
            "deliverydate": deliverydate,
            "loadnumber": loadnumber,
            "driver": driver,
            "codedate": codedate,
            "ponumber": ponumber,
            "performancediscountanswer": performancediscountanswer,
        }

        # Initialize empty dataframe for order lines
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
        specialprice: str | None = None,
        voidflag: str | None = None,
        reasoncode: str | None = None,
        discountcode: str | None = None,
        discountgroup: str | None = None,
        discountlevel: str | None = None,
        ignoredeliverycharge: str | None = None,
        orderdate: str | None = None,
        invoicecomments: str | None = None,
        orderaction: str | None = None,
        ordertype: str | None = None,
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

    def get_header_fields(self) -> dict[str, str]:
        """
        Get the header fields for this order.
        """
        return {k: v for k, v in self.header_fields.items() if v is not None}

    def __str__(self):
        """
        Allows for printing order dataframe in a readable format.
        """
        return self.order_lines.to_string(index=False)


class OrderBatchModel:
    """
    This model represents a batch of one or more orders to be processed by VIP.
    Each order is represented by one or more OrderRowModels.

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
        self.orders: list[OrderModel] = []

    def add_order(self, order: OrderModel):
        """
        Add an order to the batch.
        """
        logger.info(
            f"Adding order for retailer {order.header_fields.get('retailerid')} to batch"
        )
        self.orders.append(order)

    def remove_order(self, order: OrderModel):
        """
        Remove an order from the batch.
        """
        logger.info(
            f"Removing order for retailer {order.header_fields.get('retailerid')} from batch"
        )
        self.orders.remove(order)

    def to_flat_file(self, filename: str):
        logger.info(f"Exporting order batch to flat file: {filename}")
        # Concatenate all order dataframes, preserving the original field order
        all_data = pd.concat(
            [order.order_lines for order in self.orders], ignore_index=True
        )

        # Ensure all required columns are present in the correct order
        for col in OrderModel.FIELD_NAMES:
            if col not in all_data.columns:
                all_data[col] = None

        # Reorder columns to match the expected field order
        all_data = all_data[OrderModel.FIELD_NAMES]

        # Convert to CSV with pipe separator
        data_str = all_data.to_csv(
            sep="|", index=False, header=False, lineterminator="\n"
        )

        # Create the header string
        header_str = "|".join(OrderModel.FIELD_NAMES)

        try:
            # Write to file
            with open(filename, "w", newline="") as file:
                file.write(header_str + "\n")
                file.write(data_str)
            logger.info(
                f"Successfully exported {len(all_data)} order lines to {filename}"
            )
        except Exception as e:
            logger.error(f"Failed to write to flat file {filename}: {str(e)}")
            raise

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

    retailerid: str = Field(str_length={"min_value": 5, "max_value": 5})
    invoicenumber: str = Field(
        str_length={"min_value": 1, "max_value": 15}, str_matches=r"^\d+$"
    )
    invoicedate: str = Field(
        str_matches=r"^\d{8}$", in_range={"min_value": 19700101, "max_value": 20991231}
    )
    arstatus: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["1", "3"]
    )
    ordertype: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["S", "T"]
    )
    loadnumber: str = Field(str_length={"min_value": 8, "max_value": 8})
    driver: str = Field(str_length={"min_value": 5, "max_value": 5})
    helper1: str | None = Field(str_length={"min_value": 5, "max_value": 5})
    helper2: str | None = Field(str_length={"min_value": 5, "max_value": 5})
    helper3: str | None = Field(str_length={"min_value": 5, "max_value": 5})
    helper4: str | None = Field(str_length={"min_value": 5, "max_value": 5})
    helper5: str | None = Field(str_length={"min_value": 5, "max_value": 5})
    company: str | None = Field(str_length={"min_value": 1, "max_value": 5})
    warehouse: str | None = Field(str_length={"min_value": 1, "max_value": 5})
    flpgroup: str | None = Field(str_length={"min_value": 1, "max_value": 5})
    pricegroup: str | None = Field(str_length={"min_value": 1, "max_value": 5})
    subpricegroup: str | None = Field(str_length={"min_value": 1, "max_value": 5})
    salesrep: str | None = Field(str_length={"min_value": 1, "max_value": 5})
    voidflag: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["Y", "N"]
    )
    voidreason: str | None = Field(str_length={"min_value": 1, "max_value": 2})
    invoicetype: str | None = Field(str_length={"min_value": 1, "max_value": 1})
    artype: str | None = Field(str_length={"min_value": 1, "max_value": 1})
    trucktype: str | None = Field(str_length={"min_value": 1, "max_value": 1})
    ponumber: str | None = Field(str_length={"min_value": 1, "max_value": 15})
    linenumber: str = Field(
        str_length={"min_value": 3, "max_value": 3}, str_matches=r"^\d+$"
    )
    productcode: str = Field(str_length={"min_value": 6, "max_value": 6})
    unitofmeasure: str | None = Field(
        str_length={"min_value": 2, "max_value": 2}, isin=["CW", "CB"]
    )
    ordermode: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["0", "1", "2", "3"]
    )
    orderquantity: str | None = Field(
        str_length={"min_value": 5, "max_value": 5}, str_matches=r"^\d+$"
    )
    outquantity: str | None = Field(
        str_length={"min_value": 1, "max_value": 5}, str_matches=r"^\d+$"
    )
    onhandquantity: str | None = Field(
        str_length={"min_value": 1, "max_value": 7}, str_matches=r"^\d+$"
    )
    partialcasequantity: str | None = Field(
        str_length={"min_value": 1, "max_value": 2}, str_matches=r"^\d+$"
    )
    returnreasoncode: str | None = Field(str_length={"min_value": 2, "max_value": 2})
    codedate: str | None = Field(
        str_matches=r"^\d{8}$", in_range={"min_value": 19700101, "max_value": 20991231}
    )
    orderprice: str | None = Field(str_matches=r"^\d{1,6}(\.\d{1,3})?$")
    ordercost: str | None = Field(str_matches=r"^\d{1,7}(\.\d{1,2})?$")
    depositamount: str | None = Field(str_matches=r"^\d{1,5}(\.\d{1,2})?$")
    deposittype: str | None = Field(str_length={"min_value": 1, "max_value": 1})
    depletionallowance: str | None = Field(str_matches=r"^\d{1,6}(\.\d{1,5})?$")
    postoffamount: str | None = Field(str_matches=r"^\d{1,5}(\.\d{1,2})?$")
    discountamount: str | None = Field(str_matches=r"^\d{1,5}(\.\d{1,2})?$")
    discountlevel1: str | None = Field(str_length={"min_value": 1, "max_value": 10})
    discountlevel2: str | None = Field(str_length={"min_value": 1, "max_value": 10})
    discountlevel3: str | None = Field(str_length={"min_value": 1, "max_value": 10})
    discountlevel4: str | None = Field(str_length={"min_value": 1, "max_value": 10})
    discountlevel: str | None = Field(str_length={"min_value": 1, "max_value": 1})
    specialprice: str | None = Field(
        str_length={"min_value": 1, "max_value": 1}, isin=["0", "1"]
    )

    @staticmethod
    def generate_filename(id: str, datetime: datetime):
        """
        Generate the filename for the invoice file to be uploaded to VIP.
        """
        filename = f"90_SALESHISTORY_{id}_{datetime.strftime('%Y%m%d_%H%M%S')}.DAT"
        logger.info(f"Generated invoice filename: {filename}")
        return filename

    def to_flat_file(self, df: pd.DataFrame, filename: str):
        logger.info(f"Exporting invoice data to flat file: {filename}")
        try:
            data_str = df.to_csv(
                sep="|", index=False, header=False, lineterminator="\n"
            )
            field_names = list(self.__annotations__.keys())
            header_str = "|".join(field_names)

            with open(filename, "w", newline="") as file:
                file.write(header_str + "\n")
                file.write(data_str)
            logger.info(f"Successfully exported {len(df)} invoice lines to {filename}")
        except Exception as e:
            logger.error(
                f"Failed to write invoice data to flat file {filename}: {str(e)}"
            )
            raise
