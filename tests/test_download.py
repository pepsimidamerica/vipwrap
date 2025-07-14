import sys

sys.path.insert(0, "")

from vipwrap import gdi


def test_download_ftp():
    downloaded_files = gdi.download_files_from_gdi(
        ftp_method="ftp",
        host="sftp.vtinfo.com",
        port=21,
        user="username here",
        password="password here",
        folder="/out",
        file_string="POSTPICKV",
        delete_after_download=False,
    )

    print("Downloaded files:", downloaded_files)


if __name__ == "__main__":
    test_download_ftp()
