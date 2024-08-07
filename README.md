# Summary

At the moment, the package is mainly just a wrapper around FTP and SFTP libraries. It's used to upload files to VIP's GDI system. But could be expanded on with SQL functionality or if VIP ever added a genuine API in the future.

As is, the point of the package is largely just defining how to upload a file to VIP in one place so it doesn't need to be rewritten every time a repo involving VIP is created and can instead just be imported.

There are also pandera models defined for an order and an invoice.

## Installation

`pip install vipwrap`

## Usage

Currently consists of one function.

### Send File to VIP

Takes standard parameters expected of uploading an existing local file to a remote location via FTP or SFTP.

| parameter | type | description |
| - | - | - |
| ftp_method | str | 'ftp' or 'sftp' |
| host | str | the FTP server host |
| port | int | the SFTP server port, not used with FTP |
| user | str | username to authenticate with |
| password | str | password to authenticate with |
| folder | str | The base folder location to upload the file to |
| file | IO[str] | File stream being uploaded. Usually the output of an open() function |
