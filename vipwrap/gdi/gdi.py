"""
Module handles the actual uploading of files to VIP's GDI/GDI2 server.
The module is largely just a wrapper around the paramiko and ftplib libraries
for SFTP and FTP uploads, respectively.
"""

import logging
from ftplib import FTP_TLS
from pathlib import Path

import paramiko

logger = logging.getLogger(__name__)


class GDI1:
    """
    Simple FTP client for connecting to the VIP GDI1 server and performing file operations.
    VIP generally pushes for customers to use GDI2, but there may be some legacy processes
    that still use the GDI1 server.
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        passive: bool = True,
    ) -> None:
        """
        Initialize the FTP client and log in to the server.

        :param host: Hostname or IP address of the FTP server.
        :type host: str
        :param port: Port number for the FTP server.
        :type port: int
        :param username: Username for FTP authentication.
        :type username: str
        :param password: Password for FTP authentication.
        :type password: str
        :param passive: Use passive mode for data connections (default True).
                       Set to False for active mode if passive fails.
        :type passive: bool
        :return: None
        :rtype: None
        :raises ConnectionError: If unable to connect to the FTP server.
        :raises ValueError: If authentication fails.
        """
        self.host = host
        self.port = port
        self.username = username
        self.passive = passive
        self.ftp = FTP_TLS()

        try:
            logger.info(f"Attempting to connect to FTP server at {host}:{port}...")
            self.ftp.connect(host, port, timeout=30)
            logger.info("Connection established, initiating TLS authentication...")
            self.ftp.auth()
            logger.info(f"TLS authentication successful, logger in as {username}...")
            self.ftp.login(user=username, passwd=password)
            logger.info("Login successful, setting up protected data connection...")
            self.ftp.prot_p()

            # Set passive mode
            self.ftp.set_pasv(passive)
            mode_str = "passive" if passive else "active"
            logger.info(f"FTP mode set to: {mode_str}")
            logger.info(f"Successfully connected to FTP server at {host}:{port}")
        except OSError as e:
            error_type = type(e).__name__
            logger.error(
                f"Network error connecting to FTP server at {host}:{port}\n"
                f"Error Type: {error_type}\n"
                f"Error Code: {getattr(e, 'errno', 'N/A')}\n"
                f"Error Message: {e}\n"
                f"Possible causes: Server down, firewall blocking connection, incorrect host/port"
            )
            raise ConnectionError(
                f"Failed to connect to FTP server at {host}:{port}: [{error_type}] {e}\n"
                f"Check if server is running and firewall allows connections on port {port}"
            ) from e
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                f"FTP authentication or protocol error\n"
                f"Error Type: {error_type}\n"
                f"User: {username}\n"
                f"Error Message: {e}\n"
                f"Possible causes: Invalid credentials, TLS negotiation failed, unsupported protocol"
            )
            raise ValueError(
                f"FTP authentication/protocol failed: [{error_type}] {e}\n"
                f"Verify username/password and that server supports FTPS (FTP over TLS)"
            ) from e

    def __del__(self) -> None:
        """
        Ensure the FTP connection is closed when the object is deleted.
        """
        try:
            self.close()
        except Exception:
            logger.warning("Error closing FTP connection in destructor")

    def upload_file(self, local_path: str | Path, remote_path: str) -> None:
        """
        Upload a local file to the FTP server.

        :param local_path: Path to the local file to upload.
        :type local_path: str | pathlib.Path
        :param remote_path: Destination path on the FTP server.
        :type remote_path: str
        :return: None
        :rtype: None
        :raises FileNotFoundError: If the local file does not exist.
        :raises IOError: If there's an error reading the file or uploading to the server.
        """
        local_path_obj = Path(local_path)
        if not local_path_obj.exists():
            logger.error(f"Local file not found: {local_path}")
            raise FileNotFoundError(f"Local file not found: {local_path}")

        try:
            file_size = local_path_obj.stat().st_size
            logger.info(f"Uploading {local_path} ({file_size} bytes) to {remote_path}")
            with local_path_obj.open("rb") as file:
                self.ftp.storbinary(f"STOR {remote_path}", file)
            logger.info(f"Successfully uploaded {local_path} to {remote_path}")
        except OSError as e:
            error_type = type(e).__name__
            logger.error(
                f"Error during upload\n"
                f"Error Type: {error_type}\n"
                f"Local: {local_path}\n"
                f"Remote: {remote_path}\n"
                f"Error: {e}"
            )
            raise OSError(f"Upload failed [{error_type}]: {e}") from e
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                f"Failed to upload {local_path} to {remote_path}: [{error_type}] {e}"
            )
            raise OSError(f"Upload failed [{error_type}]: {e}") from e

    def download_file(
        self,
        remote_path: str,
        local_path: str | Path,
        delete_after_download: bool = False,
    ) -> None:
        """
        Download a file from the FTP server to a local path.

        :param remote_path: Path to the file on the FTP server.
        :type remote_path: str
        :param local_path: Local path where the file will be saved.
        :type local_path: str | pathlib.Path
        :param delete_after_download: Whether to delete the file from the server after downloading.
        :type delete_after_download: bool
        :return: None
        :rtype: None
        :raises IOError: If there's an error downloading or writing the file.
        """
        local_path_obj = Path(local_path)
        try:
            # Ensure parent directory exists
            local_path_obj.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Downloading {remote_path} to {local_path}")
            with local_path_obj.open("wb") as file:
                self.ftp.retrbinary(f"RETR {remote_path}", file.write)

            file_size = local_path_obj.stat().st_size
            logger.info(
                f"Successfully downloaded {remote_path} to {local_path} ({file_size} bytes)"
            )
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                f"Download failed\n"
                f"Error Type: {error_type}\n"
                f"Remote: {remote_path}\n"
                f"Local: {local_path}\n"
                f"Error: {e}"
            )
            # Clean up partial download
            if local_path_obj.exists():
                try:
                    local_path_obj.unlink()
                    logger.info("Cleaned up partial download")
                except Exception:
                    logger.warning("Failed to clean up partial download")
            raise OSError(f"Download failed [{error_type}]: {e}") from e

        if delete_after_download:
            try:
                self.ftp.delete(remote_path)
                logger.info(f"Deleted remote file {remote_path} after download")
            except Exception as e:
                logger.warning(f"Failed to delete remote file {remote_path}: {e}")

    def list_files(self, path: str = ".") -> list[str]:
        """
        List files in a directory on the FTP server.

        :param path: Remote directory path to list. Defaults to ".".
        :type path: str
        :return: List of file names in the specified directory.
        :rtype: list[str]
        :raises IOError: If there's an error listing the directory.
        """
        try:
            # Test if connection is still alive
            try:
                self.ftp.voidcmd("NOOP")
            except Exception as conn_test:
                logger.warning(f"Connection test failed before listing: {conn_test}")

            logger.info(f"Attempting to list files in directory: {path}")
            files = self.ftp.nlst(path)
            logger.info(f"Successfully listed {len(files)} files in {path}")
        except OSError as e:
            error_type = type(e).__name__
            error_code = getattr(e, "errno", "N/A")
            logger.error(
                f"Network error while listing files in {path}\n"
                f"Error Type: {error_type}\n"
                f"Error Code: {error_code}\n"
                f"Server: {self.host}:{self.port}\n"
                f"Error Message: {e}\n"
                f"Possible causes: Connection timeout, data connection blocked, server unresponsive"
            )
            raise OSError(
                f"Network error listing files in '{path}': [{error_type}] {e}\n"
                f"Server {self.host}:{self.port} may be unresponsive or data connection is blocked.\n"
                f"Error code {error_code}: Check firewall settings for passive FTP data connections."
            ) from e
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                f"Failed to list files in {path}\n"
                f"Error Type: {error_type}\n"
                f"Error Message: {e}\n"
                f"Possible causes: Invalid path, permission denied, server error"
            )
            raise OSError(
                f"Failed to list files in '{path}': [{error_type}] {e}\n"
                f"Verify the path exists and you have permission to access it."
            ) from e
        else:
            return files

    def close(self) -> None:
        """
        Close the FTP connection.

        :return: None
        :rtype: None
        """
        try:
            self.ftp.quit()
            logger.info("FTP connection closed successfully")
        except Exception as e:
            logger.warning(
                f"Error closing FTP connection (attempting force close): {e}"
            )
            try:
                self.ftp.close()
            except Exception:
                logger.error("Failed to force close FTP connection")


class GDI2:
    """
    Simple SFTP client for connecting to the VIP GDI2 server and performing file operations.
    """

    def __init__(self, host: str, port: int, username: str, password: str) -> None:
        """
        Initialize the SFTP client and connect to the server.

        :param host: Hostname or IP address of the SFTP server.
        :type host: str
        :param port: Port number for the SFTP server.
        :type port: int
        :param username: Username for SFTP authentication.
        :type username: str
        :param password: Password for SFTP authentication.
        :type password: str
        :return: None
        :rtype: None
        :raises ConnectionError: If unable to connect to the SFTP server.
        :raises RuntimeError: If SSH transport or SFTP session cannot be established.
        """
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(host, port=port, username=username, password=password)
            logger.info(f"Successfully connected to SFTP server at {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to connect to SFTP server at {host}:{port}: {e}")
            raise ConnectionError(f"Failed to connect to SFTP server: {e}") from e

        self.transport = self.ssh.get_transport()
        if self.transport is None:
            logger.error("Failed to establish SSH transport")
            raise RuntimeError("Failed to establish SSH transport")

        try:
            sftp = paramiko.SFTPClient.from_transport(self.transport)
            if sftp is None:
                raise RuntimeError("Failed to establish SFTP session")
            self.sftp = sftp
            logger.info("SFTP session established successfully")
        except Exception as e:
            logger.error(f"Failed to establish SFTP session: {e}")
            raise RuntimeError(f"Failed to establish SFTP session: {e}") from e

    def __del__(self) -> None:
        """
        Ensure the SFTP connection is closed when the object is deleted.
        """
        try:
            self.close()
        except Exception:
            logger.warning("Error closing SFTP connection in destructor")

    def upload_file(self, local_path: str | Path, remote_path: str) -> None:
        """
        Upload a local file to the SFTP server.

        :param local_path: Path to the local file to upload.
        :type local_path: str | pathlib.Path
        :param remote_path: Destination path on the SFTP server.
        :type remote_path: str
        :return: None
        :rtype: None
        :raises FileNotFoundError: If the local file does not exist.
        :raises IOError: If there's an error uploading the file.
        """
        local_path_obj = Path(local_path)
        if not local_path_obj.exists():
            logger.error(f"Local file not found: {local_path}")
            raise FileNotFoundError(f"Local file not found: {local_path}")

        try:
            self.sftp.put(str(local_path_obj), remote_path)
            logger.info(f"Successfully uploaded {local_path} to {remote_path}")
        except Exception as e:
            logger.error(f"Failed to upload {local_path} to {remote_path}: {e}")
            raise OSError(f"Failed to upload file: {e}") from e

    def download_file(
        self,
        remote_path: str,
        local_path: str | Path,
        delete_after_download: bool = False,
    ) -> None:
        """
        Download a file from the SFTP server to a local path.

        :param remote_path: Path to the file on the SFTP server.
        :type remote_path: str
        :param local_path: Local path where the file will be saved.
        :type local_path: str | pathlib.Path
        :param delete_after_download: Whether to delete the remote file after downloading.
        :type delete_after_download: bool
        :return: None
        :rtype: None
        :raises IOError: If there's an error downloading the file.
        """
        local_path_obj = Path(local_path)
        try:
            # Ensure parent directory exists
            local_path_obj.parent.mkdir(parents=True, exist_ok=True)

            self.sftp.get(remote_path, str(local_path_obj))
            logger.info(f"Successfully downloaded {remote_path} to {local_path}")
        except Exception as e:
            logger.error(f"Failed to download {remote_path} to {local_path}: {e}")
            # Clean up partial download
            if local_path_obj.exists():
                try:
                    local_path_obj.unlink()
                except Exception:
                    logger.warning("Failed to clean up partial download")
            raise OSError(f"Failed to download file: {e}") from e

        if delete_after_download:
            try:
                self.sftp.remove(remote_path)
                logger.info(f"Deleted remote file {remote_path} after download")
            except Exception as e:
                logger.warning(f"Failed to delete remote file {remote_path}: {e}")

    def list_files(self, path: str = ".") -> list[str]:
        """
        List files in a directory on the SFTP server.

        :param path: Remote directory path to list. Defaults to ".".
        :type path: str
        :return: List of file names in the specified directory.
        :rtype: list[str]
        :raises IOError: If there's an error listing the directory.
        """
        try:
            files = self.sftp.listdir(path)
            logger.info(f"Successfully listed {len(files)} files in {path}")
        except Exception as e:
            logger.error(f"Failed to list files in {path}: {e}")
            raise OSError(f"Failed to list files: {e}") from e
        else:
            return files

    def close(self) -> None:
        """
        Close the SFTP session, transport, and SSH connection.

        :return: None
        :rtype: None
        """
        try:
            if hasattr(self, "sftp") and self.sftp:
                self.sftp.close()
        except Exception as e:
            logger.warning(f"Error closing SFTP session: {e}")

        try:
            if hasattr(self, "transport") and self.transport:
                self.transport.close()
        except Exception as e:
            logger.warning(f"Error closing SSH transport: {e}")

        try:
            if hasattr(self, "ssh") and self.ssh:
                self.ssh.close()
                logger.info("SFTP connection closed successfully")
        except Exception as e:
            logger.warning(f"Error closing SSH client: {e}")
