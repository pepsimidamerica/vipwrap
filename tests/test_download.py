import os
import sys
import shutil
from typing import Iterable, Sequence, Literal

import pytest

# Ensure local imports work when running tests directly
sys.path.insert(0, "")

from vipwrap import gdi  # noqa: E402


def _cleanup_paths(paths: Iterable[str]) -> None:
    """
    Best-effort cleanup of downloaded paths.
    Removes files and directories (recursively). Ignores errors.
    """
    seen = set()
    for p in (paths or []):
        if not p or p in seen:
            continue
        seen.add(p)
        try:
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
            elif os.path.exists(p) or os.path.islink(p):
                os.remove(p)
        except Exception:
            # Best-effort cleanup; ignore any removal errors
            pass


@pytest.mark.parametrize(
    "protocol,host,port,username,password,remote_dir",
    [
        ("ftp", "localhost", 10021, "myuser", "mypass", "/"),
        ("sftp", "localhost", 10022, "foo", "pass", "/upload/"),
    ],
)
def test_download_from_gdi(protocol: Literal["sftp", "ftp"], host: str, port: int, username: str, password: str, remote_dir: str) -> None:
    """
    Parametrized test that attempts to download files via FTP/SFTP and cleans up downloaded artifacts.
    """
    downloaded_files: Sequence[str] = []
    try:
        downloaded_files = gdi.download_files_from_gdi(
            protocol, host, port, username, password, remote_dir, "test", False
        )


        # Validate and check only when a list/tuple is returned
        if isinstance(downloaded_files, (list, tuple)):

            # If files were downloaded, confirm they exist
            for path in downloaded_files:
                assert isinstance(path, str) and path, "Each downloaded path should be a non-empty string"
                assert os.path.exists(path), f"Downloaded path does not exist: {path}"

    finally:
        _cleanup_paths(downloaded_files)
