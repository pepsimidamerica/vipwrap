# Summary

At the moment, the package is mainly just a wrapper around FTP and SFTP libraries. It's used to upload and download files from VIP's GDI/GDI2 system. But could be expanded on with SQL functionality or if VIP ever added a genuine API in the future.

## Installation

`pip install vipwrap`

## Usage

Contains two modules, `gdi` and `models`. `gdi` covers the actual connection to VIP's GDI servers and the downloading/uploading of files. Largely just a wrapper around ftp libraries. Nothing VIP-specific happening in it. `models` contains two pandera models that describe order or sales history data. Has not been fully built out. At the moment, can be used for dataframe validation.

### Send File to GDI

Takes standard parameters expected of uploading an existing local file to a remote location via FTP or SFTP.

| parameter | type | description |
| - | - | - |
| ftp_method | str | 'ftp' or 'sftp' |
| host | str | the FTP server host |
| port | int | the SFTP server port, not used with FTP |
| user | str | username to authenticate with |
| password | str | password to authenticate with |
| folder | str | The base folder location to upload the file to, usually "/in/" or "/TO_GDI/" |
| file | IO[str] | File stream being uploaded. Usually the output of an open() function |

### Download Files from GDI

Takes standard paramers expected for connecting to a remote FTP/SFTP server as well as the file string to search for. This is being used to mass-download files that start with a given string.

| parameter | type | description |
| - | - | - |
| ftp_method | str | 'ftp' or 'sftp' |
| host | str | the FTP server host |
| port | int | the FTP/SFTP server port |
| user | str | username to authenticate with |
| password | str | password to authenticate with |
| folder | str | the folder to download the files from, usually "/out/" or "/FROM_VIP/" |
| file_string | str | string in file name to search for |
| delete_after_download | bool | whether to delete the files from the remote location once downloaded. |
