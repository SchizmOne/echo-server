import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlsplit

from echoserver.utils import generate_random_string


class EchoHandler(BaseHTTPRequestHandler):
    """The main handler of requests to EchoServer.
    """

    DEFAULT_ENCODING = sys.getfilesystemencoding()

    def _send_response(self, response_body: str) -> None:
        self.send_response(code=HTTPStatus.OK)
        self.send_header('Content-Type', f'text/html; charset={self.DEFAULT_ENCODING}')
        self.end_headers()
        self.wfile.write(bytes(response_body, encoding=self.DEFAULT_ENCODING))

    def do_GET(self) -> None:
        parsed_path = urlsplit(self.path)
        query = parse_qs(parsed_path.query)

        if parsed_path.path == '/random':
            parsed_query = {k: next(iter(v)) for k, v in query.items()}
            try:
                randomized_string = generate_random_string(**parsed_query)
                self._send_response(response_body=randomized_string)
            except (TypeError, ValueError) as err:
                self.send_error(
                    code=HTTPStatus.BAD_REQUEST,
                    message='Bad Request',
                    explain='The requested query parameters for the endpoint '
                            f'"/random" are wrong: {str(err)}'
                )
            return

        if parsed_path.path == '/hello':
            if len(query) != 0:
                self.send_error(
                    code=HTTPStatus.BAD_REQUEST,
                    message='Bad Request',
                    explain='The endpoint "/hello" does not support query parameters'
                )
                return
            self._send_response(response_body='hello')
            return

        self.send_error(
            code=HTTPStatus.NOT_IMPLEMENTED,
            message='Not Implemented',
            explain=f'The endpoint "{parsed_path.path}" does not exist. '
                     'Server cannot fulfill the request'
        )
