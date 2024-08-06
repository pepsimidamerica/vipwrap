"""
Module handles the actual uploading of files to VIP's GDI/GDI2 server.
The module is largely just a wrapper around the paramiko and ftplib libraries
for SFTP and FTP uploads, respectively.
"""

import os
import time
from ftplib import FTP
from typing import IO, Literal

import paramiko


def send_file_to_vip(
    ftp_method: Literal["sftp", "ftp"],
    host: str,
    port: int,
    user: str,
    password: str,
    folder: str,
    file: IO[str],
) -> None:
    """
    Sends file to VIP via FTP or SFTP, depending on which method specified. The
    transfer is retried 3 times if it fails.

    ftp_method: whether to upload via SFTP or FTP
    host: the hostname of the FTP/SFTP server
    port: the port number of the SFTP server
    user: the username for the FTP/SFTP server
    password: the password for the FTP/SFTP server
    folder: the folder to upload the file to
    file: file object to upload
    """

    def connect_sftp():
        """
        Connect to SFTP server
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            host,
            port=port,
            username=user,
            password=password,
            timeout=30,
        )
        return ssh

    def upload_sftp(file):
        """
        Upload file to SFTP server
        """

        with connect_sftp() as ssh:
            with ssh.open_sftp() as sftp:
                sftp.get_channel().settimeout(60)  # type: ignore
                remote_path = folder + file.name
                sftp.put(file.name, remote_path)
                local_file_size = os.path.getsize(file.name)
                remote_file_size = sftp.stat(remote_path).st_size
                print("Local file size: ", local_file_size)
                print("Remote file size: ", remote_file_size)
                if local_file_size != remote_file_size:
                    raise ValueError(
                        f"Error, file sizes do not match: {local_file_size} vs {remote_file_size}"
                    )

    def upload_ftp(file):
        """
        Upload file to FTP server
        """

        with FTP(host) as ftp:
            ftp.login(user, password)
            with open(file.name, "rb") as f:
                ftp.storbinary("STOR " + folder + file.name, f)

    for attempt in range(3):
        try:
            if ftp_method == "sftp":
                upload_sftp(file)
            elif ftp_method == "ftp":
                upload_ftp(file)
            else:
                print("Error, invalid FTP method")
                raise ValueError("Error, invalid FTP method")
            break
        except Exception as e:
            print(f"Attempt {attempt + 1}: Error sending file to VIP: {e}")
            if attempt < 2:
                time.sleep(60)  # Wait before retrying
            else:
                raise  # Reraise the exception or handle it as needed
