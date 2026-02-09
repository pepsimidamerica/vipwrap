# Summary

At the moment, the package is mainly just a wrapper around FTP and SFTP libraries. It's used to upload and download files from VIP's GDI/GDI2 system. But could be expanded on with SQL functionality or if VIP ever added a genuine API in the future.

## Installation

`pip install vipwrap`

## Usage

Vipwrap contains two modules, `gdi` and `models`.

`gdi` covers the actual connection to VIP's GDI servers and the downloading/uploading of files. Largely just a wrapper around ftp libraries. Nothing that's necessarily VIP-specific happening in it. Use of the `GDI2` class is recommended. VIP has largely phased out the `GDI1` system. See their documentation for more details.

`models` contains various classes for working with order or sales history data. Has not been fully built out yet. Intention is to be able to construct order or sales history as python objects rather than as raw flat files and include methods for conversion to .DAT format that the GDI system expects.

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
