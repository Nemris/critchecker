""" Functions that handle DA deviations. """

import re


def extract_id(url: str) -> str:
    """
    Extract the ID from a deviation URL.

    Args:
        url: The URL to a deviation.

    Returns:
        The deviation ID.

    Raises:
        ValueError: If no deviation ID is found.
    """

    try:
        return re.search(r"https://www\.deviantart\.com/\w+/\w+/.+-(\d+)$", url).group(1)
    except AttributeError as exception:
        raise (f"'{url}': invalid deviation URL") from exception
