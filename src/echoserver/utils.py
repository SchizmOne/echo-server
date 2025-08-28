import random
import string as s
import typing as t


class ServerAddress(t.NamedTuple):
    host: str
    port: int


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
        s.digits if (digits == True) or (isinstance(digits, str) and digits.lower() == 'true') else '',  # noqa
        s.ascii_lowercase if (lowercase == True) or (isinstance(lowercase, str) and lowercase.lower() == 'true') else '',  # noqa
        s.ascii_uppercase if (uppercase == True) or (isinstance(uppercase, str) and uppercase.lower() == 'true') else '',  # noqa
    ]
    charset_for_random = ''.join(charsets)
    return ''.join(random.choice(charset_for_random) for _ in range(length))
