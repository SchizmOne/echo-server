import argparse
import logging
import sys
from http.server import HTTPServer

from echoserver.handler import EchoHandler
from echoserver.utils import ServerAddress


DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8080


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
stdout_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Simple Web Server with the ability to send echoreply or generate random strings'
    )
    parser.add_argument('--host', help='Host or address for server (default: "localhost")',
                        default=DEFAULT_HOST, required=False)
    parser.add_argument('--port', help='Port for server (default: 8080)',
                        default=DEFAULT_PORT, required=False)
    args = parser.parse_args()
    server_address = ServerAddress(str(args.host), int(args.port))

    try:
        server_daemon = HTTPServer(server_address, EchoHandler)
        logger.info(
            'Starting EchoServer on the address: '
            f'"http://{server_address.host}:{server_address.port}" ...'
        )
        server_daemon.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        logger.info('Stopping EchoServer ...')
        server_daemon.server_close()
        logger.info('Stopped')
