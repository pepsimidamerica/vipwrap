"""
Module handles the actual uploading of files to VIP's GDI/GDI2 server.
The module is largely just a wrapper around the paramiko and ftplib libraries
for SFTP and FTP uploads, respectively.
"""

import os
import time
from ftplib import FTP_TLS
from typing import IO, Literal

import paramiko


def connect_sftp(host: str, port: int, user: str, password: str):
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


def upload_sftp(
    host: str, port: int, user: str, password: str, folder: str, file: IO[str]
):
    """
    Upload file to SFTP server
    """

    with connect_sftp(host, port, user, password) as ssh:
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


def download_sftp(
    host: str,
    port: int,
    user: str,
    password: str,
    folder: str,
    file_string: str,
    download_after_delete: bool = False,
) -> list[str]:
    """
    Downloads all files in a folder on the VIP GDI server whose filenames start
    with the given string.
    """
    downloaded_files = []
    with connect_sftp(host, port, user, password) as ssh:
        with ssh.open_sftp() as sftp:
            sftp.get_channel().settimeout(60)  # type: ignore
            files = sftp.listdir(folder)
            for f in files:
                if f.startswith(file_string):
                    remote_path = folder + f
                    local_path = f
                    sftp.get(remote_path, local_path)
                    downloaded_files.append(os.path.abspath(local_path))
                    if download_after_delete:
                        sftp.remove(remote_path)
    return downloaded_files


def download_ftp(
    host: str,
    port: int,
    user: str,
    password: str,
    folder: str,
    file_string: str,
    download_after_delete: bool = False,
) -> list[str]:
    """
    Downloads all files in a folder on the VIP GDI server whose filenames start
    with the given string.
    """
    ftp = FTP_TLS()
    downloaded_files = []
    try:
        ftp.connect(host, port)
        ftp.auth()
        ftp.login(user, password)
        ftp.prot_p()
        ftp.cwd(folder)  # Change to the correct directory
        files = ftp.nlst(folder)
        for f in files:
            filename = f.lstrip("/")
            if filename.startswith(file_string):
                with open(filename, "wb") as local_file:
                    ftp.retrbinary("RETR " + filename, local_file.write)
                downloaded_files.append(os.path.abspath(filename))
                if download_after_delete:
                    ftp.delete(filename)
    finally:
        ftp.quit()

    return downloaded_files


def delete_sftp(
    host: str, port: int, user: str, password: str, folder: str, filename: str
) -> None:
    """
    Deletes a file in a folder on the VIP GDI server whose filename
    matches the given string.
    """
    with connect_sftp(host, port, user, password) as ssh:
        with ssh.open_sftp() as sftp:
            sftp.get_channel().settimeout(60)  # type: ignore
            files = sftp.listdir(folder)
            for f in files:
                if f == filename:
                    remote_path = folder + f
                    sftp.remove(remote_path)


def upload_ftp(host: str, user: str, password: str, folder: str, file: IO[str]):
    """
    Upload file to FTP server
    """

    with FTP_TLS(host) as ftp:
        ftp.auth()
        ftp.login(user, password)
        ftp.prot_p()
        with open(file.name, "rb") as f:
            ftp.storbinary("STOR " + folder + file.name, f)


def send_file_to_gdi(
    ftp_method: Literal["sftp", "ftp"],
    host: str,
    port: int,
    user: str,
    password: str,
    folder: str,
    file: IO[str],
) -> None:
    """
    Sends file to VIP GDI server via FTP or SFTP, depending on which method specified.
    The transfer is retried 3 times if it fails.

    ftp_method: whether to upload via SFTP or FTP
    host: the hostname of the FTP/SFTP server
    port: the port number of the SFTP server
    user: the username for the FTP/SFTP server
    password: the password for the FTP/SFTP server
    folder: the folder to upload the file to
    file: file object to upload
    """

    for attempt in range(3):
        try:
            if ftp_method == "sftp":
                upload_sftp(host, port, user, password, folder, file)
            elif ftp_method == "ftp":
                upload_ftp(host, user, password, folder, file)
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


def download_files_from_gdi(
    ftp_method: Literal["sftp", "ftp"],
    host: str,
    port: int,
    user: str,
    password: str,
    folder: str,
    file_string: str,
    delete_after_download: bool = False,
) -> list[str]:
    """
    Downloads all files in a folder on the VIP GDI server whose filenames start
    with the given string.

    Returns a list of paths to the downloaded files.

    ftp_method: whether to download via SFTP or FTP
    host: the hostname of the FTP/SFTP server
    port: the port number of the SFTP
    user: the username for the FTP/SFTP server
    password: the password for the FTP/SFTP server
    folder: the folder to download the files from
    file_string: the string that the filenames must start with
    delete_after_download: whether to delete the files from the server after downloading
    """
    if ftp_method == "sftp":
        return download_sftp(
            host, port, user, password, folder, file_string, delete_after_download
        )
    elif ftp_method == "ftp":
        return download_ftp(
            host, port, user, password, folder, file_string, delete_after_download
        )
    else:
        print("Error, invalid FTP method")
        raise ValueError("Error, invalid FTP method")
