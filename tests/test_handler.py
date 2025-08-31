import logging
import string
import sys
import unittest
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.parse import urljoin

import requests

from echoserver.handler import EchoHandler
from echoserver.utils import (
    is_server_address_busy,
    ServerAddress
)


DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8080


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
stdout_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)


class TestHandler(unittest.TestCase):

    def setUp(self):
        server_address = ServerAddress(DEFAULT_HOST, DEFAULT_PORT)
        if is_server_address_busy(host=server_address.host, port=server_address.port):
            self.fail('Failed to start the instance of EchoServer:\n'
                      f'Given address is already busy: {server_address}')

        self.server_address = server_address
        self.server_daemon = ThreadingHTTPServer(server_address, EchoHandler)
        self.server_thread = Thread(target=self.server_daemon.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.session = requests.sessions.Session()
        logger.info('Main thread with EchoServer has started...')

    def test_hello(self):
        response = self.session.get(url=urljoin(str(self.server_address), 'hello'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.text, 'hello')

    def test_random_default(self):
        allowed_chars = ''.join([string.ascii_lowercase, string.digits])
        response = self.session.get(url=urljoin(str(self.server_address), 'random'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response_string = response.text
        self.assertEqual(len(response_string), 10)
        self.assertTrue(all(char in allowed_chars for char in response_string))

    def tearDown(self):
        if getattr(self, 'server_daemon', None):
            logger.info('Stopping server...')
            self.server_daemon.shutdown()
            self.server_thread.join()
            logger.info('Server stopped successfully')
            self.server_daemon.server_close()
