import argparse
import logging
import sys
import typing as t
from pathlib import Path
from textwrap import dedent
from urllib.parse import urljoin

import requests
import paramiko


DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8080
DEFAULT_SERVER_ADDRESS = f'http://{DEFAULT_HOST}:{DEFAULT_PORT}'
DEFAULT_FILENAME = 'filename.txt'


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
stdout_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)


DESCRIPTION = dedent("""
Script that serves as the EchoServer client.

This script allows the user to use it in two modes:
1. Makes a GET request to /hello endpoint of the running instance of EchoServer
   and saves the response to a local file.
2. Makes a GET request to /random endpoint of the running instance of EchoServer,
   then connects via SSH to a remote machine, and saves the phrase as /filename.txt.
""")


class RemoteHostCreds(t.NamedTuple):
    host: str
    username: str
    password: str


def local_mode(server_address: str, filename: str) -> None:
    session = requests.sessions.Session()
    response = session.get(url=urljoin(server_address, 'hello'))
    response.raise_for_status()

    with Path(filename).open('w', encoding='UTF-8', newline='\n') as f:
        f.write(response.text)


def remote_mode(server_address: str, filename: str, remote_host_creds: RemoteHostCreds) -> None:
    session = requests.sessions.Session()
    response = session.get(url=urljoin(server_address, 'random'))
    response.raise_for_status()

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=remote_host_creds.host,
                           username=remote_host_creds.username,
                           password=remote_host_creds.password, timeout=10)
        sftp_session = ssh_client.open_sftp()
        with sftp_session.file(filename, 'w') as remote_f:
            remote_f.write(response.text)
        sftp_session.close()
    finally:
        ssh_client.close()


def main(
    mode: t.Literal['local', 'remote'],
    server_address: str,
    filename: str,
    remote_host: t.Optional[str],
    remote_creds: t.Optional[str]
) -> None:

    if mode == 'local':
        local_mode(server_address=server_address, filename=filename)
    elif mode == 'remote':
        if remote_host is None or remote_creds is None:
            raise ValueError('For the remote mode of the script you have to provide '
                             'both remote host address and user credentials')
        remote_username, remote_password = remote_creds.split(':')
        remote_host_creds = RemoteHostCreds(
            host=remote_host, username=remote_username, password=remote_password
        )
        remote_mode(
            server_address=server_address, filename=filename, remote_host_creds=remote_host_creds
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter, description=DESCRIPTION
    )
    parser.add_argument('-m', '--mode', help='Modes of the client',
                        choices=['local', 'remote'], required=True)
    parser.add_argument('-s', '--server_address',
                        help='Address of the running instance of EchoServer '
                            f'(default: {DEFAULT_SERVER_ADDRESS})',
                        default=DEFAULT_SERVER_ADDRESS, required=False)
    parser.add_argument('-f', '--filename',
                        help='Name of the file to which the text from server response will be saved '
                             f'(default: {DEFAULT_FILENAME})',
                        default=DEFAULT_FILENAME, required=False)
    parser.add_argument('--remote_host',
                        help='Host address of the remote machine where the file '
                             'will be saved via SSH (required for remote mode)',
                        required=False)
    parser.add_argument('--remote_creds',
                        help='Username and password for the access via SSH to '
                             'the remote machine (required for remote mode, e.g. "username:password")',
                        required=False)

    args = parser.parse_args()
    main(
        mode=args.mode,
        server_address=args.server_address,
        filename=args.filename,
        remote_host=args.remote_host,
        remote_creds=args.remote_creds
    )
