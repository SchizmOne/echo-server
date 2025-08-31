import argparse
import logging
import sys
from http.server import HTTPServer
from textwrap import dedent

from echoserver.handler import EchoHandler
from echoserver.utils import (
    is_server_address_busy,
    ServerAddress
)


DEFAULT_BIND = '0.0.0.0'
DEFAULT_PORT = 8080


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
stdout_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)


DESCRIPTION = dedent("""
Simple webserver with the ability to send echoreply or generate random strings.
There are two API endpoints for the EchoServer and both are simple and easy to use:

GET /hello
- Response code: 200 OK
- Response body: 'hello'
- curl example: curl -XGET 'http://localhost:8080/hello'

GET /random
- Query parameters:
    - length (int | str, default is '10'): Length of the expected randomized string
    - digits (boolean | str, default is 'true'): Allow digits in the expected
                                                 randomized string
    - lowercase (boolean | str, default is 'true'): Allow lowercase ascii letters in
                                                    the expected randomized string
    - uppercase (boolean | str, default is 'false'): Allow uppercase ascii letters in
                                                     the expected randomized string
- Response code: 200 OK or 400 Bad Request if query params are invalid
- Response body: RANDOMIZED_STRING
- curl example: curl -XGET 'http://localhost:8080/random?length=20&digits=false&uppercase=True'
""")


def main(server_address: ServerAddress) -> None:
    if is_server_address_busy(host=server_address.host, port=server_address.port):
        logger.error('Failed to start the instance of EchoServer:\n'
                    f'Given address is already busy: {server_address}')
        return

    try:
        server_daemon = HTTPServer(server_address, EchoHandler)
        logger.info(
            'Starting EchoServer on the address: '
            f'"http://{server_address.host}:{server_address.port}" ...'
        )
        server_daemon.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        logger.exception(exc_info=e)
    finally:
        if 'server_daemon' in locals() and server_daemon:
            logger.info('Stopping EchoServer ...')
            server_daemon.server_close()
            logger.info('Stopped')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter, description=DESCRIPTION
    )
    parser.add_argument('--port', help=f'Port for server (default: {DEFAULT_PORT})',
                        default=DEFAULT_PORT, required=False)
    parser.add_argument('--bind', help='Bind server to a particular '
                                      f'IP address (default: "{DEFAULT_BIND}")',
                        default=DEFAULT_BIND, required=False)
    args = parser.parse_args()
    server_address = ServerAddress(str(args.bind), int(args.port))
    main(server_address)
