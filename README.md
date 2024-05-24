# vippy

It looks like you're trying to interact with the Vermont Information Processing system. I can help.

At the moment, the package is mainly just a wrapper around FTP and SFTP libraries. It's used to upload files to VIP's GDI system. But could be expanded on with SQL functionality or if VIP ever added a genuine API in the future.

As is, the point of the package is largely just defining how to upload a file to VIP in one place so it doesn't need to be rewritten every time a repo involving VIP is created and can instead just be imported. Could also be made more generic and just used for any project involving FTP/SFTP. But I'm following general principle used with other similiar projects (grafap, nacwrap, clope), where the repo contains whatever all is needed to interact with that particular software.

TODO: Perhaps make more abstract. Handle order or sales file creation in here and just pass the data in as dataframe or list of dictionaries or something similar.

## Installation

Haven't yet bothered to publish as a python package, intent is to simply add vippy as a git submodule in any projects where it's needed.

## Usage

Currently consists of one function.

### Send File to VIP

Takes standard parameters expected of uploading a file to a remote location via FTP or SFTP.

| parameter | type | description |
| - | - | - |
| ftp_method | str | 'ftp' or 'sftp' |
| host | str | the FTP server host |
| port | int | the SFTP server port, not used with FTP |
| user | str | username to authenticate with |
| password | str | password to authenticate with |
| folder | str | The base folder location to upload the file to |
| file | IO[str] | File stream being uploaded. Usually the output of an open() function |
