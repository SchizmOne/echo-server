import argparse
import os
import typing as t
from pathlib import Path
from textwrap import dedent
from urllib.parse import urljoin

import requests
import paramiko
from rich.console import Console


DEFAULT_SERVER_ADDRESS = 'http://localhost:8080'
DEFAULT_FILENAME = 'filename.txt'
OUTPUT_DIR = Path('output')
REMOTE_CREDS_ENV_NAME = 'REMOTE_CREDS'


console = Console()


DESCRIPTION = dedent("""
This script serves as the EchoServer client.

It allows user to execute it in two modes:
1. (local) Makes a GET request to the /hello endpoint of the running instance
   of EchoServer and saves the phrase from server response to the local file
   by a given name. The file is overwritten each time because the response
   is always the same phrase.

   EXAMPLE:
   python3 client.py -m=local --filename='local_name.txt'

2. (remote) Makes a GET request to the /random endpoint (without any query params)
   of the running instance of EchoServer, then connects via SSH to a remote machine,
   and saves the randomly generated text from server response to the file by a given
   name. Each new phrase will be added to the file.

   EXAMPLE:
   python3 client.py -m=remote --server_address='http://127.0.0.1:8080'
   --remote_host='192.168.100.30' --filename='remote_name.txt'

If you want to use the remote mode, then you have to provide remote host address
in the arguments and write the user credentials for SSH access to this host to
the environment variable called REMOTE_CREDS (value format is "username:password").
""")


class RemoteHostCreds(t.NamedTuple):
    host: str
    username: str
    password: str


def local_mode(server_address: str, filename: str) -> None:
    session = requests.sessions.Session()
    response = session.get(url=urljoin(server_address, 'hello'))
    response.raise_for_status()
    console.log('Successfully received response from the endpoint /hello')

    file_path = Path(OUTPUT_DIR / filename)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open('w', encoding='UTF-8') as f:
        f.write(f'{response.text}\n')


def remote_mode(server_address: str, filename: str, remote_host_creds: RemoteHostCreds) -> None:
    session = requests.sessions.Session()
    response = session.get(url=urljoin(server_address, 'random'))
    response.raise_for_status()
    console.log('Successfully received response from the endpoint /random\n'
               f'Generated phrase: "{response.text}"')

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=remote_host_creds.host,
                           username=remote_host_creds.username,
                           password=remote_host_creds.password, timeout=10)
        sftp_session = ssh_client.open_sftp()
        with sftp_session.file(filename, 'a') as remote_f:
            remote_f.write(f'{response.text}\n')
        sftp_session.close()
    finally:
        ssh_client.close()


def main(
    mode: t.Literal['local', 'remote'],
    server_address: str,
    filename: str,
    remote_host: t.Optional[str]
) -> None:

    try:
        if mode == 'local':
            console.print(f'Selected mode: {mode}')
            local_mode(server_address=server_address, filename=filename)
        elif mode == 'remote':
            console.print(f'Selected mode: {mode}')
            remote_creds = os.environ.get(REMOTE_CREDS_ENV_NAME, None)
            if remote_host is None or remote_creds is None:
                raise ValueError('For the remote mode of this script you have to provide '
                                 'both remote host address as the script argument --remote_host '
                                 'and user credentials in the environment variable REMOTE_CREDS')
            try:
                remote_username, remote_password = remote_creds.split(':')
            except ValueError as e:
                raise ValueError(f'The value of {REMOTE_CREDS_ENV_NAME} variable should be '
                                  'written in the following format: "username:password"') from e
            remote_host_creds = RemoteHostCreds(
                host=remote_host, username=remote_username, password=remote_password
            )
            remote_mode(
                server_address=server_address, filename=filename, remote_host_creds=remote_host_creds
            )
    except Exception:
        console.print_exception(show_locals=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter, description=DESCRIPTION
    )
    parser.add_argument('-m', '--mode', help='Modes of the echo-server client',
                        choices=['local', 'remote'], required=True)
    parser.add_argument('-s', '--server_address',
                        help='Address of the running instance of EchoServer. '
                            f'(default: {DEFAULT_SERVER_ADDRESS})',
                        default=DEFAULT_SERVER_ADDRESS, required=False)
    parser.add_argument('-f', '--filename',
                        help='Name of the file to which the text from server response will be saved '
                            f'(default: "{DEFAULT_FILENAME}")',
                        default=DEFAULT_FILENAME, required=False)
    parser.add_argument('--remote_host',
                        help='Host address of the remote machine where the file '
                             'will be saved via SSH (required for remote mode)',
                        required=False)

    args = parser.parse_args()
    main(
        mode=args.mode,
        server_address=args.server_address,
        filename=args.filename,
        remote_host=args.remote_host
    )
