# Summary

vipwrap is a package used to interact with the Vermont Information Processing software (VIP). It is mainly just a wrapper around FTP and SFTP libraries. Used to upload and download files from VIP's GDI system. But could be expanded on with SQL functionality or if VIP ever added a genuine API in the future.

## Installation

`pip install vipwrap`

## Usage

Vipwrap contains two modules, `gdi` and `models`.

`gdi` covers the actual connection to VIP's GDI servers and the downloading/uploading of files. Largely just a wrapper around ftp libraries. Nothing that's necessarily VIP-specific happening in it. Use of the `GDI2` class is recommended. VIP has largely phased out their `GDI1` system. See their documentation/customer support for more details.

Example usage:
```python
from vipwrap.gdi import GDI2

gdi = GDI2(
    host=os.environ["FTP_HOST"],
    port=int(os.environ["FTP_PORT"]),
    username=os.environ["FTP_USER"],
    password=os.environ["FTP_PASS"],
)
gdi.download_file("./FILENAME.csv", "LOCAL_PATH.csv")
```

`models` contains various classes for working with order or sales history data. Intention is to be able to construct order or sales history as python objects rather than as raw flat files and include methods for conversion to/from .DAT format that the GDI system expects. Has not been extensively tested in prod yet.

```python
from vipwrap.models import InvoiceBatch, OrderBatch

ords = OrderBatch().from_flat_file(
    r"LOCATION\85_ORDERS_0000001234_20261021_123456.DAT"
)
invs = InvoiceBatch().from_flat_file(
    r"LOCATION\90_SALESHISTORY_0000001234_20261021_123456.DAT"
)
```
