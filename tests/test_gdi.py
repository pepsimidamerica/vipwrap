"""
Tests for GDI module.
"""

import logging
import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, "")
load_dotenv()

from vipwrap.gdi import GDI1

logger = logging.getLogger(__name__)


def test_download_picking() -> None:
    """
    Test downloading picking files from GDI server.
    """
    gdi = GDI1(
        host=os.getenv("GDI_HOST", "gdi.example.com"),
        port=10021,
        username="myuser",
        password="mypass",
    )
    files = gdi.list_files("/out")

    picking_files = [f for f in files if "POSTPICKV" in f.upper()]

    logger.info(f"Found {len(picking_files)} picking files.")


if __name__ == "__main__":
    test_download_picking()
