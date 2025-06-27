"""
The gdi module handles uploading of files to VIP's GDI/GDI2 server.
"""

from .gdi import (
    download_files_from_gdi,
    send_file_to_gdi,
)

__all__ = [
    "send_file_to_gdi",
    "download_files_from_gdi",
]
