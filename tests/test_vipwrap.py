import os
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

from vipwrap.upload_handling import send_file_to_vip


class TestVipwrap(unittest.TestCase):

    @patch("vipwrap.upload_handling.upload_sftp")
    @patch("vipwrap.upload_handling.upload_ftp")
    def test_send_file_to_vip_sftp(self, mock_upload_ftp, mock_upload_sftp):
        # Mock the file object
        mock_file = StringIO("dummy file content")

        # Call the function with SFTP method
        send_file_to_vip(
            ftp_method="sftp",
            host="localhost",
            port=10022,
            user="foo",
            password="pass",
            folder="/upload/",
            file=mock_file,
        )

        # Assert that upload_sftp was called
        mock_upload_sftp.assert_called_once_with(mock_file)
        mock_upload_ftp.assert_not_called()

    @patch("vipwrap.upload_handling.upload_sftp")
    @patch("vipwrap.upload_handling.upload_ftp")
    def test_send_file_to_vip_ftp(self, mock_upload_ftp, mock_upload_sftp):
        # Mock the file object
        mock_file = StringIO("dummy file content")

        # Call the function with FTP method
        send_file_to_vip(
            ftp_method="ftp",
            host="localhost",
            port=10021,
            user="myuser",
            password="mypass",
            folder="/",
            file=mock_file,
        )

        # Assert that upload_ftp was called
        mock_upload_ftp.assert_called_once_with(mock_file)
        mock_upload_sftp.assert_not_called()

    @patch("vipwrap.upload_handling.upload_sftp")
    @patch("vipwrap.upload_handling.upload_ftp")
    def test_send_file_to_vip_invalid_method(self, mock_upload_ftp, mock_upload_sftp):
        # Mock the file object
        mock_file = StringIO("dummy file content")

        # Call the function with an invalid method
        with self.assertRaises(ValueError):
            send_file_to_vip(
                ftp_method="invalid",
                host="dummy_host",
                port=21,
                user="dummy_user",
                password="dummy_password",
                folder="dummy_folder",
                file=mock_file,
            )

        # Assert that neither upload function was called
        mock_upload_ftp.assert_not_called()
        mock_upload_sftp.assert_not_called()


if __name__ == "__main__":
    unittest.main()
