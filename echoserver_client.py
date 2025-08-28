import argparse
import typing as t
from functools import wraps
from http.server import ThreadingHTTPServer
from pathlib import Path
from textwrap import dedent
from threading import Thread
from urllib.parse import urljoin

import requests
import paramiko
from rich.console import Console

from echoserver.handler import EchoHandler
from echoserver.utils import ServerAddress


DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8080
DEFAULT_SERVER_ADDRESS = f'http://{DEFAULT_HOST}:{DEFAULT_PORT}'
DEFAULT_FILENAME = 'filename.txt'


console = Console()


DESCRIPTION = dedent("""
Script that serves as the EchoServer client.

This script allows the user to use it in two modes:
1. (local) Makes a GET request to the /hello endpoint of the running instance of EchoServer
   and saves the phrase from server response to the local file by a given name.
   File will be rewritten every time because it's always the same phrase.

   EXAMPLE:
   python3 echoserver_client.py -m=local --server_address='http://127.0.0.1:8080'
   --filename='testname.txt'

2. (remote) Makes a GET request to the /random endpoint (without any query params) of the running
   instance of EchoServer, then connects via SSH to a remote machine, and saves the
   randomly generated text from server response to the file by a given name. Each new
   phrase will be added to the file.

   EXAMPLE:
   python3 echoserver_client.py -m=remote --remote_host='192.168.100.30'
   --remote_creds='username:password' --filename='another_name.txt'

If you don't provide the address of the currently running instance of EchoServer then
this script will start this instance automatically at the address "http:///localhost:8080".
This can lead to errors if you have some locally running instances of EchoServer, so be careful.

Also, if you want to use the remote mode, then you have to provide both remote host
address and the user credentials for SSH access to this host.
""")


class RemoteHostCreds(t.NamedTuple):
    host: str
    username: str
    password: str


def setup_echoserver(decorated: t.Callable) -> t.Callable:
    @wraps(decorated)
    def wrapper(*args: t.Any, **kwargs: t.Any):
        server_address = kwargs['server_address']
        if server_address == DEFAULT_SERVER_ADDRESS:
            console.log('Server address was not provided, setting up server in daemon thread...')
            server_daemon = ThreadingHTTPServer(ServerAddress(DEFAULT_HOST, DEFAULT_PORT), EchoHandler)
            server_thread = Thread(target=server_daemon.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            console.log(f'EchoServer started locally at the address of "{DEFAULT_SERVER_ADDRESS}"')

        try:
            result = decorated(*args, **kwargs)
        finally:
            if server_address == DEFAULT_SERVER_ADDRESS:
                console.log('Stopping EchoServer...')
                server_daemon.shutdown()
                server_thread.join()
                console.log('EchoServer stopped successfully')
                server_daemon.server_close()
        return result
    return wrapper


@setup_echoserver
def local_mode(server_address: str, filename: str) -> None:
    session = requests.sessions.Session()
    response = session.get(url=urljoin(server_address, 'hello'))
    response.raise_for_status()

    with Path(filename).open('w', encoding='UTF-8', newline='\n') as f:
        f.write(response.text)


@setup_echoserver
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
        with sftp_session.file(filename, 'a') as remote_f:
            remote_f.write(f'{response.text}\n')
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

    try:
        if mode == 'local':
            console.print(f'Selected mode: {mode}')
            local_mode(server_address=server_address, filename=filename)
        elif mode == 'remote':
            console.print(f'Selected mode: {mode}')
            if remote_host is None or remote_creds is None:
                raise ValueError('For the remote mode of the script you have to provide '
                                'both remote host address and user credentials')
            try:
                remote_username, remote_password = remote_creds.split(':')
            except ValueError as e:
                raise ValueError('The remote credentials should be given in the following format:\n'
                                 '--remote_creds="username:password"') from e
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
    parser.add_argument('-m', '--mode', help='Modes of the client',
                        choices=['local', 'remote'], required=True)
    parser.add_argument('-s', '--server_address',
                        help='Address of the running instance of EchoServer. If leave by default, this '
                             'script will start the instance of the server in a daemon thread '
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
