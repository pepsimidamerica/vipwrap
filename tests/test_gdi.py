"""
Tests for GDI module.
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, "")
load_dotenv()

from vipwrap.gdi import GDI1, GDI2

logger = logging.getLogger(__name__)

# Set logger to output to console
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

TEST_DIR = Path(__file__).parent


def test_download_picking() -> None:
    """
    Test downloading picking files from GDI server.
    """
    gdi = GDI2(
        host=os.environ["FTP_HOST"],
        port=int(os.environ["FTP_PORT"]),
        username=os.environ["FTP_USER"],
        password=os.environ["FTP_PASS"],
        # passive=True,
        # use_tls=False,
    )
    files = gdi.list_files(".")

    picking_files = [f for f in files if "POSTPICKV" in f.upper()]

    logger.info(f"Found {len(picking_files)} picking files.")

    test_file = picking_files[0] if picking_files else None
    if test_file:
        logger.info(f"Downloading test file: {test_file}")
        gdi.download_file(
            remote_path=picking_files[0], local_path=TEST_DIR / "test_picking_file.csv"
        )
    else:
        logger.warning("No picking files found to download.")

    del gdi


if __name__ == "__main__":
    test_download_picking()
