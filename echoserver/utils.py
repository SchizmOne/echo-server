import random
import socket
import string as s
import typing as t


class ServerAddress(t.NamedTuple):
    host: str
    port: int

    def __str__(self):
        return f'http://{self.host}:{self.port}'


def generate_random_string(
    length: t.Union[int, str] = 10,
    digits: t.Union[bool, str] = True,
    lowercase: t.Union[bool, str] = True,
    uppercase: t.Union[bool, str] = False,
) -> str:
    """This method generates and returns random string.

    Args:
        length (int | str): Length of the desired string
        digits (bool | str): Allow digits
        lowercase (bool | str): Allow lower case letters
        uppercase (bool | str): Allow upper case letters
    Returns:
        Generated random string
    """
    try:
        length = int(length)
    except ValueError as e:
        raise ValueError('Failed to convert the value of variable length to integer') from e

    charsets = [
        s.digits if (digits is True) or (isinstance(digits, str) and digits.lower() == 'true') else '',
        s.ascii_lowercase if (lowercase is True) or (isinstance(lowercase, str) and lowercase.lower() == 'true') else '',
        s.ascii_uppercase if (uppercase is True) or (isinstance(uppercase, str) and uppercase.lower() == 'true') else '',
    ]
    charset_for_random = ''.join(charsets)
    return ''.join(random.choice(charset_for_random) for _ in range(length))



def is_server_address_busy(host: str, port: int, timeout: int = 1) -> bool:
    """Checks if a given server address is open and listening.

    Args:
        host (str): The target host's IP address or hostname.
        port (int): The target port number.
        timeout (int): The timeout in seconds for the connection attempt.
                       (default: 1)

    Returns:
        True if the port is open and a connection can be established,
        False otherwise.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False
    finally:
        if 'sock' in locals() and sock:
            sock.close()
