"""
Random tests.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load env vars from a .env file
load_dotenv()

sys.path.insert(0, "")

from vipwrap.models import InvoiceBatch, OrderBatch

ords = OrderBatch().from_flat_file(r"")
invs = InvoiceBatch().from_flat_file(r"")

print(ords)
print(invs)

pass
